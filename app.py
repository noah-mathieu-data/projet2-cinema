import numpy as np
import pandas as pd
import streamlit as st

from design import (
    appliquer_style, intro_hacker, effets_globaux, ecran_ouverture, pilules,
    fiche_film, cartes_recommandations, explorer_matrice, pied_de_page,
    a_l_affiche, salle_neuf,
)
from programmation import numero_semaine, programmer, seances, decor, lire_votes, ajouter_vote

FICHIER = "data/films_filtres.csv"
FICHIER_TMDB = "data/films_tmdb.csv"

st.set_page_config(page_title="Cinémaniak", page_icon="static/logo.png", layout="wide")


@st.cache_data
def charger_films(chemin, chemin_tmdb):
    films = pd.read_csv(chemin)
    tmdb = pd.read_csv(chemin_tmdb)
    films = films.merge(tmdb, on="tconst", how="left")
    films = films.sort_values("numVotes", ascending=False)
    films["libelle"] = films["primaryTitle"] + " (" + films["startYear"].astype(int).astype(str) + ")"

    # Petit décalage aléatoire pour que les points du graphique ne soient pas empilés
    hasard = np.random.default_rng(7)
    films["x"] = films["startYear"] + hasard.uniform(-0.45, 0.45, len(films))
    films["y"] = films["averageRating"] + hasard.uniform(-0.045, 0.045, len(films))
    return films


def recommander(films, film, nombre=6):
    # Recommandation simple en attendant le KNN : genres en commun, année et note proches
    genres_film = set(film["genres"].split(","))
    autres = films[films["tconst"] != film["tconst"]].copy()

    genres_autres = autres["genres"].str.split(",").apply(set)
    communs = genres_autres.apply(lambda g: len(g & genres_film))
    total = genres_autres.apply(lambda g: len(g | genres_film))
    score_genres = communs / total

    ecart_annee = (autres["startYear"] - film["startYear"]).abs().clip(upper=30)
    ecart_note = (autres["averageRating"] - film["averageRating"]).abs().clip(upper=4)

    autres["score"] = 0.6 * score_genres + 0.2 * (1 - ecart_annee / 30) + 0.2 * (1 - ecart_note / 4)
    return autres.sort_values(["score", "numVotes"], ascending=False).head(nombre)


def choisir(tconst):
    st.session_state["choix"] = tconst


def clic_matrice():
    points = st.session_state["matrice"]["selection"]["points"]
    if points:
        choisir(points[0]["customdata"][0])


def pilule_bleue():
    # Un grand classique culte au hasard
    classiques = films[(films["numVotes"] > 300000) & (films["averageRating"] >= 7.8)]
    choisir(classiques["tconst"].sample(1).iloc[0])


def pilule_rouge():
    # Une pépite cachée : très bien notée mais peu connue
    pepites = films[(films["numVotes"] < 60000) & (films["averageRating"] >= 7.5) & films["poster_path"].notna() & films["original_language"].isin(["en", "fr"])]
    choisir(pepites["tconst"].sample(1).iloc[0])


@st.cache_data
def programme_de_la_semaine(films, semaine):
    return programmer(films, semaine)


def voter(tconst):
    ajouter_vote(semaine, tconst)
    st.session_state["a_vote"] = tconst


films = charger_films(FICHIER, FICHIER_TMDB)
semaine = numero_semaine()
programme, candidats = programme_de_la_semaine(films, semaine)
libelles = dict(zip(films["tconst"], films["libelle"]))

# À chaque ouverture du site, un grand classique différent est affiché
if "choix" not in st.session_state:
    pilule_bleue()

appliquer_style()
intro_hacker()
effets_globaux()
ecran_ouverture(len(films))
pilules(pilule_bleue, pilule_rouge)
a_l_affiche(programme, choisir)
votes = lire_votes(semaine)
candidats_votes = candidats.copy()
candidats_votes["votes"] = [votes.get(t, 0) for t in candidats["tconst"]]
salle_neuf(candidats_votes, voter, st.session_state.get("a_vote"), decor)

choix = st.selectbox(
    "root@cinemaniak:~$ rechercher_film",
    films["tconst"],
    format_func=lambda t: libelles[t],
    key="choix",
)

film = films[films["tconst"] == choix].iloc[0]

# Le film est-il à l'affiche, candidat à la Salle 9 ou hors programmation ?
if film["tconst"] in programme["tconst"].values:
    rang = programme["tconst"].tolist().index(film["tconst"])
    salle = int(programme.iloc[rang]["salle"])
    fiche_film(film, "affiche", salle, seances(semaine, rang))
elif film["tconst"] in candidats["tconst"].values:
    fiche_film(film, "candidat")
else:
    fiche_film(film, "hors")

recos = recommander(films, film)
cartes_recommandations(recos, choisir)
explorer_matrice(films, film, recos, clic_matrice)

pied_de_page(len(films))
