import json
import random
from pathlib import Path

import plotly.express as px
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

def effets_globaux():
    html = (DOSSIER / "effets.html").read_text(encoding="utf-8")
    components.html(html, height=1)


def intro_hacker():
    html = (DOSSIER / "intro.html").read_text(encoding="utf-8")
    components.html(html, height=1)


def fiche_film(film, statut="hors", salle=None, jours=None):
    html = (DOSSIER / "fiche.html").read_text(encoding="utf-8")

    resume = film["overview"] if isinstance(film["overview"], str) else ""
    if len(resume) > 230:
        resume = resume[:230].rsplit(" ", 1)[0] + "…"

    donnees = {
        "tconst": film["tconst"],
        "titre": film["primaryTitle"],
        "annee": int(film["startYear"]),
        "duree": int(film["runtimeMinutes"]),
        "langue": film["original_language"] if isinstance(film["original_language"], str) else "??",
        "genres": film["genres"].split(","),
        "note": float(film["averageRating"]),
        "votes": int(film["numVotes"]),
        "accroche": film["tagline"] if isinstance(film["tagline"], str) else "",
        "resume": resume,
        "affiche": "https://image.tmdb.org/t/p/w500" + film["poster_path"] if isinstance(film["poster_path"], str) else "",
        "fond": "https://image.tmdb.org/t/p/w1280" + film["backdrop_path"] if isinstance(film["backdrop_path"], str) else "",
        "statut": statut,
        "salle": salle,
        "jours": jours or [],
    }
    components.html(html.replace("DONNEES_FILM", json.dumps(donnees)), height=680)


def cartes_recommandations(recos, choisir):
    st.markdown(
        '<div class="recos-titre">&gt; ANALYSE TERMINÉE · '
        f'<span>{len(recos)} FILMS COMPATIBLES DÉTECTÉS</span><i class="curseur-recos"></i></div>',
        unsafe_allow_html=True,
    )
    colonnes = st.columns(len(recos))
    for i, (colonne, (_, reco)) in enumerate(zip(colonnes, recos.iterrows())):
        if isinstance(reco["poster_path"], str):
            image = f'<img src="https://image.tmdb.org/t/p/w342{reco["poster_path"]}" alt="">'
        else:
            image = '<div class="carte-perdu"><b>SIGNAL<br>PERDU</b></div>'
        signal = round(reco["score"] * 100)
        with colonne:
            st.markdown(
                f'<div class="carte" style="animation-delay:{0.15 * i:.2f}s">'
                f'<div class="carte-signal">SIGNAL {signal}%</div>'
                f'<div class="carte-image">{image}<div class="carte-reflet"></div></div>'
                f'<div class="carte-titre">{reco["primaryTitle"]}</div>'
                f'<div class="carte-infos">{int(reco["startYear"])} · ★ {reco["averageRating"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.button("▸ ANALYSER", key=f"voir_{reco['tconst']}", on_click=choisir,
                      args=(reco["tconst"],), width="stretch")


def pilules(pilule_bleue, pilule_rouge):
    st.markdown(
        '<div class="morpheus">« Prends la pilule bleue et tu regardes un grand classique. '
        'Prends la pilule rouge et je te montre jusqu\'où va le terrier du lapin blanc. »</div>',
        unsafe_allow_html=True,
    )
    gauche, droite = st.columns(2)
    with gauche:
        st.button("💊 PILULE BLEUE", key="pilule_bleue", on_click=pilule_bleue, width="stretch")
        st.markdown('<div class="pilule-texte bleu">UN CLASSIQUE CULTE AU HASARD</div>', unsafe_allow_html=True)
    with droite:
        st.button("💊 PILULE ROUGE", key="pilule_rouge", on_click=pilule_rouge, width="stretch")
        st.markdown('<div class="pilule-texte rouge">UNE PÉPITE CACHÉE DE LA MATRICE</div>', unsafe_allow_html=True)


