import json
import random
from pathlib import Path

import numpy as np
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
        "original": film["titre_original"] if film["titre_original"] != film["primaryTitle"] else "",
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
        '<div class="recos-titre" id="sec-recos">&gt; ANALYSE TERMINÉE · '
        f'<span>{len(recos)} FILMS COMPATIBLES DÉTECTÉS</span><i class="curseur-recos"></i></div>',
        unsafe_allow_html=True,
    )
    colonnes = st.container(key="recos").columns(len(recos))
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
        '<div class="recos-titre" id="sec-matrice">&gt; EXPLORER LA MATRICE · '
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
        font=dict(family="Matrix Sans Video, monospace", size=18, color="#7CFC9A"),
        margin=dict(l=10, r=10, t=10, b=10), dragmode="pan",
        hoverlabel=dict(bgcolor="#001a07", bordercolor="#00FF41", font=dict(family="Matrix Sans Video, monospace", size=20, color="#E8FFE8")),
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
<div class="meteo-matrice">&gt; météo de la Matrice : …</div>
<div class="pied-fin">&gt; déconnexion<i class="curseur-recos"></i></div>
</div>''',
        unsafe_allow_html=True,
    )


def affiche(film, taille="w342"):
    if isinstance(film["poster_path"], str):
        return f'<img src="https://image.tmdb.org/t/p/{taille}{film["poster_path"]}" alt="">'
    return '<div class="carte-perdu"><b>SIGNAL<br>PERDU</b></div>'


def a_l_affiche(programme, choisir, elu=None, statut_elu=""):
    st.markdown(
        '<div class="recos-titre" id="sec-affiche">&gt; À L\'AFFICHE CETTE SEMAINE · '
        '<span>8 SALLES · 15 FILMS</span><i class="curseur-recos"></i></div>'
        '<div class="matrice-aide">La programmation change chaque lundi. Clique sur un film pour ouvrir son dossier et réserver.</div>',
        unsafe_allow_html=True,
    )
    lignes = [programme.iloc[:8], programme.iloc[8:]]
    zone = st.container(key="programme")
    for numero, ligne in enumerate(lignes):
        colonnes = zone.columns(8)
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
                if elu is not None:
                    # Le film élu (ou en tête du vote) prend sa place dans la Salle 9
                    st.markdown(
                        f'<div class="carte petite neuf gagnant"><div class="carte-signal">SALLE 9 · {statut_elu}</div>'
                        f'<div class="carte-image">{affiche(elu, "w185")}<div class="carte-reflet"></div></div>'
                        f'<div class="carte-titre">{elu["primaryTitle"]}</div></div>',
                        unsafe_allow_html=True,
                    )
                    st.button("▸ DOSSIER", key=f"prog9_{elu['tconst']}", on_click=choisir, args=(elu["tconst"],), width="stretch")
                else:
                    st.markdown(
                        '<div class="carte petite neuf"><div class="carte-signal">SALLE 9</div>'
                        '<div class="carte-image neuf-image"><b>?</b><span>FILM ÉLU<br>PAR VOUS</span></div>'
                        '<div class="carte-titre">Jeudi 21:00 · vote ci-dessous</div></div>',
                        unsafe_allow_html=True,
                    )


def salle_neuf(candidats, voter, a_vote, decor, force=None):
    total = int(candidats["votes"].sum())
    tete = candidats.sort_values("votes", ascending=False).iloc[0]
    if force in candidats["tconst"].values:
        tete = candidats[candidats["tconst"] == force].iloc[0]
    st.markdown(
        '<div class="recos-titre neuf-titre" id="sec-salle9">&gt; SALLE 9 · <span>LA SALLE IMMERSIVE</span></div>'
        '<div class="matrice-aide">Chaque semaine, vous élisez le film projeté jeudi à 21:00 dans la Salle 9. '
        'La salle est entièrement décorée aux couleurs du film gagnant. Un vote par visite.</div>',
        unsafe_allow_html=True,
    )
    colonnes = st.container(key="salle9").columns([1, 1, 1, 1, 2.2])
    for colonne, (_, film) in zip(colonnes[:4], candidats.iterrows()):
        part = round(100 * film["votes"] / total) if total else 0
        en_tete = (total > 0 or force is not None) and film["tconst"] == tete["tconst"]
        with colonne:
            st.markdown(
                f'<div class="carte neuf{" gagnant" if en_tete else ""}">'
                f'<div class="carte-signal">{("★ ÉLU" if force else "★ EN TÊTE") if en_tete else "CANDIDAT"}</div>'
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
    if force in candidats["tconst"].values:
        texte = f'<b>{tete["primaryTitle"]}</b> a été choisi par l\'équipe du Cinémaniak. Décor prévu : {decor(tete)}.'
    elif total:
        texte = f'<b>{tete["primaryTitle"]}</b> est en tête. Décor prévu : {decor(tete)}.'
    else:
        texte = "Aucun vote pour l\'instant. Sois le premier à choisir le film de jeudi !"
    with colonnes[4]:
        st.markdown(
            '<div class="decor"><div class="decor-titre">&gt; LA SALLE 9 CETTE SEMAINE</div>'
            '<div class="decor-ligne">▸ Séance unique jeudi à 21:00 · dans <span class="cm-compte" data-cible="jeudi"></span></div>'
            '<div class="decor-ligne">▸ Vote clos dimanche à minuit · dans <span class="cm-compte" data-cible="dimanche"></span></div>'
            '<div class="decor-ligne">▸ Seaux à pop-corn collector aux couleurs du film</div>'
            f'<div class="decor-texte">&gt; {texte}</div></div>',
            unsafe_allow_html=True,
        )


def style_graphe(fig, hauteur=320):
    # Habillage Matrix commun à tous les graphiques Plotly
    fig.update_layout(
        height=hauteur, paper_bgcolor="rgba(0, 0, 0, 0)", plot_bgcolor="rgba(0, 12, 3, 0.75)",
        font=dict(family="Matrix Sans Video, monospace", size=17, color="#7CFC9A"),
        margin=dict(l=10, r=10, t=40, b=10), showlegend=False,
        title=dict(font=dict(size=21, color="#00FF41")),
        hoverlabel=dict(bgcolor="#001a07", bordercolor="#00FF41", font=dict(family="Matrix Sans Video, monospace", size=19, color="#E8FFE8")),
        xaxis=dict(gridcolor="rgba(0, 255, 65, 0.08)", zeroline=False),
        yaxis=dict(gridcolor="rgba(0, 255, 65, 0.08)", zeroline=False),
    )
    fig.update_traces(marker_color="#00FF41", marker_line_color="#003b10", marker_line_width=1)
    return fig


def oracle(consulter, resultat, choisir):
    st.markdown(
        '<div class="recos-titre oracle-titre" id="sec-oracle">&gt; L\'ORACLE · '
        '<span>ELLE SAIT DÉJÀ CE QUE TU VAS REGARDER</span></div>'
        '<div class="matrice-aide">Réponds à ses trois questions. Et prends un cookie, ils sortent du four.</div>',
        unsafe_allow_html=True,
    )
    with st.container(key="oracle"):
        q1, q2, q3 = st.columns(3)
        with q1:
            st.pills("CE SOIR TU VEUX…", ["😱 Frissonner", "😂 Rire", "🚀 Décoller", "💥 De l'adrénaline"],
                     key="q_humeur", default="🚀 Décoller")
        with q2:
            st.pills("TON ÉPOQUE", ["📼 70-80", "💿 90-2000", "📱 2010 et +"], key="q_epoque", default="💿 90-2000")
        with q3:
            st.pills("AVEC QUI ?", ["🧍 Seul", "👥 Entre potes"], key="q_compagnie", default="👥 Entre potes")
        st.button("🔮 CONSULTER L'ORACLE", key="consulter_oracle", on_click=consulter, width="stretch")

    if resultat:
        film, prophetie = resultat
        gauche, droite = st.columns([1, 4])
        with gauche:
            st.markdown(f'<div class="carte oracle-carte"><div class="carte-image">{affiche(film)}</div></div>',
                        unsafe_allow_html=True)
        with droite:
            st.markdown(
                f'<div class="prophetie"><div class="prophetie-titre">&gt; PROPHÉTIE</div>'
                f'<div class="prophetie-texte">« {prophetie} »</div>'
                f'<div class="prophetie-film">{film["primaryTitle"]} <small>({int(film["startYear"])} · ★ {film["averageRating"]})</small></div></div>',
                unsafe_allow_html=True,
            )
            st.button("▸ OUVRIR LE DOSSIER", key="oracle_dossier", on_click=choisir, args=(film["tconst"],))


def duel(films, libelles):
    st.markdown(
        '<div class="recos-titre" id="sec-duel">&gt; DUEL · <span>DEUX FILMS ENTRENT, UN SEUL SORT</span></div>',
        unsafe_allow_html=True,
    )
    gauche, droite = st.columns(2)
    with gauche:
        a = st.selectbox("JOUEUR 1", films["tconst"], format_func=lambda t: libelles[t], key="duel_a")
    with droite:
        b = st.selectbox("JOUEUR 2", films["tconst"], format_func=lambda t: libelles[t], key="duel_b")
    fa = films[films["tconst"] == a].iloc[0]
    fb = films[films["tconst"] == b].iloc[0]

    # Seuls les critères qui disent si un film est meilleur comptent pour le duel
    def score_culte(f):
        # La note pondérée par la popularité : un 8/10 vu par 2 millions de personnes pèse plus qu'un 8/10 vu par 10 000
        return round(float(f["averageRating"]) * np.log10(int(f["numVotes"])), 1)

    criteres = [
        ("NOTE IMDb", float(fa["averageRating"]), float(fb["averageRating"]), "{:.1f}", 5),
        ("SPECTATEURS", int(fa["numVotes"]), int(fb["numVotes"]), "{:,}", 0),
        ("SCORE CULTE", score_culte(fa), score_culte(fb), "{:.1f}", 25),
    ]
    points_a = points_b = 0
    lignes = ""
    for i, (nom, va, vb, forme, base) in enumerate(criteres):
        # Les barres partent d'un plancher pour que les écarts se voient bien
        plus_grand = (max(va, vb) - base) or 1
        gagne_a, gagne_b = va > vb, vb > va
        points_a += gagne_a
        points_b += gagne_b
        lignes += (
            f'<div class="duel-ligne" style="animation-delay:{0.3 + i * 0.25:.2f}s">'
            f'<div class="duel-val{" gagne" if gagne_a else ""}">{forme.format(va).replace(",", " ")}</div>'
            f'<div class="duel-barre gauche"><i style="width:{max(4, 100 * (va - base) / plus_grand):.0f}%"></i></div>'
            f'<div class="duel-nom">{nom}</div>'
            f'<div class="duel-barre"><i style="width:{max(4, 100 * (vb - base) / plus_grand):.0f}%"></i></div>'
            f'<div class="duel-val{" gagne" if gagne_b else ""}">{forme.format(vb).replace(",", " ")}</div></div>'
        )
    if points_a == points_b:
        verdict = "ÉGALITÉ PARFAITE · LA MATRICE N'A PAS PU TRANCHER"
    else:
        vainqueur = fa if points_a > points_b else fb
        verdict = f"VAINQUEUR : {vainqueur['primaryTitle'].upper()} · {max(points_a, points_b)} – {min(points_a, points_b)}"
    st.markdown(
        f'''<div class="duel">
