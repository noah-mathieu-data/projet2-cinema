"""Chargement du catalogue et modèle partagé par le notebook et Streamlit."""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MultiLabelBinarizer

ROOT = Path(__file__).resolve().parent
POIDS = {"genres": 0.4, "resume": 0.4, "annee": 0.1, "duree": 0.1}


def filtrer_catalogue(films, *, genres=None, annees=None, duree_max=None, note_min=None):
    """Combiner les critères. Plusieurs genres sont acceptés au choix."""
    masque = pd.Series(True, index=films.index)
    if genres:
        genres_choisis = set(genres)
        masque &= films["genres"].fillna("").map(
            lambda valeur: bool({g.strip() for g in valeur.split(",")} & genres_choisis)
        )
    if annees is not None:
        masque &= pd.to_numeric(films["startYear"], errors="coerce").between(*annees)
    if duree_max is not None:
        masque &= pd.to_numeric(films["runtimeMinutes"], errors="coerce").le(duree_max)
    if note_min is not None and note_min > 0:
        masque &= pd.to_numeric(films["averageRating"], errors="coerce").ge(note_min)
    return films.loc[masque].copy()


def charger_catalogue():
    """Enrichir la sélection existante avec les résumés TMDB, par morceaux."""
    chemin = ROOT / "data" / "films_selection.csv"
    if not chemin.exists():
        raise FileNotFoundError(f"Préparez d'abord la sélection de films : {chemin}")
    films = pd.read_csv(chemin, dtype={"tconst": "string"})
    films = films.dropna(subset=["tconst"]).copy()
    films["tconst"] = films["tconst"].str.strip()
    films = films[films["tconst"].str.fullmatch(r"tt\d+", na=False)]
    films = films.drop_duplicates("tconst").reset_index(drop=True)
    films["title"] = films["title"].fillna(films["primaryTitle"])
    for colonne in ["startYear", "runtimeMinutes", "averageRating", "numVotes"]:
        films[colonne] = pd.to_numeric(films[colonne], errors="coerce")

    chemins_tmdb = [ROOT / "data" / "TMDB_movie_dataset_v11.csv",
                    ROOT.parent / "Docs" / "TMDB_movie_dataset_v11.csv"]
    chemin_tmdb = next((p for p in chemins_tmdb if p.exists()), None)
    films["overview"] = ""
    films["backdrop_path"] = ""
    if chemin_tmdb is not None:
        morceaux = []
        identifiants = set(films["tconst"])
        for morceau in pd.read_csv(
            chemin_tmdb, usecols=["imdb_id", "overview", "vote_count", "backdrop_path"],
            dtype={"imdb_id": "string"}, chunksize=100_000,
        ):
            morceau["imdb_id"] = morceau["imdb_id"].str.strip()
            morceaux.append(morceau[morceau["imdb_id"].isin(identifiants)])
        resumes = pd.concat(morceaux, ignore_index=True)
        resumes["vote_count"] = pd.to_numeric(resumes["vote_count"], errors="coerce")
        resumes = resumes.sort_values("vote_count", ascending=False).drop_duplicates("imdb_id")
        films["overview"] = films["tconst"].map(resumes.set_index("imdb_id")["overview"]).fillna("")
        films["backdrop_path"] = films["tconst"].map(resumes.set_index("imdb_id")["backdrop_path"]).fillna("")

    films["poster_url"] = films["poster_path"].fillna("").map(
        lambda chemin: "https://image.tmdb.org/t/p/w500" + chemin if chemin.startswith("/") else ""
    )
    films.attrs["source_resumes"] = str(chemin_tmdb) if chemin_tmdb else None
    return films


