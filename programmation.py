import json
from datetime import date, timedelta
from pathlib import Path

import numpy as np

FICHIER_VOTES = Path(__file__).parent / "data" / "votes_salle9.json"
JOURS = ["LUN", "MAR", "MER", "JEU", "VEN", "SAM", "DIM"]

# Décor de la Salle 9 selon le genre principal du film élu
DECORS = {
    "Sci-Fi": "néons et écrans géants sur les côtés de l'écran, fumée au sol, lumière froide",
    "Horror": "lumière rouge, brouillard dans les allées, sièges qui vibrent aux moments chocs",
    "Thriller": "salle plongée dans le noir, faisceaux de lampes torches, bande-son spatialisée",
    "Action": "son poussé à fond, sièges vibrants, lumières stroboscopiques pendant les poursuites",
    "Adventure": "lianes et caisses en bois dans le hall, carte au trésor sur chaque siège",
    "War": "filets de camouflage, sacs de sable à l'entrée, son de bataille à 360°",
    "Comedy": "photomaton avec déguisements du film, bonus pop-corn caramel",
    "Fantasy": "guirlandes lumineuses, fumée bleutée, costumes pour l'équipe du ciné",
}
DECOR_MATRIX = (
    "pluie de code verte sur des écrans géants de chaque côté de l'écran, "
    "Morpheus en carton à l'entrée, bonbons pilule rouge ou pilule bleue à l'accueil"
)


def numero_semaine():
    annee, semaine, _ = date.today().isocalendar()
    return annee * 100 + semaine


def programmer(films, semaine):
    # 15 films à l'affiche dans les salles 1 à 8 + 4 candidats au vote de la Salle 9
    # La sélection change automatiquement chaque lundi
    vivier = films[
        (films["numVotes"] > 150000)
        & (films["averageRating"] >= 7.4)
        & films["poster_path"].notna()
        & films["original_language"].isin(["en", "fr"])
    ]
    choisis = vivier.sample(19, random_state=semaine)
    programme = choisis.head(15).copy()
    programme["salle"] = [i % 8 + 1 for i in range(15)]
    candidats = choisis.tail(4).copy()
    return programme, candidats


def seances(semaine, rang):
    # Toujours les mêmes horaires pour un film donné pendant la semaine
    hasard = np.random.default_rng(semaine * 100 + rang)
    creneaux = ["14:00", "16:30", "19:15", "21:45"] if rang < 8 else ["13:45", "17:00", "20:30", "22:45"]
    jours = []
    for j in range(4):
        jour = date.today() + timedelta(days=j)
        nom = "AUJ." if j == 0 else f"{JOURS[jour.weekday()]} {jour.day}"
        nombre = int(hasard.integers(2, 4))
        heures = sorted(hasard.choice(creneaux, nombre, replace=False).tolist())
        jours.append([nom, heures])
    return jours


def decor(film):
    if film["tconst"] == "tt0133093":
        return DECOR_MATRIX
    genres = film["genres"].split(",")
    for genre in genres:
        if genre in DECORS:
            return DECORS[genre]
    return "décor aux couleurs du film et ambiance sonore sur mesure"


def lire_votes(semaine):
    try:
        tous = json.loads(FICHIER_VOTES.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        tous = {}
    return tous.get(str(semaine), {})


def ajouter_vote(semaine, tconst):
    try:
        tous = json.loads(FICHIER_VOTES.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        tous = {}
    votes = tous.setdefault(str(semaine), {})
    votes[tconst] = votes.get(tconst, 0) + 1
    FICHIER_VOTES.write_text(json.dumps(tous, indent=2), encoding="utf-8")