<div class="duel-tete"><div class="duel-joueur"><div class="duel-affiche">{affiche(fa)}</div><div class="duel-fiche">{int(fa["startYear"])} · {int(fa["runtimeMinutes"])} min</div></div><div class="duel-vs">VS</div><div class="duel-joueur"><div class="duel-affiche">{affiche(fb)}</div><div class="duel-fiche">{int(fb["startYear"])} · {int(fb["runtimeMinutes"])} min</div></div></div>
{lignes}
<div class="duel-verdict">&gt; {verdict}</div>
<div class="duel-aide">Score culte = note × popularité. L'année et la durée sont affichées pour info, elles ne comptent pas.</div></div>''',
        unsafe_allow_html=True,
    )


def salle_des_machines(films):
    st.markdown(
        '<div class="recos-titre" id="sec-machines">&gt; LA SALLE DES MACHINES · '
        '<span>CE QUE CACHE LE CATALOGUE</span></div>',
        unsafe_allow_html=True,
    )
    with st.expander("▸ OUVRIR LA SALLE DES MACHINES"):
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("FILMS", f"{len(films):,}".replace(",", " "))
        k2.metric("NOTE MOYENNE", f"{films['averageRating'].mean():.1f} / 10")
        k3.metric("DURÉE MOYENNE", f"{films['runtimeMinutes'].mean():.0f} min")
        k4.metric("VOTES CUMULÉS", f"{films['numVotes'].sum() / 1e6:.0f} M")

        decennies = (films["startYear"] // 10 * 10).astype(int).value_counts().sort_index()
        genres = films["genres"].str.split(",").explode().value_counts().head(10).sort_values()
        notes_genre = (
            films.assign(genre=films["genres"].str.split(",")).explode("genre")
            .groupby("genre")["averageRating"].mean().sort_values().tail(10)
        )
        g1, g2, g3 = st.columns(3)
        with g1:
            fig = px.bar(x=decennies.index.astype(str) + "s", y=decennies.values, title="FILMS PAR DÉCENNIE",
                         labels={"x": "", "y": "films"})
            st.plotly_chart(style_graphe(fig), config={"displayModeBar": False})
        with g2:
            fig = px.bar(x=genres.values, y=genres.index, orientation="h", title="LES 10 GENRES LES PLUS PRÉSENTS",
                         labels={"x": "films", "y": ""})
            st.plotly_chart(style_graphe(fig), config={"displayModeBar": False})
        with g3:
            fig = px.bar(x=notes_genre.values.round(2), y=notes_genre.index, orientation="h",
                         title="NOTE MOYENNE PAR GENRE", labels={"x": "note", "y": ""})
            fig.update_xaxes(range=[6, notes_genre.max() + 0.1])
            st.plotly_chart(style_graphe(fig), config={"displayModeBar": False})


def tableau_seances(lignes):
    st.markdown(
        '<div class="recos-titre" id="sec-tableau">&gt; TABLEAU DES SÉANCES · <span>EN DIRECT DU HALL</span></div>',
        unsafe_allow_html=True,
    )
    html = (DOSSIER / "tableau.html").read_text(encoding="utf-8")
    components.html(html.replace("DONNEES_TABLEAU", json.dumps(lignes)), height=48 + 36 * len(lignes) + 70)


def decryptage(manches, nouvelle_partie):
    st.markdown(
        '<div class="recos-titre" id="sec-jeu">&gt; DÉCRYPTAGE · <span>RETROUVE LE FILM AVANT QUE LE SIGNAL SOIT CLAIR</span></div>'
        '<div class="matrice-aide">5 manches. Plus tu réponds vite, plus tu marques de points.</div>',
        unsafe_allow_html=True,
    )
    html = (DOSSIER / "decryptage.html").read_text(encoding="utf-8")
    components.html(html.replace("DONNEES_JEU", json.dumps(manches)), height=520)
    st.button("↻ NOUVELLE PARTIE", key="nouvelle_partie", on_click=nouvelle_partie)


def terminal(historique, executer):
    st.markdown(
        '<div class="recos-titre" id="sec-terminal">&gt; TERMINAL DE L\'OPÉRATEUR · <span>FOUILLE LE CATALOGUE EN LIGNE DE COMMANDE</span></div>',
        unsafe_allow_html=True,
    )
    lignes = ""
    for commande, sortie in historique[-6:]:
        lignes += f'<div class="term-cmd">operateur@cinemaniak:~$ {commande}</div>'
        lignes += "".join(f'<div class="term-out">{ligne}</div>' for ligne in sortie)
    if not historique:
        lignes = '<div class="term-out">Connexion établie. Tape <b>aide</b> pour voir les commandes.</div>'
    with st.container(key="terminal"):
        st.markdown(f'<div class="terminal">{lignes}</div>', unsafe_allow_html=True)
        st.text_input("operateur@cinemaniak:~$", key="commande", on_change=executer, placeholder="tape une commande puis Entrée…")


def ma_liste(liste, films, choisir, retirer):
    st.markdown(
        f'<div class="recos-titre liste-section" id="sec-liste">&gt; MA LISTE · <span>{len(liste)} FILM{"S" if len(liste) > 1 else ""} EN FAVORIS</span></div>',
        unsafe_allow_html=True,
    )
    if not liste:
        st.markdown('<div class="matrice-aide">&gt; Ta liste est vide. Ouvre un dossier et clique sur ☆ AJOUTER À MA LISTE.</div>',
                    unsafe_allow_html=True)
        return
    zone = st.container(key="liste")
    for debut in range(0, len(liste), 6):
        colonnes = zone.columns(6)
        for colonne, tconst in zip(colonnes, liste[debut:debut + 6]):
            film = films[films["tconst"] == tconst].iloc[0]
            with colonne:
                st.markdown(
                    f'<div class="carte favori"><div class="carte-signal">★ FAVORI</div>'
                    f'<div class="carte-image">{affiche(film)}<div class="carte-reflet"></div></div>'
                    f'<div class="carte-titre">{film["primaryTitle"]}</div>'
                    f'<div class="carte-infos">{int(film["startYear"])} · ★ {film["averageRating"]}</div></div>',
                    unsafe_allow_html=True,
                )
                a, b = st.columns([2, 1])
                a.button("▸ DOSSIER", key=f"liste_voir_{tconst}", on_click=choisir, args=(tconst,), width="stretch")
                b.button("✕", key=f"liste_retirer_{tconst}", on_click=retirer, args=(tconst,), width="stretch")


def bouton_liste(dans_liste, basculer):
    texte = "★ DANS MA LISTE · RETIRER" if dans_liste else "☆ AJOUTER À MA LISTE"
    st.button(texte, key="bouton_liste", on_click=basculer)
