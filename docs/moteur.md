# Comment fonctionne le moteur de recommandation

Ce document explique comment le moteur décrit chaque film, comment il trouve
les films qui se ressemblent, et comment le régler ou l'enrichir. Tout le
moteur tient dans le fichier `scripts/reco.py`. L'appli de démonstration est
`scripts/app_pierre.py` ; elle se lance depuis la racine du projet avec
`streamlit run scripts/app_pierre.py`.

## 1. Le principe

1. Chaque film du catalogue (6 942 films, fichier `data/films_prepares.csv`)
   est transformé en une **ligne de nombres** : son vecteur.
2. Pour un film choisi, on cherche les films dont le vecteur est le plus
   **proche**, avec `NearestNeighbors` de scikit-learn et la **distance
   cosinus**.
3. L'appli affiche deux lignes :
   - **Dans le même esprit** : les 5 films les plus proches ;
   - **Pour changer un peu** : 5 films tirés au hasard parmi les voisins de
     rang 15 à 30 (le tirage est fixe pour un film donné).

`NearestNeighbors` est un outil **non supervisé** : il n'y a rien à prédire,
pas de jeu d'entraînement ni de test. Le `fit` se contente de mémoriser les
vecteurs ; le calcul des distances se fait au moment de la recherche.

## 2. Les sept blocs du vecteur

Le vecteur d'un film est la mise bout à bout de **sept blocs**. Chaque bloc
est préparé avec la méthode qui lui convient, puis multiplié par un **poids**.

| Bloc | Colonne d'origine | Préparation | Nombre de colonnes | Poids actuel |
|---|---|---|---|---|
| Genres | `genres` | colonnes 0/1, une par genre (*multi-hot*) | 21 | 0,7 |
| Année | `startYear` | min-max (ramenée entre 0 et 1) | 1 | 0,7 |
| Durée | `runtimeMinutes` | plafonnée à 180 min, puis min-max | 1 | **0** (désactivée) |
| Note | `averageRating` | min-max | 1 | 0,7 |
| Popularité | `numVotes` | logarithme (base 10), puis min-max | 1 | 0,7 |
| Mots-clés | `keywords` (TMDB) | TF-IDF | 6 934 | 1 |
| Langue | `original_language` | colonnes 0/1, une par langue (*one-hot*) | 50 | 0,8 |

Au total, chaque film est décrit par **7 009 nombres**.

### 2.1. Les genres et la langue : des colonnes 0/1

- **Genres** : un film a jusqu'à 3 genres IMDb (Action, Comedy, Sci-Fi…).
  Chaque genre devient une colonne qui vaut 1 si le film a ce genre, 0 sinon
  (`str.get_dummies(sep=",")`). Plusieurs 1 par ligne : c'est du *multi-hot*.
- **Langue** : un film n'a qu'une langue originale. Chaque langue devient une
  colonne 0/1 (`pd.get_dummies`), avec un seul 1 par ligne : c'est du
  *one-hot*. Ce bloc a été ajouté pour que les films non anglophones
  retrouvent des films de leur langue (sans lui, *Taxi* ne recommandait plus
  *Taxi 2*).

### 2.2. Les valeurs numériques : min-max

L'année, la durée, la note et la popularité n'ont pas la même échelle
(de 1970 à 2026, de 63 à 566 minutes, de 1,8 à 9,3, de 2 000 à 3,27 millions de votes). Le
`MinMaxScaler` ramène chacune entre 0 et 1, pour qu'aucune n'écrase les autres
à cause de son unité. Deux préparations avant cela :

- **Popularité** : on prend le **logarithme** du nombre de votes, qui va de
  2 000 à 3,27 millions. Sans lui, quelques blockbusters seraient
  proches de 1 et presque tous les autres films écrasés près de 0.
- **Durée** : plafonnée à 180 minutes, pour que quelques films très longs
  (jusqu'à 566 minutes) ne tassent pas tous les autres près de 0.

Chacune des quatre valeurs forme **un bloc d'une seule colonne**, avec son
propre poids : on peut donc régler séparément l'importance de l'année, de la
durée, de la note et de la popularité.

### 2.3. Les mots-clés : TF-IDF

Les mots-clés TMDB (« space marine », « xenomorph », « android »…) décrivent
le contenu du film, ce que les genres ne disent pas. Ils sont transformés avec
`TfidfVectorizer` de scikit-learn :

- **une colonne par mot-clé** du vocabulaire ;
- chaque mot-clé reçoit un poids d'autant plus grand qu'il est **rare** dans
  le catalogue (c'est l'IDF). Exemple : « xenomorph » (7 films, la saga Alien et
  les deux Alien vs. Predator) pèse beaucoup plus que « alien » (112 films). Partager un mot rare rapproche
  donc fortement deux films ; partager un mot courant les rapproche peu ;
- réglages utilisés :
  - découpage aux virgules (`tokenizer`), pour que « space marine » reste un
    seul mot-clé ;
  - `binary=True` : un mot-clé répété dans la liste d'un film (erreur de
    saisie de TMDB) ne compte qu'une fois ;
  - `min_df=2` : les mots-clés présents dans un seul film (48 % du
    vocabulaire) sont écartés, puisqu'ils ne peuvent rapprocher aucun film d'un
    autre.

Pour comprendre en détail le TF-IDF et la distance cosinus, voir l'article
[`tfidf_cosinus.pdf`](tfidf_cosinus.pdf).

Les mots-clés ne sont pas nettoyés (pas de mots vides, pas de lemmatisation) :
ce sont déjà des étiquettes courtes, pas du texte libre.

