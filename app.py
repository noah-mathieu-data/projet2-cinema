import numpy as np
import pandas as pd
import streamlit as st
import reco

from design import (
    appliquer_style, intro_hacker, effets_globaux, ecran_ouverture, pilules,
    fiche_film, cartes_recommandations, explorer_matrice, pied_de_page,
    a_l_affiche, salle_neuf, oracle, duel, salle_des_machines,
    tableau_seances, decryptage, terminal, ma_liste, bouton_liste,
)
import html
from pathlib import Path
import random
from datetime import datetime
from programmation import numero_semaine, programmer, seances, decor, lire_votes, ajouter_vote, FICHIER_VOTES
from operateur import (
    fenetre_connexion, bandeau_annonce, signal_evenement, salle_de_controle, compter, forces, lire, ecrire,
    journal, appliquer_ambiance,
)
import streamlit.components.v1 as components

FICHIER = "data/films_selection.csv"
FICHIER_TMDB = "data/films_tmdb.csv"
DOSSIER_ASSETS = Path(__file__).parent / "assets"

# En mode opérateur, tout le site passe du vert à l'or
OPERATEUR_CSS = """
.stApp { filter: hue-rotate(-78deg) saturate(1.25) brightness(1.05); }
.annonce { border-color: #00FF41 !important; background: rgba(0, 40, 10, 0.75) !important; }
.annonce-defile { color: #00FF41 !important; text-shadow: 0 0 8px #00FF41 !important; }
.bandeau-operateur { position: fixed; top: 0; left: 50%; transform: translateX(-50%); z-index: 999992; padding: 4px 22px;
  background: rgba(0, 0, 0, 0.9); border: 1px solid #00FF41; border-top: none; color: #00FF41; letter-spacing: 0.25em; font-size: 1.1rem;
  text-shadow: 0 0 8px #00FF41; animation: clignote-recos 1.6s steps(1) infinite; }
"""

st.set_page_config(page_title="Cinémaniak", page_icon="static/logo.png", layout="wide", initial_sidebar_state="collapsed")


@st.cache_data
def charger_films(chemin, chemin_tmdb):
    films = pd.read_csv(chemin)

    # Titres français (travail de Clémence) : on affiche le titre français partout
    # et on garde le titre original à côté
    films = films.rename(columns={"title": "titre_fr"})
    films["titre_original"] = films["primaryTitle"]
    films["primaryTitle"] = films["titre_fr"].fillna(films["primaryTitle"])

    # On ajoute les infos TMDB sans dupliquer les colonnes déjà présentes
    tmdb = pd.read_csv(chemin_tmdb)
    tmdb = tmdb.drop(columns=[c for c in tmdb.columns if c in films.columns and c != "tconst"])
    films = films.merge(tmdb, on="tconst", how="left")
    films = films.sort_values("numVotes", ascending=False)

    # Le libellé de la recherche contient les deux titres : on peut taper l'un ou l'autre
    annee = " (" + films["startYear"].astype(int).astype(str) + ")"
    films["libelle"] = films["primaryTitle"] + annee
    different = films["titre_original"] != films["primaryTitle"]
    films.loc[different, "libelle"] = films["primaryTitle"] + annee + " · " + films["titre_original"]

    # Petit décalage aléatoire pour que les points du graphique ne soient pas empilés
    hasard = np.random.default_rng(7)
    films["x"] = films["startYear"] + hasard.uniform(-0.45, 0.45, len(films))
    films["y"] = films["averageRating"] + hasard.uniform(-0.045, 0.045, len(films))
    return films


@st.cache_resource
def preparer_moteur(_films):
    # Moteur de recommandation de Pierre (reco.py) : on calcule une seule fois le vecteur de chaque film
    base = _films.reset_index(drop=True)
    base["keywords"] = base["keywords"].fillna("")
    X = reco.preparer_caracteristiques(base)
    modele = reco.creer_modele(X)
    return base, X, modele


