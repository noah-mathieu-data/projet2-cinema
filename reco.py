import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors


# Poids retenus dans le notebook (version 3, durée à 0)
POIDS = {"genres": 0.7, "startYear": 0.7, "runtimeMinutes": 0,
         "averageRating": 0.7, "log_votes": 0.7,
         "mots_cles": 1, "langue": 0.8}


def decouper(texte):
    return texte.split(", ")    # un mot-clé = une expression entre virgules


def preparer_caracteristiques(films, poids=POIDS):
    # Genres en colonnes 0/1
    genres = films["genres"].str.get_dummies(sep=",")

    # Valeurs numériques normalisées entre 0 et 1, puis pondérées
    numeriques = films[["startYear", "runtimeMinutes", "averageRating"]].copy()
    numeriques["runtimeMinutes"] = numeriques["runtimeMinutes"].clip(upper=180)
    numeriques["log_votes"] = np.log10(films["numVotes"])
    numeriques_norm = pd.DataFrame(MinMaxScaler().fit_transform(numeriques),
                                   columns=numeriques.columns)
    for col in numeriques_norm.columns:
        numeriques_norm[col] = numeriques_norm[col] * poids[col]

    # Mots-clés en TF-IDF
    tfidf = TfidfVectorizer(tokenizer=decouper, token_pattern=None,
                            binary=True, min_df=2)
    mots = tfidf.fit_transform(films["keywords"]).toarray()

    # Langue originale en colonnes 0/1
    langues = pd.get_dummies(films["original_language"].fillna("inconnue")).astype(int)

    X = np.hstack([poids["genres"] * genres.values,
                   numeriques_norm.values,
                   poids["mots_cles"] * mots,
                   poids["langue"] * langues.values])
    return pd.DataFrame(X)


def creer_modele(X):
    modele = NearestNeighbors(metric="cosine")
    modele.fit(X)
    return modele


def recommander(tconst, films, X, modele, nb=5):
    # films doit avoir un index 0, 1, 2… aligné sur les lignes de X
    i = films[films["tconst"] == tconst].index[0]
    distances, indices = modele.kneighbors(X.iloc[[i]], n_neighbors=nb + 1)
    voisins = films.iloc[indices[0][1:]][["tconst", "title", "startYear", "genres"]]
    voisins["distance"] = distances[0][1:]
    return voisins