### 2.4. Pourquoi les mots-clés n'écrasent pas les autres blocs

On pourrait craindre que les 6 934 colonnes des mots-clés pèsent plus que les
quelques colonnes des autres blocs. Ce n'est pas le cas : `TfidfVectorizer`
ramène la ligne de chaque film à une **longueur de 1**, quel que soit son
nombre de colonnes. En longueur, les trois grandes familles de blocs sont du
même ordre de grandeur (genres : 1,14 en moyenne ; valeurs numériques : 0,80 ;
mots-clés : 1). Ce sont donc bien les **poids** qui règlent l'importance de
chaque bloc.

## 3. La distance cosinus

La distance cosinus compare la **direction** de deux vecteurs, pas leur
longueur. Un film décrit par 30 mots-clés et un film décrit par 5 mots-clés sur
le même thème restent proches. Elle vaut 0 pour deux films au même profil, et
grandit quand leurs profils divergent.

## 4. Les poids : on peut les modifier

Les sept poids sont rangés dans le dictionnaire `POIDS`, en haut de
`reco.py` :

```python
POIDS = {"genres": 0.7, "startYear": 0.7, "runtimeMinutes": 0,
         "averageRating": 0.7, "log_votes": 0.7,
         "mots_cles": 1, "langue": 0.8}
```

Pour essayer un autre réglage, il suffit de changer ces valeurs et de relancer
l'appli. On peut aussi passer un autre dictionnaire à la fonction :

```python
X = reco.preparer_caracteristiques(films, poids=mes_poids)
```

Ce qu'il faut savoir pour régler les poids :

- **Seules les proportions comptent.** Avec la distance cosinus, multiplier
  tous les poids par un même nombre ne change aucune recommandation. On peut
  donc toujours les garder entre 0 et 1.
- **Un poids à 0 désactive un bloc.** C'est le cas de la durée : avec ou sans
  elle, les recommandations des films tests changeaient à peine (un seul film
  sur cinq, pour deux des huit films tests).
  Deux films de 90 et de 120 minutes peuvent très bien se ressembler.
- **Les poids ne sont pas des pourcentages d'influence** : l'effet d'un bloc
  dépend aussi de son nombre de colonnes et de ses valeurs. Ils se règlent en
  observant les recommandations obtenues sur quelques films tests (Alien, Taxi,
  Toy Story, Matrix, Intouchables, Amélie…).
- **Piste de réglage** : les genres pèsent encore beaucoup. *Aliens* n'arrive
  qu'au 71ᵉ rang des voisins d'*Alien*, alors qu'il partage 7 mots-clés avec
  lui, parce qu'IMDb le classe en Action, Adventure, Horror, sans Sci-Fi. Un
  poids plus faible pour les genres serait à essayer.

## 5. Les évolutions possibles

Le moteur est construit en blocs : on peut en ajouter de nouveaux, chacun avec
son poids, sans toucher aux autres.

### 5.1. Réalisateurs et acteurs principaux

On applique la même démarche que pour les mots-clés, mais avec des personnes :

- **les sources** : les fichiers IMDb `title.crew` (réalisateurs) et
  `title.principals` (acteurs, avec leur rang au générique, colonne
  `ordering`) ;
- **les identifiants plutôt que les noms** : chaque personne est désignée par
  son identifiant IMDb (`nconst`, de la forme `nm0000…`), pour éviter les
  homonymes ;
- **les têtes d'affiche seulement** : 3 à 5 premiers rôles, pour ne pas
  rapprocher deux films par un figurant ;
- **TF-IDF avec `min_df=2`**, comme pour les mots-clés : un réalisateur peu
  prolifique partagé par deux films est un signal fort ; un acteur présent
  dans des dizaines de films l'est beaucoup moins.

Exemple : *Alien* et *Aliens* n'ont pas le même réalisateur (Ridley Scott,
James Cameron), mais partagent leur actrice principale, Sigourney Weaver.

Ce serait deux nouveaux blocs, donc deux nouveaux poids.

### 5.2. Le résumé du film (synopsis)

La colonne `overview` de TMDB (absente du catalogue actuel, à récupérer par
jointure) pourrait former un bloc TF-IDF de plus. Mais c'est du **texte libre**,
en anglais, qu'il faudrait préparer :

- enlever les mots vides (`stop_words="english"`) ;
- éventuellement regrouper les formes d'un même mot (lemmatisation ou
  stemming), en vérifiant que ça améliore vraiment les résultats ;
- régler `min_df`, `max_df`, voire `ngram_range=(1, 2)`.

Atout : les résumés citent souvent les personnages (Ripley, Neo, Astérix…),
des mots rares qui relieraient les films d'une même saga.

### 5.3. Les sagas

Certaines sagas sont incomplètes, soit parce que des films sont absents du
catalogue (filtres sur l'année, la note ou le nombre de votes), soit parce que
le moteur les retrouve mal. Ce point fait l'objet d'une note séparée :
`sagas_incompletes.md`.

## 6. Utiliser le moteur dans du code

Depuis la racine du projet :

```python
import sys
import pandas as pd

sys.path.append("scripts")    # reco.py est dans scripts/
import reco

films = pd.read_csv("data/films_prepares.csv")
X = reco.preparer_caracteristiques(films)        # les 7 blocs pondérés
modele = reco.creer_modele(X)                     # NearestNeighbors, cosinus
reco.recommander("tt0078748", films, X, modele)   # les 5 voisins d'Alien
```

`recommander` accepte un paramètre `nb` pour demander plus de voisins
(par exemple `nb=10`).
