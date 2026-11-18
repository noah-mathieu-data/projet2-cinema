import streamlit as st
import pandas as pd

from design import appliquer_style, intro_hacker, ecran_ouverture, nom_film, badges_genres

FICHIER = "data/films_filtres.csv"

st.set_page_config(page_title="Cinémaniak", page_icon="🟩", layout="wide")


@st.cache_data
def charger_films(chemin):
    films = pd.read_csv(chemin)
    films = films.sort_values("numVotes", ascending=False)
    films["libelle"] = films["primaryTitle"] + " (" + films["startYear"].astype(int).astype(str) + ")"
    return films


films = charger_films(FICHIER)
libelles = dict(zip(films["tconst"], films["libelle"]))

appliquer_style()
intro_hacker()
ecran_ouverture(len(films))

choix = st.selectbox(
    "> Entre un film que tu as aimé",
    films["tconst"],
    format_func=lambda t: libelles[t],
)

film = films[films["tconst"] == choix].iloc[0]

nom_film(film["primaryTitle"])
col1, col2, col3, col4 = st.columns(4)
col1.metric("ANNÉE", int(film["startYear"]))
col2.metric("NOTE IMDb", f"{film['averageRating']} / 10")
col3.metric("VOTES", f"{int(film['numVotes']):,}".replace(",", " "))
col4.metric("DURÉE", f"{int(film['runtimeMinutes'])} min")
badges_genres(film["genres"])

st.caption(f"Team Maniak · {len(films)} films au catalogue · Projet Wild Code School")