def explorer_matrice(films, film, recos, clic_matrice):
    st.markdown(
        '<div class="recos-titre">&gt; EXPLORER LA MATRICE · '
        '<span>CHAQUE POINT EST UN FILM DU CATALOGUE</span></div>'
        '<div class="matrice-aide">Le film choisi brille en blanc, ses films compatibles sont reliés. '
        'Clique sur un point pour ouvrir son dossier.</div>',
        unsafe_allow_html=True,
    )
    fig = px.scatter(
        films, x="x", y="y", hover_name="primaryTitle", custom_data=["tconst", "startYear", "averageRating"],
        render_mode="webgl", height=560,
    )
    fig.update_traces(
        marker=dict(size=4, color="rgba(0, 255, 65, 0.28)"),
        hovertemplate="%{hovertext}<br>%{customdata[1]:.0f} · ★ %{customdata[2]}<extra></extra>",
    )

    # Les traits entre le film choisi et ses recommandations
    for _, reco in recos.iterrows():
        fig.add_scatter(
            x=[film["x"], reco["x"]], y=[film["y"], reco["y"]], mode="lines", hoverinfo="skip",
            line=dict(color="rgba(232, 255, 232, 0.55)", width=1.5, dash="dot"), showlegend=False,
        )
    fig.add_scatter(
        x=recos["x"], y=recos["y"], mode="markers", showlegend=False, hovertext=recos["primaryTitle"],
        customdata=recos[["tconst", "startYear", "averageRating"]].values,
        hovertemplate="%{hovertext}<br>%{customdata[1]:.0f} · ★ %{customdata[2]}<extra></extra>",
        marker=dict(size=13, color="#00FF41", line=dict(color="#E8FFE8", width=1.5)),
    )
    fig.add_scatter(
        x=[film["x"]], y=[film["y"]], mode="markers", showlegend=False, hovertext=[film["primaryTitle"]],
        customdata=[[film["tconst"], film["startYear"], film["averageRating"]]],
        hovertemplate="%{hovertext}<br>%{customdata[1]:.0f} · ★ %{customdata[2]}<extra></extra>",
        marker=dict(size=24, color="#FFFFFF", symbol="star", line=dict(color="#00FF41", width=2)),
    )
    fig.update_layout(
        paper_bgcolor="rgba(0, 0, 0, 0)", plot_bgcolor="rgba(0, 12, 3, 0.75)",
        font=dict(family="VT323, monospace", size=18, color="#7CFC9A"),
        margin=dict(l=10, r=10, t=10, b=10), dragmode="pan",
        hoverlabel=dict(bgcolor="#001a07", bordercolor="#00FF41", font=dict(family="VT323, monospace", size=20, color="#E8FFE8")),
        xaxis=dict(title="ANNÉE DE SORTIE", gridcolor="rgba(0, 255, 65, 0.08)", zeroline=False, tickfont=dict(size=18)),
        yaxis=dict(title="NOTE IMDb", gridcolor="rgba(0, 255, 65, 0.08)", zeroline=False, tickfont=dict(size=18), range=[5.8, 9.7]),
    )
    st.plotly_chart(
        fig, key="matrice", on_select=clic_matrice, selection_mode="points",
        config={"displayModeBar": False, "scrollZoom": True},
    )


def pied_de_page(nb_films):
    nb = f"{nb_films:,}".replace(",", " ")
    st.markdown(
        f'''<div class="pied">
<div>&gt; CINÉMANIAK · LE CINÉ DES FILMS CULTES · ANGERS</div>
<div>&gt; catalogue : {nb} films · mise à jour quotidienne de la Matrice</div>
<div>&gt; équipe : Team Maniak · Noah · Clémence · Sébastien · Jordan · Pierre</div>
<div>&gt; Projet 2 · Wild Code School · 2026</div>
<div class="pied-fin">&gt; déconnexion<i class="curseur-recos"></i></div>
</div>''',
        unsafe_allow_html=True,
    )


def affiche(film, taille="w342"):
    if isinstance(film["poster_path"], str):
        return f'<img src="https://image.tmdb.org/t/p/{taille}{film["poster_path"]}" alt="">'
    return '<div class="carte-perdu"><b>SIGNAL<br>PERDU</b></div>'