class ModeleRecommandation:
    """Comparer séparément les quatre critères, puis pondérer leurs similarités."""

    def __init__(self, films):
        if films.empty or films["tconst"].isna().any() or not films["tconst"].is_unique:
            raise ValueError("Le catalogue doit contenir des identifiants uniques et renseignés.")
        self.films = films.copy().reset_index(drop=True)
        self.genres = self.films["genres"].fillna("").map(
            lambda valeur: set(g.strip() for g in valeur.split(",") if g.strip())
        )
        self.encodeur_genres = MultiLabelBinarizer(sparse_output=True)
        self.matrice_genres = self.encodeur_genres.fit_transform(self.genres)
        self.vectoriseur = TfidfVectorizer(
            stop_words="english", max_features=20_000, sublinear_tf=True, dtype=np.float32,
        )
        # Les résumés fournis sont majoritairement anglais. Un catalogue multilingue
        # demanderait une préparation linguistique adaptée.
        self.matrice_resumes = None
        textes = self.films["overview"].fillna("")
        if textes.str.contains(r"\b\w\w+\b", regex=True).any():
            try:
                self.matrice_resumes = self.vectoriseur.fit_transform(textes)
            except ValueError as erreur:
                if "empty vocabulary" not in str(erreur):
                    raise

    def recommander(self, tconst, nombre=5, *, candidats=None):
        if tconst not in set(self.films["tconst"]):
            raise ValueError("Ce film ne figure pas dans le catalogue.")
        if not isinstance(nombre, int) or nombre < 1:
            raise ValueError("Le nombre de recommandations doit être un entier positif.")
        index = self.films.index[self.films["tconst"] == tconst][0]
        scores = np.zeros(len(self.films))
        poids_disponibles = np.zeros(len(self.films))
        contributions = {}
        for nom, matrice in [("genres", self.matrice_genres), ("resume", self.matrice_resumes)]:
            valeurs = np.zeros(len(self.films))
            disponibles = np.zeros(len(self.films), dtype=bool)
            if matrice is not None and matrice.shape[1] > 0 and matrice[index].nnz:
                valeurs = cosine_similarity(matrice[index], matrice).ravel()
                disponibles = np.asarray(matrice.getnnz(axis=1)).ravel() > 0
            contributions[nom] = valeurs
            scores += POIDS[nom] * valeurs
            poids_disponibles += POIDS[nom] * disponibles

        for nom, colonne, ecart in [("annee", "startYear", 30), ("duree", "runtimeMinutes", 90)]:
            nombres = pd.to_numeric(self.films[colonne], errors="coerce").to_numpy(dtype=float)
            disponibles = np.isfinite(nombres) & np.isfinite(nombres[index])
            valeurs = np.zeros(len(nombres))
            valeurs[disponibles] = np.clip(1 - np.abs(nombres[disponibles] - nombres[index]) / ecart, 0, 1)
            contributions[nom] = valeurs
            scores += POIDS[nom] * valeurs
            poids_disponibles += POIDS[nom] * disponibles

        resultat = self.films.copy()
        # Un critère manquant apporte zéro point pour éviter de favoriser les fiches
        # incomplètes face à celles dont les quatre critères sont comparables.
        resultat["similarite"] = np.clip(scores / sum(POIDS.values()), 0, 1)
        resultat = resultat[(resultat["tconst"] != tconst) & (poids_disponibles > 0)]
        if candidats is not None:
            resultat = resultat[resultat["tconst"].isin(candidats)]
        resultat = resultat.sort_values(
            ["similarite", "averageRating", "numVotes", "tconst"],
            ascending=[False, False, False, True], na_position="last",
        ).head(nombre)
        explications = []
        for autre in resultat.index:
            raisons = []
            communs = sorted(self.genres[index] & self.genres[autre])
            if communs:
                raisons.append("Genres communs · " + ", ".join(communs))
            if contributions["resume"][autre] > 0.05:
                raisons.append("Vocabulaire des résumés proche")
            if contributions["annee"][autre] >= 0.8:
                raisons.append("Époque de sortie proche")
            if contributions["duree"][autre] >= 0.9:
                raisons.append("Durée proche")
            explications.append(". ".join(raisons) or "Ressemblance limitée sur les critères disponibles")
        resultat["explication"] = explications
        return resultat.reset_index(drop=True)

    def decouvrir(self, nombre=5, *, candidats=None):
        """Sélection sans film de départ, classée par note IMDb pondérée."""
        if not isinstance(nombre, int) or nombre < 1:
            raise ValueError("Le nombre de suggestions doit être un entier positif.")
        films = self.films.copy()
        notes = pd.to_numeric(films["averageRating"], errors="coerce")
        votes = pd.to_numeric(films["numVotes"], errors="coerce").fillna(0).clip(lower=0)
        moyenne = notes.mean() if notes.notna().any() else 0
        seuil = max(float(votes.median()), 1)
        films["score_qualite"] = (
            votes / (votes + seuil) * notes.fillna(moyenne)
            + seuil / (votes + seuil) * moyenne
        )
        if candidats is not None:
            films = films[films["tconst"].isin(candidats)]
        films = films.sort_values(
            ["score_qualite", "numVotes", "tconst"], ascending=[False, False, True],
        ).head(nombre)
        films["explication"] = [
            f"{note:.1f}/10 sur IMDb · {int(votes.loc[index]):,} votes".replace(",", " ")
            if pd.notna(note) else "Note IMDb indisponible"
            for index, note in notes.loc[films.index].items()
        ]
        return films.reset_index(drop=True)
