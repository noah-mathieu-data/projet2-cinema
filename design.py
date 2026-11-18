import random
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


DOSSIER = Path(__file__).parent / "assets"
SIGNES = "ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ0123456789"


def appliquer_style():
    css = (DOSSIER / "style.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

    random.seed(7)
    gouttes = ""
    for i in range(45):
        texte = "".join(random.choice(SIGNES) for _ in range(28))
        gouttes += (
            f'<div class="goutte" style="left:{i * 2.25}vw; '
            f'animation-duration:{random.uniform(7, 18):.1f}s; '
            f'animation-delay:{random.uniform(-18, 0):.1f}s; '
            f'font-size:{random.choice([13, 15, 17, 20])}px;">{texte}</div>'
        )
    st.markdown(f'<div class="pluie">{gouttes}</div>', unsafe_allow_html=True)


def ecran_ouverture(nb_films):
    html = (DOSSIER / "ouverture.html").read_text(encoding="utf-8")
    nb = f"{nb_films:,}".replace(",", " ")
    components.html(html.replace("NB_FILMS", nb), height=420)


def nom_film(titre):
    st.markdown(f'<div class="nom-film">▸ {titre}</div>', unsafe_allow_html=True)


def badges_genres(genres):
    badges = "".join(f'<span class="badge">{g}</span>' for g in genres.split(","))
    st.markdown(badges, unsafe_allow_html=True)

def intro_hacker():
    html = (DOSSIER / "intro.html").read_text(encoding="utf-8")
    components.html(html, height=1)