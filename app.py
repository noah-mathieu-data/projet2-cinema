"""Lancer avec python -m streamlit run app.py depuis le dossier du projet."""
from html import escape
from urllib.parse import quote

import pandas as pd
import streamlit as st

from recommandation import ROOT, ModeleRecommandation, charger_catalogue, filtrer_catalogue

st.set_page_config(
    page_title="Ciné Maniak · Films que vous aimerez", page_icon="🎬",
    layout="wide", initial_sidebar_state="collapsed",
)
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo+Black&family=DM+Sans:wght@400;500;600;700&display=swap');
[data-testid="stAppViewContainer"] {background: #141414;}
[data-testid="stMainBlockContainer"] {
    max-width: 1540px; padding: 1.5rem 3.5rem 4rem;
    font-family: "DM Sans", sans-serif;
}
[data-testid="stHeader"] {background: transparent;}
[data-testid="stToolbar"] {visibility: hidden;}
.cinema-nav {display: flex; align-items: center; gap: 2.5rem; min-height: 48px;}
.cinema-nav .cinema-brand {
    font-family: "Archivo Black", sans-serif; font-size: 1.65rem;
    letter-spacing: -0.06em; color: #e50914 !important; text-decoration: none;
}
.cinema-nav a {color: #dedede; text-decoration: none; font-size: 0.9rem;}
.cinema-nav a:hover {color: #ffffff; text-decoration: underline;}
.cinema-nav .cinema-brand:hover {text-decoration: none;}
.cinema-location {margin-left: auto; color: #aaaaaa; font-size: 0.85rem;}
.cinema-hero {
    min-height: 420px; display: flex; align-items: center;
    margin: 0 -3.5rem; padding: 3rem 3.5rem 4rem;
    background-color: #1c1c1c; background-size: cover; background-position: center 35%;
}
.hero-copy {max-width: 540px;}
.hero-eyebrow {color: #d2d2d2; font-size: 0.8rem; letter-spacing: 0.16em; text-transform: uppercase;}
.cinema-hero h1 {
    font-family: "Archivo Black", sans-serif; font-size: clamp(2.5rem, 5vw, 4.7rem);
    color: #ffffff; line-height: 1.05; letter-spacing: -0.045em; margin: 0.8rem 0;
}
.hero-meta {color: #dedede; font-size: 0.95rem; margin: 1.2rem 0 0.7rem;}
.hero-note {color: #85d69b; font-weight: 700;}
.hero-description {color: #e1e1e1; font-size: 1rem; line-height: 1.6; max-width: 475px;}
.hero-action {
    display: inline-block; background: #ffffff; color: #141414 !important;
    padding: 0.7rem 1.35rem; margin-top: 0.75rem; border-radius: 4px;
    font-size: 0.95rem; font-weight: 700; text-decoration: none;
}
.hero-action:hover {background: #dedede; text-decoration: none;}
h2 {font-family: "DM Sans", sans-serif; font-size: 1.65rem; font-weight: 700; letter-spacing: -0.025em;}
.st-key-exemples button {width: 100%; min-height: 44px; border-radius: 4px;}
.st-key-exemples button p {font-size: 0.9rem;}
.st-key-exemples button[kind="primary"] {background: #e50914; border-color: #e50914;}
.st-key-recherche {background: #1b1b1b; padding: 1.1rem; border-radius: 6px;}
[data-testid="stBaseButton-primary"] {background: #e50914; border-color: #e50914; border-radius: 4px;}
[data-testid="stBaseButton-primary"]:hover {background: #c80812; border-color: #c80812;}
.st-key-recommandations [data-testid="stImage"] {
    overflow: hidden; border-radius: 4px; background: #202020;
}
.st-key-recommandations [data-testid="stImage"] img {
    aspect-ratio: 2 / 3; object-fit: contain; background: #202020;
    transition: transform 180ms ease;
}
.st-key-recommandations [data-testid="stImage"]:hover img {transform: scale(1.035);}
.film-title {font-size: 1rem; font-weight: 700; line-height: 1.35; margin: 0.8rem 0 0.3rem; color: #ffffff;}
.film-meta {color: #b2b2b2; font-size: 0.875rem; margin-bottom: 0.65rem;}
.film-reason {font-size: 0.9rem; color: #d0d0d0; line-height: 1.5;}
.poster-missing {
    aspect-ratio: 2 / 3; display: flex; align-items: center; justify-content: center;
    padding: 1rem; border: 1px solid #333333; border-radius: 4px;
    background: #202020; color: #b2b2b2; text-align: center;
}
@media (max-width: 640px) {
    [data-testid="stMainBlockContainer"] {padding: 4rem 1.1rem 3rem;}
    .cinema-nav {gap: 1rem; flex-wrap: wrap; padding-bottom: 0.5rem;}
    .cinema-nav .cinema-brand {font-size: 1.35rem;}
    .cinema-nav a:not(.cinema-brand) {font-size: 0.8rem;}
    .cinema-location {display: none;}
    .cinema-hero {
        margin: 0 -1.1rem; padding: 3rem 1.1rem 2.5rem; min-height: 390px;
        background-position: 60% center;
    }
    .hero-description {font-size: 0.95rem;}
    .st-key-exemples [data-testid="stHorizontalBlock"] {
        display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.65rem;
    }
    .st-key-exemples [data-testid="stColumn"] {width: 100%; min-width: 0;}
    .st-key-recommandations [data-testid="stHorizontalBlock"] {
        display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1.5rem 0.8rem;
    }
    .st-key-recommandations [data-testid="stColumn"] {width: 100%; min-width: 0;}
    .film-title {font-size: 0.95rem;}
    .film-reason {font-size: 0.85rem;}
}
@media (prefers-reduced-motion: reduce) {
    .st-key-recommandations [data-testid="stImage"] img {transition: none;}
}
</style>""", unsafe_allow_html=True)


@st.cache_resource(show_spinner="Préparation du catalogue et des ressemblances…")
def charger_modele(signature):
    return ModeleRecommandation(charger_catalogue())


def choisir_exemple(identifiant):
    st.session_state["film_choisi"] = identifiant
    st.session_state.pop("film_recommande", None)


sources = [ROOT / "recommandation.py", ROOT / "data" / "films_selection.csv", ROOT / "data" / "TMDB_movie_dataset_v11.csv",
           ROOT.parent / "Docs" / "TMDB_movie_dataset_v11.csv"]
signature = tuple((str(p), p.stat().st_mtime_ns, p.stat().st_size) for p in sources if p.exists())

st.markdown(
    '<nav class="cinema-nav" aria-label="Navigation principale">'
    '<a class="cinema-brand" href="#accueil">CINÉ MANIAK</a>'
    '<a href="#films-que-vous-aimerez">Films que vous aimerez</a>'
    '<a href="#recherche">Rechercher</a>'
    '<span class="cinema-location">Angers</span></nav>',
    unsafe_allow_html=True,
)

try:
    modele = charger_modele(signature)
except (FileNotFoundError, ValueError, KeyError) as erreur:
    st.error(f"Le catalogue ne peut pas être chargé. {erreur}")
    st.stop()

films = modele.films
identifiant_hero = st.session_state.get("film_choisi") or "tt1375666"
selection_hero = films[films["tconst"].eq(identifiant_hero)]
film_hero = selection_hero.iloc[0] if not selection_hero.empty else films.iloc[0]
chemin_fond = film_hero.get("backdrop_path", "")
image_hero = "https://image.tmdb.org/t/p/w1280" + chemin_fond if chemin_fond else film_hero["poster_url"]
image_hero = quote(image_hero, safe="/:")
resume_hero = film_hero["overview"] or "Des films cultes à découvrir sur grand écran au Ciné Maniak."
if len(resume_hero) > 230:
    resume_hero = resume_hero[:230].rsplit(" ", 1)[0] + "…"
annee_hero = str(int(film_hero["startYear"])) if pd.notna(film_hero["startYear"]) else ""
duree_hero = f'{int(film_hero["runtimeMinutes"])} min' if pd.notna(film_hero["runtimeMinutes"]) else ""
note_hero = f'{film_hero["averageRating"]:.1f}/10 IMDb' if pd.notna(film_hero["averageRating"]) else ""
contexte_hero = "Votre film de départ" if st.session_state.get("film_choisi") else "À découvrir"
st.markdown(
    f'<section id="accueil" class="cinema-hero" style="background-image:'
    f"linear-gradient(90deg,rgba(20,20,20,.98),rgba(20,20,20,.65)45%,rgba(20,20,20,.1)),"
    f"linear-gradient(0deg,#141414,transparent 50%),url('{image_hero}')"
    f'"><div class="hero-copy"><p class="hero-eyebrow">{contexte_hero}</p>'
    f'<h1>{escape(film_hero["title"])}</h1>'
    f'<p class="hero-meta"><span class="hero-note">{note_hero}</span> · {annee_hero} · {duree_hero}</p>'
    f'<p class="hero-description">{escape(resume_hero)}</p>'
    '<a class="hero-action" href="#recherche">Choisir un film</a></div></section>',
    unsafe_allow_html=True,
)
if not films["overview"].fillna("").str.strip().ne("").any():
    st.info("Les résumés sont indisponibles. Les recommandations utilisent les genres, l’année et la durée.")

libelles = {}
for film in films.itertuples():
    annee = str(int(film.startYear)) if pd.notna(film.startYear) else "année inconnue"
    libelles[film.tconst] = f"{film.title} ({annee}) · {film.tconst}"

# Des films du catalogue pour démarrer une recherche en un clic.
exemples = films.set_index("tconst").reindex(
    ["tt1375666", "tt0133093", "tt0816692", "tt0081505"]
).dropna(subset=["title"]).reset_index()
if not exemples.empty:
    with st.container(key="exemples"):
        for colonne, film in zip(st.columns(len(exemples), gap="small"), exemples.itertuples()):
            with colonne:
                st.button(
                    film.title, key=f"exemple_{film.tconst}", on_click=choisir_exemple,
                    args=(film.tconst,),
                    type="primary" if st.session_state.get("film_choisi") == film.tconst else "secondary",
                    width="stretch",
                )

st.markdown('<div id="recherche"></div>', unsafe_allow_html=True)
with st.container(border=True, key="recherche"):
    choix = st.selectbox(
        "Un film que vous aimez (facultatif)", list(libelles), format_func=libelles.get,
        index=None, key="film_choisi", placeholder="Saisissez un titre…",
    )
    with st.expander("Affiner les suggestions"):
        genres_fr = {
            "Action": "Action", "Adventure": "Aventure", "Animation": "Animation",
            "Biography": "Biographie", "Comedy": "Comédie", "Crime": "Policier",
            "Documentary": "Documentaire", "Drama": "Drame", "Family": "Famille",
            "Fantasy": "Fantastique", "History": "Histoire", "Horror": "Horreur",
            "Music": "Musique", "Musical": "Comédie musicale", "Mystery": "Mystère",
            "Romance": "Romance", "Sci-Fi": "Science-fiction", "Sport": "Sport",
            "Thriller": "Thriller", "War": "Guerre", "Western": "Western",
        }
        genres_disponibles = sorted(modele.encodeur_genres.classes_, key=lambda g: genres_fr.get(g, g))
        genres_choisis = st.multiselect(
            "Genres souhaités", genres_disponibles, format_func=lambda g: genres_fr.get(g, g),
            key="genres_souhaites", help="Un film doit correspondre à au moins un des genres choisis.",
            placeholder="Tous les genres",
        )
        bornes_annees = (int(films["startYear"].min()), int(films["startYear"].max()))
        annees = st.slider(
            "Années de sortie", *bornes_annees, value=bornes_annees, key="annees_souhaitees",
        )
        colonne_duree, colonne_note = st.columns(2)
        with colonne_duree:
            duree_max = st.selectbox(
                "Durée maximale", [0, 90, 120, 150, 180], key="duree_max",
                format_func=lambda v: "Toutes les durées" if not v else f"{v} minutes",
            )
        with colonne_note:
            note_min = st.selectbox(
                "Note IMDb minimale", [0.0, 6.5, 7.0, 7.5, 8.0], key="note_min",
                format_func=lambda v: "Toutes les notes" if v == 0 else f"{v:.1f}/10",
            )
    recherche_lancee = st.button(
        "Films que vous aimerez", type="primary", key="recommander",
    )

if recherche_lancee:
    st.session_state["film_recommande"] = choix

films_eligibles = filtrer_catalogue(
    films, genres=genres_choisis, annees=annees if annees != bornes_annees else None,
    duree_max=duree_max or None, note_min=note_min,
)
candidats = set(films_eligibles["tconst"])
st.subheader("Films que vous aimerez", anchor="films-que-vous-aimerez")

if st.session_state.get("film_recommande") == choix and choix is not None:
    resultats = modele.recommander(choix, candidats=candidats)
    titre_choisi = films.loc[films["tconst"].eq(choix), "title"].iloc[0]
    st.caption(f"Parce que vous avez aimé {titre_choisi}")
    candidats.discard(choix)
else:
    resultats = modele.decouvrir(candidats=candidats)
    st.caption("Pour découvrir le catalogue, une sélection classée selon les notes et le nombre de votes IMDb.")

st.caption(f"{len(candidats):,} films correspondent aux critères.".replace(",", " "))
if resultats.empty:
    st.info("Aucun film à proposer avec ces critères. Élargissez la période, la durée ou les genres, ou baissez la note minimale.")
else:
    if len(resultats) < 5:
        st.info(f"{len(resultats)} suggestion(s) disponible(s). Élargissez les critères pour en découvrir davantage.")
    with st.container(key="recommandations"):
        for colonne, (_, film) in zip(st.columns(max(1, len(resultats))), resultats.iterrows()):
            with colonne:
                if film["poster_url"]:
                    st.image(film["poster_url"], width="stretch")
                else:
                    st.markdown('<div class="poster-missing">Affiche indisponible</div>', unsafe_allow_html=True)
                st.markdown(f'<p class="film-title">{escape(film["title"])}</p>', unsafe_allow_html=True)
                annee = str(int(film["startYear"])) if pd.notna(film["startYear"]) else "Année inconnue"
                duree = f"{int(film['runtimeMinutes'])} min" if pd.notna(film["runtimeMinutes"]) else "Durée inconnue"
                st.markdown(f'<p class="film-meta">{annee} · {duree}</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="film-reason">{escape(film["explication"])}</p>', unsafe_allow_html=True)
                with st.expander("Résumé"):
                    st.write(film["overview"] or "Résumé indisponible")

