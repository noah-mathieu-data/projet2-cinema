import hmac
import html
import json
import time
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DATA = Path(__file__).parent / "data"
FICHIER_ANNONCE = DATA / "annonce.json"
FICHIER_EVENEMENT = DATA / "evenement.json"
FICHIER_STATS = DATA / "stats.json"
FICHIER_FORCES = DATA / "forces.json"
FICHIER_ACTIVITE = DATA / "activite.json"
FICHIER_INTRUSIONS = DATA / "intrusions.json"
FICHIER_AMBIANCE = DATA / "ambiance.json"

# Les ambiances changent la teinte de tout le site (le vert de base tourne sur le cercle des couleurs)
AMBIANCES = {
    "🟢 Matrice (vert)": "",
    "🔴 Alerte rouge": "hue-rotate(-125deg) saturate(1.3)",
    "🔵 Bleu nuit": "hue-rotate(95deg) saturate(1.1) brightness(0.95)",
    "🟣 Violet néon": "hue-rotate(150deg) saturate(1.3)",
    "🟠 Halloween": "hue-rotate(-95deg) saturate(1.5) contrast(1.1)",
    "⚪ Noir et blanc": "grayscale(1) contrast(1.2)",
}

EFFETS = {
    "🐇 Pluie rouge (WAKE UP)": "neo",
    "🌍 Monde réel": "reel",
    "🕴️ Agent Smith": "agent",
    "🐈‍⬛ Déjà-vu": "dejavu",
    "🏛️ Construct": "construct",
    "🥄 Il n'y a pas de cuillère": "cuillere",
    "⚡ Glitch géant": "glitch",
}


