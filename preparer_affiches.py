# Récupère les affiches et résumés TMDB de nos 6447 films
import pandas as pd

films = pd.read_csv("data/films_filtres.csv")

colonnes = ["imdb_id", "poster_path", "backdrop_path", "overview", "tagline", "keywords", "original_language"]
morceaux = []
for morceau in pd.read_csv("data/TMDB_movie_dataset_v11.csv", usecols=colonnes, chunksize=200000):
    morceaux.append(morceau[morceau["imdb_id"].isin(films["tconst"])])
tmdb = pd.concat(morceaux).drop_duplicates("imdb_id")

tmdb = tmdb.rename(columns={"imdb_id": "tconst"})
tmdb.to_csv("data/films_tmdb.csv", index=False)
print(len(tmdb), "films trouvés dans TMDB sur", len(films))
print(tmdb["poster_path"].notna().sum(), "ont une affiche")
