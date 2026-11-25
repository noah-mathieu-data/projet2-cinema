# Sagas incomplètes : constats et décisions à prendre

Note de travail sur le moteur de recommandation (projet cinéma, Angers).
Rédigée le 24 novembre 2026, mise à jour le 25 novembre 2026 pour le catalogue
définitif (6 942 films). Les points marqués « à vérifier » n'ont pas été
contrôlés dans les données.

## 1. Les critères de sélection du catalogue

Le catalogue (`data/films_prepares.csv`) compte 6 942 films. L'équipe a revu
ses règles de sélection (sagas complètes, seuil adapté pour les films français,
films cultes de tous genres). Les valeurs observées dans le catalogue montrent
les seuils suivants :

- année de sortie à partir de 1970 (film le plus ancien : 1970) ;
- films en français (langue originale `fr`, 739 films) : au moins 2 000 votes
  IMDb (minimum observé : 2 001) et une note d'au moins 6 ;
- autres films : au moins 10 000 votes IMDb (minimum observé : 10 009) ;
- note IMDb d'au moins 6, sauf pour les films très populaires : les 260 films
  notés sous 6 ont tous plus de 100 000 votes (note la plus basse : 1,8, pour
  *Radhe*).

Ces règles récupèrent une partie des sagas (Matrix Resurrections, les Alien
vs. Predator, deux Gendarme) et de nombreux films français. Elles laissent
encore de côté les suites françaises mal notées et les films d'avant 1970.

## 2. Les manques repérés

Deux familles de problèmes sont à distinguer.

### 2.1. Films absents du catalogue (problème de sélection)

| Saga | Présents dans le catalogue | Absents | Raison |
|---|---|---|---|
| Matrix | les 4 films, dont Matrix Resurrections (2021, note 5,6) | aucun | réglé : plus de 100 000 votes |
| Alien | les 5 films de la saga principale, Alien: Romulus et les deux Alien vs. Predator (notes 5,7 et 4,6) | aucun | réglé : plus de 100 000 votes |
| Taxi | Taxi (1998), Taxi 2 (2000) | Taxi 3, Taxi 4, Taxi 5 | films français notés sous 6 (5,8, 5,6 et 4,6 sur IMDb) |
| Le Gendarme | Le Gendarme en balade (1970), Le Gendarme et les Extra-terrestres (1979), Le Gendarme et les Gendarmettes (1982) | Le Gendarme de Saint-Tropez (1964), Le Gendarme à New York (1965), Le Gendarme se marie (1968) | sortis avant 1970 |
| Les Tuche | aucun | Les Tuche (2011), Les Tuche 2 (2016), Les Tuche 3 (2018), Les Tuche 4 (2021), God Save the Tuche (2025) | films français notés sous 6 (5,5 pour le premier, 4,7 pour le troisième, 4,5 pour le quatrième, 4,6 pour God Save the Tuche), avec peu de votes |

Les notes de Taxi 3 à 5 et des Tuche ont été relevées sur imdb.com (celle de
Les Tuche 2 reste à vérifier) ; les autres viennent du catalogue.

### 2.1 bis. Un cas à part : les succès populaires français