def recommander(films, film, nombre=6):
    base, X, modele = preparer_moteur(films)
    i = base.index[base["tconst"] == film["tconst"]][0]
    distances, indices = modele.kneighbors(X.iloc[[i]], n_neighbors=nombre + 1)
    voisins = base.iloc[indices[0]].copy()
    voisins["score"] = 1 - distances[0]
    return voisins[voisins["tconst"] != film["tconst"]].head(nombre)


def choisir(tconst):
    st.session_state["choix"] = tconst


def clic_matrice():
    points = st.session_state["matrice"]["selection"]["points"]
    if points:
        choisir(points[0]["customdata"][0])


PROPHETIES = {
    "😱 Frissonner": ["Tu ne dormiras pas tout de suite ce soir. Et ce n'est pas grave.",
                     "Ce que tu crains n'est pas dans le noir. Il est dans ce film."],
    "😂 Rire": ["Tu vas rire si fort que tes voisins voudront savoir quel film tu regardes.",
               "Le plus dur ce soir sera de ne pas recracher ton pop-corn."],
    "🚀 Décoller": ["Ton esprit va quitter cette pièce. Ton corps restera sur le canapé.",
                   "Après ce film, tu regarderas le ciel autrement."],
    "💥 De l'adrénaline": ["Ton cœur va battre plus vite que la musique. Accroche-toi.",
                          "Tu vas vouloir courir après le générique. Ne le fais pas dans le salon."],
}
GENRES_HUMEUR = {
    "😱 Frissonner": "Horror|Thriller",
    "😂 Rire": "Comedy",
    "🚀 Décoller": "Sci-Fi|Adventure",
    "💥 De l'adrénaline": "Action|War",
}
EPOQUES = {"📼 70-80": (1970, 1989), "💿 90-2000": (1990, 2009), "📱 2010 et +": (2010, 2100)}


def consulter_oracle():
    humeur = st.session_state.get("q_humeur") or "🚀 Décoller"
    epoque = st.session_state.get("q_epoque") or "💿 90-2000"
    compagnie = st.session_state.get("q_compagnie") or "👥 Entre potes"
    debut, fin = EPOQUES[epoque]

    choix = films[films["genres"].str.contains(GENRES_HUMEUR[humeur]) & films["startYear"].between(debut, fin)]
    choix = choix[choix["poster_path"].notna() & choix["original_language"].isin(["en", "fr"])]
    if compagnie == "🧍 Seul":
        filtre = choix[(choix["numVotes"] < 200000) & (choix["averageRating"] >= 7.2)]
    else:
        filtre = choix[choix["numVotes"] >= 200000]
    if len(filtre) > 0:
        choix = filtre
    film = choix.sample(1).iloc[0]
    compter("oracle")
    journal(f"🔮 L'Oracle prédit {film['primaryTitle']}")
    st.session_state["oracle"] = (film["tconst"], random.choice(PROPHETIES[humeur]))


# ---------- Tableau des séances ----------
def film_salle_neuf():
    # Le film choisi par l'opérateur, sinon celui en tête des votes
    force = forces().get("salle9", {}).get(str(semaine))
    if force in candidats["tconst"].values:
        return candidats[candidats["tconst"] == force].iloc[0], "★ ÉLU"
    votes = lire_votes(semaine)
    if votes and max(votes.get(t, 0) for t in candidats["tconst"]) > 0:
        meilleur = max(candidats["tconst"], key=lambda t: votes.get(t, 0))
        return candidats[candidats["tconst"] == meilleur].iloc[0], "EN TÊTE"
    return None, ""


