# Projet 2 · (Team Maniak - Cinémaniak)

Projet de groupe de la Wild Code School avec Pierre, Clémence, Sébastien, Jordan et moi.

On répond à un appel à projets du CNC pour ouvrir un cinéma à Angers. Notre public ce sont les étudiants et les jeunes de 18 à 30 ans. Notre catalogue rassemble des films cultes depuis 1970 en action, aventure, science-fiction, thriller, horreur, guerre et comédie.

## Où on en est

Le notebook preparation_donnees lit les fichiers IMDb directement en ligne et applique nos filtres un par un. On passe de presque 13 millions de titres à 6 447 films. Le résultat est dans data/films_filtres.csv et le détail des filtres dans data/bilan_filtres.csv.

## Pour lancer le projet chez toi

Clone le dépôt puis ouvre le dossier dans VS Code. Dans le terminal tape ces lignes une par une.

    python -m venv .venv
    source .venv/Scripts/activate
    pip install -r requirements.txt

Le fichier TMDB est trop lourd pour GitHub. Récupère TMDB_movie_dataset_v11.csv sur le Drive de la formatrice et range le dans le dossier data.