Les Tuche montrent un biais qui va au-delà des sagas. Ces films ont eu un grand
succès en salles en France (environ 1,5 million d'entrées pour le premier,
4,6 millions pour Les Tuche 2, d'après AlloCiné), mais IMDb est un site
international, surtout anglophone : les comédies populaires françaises y
reçoivent peu de votes, et souvent des notes sévères.

Le nouveau seuil de 2 000 votes pour les films français a corrigé une partie du
problème (Les Bronzés, Le Gendarme en balade… sont entrés). Mais la note
minimale de 6 continue d'écarter les comédies populaires mal notées, alors que
les films étrangers très votés sont admis quelle que soit leur note.

### 2.2. Films présents mais mal retrouvés (problème du moteur)

| Film de départ | Constat | Raison |
|---|---|---|
| Alien (1979) | le moteur propose Alien 3, Alien: Covenant, Alien: Romulus et Alien, la résurrection dans son top 5 ; Aliens (1986) n'est que 71ᵉ (version 2 du notebook) | Aliens partage 7 mots-clés avec Alien, dont « xenomorph », mais IMDb le classe en Action, Adventure, Horror, sans Sci-Fi : il diffère d'Alien sur 3 genres |
| Astérix & Obélix : Mission Cléopâtre (2002) | 8 autres films Astérix dans le catalogue, mais un seul dans les recommandations (Astérix & Obélix contre César) ; les autres places vont à des films familiaux français (Le Petit Nicolas, La Guerre des boutons…) | les dessins animés ont des genres (Animation) et des mots-clés trop différents de ceux des films en prises de vue réelles |

## 3. Décisions à prendre (en équipe)

Le catalogue est désormais considéré comme définitif. Les options qui touchent
à la sélection (B et C ci-dessous) sont donc des pistes pour plus tard ; les
options A et D agissent sans changer le catalogue.

### Option A : un fichier de sagas fait main

Un fichier `sagas.csv` (colonnes `saga` et `tconst`), tenu à la main pour
quelques dizaines de sagas « cultes ».

- Avantages : contrôle film par film, simple à expliquer, utilisable aussi
  dans l'appli (une ligne « Dans la même saga »).
- Inconvénients : travail manuel, liste forcément incomplète.
- Question : quelle source pour l'appartenance à une saga ? Piste : TMDB
  regroupe les films en « collections » (à vérifier : ce champ est-il présent
  dans le fichier TMDB utilisé ?).

### Option B : assouplir encore la note des films français d'une saga

Si un film d'une saga est dans la sélection, on ajouterait les autres films de
la saga avec une note minimale plus basse, par exemple 5.

- Récupérerait : Taxi 3 (5,8), Taxi 4 (5,6), Les Tuche (5,5).
- Ne récupérerait pas : Taxi 5 (4,6), les autres Tuche (de 4,5 à 4,7), ni les
  Gendarme d'avant 1970.
- Suppose l'option A, ou une autre source pour savoir qui appartient à une
  saga.

### Option C : abaisser le seuil d'année

Passer à 1960 au lieu de 1970, par exemple, récupérerait les premiers Gendarme
et de nombreux classiques des années 1960. Le public d'un cinéma de quartier à
Angers peut être sensible à ces films. Conséquences à mesurer : taille du
catalogue, part de films anciens dans les recommandations, cohérence avec
l'étude de marché de l'équipe.

### Question de fond : les films mal notés

Les nouvelles règles admettent des films très votés mais très mal notés
(*Radhe* : 1,8 ; *Blanche Neige* 2025 : 2,2). Un cinéma d'Angers veut-il les
recommander ? Et, à l'inverse, pourquoi admettre ces films étrangers mais pas
les Tuche ? La note mesure la qualité perçue par les votants d'IMDb, pas le
succès auprès du public français. Piste : une autre source de popularité en
France (nombre d'entrées, notes AlloCiné), absente des données actuelles.

Pour inclure les Tuche à coup sûr, seule l'option A (ajout manuel) suffit.

### Option D : agir sur le moteur

- Ajouter un bloc « saga » au vecteur des films (une colonne 0/1 par saga,
  avec un poids), à partir du fichier de l'option A : les films d'une même
  saga se rapprocheraient fortement.
- Ajouter les résumés TMDB (`overview`) comme bloc TF-IDF : les noms des
  personnages (Ripley, Neo, Astérix…) relieraient naturellement les films
  d'une saga (voir `moteur.md`, section 5.1).
- Baisser le poids des genres : Aliens remonterait, mais l'effet sur les
  autres films est à tester.

## 4. Proposition

À discuter, mais une combinaison simple semble réaliste avant la soutenance :

1. option A pour une courte liste de sagas importantes pour le public visé,
   avec une ligne « Dans la même saga » dans l'appli ;
2. le reste (options B, C et D) noté comme pistes d'amélioration.