def lignes_tableau():
    maintenant = datetime.now()
    lignes = []
    for salle in range(1, 9):
        meilleur = None
        for rang, (_, f) in enumerate(programme.iterrows()):
            if f["salle"] != salle:
                continue
            jours = seances(semaine, rang)
            for decalage, (nom, heures) in enumerate(jours[:2]):
                for heure in heures:
                    h, m = map(int, heure.split(":"))
                    debut = maintenant.replace(hour=h, minute=m, second=0, microsecond=0) + pd.Timedelta(days=decalage)
                    fin = debut + pd.Timedelta(minutes=int(f["runtimeMinutes"]))
                    if fin < maintenant:
                        continue
                    # On affiche en priorité la prochaine séance qui n'a pas encore commencé
                    a_venir = debut > maintenant
                    if meilleur is None or (a_venir and not meilleur[5]) or (a_venir == meilleur[5] and debut < meilleur[0]):
                        meilleur = (debut, fin, f, decalage, heure, a_venir)
        if meilleur is None:
            continue
        debut, fin, f, decalage, heure, _ = meilleur
        if debut <= maintenant:
            statut = "EN COURS"
        elif decalage > 0:
            statut = "DEMAIN"
        elif (debut - maintenant).total_seconds() < 20 * 60:
            statut = "EMBARQUEMENT"
        elif (semaine + salle * 7 + debut.hour) % 5 == 0:
            statut = "COMPLET"
        else:
            statut = "À L'HEURE"
        lignes.append({"salle": f"{salle:02d}", "film": f["primaryTitle"], "heure": heure, "statut": statut})
    elu, statut_elu = film_salle_neuf()
    if elu is not None:
        lignes.append({"salle": "09", "film": elu["primaryTitle"], "heure": "21:00", "statut": "ÉLU · JEUDI" if statut_elu == "★ ÉLU" else "EN TÊTE"})
    else:
        lignes.append({"salle": "09", "film": "FILM ÉLU PAR LE PUBLIC", "heure": "21:00", "statut": "VOTE OUVERT"})
    return lignes


# ---------- Décryptage ----------
def nouvelle_partie():
    st.session_state["partie"] = random.randint(0, 10**6)


def manches_decryptage(graine):
    vivier = films[(films["numVotes"] > 250000) & films["poster_path"].notna()]
    tirage = vivier.sample(5, random_state=graine)
    manches = []
    for i, (_, f) in enumerate(tirage.iterrows()):
        faux = vivier[vivier["tconst"] != f["tconst"]].sample(3, random_state=graine + i)["primaryTitle"].tolist()
        choix = faux + [f["primaryTitle"]]
        random.Random(graine + i).shuffle(choix)
        manches.append({"affiche": "https://image.tmdb.org/t/p/w342" + f["poster_path"], "bon": f["primaryTitle"], "choix": choix})
    return manches


# ---------- Terminal de l'opérateur ----------
GENRES_FR = {"action": "Action", "horreur": "Horror", "thriller": "Thriller", "sf": "Sci-Fi", "science-fiction": "Sci-Fi",
             "aventure": "Adventure", "guerre": "War", "comedie": "Comedy", "comédie": "Comedy", "drame": "Drama",
             "crime": "Crime", "fantastique": "Fantasy", "animation": "Animation", "romance": "Romance"}


def liste_films(selection):
    st.session_state["derniere_liste"] = selection["tconst"].tolist()
    return [f"[{i + 1}] {html.escape(f['primaryTitle'])} · {int(f['startYear'])} · ★ {f['averageRating']}"
            for i, (_, f) in enumerate(selection.iterrows())]


