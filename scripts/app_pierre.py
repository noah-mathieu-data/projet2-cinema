from pathlib import Path

import streamlit as st
import pandas as pd
import reco

DOSSIER = Path(__file__).parent.parent    # la racine du projet (scripts/ est un cran plus bas)

st.set_page_config(page_title="Que voir ensuite ?", page_icon="🎬")


def libelle(film):
    texte = f"{film['title']} ({int(film['startYear'])})"
    # titre original seulement s'il existe et s'il est différent
    if pd.notna(film["original_title"]) and film["original_title"] != film["title"]:
        texte = texte + " — " + film["original_title"]
    return texte


@st.cache_resource
def preparer_moteur():
    films = pd.read_csv(DOSSIER / "data" / "films_prepares.csv")
    films["libelle"] = films.apply(libelle, axis=1)
    X = reco.preparer_caracteristiques(films)
    modele = reco.creer_modele(X)
    return films, X, modele


films, X, modele = preparer_moteur()


def afficher_libelle(i):
    return films["libelle"][i]


def url_affiche(chemin):
    if pd.isna(chemin):
        return "app/static/affiche_manquante.png"    # servie par Streamlit
    return "https://image.tmdb.org/t/p/w342" + chemin


def afficher_ligne(voisins):
    colonnes = st.columns(5)
    for k in range(len(voisins)):
        j = voisins.index[k]    # position du film dans le catalogue
        with colonnes[k]:
            # affiche cliquable : un lien qui recharge l'appli sur ce film
            st.markdown(f'<a href="?film={j}" target="_self">'
                        f'<img src="{url_affiche(films["poster_path"][j])}" '
                        f'style="width:100%; border-radius:8px;"></a>',
                        unsafe_allow_html=True)
            st.caption(films["libelle"][j])


st.title("🎬 Que voir ensuite ?")

# film demandé dans l'adresse (après un clic sur une affiche)
depart = None
if "film" in st.query_params:
    depart = int(st.query_params["film"])

i_film = st.selectbox("Un film que vous avez aimé :", films.index,
                      format_func=afficher_libelle,
                      index=depart, placeholder="Tapez le titre d'un film…")

if i_film is not None:
    tconst = films["tconst"][i_film]
    st.caption("Cliquez sur une affiche pour voir les films qui lui ressemblent.")

    st.subheader("Dans le même esprit")
    proches = reco.recommander(tconst, films, X, modele, nb=5)
    afficher_ligne(proches)

    st.subheader("Pour changer un peu")
    voisins = reco.recommander(tconst, films, X, modele, nb=30)
    plus_loin = voisins.iloc[14:30]    # voisins de rang 15 à 30
    afficher_ligne(plus_loin.sample(5, random_state=i_film))