# ---------- Petits fichiers JSON qui servent de mémoire au site ----------
def lire(fichier, defaut):
    try:
        return json.loads(fichier.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return defaut


def ecrire(fichier, contenu):
    fichier.write_text(json.dumps(contenu, indent=2, ensure_ascii=False), encoding="utf-8")


# ---------- Journal d'activité (pour le mur de surveillance) ----------
def journal(texte):
    activite = lire(FICHIER_ACTIVITE, [])
    activite.append({"heure": time.strftime("%H:%M:%S"), "texte": texte})
    ecrire(FICHIER_ACTIVITE, activite[-40:])


# ---------- Statistiques du site ----------
def compter(cle, sous_cle=None):
    stats = lire(FICHIER_STATS, {})
    if sous_cle is None:
        stats[cle] = stats.get(cle, 0) + 1
    else:
        bloc = stats.setdefault(cle, {})
        bloc[sous_cle] = bloc.get(sous_cle, 0) + 1
    ecrire(FICHIER_STATS, stats)


# ---------- Connexion ----------
def identifiants_configures():
    try:
        return "operateur" in st.secrets and "mot_de_passe" in st.secrets["operateur"]
    except Exception:
        return False


def verifier_connexion():
    identifiant = st.session_state.get("op_identifiant", "")
    mot_de_passe = st.session_state.get("op_mot_de_passe", "")
    attendu_id = st.secrets["operateur"]["identifiant"]
    attendu_mdp = st.secrets["operateur"]["mot_de_passe"]
    # compare_digest compare en temps constant : on ne peut pas deviner le mot de passe lettre par lettre
    ok = hmac.compare_digest(identifiant, attendu_id) and hmac.compare_digest(mot_de_passe, attendu_mdp)
    st.session_state["op_mot_de_passe"] = ""
    if ok:
        st.session_state["operateur"] = True
        st.session_state["scan"] = True
        st.session_state["op_erreur"] = False
        st.session_state["login_visible"] = False
    else:
        st.session_state["op_erreur"] = True
        intrusions = lire(FICHIER_INTRUSIONS, [])
        intrusions.append({"date": time.strftime("%d/%m/%Y"), "heure": time.strftime("%H:%M:%S"),
                           "identifiant": identifiant[:20] or "(vide)"})
        ecrire(FICHIER_INTRUSIONS, intrusions[-50:])
        journal("⚠ Tentative d'intrusion bloquée")


def deconnexion():
    st.session_state["operateur"] = False
    st.session_state["sortie_operateur"] = True


def basculer_login():
    st.session_state["login_visible"] = not st.session_state.get("login_visible", False)


def fenetre_connexion():
    # Petit bouton discret, toujours présent pour que la page garde la même structure
    st.button("⌬", key="acces_operateur", on_click=basculer_login, help="Accès opérateur")
    if not st.session_state.get("login_visible") or st.session_state.get("operateur"):
        return
    with st.container(key="login"):
        st.markdown('<div class="login-titre">&gt; ACCÈS RESTREINT · AUTHENTIFICATION REQUISE</div>', unsafe_allow_html=True)
        if not identifiants_configures():
            st.markdown('<div class="login-erreur">&gt; Aucun identifiant configuré dans .streamlit/secrets.toml</div>',
                        unsafe_allow_html=True)
            return
        with st.form("formulaire_login", border=False):
            st.text_input("IDENTIFIANT", key="op_identifiant")
            st.text_input("MOT DE PASSE", key="op_mot_de_passe", type="password")
            st.form_submit_button("▸ S'AUTHENTIFIER", on_click=verifier_connexion)
        if st.session_state.get("op_erreur"):
            st.markdown('<div class="login-erreur">&gt; ACCÈS REFUSÉ · tentative enregistrée</div>', unsafe_allow_html=True)


# ---------- Ce que voient tous les visiteurs ----------
def bandeau_annonce():
    annonce = lire(FICHIER_ANNONCE, {}).get("texte", "")
    if annonce:
        texte = (f"⚠ {annonce} &nbsp;&nbsp;·&nbsp;&nbsp; ") * 6
        st.markdown(f'<div class="annonce"><div class="annonce-defile">{texte}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="annonce-vide"></div>', unsafe_allow_html=True)


def signal_evenement():
    evenement = lire(FICHIER_EVENEMENT, {})
    st.markdown(
        f'<div id="cm-evenement" data-id="{evenement.get("id", "")}" data-effet="{evenement.get("effet", "")}"'
        f' data-temps="{evenement.get("temps", 0)}"></div>',
        unsafe_allow_html=True,
    )


def appliquer_ambiance():
    filtre = lire(FICHIER_AMBIANCE, {}).get("filtre", "")
    regle = f'[data-testid="stAppViewContainer"] {{ filter: {filtre}; }}' if filtre else ""
    st.markdown(f'<style>{regle}</style><div id="cm-ambiance" data-nom="{lire(FICHIER_AMBIANCE, {}).get("nom", "")}"></div>',
                unsafe_allow_html=True)


def forces():
    return lire(FICHIER_FORCES, {})


# ---------- La salle de contrôle ----------
def salle_de_controle(films, libelles, programme, candidats, semaine, votes, effacer_votes, seances_fn):
    st.markdown(
        '<div class="recos-titre controle-titre" id="sec-controle">&gt; SALLE DE CONTRÔLE · '
        '<span>OPÉRATEUR NIVEAU 5</span></div>',
        unsafe_allow_html=True,
    )
    onglets = st.tabs(["🖥️ SURVEILLANCE", "📢 ANNONCE", "🗳️ SALLE 9", "🎬 PROGRAMMATION", "🎟️ BILLETTERIE", "📊 STATISTIQUES",
                       "📜 INTRUSIONS", "🎨 AMBIANCE", "🔴 BOUTON ROUGE", "🗝️ MODE DÉMO", "⏻ DÉCONNEXION"])
    surveillance, onglets = onglets[0], onglets[1:]

    with surveillance:
        mur_de_surveillance()

    with onglets[0]:
        actuelle = lire(FICHIER_ANNONCE, {}).get("texte", "")
        st.markdown(f'<div class="controle-info">&gt; annonce en cours : <b>{actuelle or "aucune"}</b></div>',
                    unsafe_allow_html=True)
        texte = st.text_input("MESSAGE POUR TOUS LES VISITEURS", key="op_annonce", placeholder="AVANT-PREMIÈRE SURPRISE JEUDI 22H")
        a, b = st.columns(2)
        if a.button("📢 DIFFUSER", key="op_diffuser", width="stretch") and texte.strip():
            ecrire(FICHIER_ANNONCE, {"texte": texte.strip().upper()})
            st.rerun()
        if b.button("✕ RETIRER L'ANNONCE", key="op_retirer", width="stretch"):
            ecrire(FICHIER_ANNONCE, {})
            st.rerun()

    with onglets[1]:
        total = sum(votes.values())
        lignes = "".join(
            f'<div class="controle-info">&gt; {libelles[t]} · <b>{votes.get(t, 0)}</b> vote(s)</div>'
            for t in candidats["tconst"]
        )
        st.markdown(lignes + f'<div class="controle-info">&gt; total : <b>{total}</b></div>', unsafe_allow_html=True)
        force = forces().get("salle9", {}).get(str(semaine))
        choix = st.selectbox("DÉSIGNER LE GAGNANT", ["(laisser voter le public)"] + candidats["tconst"].tolist(),
                             format_func=lambda t: libelles.get(t, t), key="op_gagnant",
                             index=(candidats["tconst"].tolist().index(force) + 1) if force in candidats["tconst"].tolist() else 0)
        a, b = st.columns(2)
        if a.button("★ VALIDER LE GAGNANT", key="op_valider_gagnant", width="stretch"):
            tout = forces()
            salle9 = tout.setdefault("salle9", {})
            if choix.startswith("("):
                salle9.pop(str(semaine), None)
            else:
                salle9[str(semaine)] = choix
            ecrire(FICHIER_FORCES, tout)
            st.rerun()
        if b.button("↺ REMETTRE LES VOTES À ZÉRO", key="op_reset_votes", width="stretch"):
            effacer_votes()
            st.rerun()

    with onglets[2]:
        st.markdown('<div class="controle-info">&gt; choisis le film principal de chaque salle cette semaine</div>',
                    unsafe_allow_html=True)
        actuels = programme.iloc[:8]["tconst"].tolist()
        options = films["tconst"].tolist()
        nouveaux = []
        colonnes = st.columns(4)
        for i in range(8):
            with colonnes[i % 4]:
                nouveaux.append(st.selectbox(f"SALLE {i + 1}", options, index=options.index(actuels[i]),
                                             format_func=lambda t: libelles[t], key=f"op_salle_{i}"))
        a, b = st.columns(2)
        if a.button("💾 ENREGISTRER LA PROGRAMMATION", key="op_prog", width="stretch"):
            tout = forces()
            tout.setdefault("programme", {})[str(semaine)] = nouveaux
            ecrire(FICHIER_FORCES, tout)
            st.cache_data.clear()
            st.rerun()
        if b.button("↺ REVENIR AU TIRAGE AUTOMATIQUE", key="op_prog_reset", width="stretch"):
            tout = forces()
            tout.get("programme", {}).pop(str(semaine), None)
            ecrire(FICHIER_FORCES, tout)
            st.cache_data.clear()
            st.rerun()

    with onglets[4]:
        stats = lire(FICHIER_STATS, {})
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("VISITES", stats.get("visites", 0))
        k2.metric("PILULES BLEUES", stats.get("pilules", {}).get("bleue", 0))
        k3.metric("PILULES ROUGES", stats.get("pilules", {}).get("rouge", 0))
        k4.metric("ORACLE CONSULTÉ", stats.get("oracle", 0))
        consultes = stats.get("films", {})
        if consultes:
            top = pd.Series(consultes).sort_values().tail(8)
            fig = px.bar(x=top.values, y=[libelles.get(t, t) for t in top.index], orientation="h",
                         title="LES FILMS LES PLUS CONSULTÉS", labels={"x": "consultations", "y": ""})
            from design import style_graphe
            fig = style_graphe(fig, 340)
            fig.update_traces(marker_color="#00FF41", marker_line_color="#003b10")  # le mode opérateur le rend doré
            st.plotly_chart(fig, config={"displayModeBar": False})
        else:
            st.markdown('<div class="controle-info">&gt; pas encore de données</div>', unsafe_allow_html=True)

    with onglets[7]:
        st.markdown('<div class="controle-info">&gt; déclenche un effet chez tous les visiteurs connectés '
                    '(au prochain rafraîchissement de leur page)</div>', unsafe_allow_html=True)
        effet = st.selectbox("EFFET", list(EFFETS.keys()), key="op_effet")
        if st.button("🔴 DÉCLENCHER", key="op_bouton_rouge", width="stretch"):
            ecrire(FICHIER_EVENEMENT, {"id": str(int(time.time() * 1000)), "effet": EFFETS[effet], "temps": int(time.time())})
            st.rerun()

    with onglets[3]:
        billetterie(programme, semaine, seances_fn)

    with onglets[5]:
        intrusions = lire(FICHIER_INTRUSIONS, [])
        st.markdown(f'<div class="controle-info">&gt; tentatives d\'intrusion bloquées : <b>{len(intrusions)}</b></div>',
                    unsafe_allow_html=True)
        lignes = "".join(f'<div class="intrusion">[{i["date"]} {i["heure"]}] ACCÈS REFUSÉ · identifiant tenté : '
                         f'<b>{html.escape(i["identifiant"])}</b></div>' for i in reversed(intrusions[-12:]))
        st.markdown(f'<div class="terminal journal">{lignes or "&gt; aucune intrusion. La Matrice est calme."}</div>',
                    unsafe_allow_html=True)
        if intrusions and st.button("✕ VIDER LE JOURNAL", key="op_vider_intrusions"):
            ecrire(FICHIER_INTRUSIONS, [])
            st.rerun()

    with onglets[6]:
        actuelle = lire(FICHIER_AMBIANCE, {}).get("nom", "🟢 Matrice (vert)")
        st.markdown(f'<div class="controle-info">&gt; ambiance actuelle pour tous les visiteurs : <b>{actuelle}</b></div>',
                    unsafe_allow_html=True)
        choix = st.selectbox("NOUVELLE AMBIANCE", list(AMBIANCES.keys()), key="op_ambiance",
                             index=list(AMBIANCES.keys()).index(actuelle) if actuelle in AMBIANCES else 0)
        if st.button("🎨 APPLIQUER À TOUT LE SITE", key="op_appliquer_ambiance", width="stretch"):
            ecrire(FICHIER_AMBIANCE, {"nom": choix, "filtre": AMBIANCES[choix]})
            journal(f"🎨 Ambiance changée : {choix}")
            st.rerun()

    with onglets[8]:
        st.markdown('<div class="controle-info">&gt; le site se présente tout seul : il défile, ouvre un dossier, prend une pilule, '
                    'lance des effets. Parfait pour une soutenance. Appuie sur Échap pour l\'arrêter.</div>', unsafe_allow_html=True)
        if st.button("🗝️ LANCER LA VISITE GUIDÉE", key="op_demo", width="stretch"):
            st.session_state["lancer_demo"] = True
            st.rerun()

    with onglets[9]:
        st.markdown('<div class="controle-info">&gt; quitter le mode opérateur et revenir dans la Matrice</div>',
                    unsafe_allow_html=True)
        st.button("⏻ SE DÉCONNECTER", key="op_deconnexion", on_click=deconnexion, width="stretch")


# ---------- Le mur de surveillance (se met à jour tout seul toutes les 3 secondes) ----------
@st.fragment(run_every=3)
def mur_de_surveillance():
    activite = lire(FICHIER_ACTIVITE, [])[-9:][::-1]
    while len(activite) < 9:
        activite.append({"heure": "--:--:--", "texte": "· signal en attente ·"})
    ecrans = "".join(
        f'<div class="cam"><div class="cam-nom">CAM {i + 1:02d} · {e["heure"]}</div>'
        f'<div class="cam-texte">{html.escape(e["texte"])}</div><i class="rec">● REC</i></div>'
        for i, e in enumerate(activite)
    )
    st.markdown(f'<div class="mur">{ecrans}</div>', unsafe_allow_html=True)


# ---------- La billetterie : remplissage des salles aujourd'hui ----------
def places_prises(titre, jour, heure):
    # Même calcul que le plan de salle du site, pour retrouver exactement les mêmes sièges occupés
    graine = 0
    for c in titre + jour + heure:
        graine = (graine * 31 + ord(c)) % 99991
    prises = 0
    for _ in range(9 * 14):
        graine = (graine * 9301 + 49297) % 233280
        prises += graine / 233280 < 0.38
    return prises


def billetterie(programme, semaine, seances_fn):
    st.markdown('<div class="controle-info">&gt; remplissage des séances d\'aujourd\'hui (126 places par salle)</div>',
                unsafe_allow_html=True)
    lignes = ""
    for rang, (_, f) in enumerate(programme.iterrows()):
        nom, heures = seances_fn(semaine, rang)[0]
        for h in heures:
            prises = places_prises(f["primaryTitle"], nom, h)
            taux = round(100 * prises / 126)
            lignes += (f'<div class="billet-ligne"><span>SALLE {f["salle"]} · {h}</span><span class="billet-film">{html.escape(f["primaryTitle"])}</span>'
                       f'<span class="billet-barre"><i style="width:{taux}%"></i></span><span>{prises}/126 · {taux} %</span></div>')
    st.markdown(f'<div class="billetterie">{lignes}</div>', unsafe_allow_html=True)