def executer():
    commande = st.session_state["commande"].strip()
    st.session_state["commande"] = ""
    if not commande:
        return
    mots = commande.lower().split()
    ordre, reste = mots[0], " ".join(mots[1:])
    if ordre == "aide":
        sortie = ["<b>top &lt;genre&gt;</b> · les 5 meilleurs films d'un genre (action, horreur, sf, comedie, guerre…)",
                  "<b>annee &lt;AAAA&gt;</b> · les 5 films les plus vus d'une année",
                  "<b>cherche &lt;mot&gt;</b> · les films dont le titre contient ce mot",
                  "<b>hasard</b> · un film tiré au sort",
                  "<b>stats</b> · les chiffres clés du catalogue",
                  "<b>ouvre &lt;n&gt;</b> · ouvre le dossier du film n de la dernière liste",
                  "<b>effacer</b> · vide l'écran"]
    elif ordre == "top" and reste in GENRES_FR:
        selection = films[films["genres"].str.contains(GENRES_FR[reste]) & (films["numVotes"] > 50000)]
        sortie = liste_films(selection.sort_values("averageRating", ascending=False).head(5))
    elif ordre == "annee" and reste.isdigit():
        selection = films[films["startYear"] == int(reste)]
        sortie = liste_films(selection.head(5)) if len(selection) else [f"Aucun film de {reste} dans la Matrice."]
    elif ordre == "cherche" and reste:
        selection = films[films["primaryTitle"].str.lower().str.contains(reste, regex=False)
                          | films["titre_original"].str.lower().str.contains(reste, regex=False)]
        sortie = liste_films(selection.head(5)) if len(selection) else [f"Aucun titre ne contient « {html.escape(reste)} »."]
    elif ordre == "hasard":
        sortie = liste_films(films.sample(1))
    elif ordre == "stats":
        sortie = [f"films ........... {len(films)}",
                  f"note moyenne .... {films['averageRating'].mean():.2f} / 10",
                  f"durée moyenne ... {films['runtimeMinutes'].mean():.0f} min",
                  f"plus ancien ..... {int(films['startYear'].min())}",
                  f"plus récent ..... {int(films['startYear'].max())}",
                  f"meilleur film ... {html.escape(films.sort_values('averageRating').iloc[-1]['primaryTitle'])}"]
    elif ordre == "ouvre" and reste.isdigit() and 0 < int(reste) <= len(st.session_state.get("derniere_liste", [])):
        choisir(st.session_state["derniere_liste"][int(reste) - 1])
        sortie = ["Ouverture du dossier… remonte voir la fiche."]
    elif ordre == "effacer":
        st.session_state["historique"] = []
        return
    else:
        sortie = [f"Commande inconnue : {html.escape(commande)}. Tape <b>aide</b>."]
    st.session_state.setdefault("historique", []).append((html.escape(commande), sortie))


# ---------- Ma liste ----------
def basculer_liste():
    liste = st.session_state.setdefault("liste", [])
    tconst = st.session_state["choix"]
    if tconst in liste:
        liste.remove(tconst)
    else:
        liste.append(tconst)


def retirer_liste(tconst):
    st.session_state.setdefault("liste", []).remove(tconst)


def pilule_bleue_cliquee():
    compter("pilules", "bleue")
    journal("💊 Pilule bleue avalée")
    pilule_bleue()


def pilule_rouge_cliquee():
    compter("pilules", "rouge")
    journal("💊 Pilule rouge avalée")
    pilule_rouge()


def pilule_bleue():
    # Un grand classique culte au hasard
    classiques = films[(films["numVotes"] > 300000) & (films["averageRating"] >= 7.8)]
    choisir(classiques["tconst"].sample(1).iloc[0])


def pilule_rouge():
    # Une pépite cachée : très bien notée mais peu connue
    pepites = films[(films["numVotes"] < 60000) & (films["averageRating"] >= 7.5) & films["poster_path"].notna() & films["original_language"].isin(["en", "fr"])]
    choisir(pepites["tconst"].sample(1).iloc[0])


@st.cache_data
def programme_de_la_semaine(films, semaine, choix_operateur):
    programme, candidats = programmer(films, semaine)
    # Si l'opérateur a choisi lui-même les films principaux des 8 salles, on les met à la place
    if choix_operateur:
        for rang, tconst in enumerate(choix_operateur[:8]):
            ligne = films[films["tconst"] == tconst].iloc[0].copy()
            ligne["salle"] = rang + 1
            programme.iloc[rang] = ligne[programme.columns]
    return programme, candidats


def effacer_votes():
    tous = lire(FICHIER_VOTES, {})
    tous.pop(str(semaine), None)
    ecrire(FICHIER_VOTES, tous)


def voter(tconst):
    ajouter_vote(semaine, tconst)
    journal(f"🗳️ Vote Salle 9 : {libelles.get(tconst, tconst)}")
    st.session_state["a_vote"] = tconst


films = charger_films(FICHIER, FICHIER_TMDB)
semaine = numero_semaine()
programme, candidats = programme_de_la_semaine(films, semaine, tuple(forces().get("programme", {}).get(str(semaine), [])))
libelles = dict(zip(films["tconst"], films["libelle"]))