def a_l_affiche(programme, choisir):
    st.markdown(
        '<div class="recos-titre">&gt; À L\'AFFICHE CETTE SEMAINE · '
        '<span>8 SALLES · 15 FILMS</span><i class="curseur-recos"></i></div>'
        '<div class="matrice-aide">La programmation change chaque lundi. Clique sur un film pour ouvrir son dossier et réserver.</div>',
        unsafe_allow_html=True,
    )
    lignes = [programme.iloc[:8], programme.iloc[8:]]
    for numero, ligne in enumerate(lignes):
        colonnes = st.columns(8)
        for i, (_, film) in enumerate(ligne.iterrows()):
            with colonnes[i]:
                st.markdown(
                    f'<div class="carte petite" style="animation-delay:{0.06 * (numero * 8 + i):.2f}s">'
                    f'<div class="carte-signal">SALLE {film["salle"]}</div>'
                    f'<div class="carte-image">{affiche(film, "w185")}<div class="carte-reflet"></div></div>'
                    f'<div class="carte-titre">{film["primaryTitle"]}</div></div>',
                    unsafe_allow_html=True,
                )
                st.button("▸ DOSSIER", key=f"prog_{film['tconst']}", on_click=choisir,
                          args=(film["tconst"],), width="stretch")
        if numero == 1:
            with colonnes[7]:
                st.markdown(
                    '<div class="carte petite neuf"><div class="carte-signal">SALLE 9</div>'
                    '<div class="carte-image neuf-image"><b>?</b><span>FILM ÉLU<br>PAR VOUS</span></div>'
                    '<div class="carte-titre">Jeudi 21:00 · vote ci-dessous</div></div>',
                    unsafe_allow_html=True,
                )


def salle_neuf(candidats, voter, a_vote, decor):
    total = int(candidats["votes"].sum())
    tete = candidats.sort_values("votes", ascending=False).iloc[0]
    st.markdown(
        '<div class="recos-titre neuf-titre">&gt; SALLE 9 · <span>LA SALLE IMMERSIVE</span></div>'
        '<div class="matrice-aide">Chaque semaine, vous élisez le film projeté jeudi à 21:00 dans la Salle 9. '
        'La salle est entièrement décorée aux couleurs du film gagnant. Un vote par visite.</div>',
        unsafe_allow_html=True,
    )
    colonnes = st.columns([1, 1, 1, 1, 2.2])
    for colonne, (_, film) in zip(colonnes[:4], candidats.iterrows()):
        part = round(100 * film["votes"] / total) if total else 0
        en_tete = total > 0 and film["tconst"] == tete["tconst"]
        with colonne:
            st.markdown(
                f'<div class="carte neuf{" gagnant" if en_tete else ""}">'
                f'<div class="carte-signal">{"★ EN TÊTE" if en_tete else "CANDIDAT"}</div>'
                f'<div class="carte-image">{affiche(film)}<div class="carte-reflet"></div></div>'
                f'<div class="carte-titre">{film["primaryTitle"]}</div>'
                f'<div class="jauge-vote"><i style="width:{part}%"></i></div>'
                f'<div class="carte-infos">{part} % · {int(film["votes"])} vote{"s" if film["votes"] > 1 else ""}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if a_vote == film["tconst"]:
                st.button("✔ TON VOTE", key=f"vote_{film['tconst']}", disabled=True, width="stretch")
            else:
                st.button("▲ VOTER", key=f"vote_{film['tconst']}", on_click=voter, args=(film["tconst"],),
                          disabled=a_vote is not None, width="stretch")
    if total:
        texte = f'<b>{tete["primaryTitle"]}</b> est en tête. Décor prévu : {decor(tete)}.'
    else:
        texte = "Aucun vote pour l\'instant. Sois le premier à choisir le film de jeudi !"
    with colonnes[4]:
        st.markdown(
            '<div class="decor"><div class="decor-titre">&gt; LA SALLE 9 CETTE SEMAINE</div>'
            '<div class="decor-ligne">▸ Séance unique jeudi à 21:00</div>'
            '<div class="decor-ligne">▸ Résultat du vote dimanche à minuit</div>'
            '<div class="decor-ligne">▸ Seaux à pop-corn collector aux couleurs du film</div>'
            f'<div class="decor-texte">&gt; {texte}</div></div>',
            unsafe_allow_html=True,
        )