# À chaque ouverture du site, un grand classique différent est affiché
if "choix" not in st.session_state:
    compter("visites")
    journal("🟢 Nouveau visiteur connecté")
    pilule_bleue()
    st.session_state["duel_a"] = st.session_state["choix"]
    pilule_bleue()
    st.session_state["duel_b"] = st.session_state["choix"]
    st.session_state["choix"] = st.session_state["duel_a"]

appliquer_style()
intro_hacker()
effets_globaux()
ecran_ouverture(len(films))
bandeau_annonce()
signal_evenement()
appliquer_ambiance()
if st.session_state.get("operateur"):
    st.markdown('<style>' + OPERATEUR_CSS + '</style><div class="bandeau-operateur">⚠ ACCÈS NIVEAU 5 · BIENVENUE, ' + html.escape(str(st.secrets["operateur"].get("identifiant", "")).upper()) + '</div>',
                unsafe_allow_html=True)
    salle_de_controle(films, libelles, programme, candidats, semaine, lire_votes(semaine), effacer_votes, seances)
pilules(pilule_bleue_cliquee, pilule_rouge_cliquee)
tableau_seances(lignes_tableau())
a_l_affiche(programme, choisir, *film_salle_neuf())
votes = lire_votes(semaine)
candidats_votes = candidats.copy()
candidats_votes["votes"] = [votes.get(t, 0) for t in candidats["tconst"]]
salle_neuf(candidats_votes, voter, st.session_state.get("a_vote"), decor, forces().get("salle9", {}).get(str(semaine)))

resultat = None
if "oracle" in st.session_state:
    tconst_oracle, prophetie = st.session_state["oracle"]
    resultat = (films[films["tconst"] == tconst_oracle].iloc[0], prophetie)
oracle(consulter_oracle, resultat, choisir)

st.markdown('<div id="sec-recherche"></div>', unsafe_allow_html=True)
choix = st.selectbox(
    "root@cinemaniak:~$ rechercher_film",
    films["tconst"],
    format_func=lambda t: libelles[t],
    key="choix",
)

film = films[films["tconst"] == choix].iloc[0]
if st.session_state.get("dernier_compte") != choix:
    st.session_state["dernier_compte"] = choix
    compter("films", choix)
    journal(f"📁 Dossier ouvert : {film['primaryTitle']}")

# Le film est-il à l'affiche, candidat à la Salle 9 ou hors programmation ?
if film["tconst"] in programme["tconst"].values:
    rang = programme["tconst"].tolist().index(film["tconst"])
    salle = int(programme.iloc[rang]["salle"])
    fiche_film(film, "affiche", salle, seances(semaine, rang))
elif film["tconst"] in candidats["tconst"].values:
    fiche_film(film, "candidat")
else:
    fiche_film(film, "hors")

bouton_liste(film["tconst"] in st.session_state.get("liste", []), basculer_liste)

recos = recommander(films, film)
cartes_recommandations(recos, choisir)
ma_liste(st.session_state.get("liste", []), films, choisir, retirer_liste)
explorer_matrice(films, film, recos, clic_matrice)
duel(films, libelles)
if "partie" not in st.session_state:
    nouvelle_partie()
decryptage(manches_decryptage(st.session_state["partie"]), nouvelle_partie)
terminal(st.session_state.get("historique", []), executer)
salle_des_machines(films)

pied_de_page(len(films))
fenetre_connexion()

# Animations d'entrée et de sortie du mode opérateur (jouées une seule fois)
if st.session_state.pop("scan", False):
    nom = html.escape(str(st.secrets["operateur"].get("identifiant", "opérateur")).upper())
    components.html((DOSSIER_ASSETS / "scan.html").read_text(encoding="utf-8").replace("NOM_OPERATEUR", nom), height=1)
if st.session_state.pop("lancer_demo", False):
    components.html("<script>setTimeout(function(){try{window.parent.cinemaniakDemo();}catch(e){}}, 600);</script>", height=1)
if st.session_state.pop("sortie_operateur", False):
    components.html("<script>try{window.parent.cinemaniakGlitch();}catch(e){}</script>", height=1)
