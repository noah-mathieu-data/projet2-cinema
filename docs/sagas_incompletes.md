# Sagas incomplètes : constats et décisions à prendre

Note de travail sur le moteur de recommandation (projet cinéma, Angers).
Rédigée le 24 novembre 2026. Les points marqués « à vérifier » n'ont pas été
contrôlés dans les données.

## 1. Les critères de sélection du catalogue

Le catalogue (`data/films_prepares.csv`) compte 6 089 films. Les valeurs
minimales observées montrent trois seuils appliqués par le filtre de l'équipe :

- année de sortie à partir de 1970 (film le plus ancien : 1970) ;
- note IMDb d'au moins 6 (note la plus basse : 6,0) ;
- au moins 10 000 votes IMDb (minimum observé : 10 004).

Ces seuils sont raisonnables pour un catalogue général, mais ils coupent
certaines sagas : une suite moins bien notée, ou un premier épisode trop
ancien, disparaît du catalogue, et le moteur ne peut pas la recommander.

## 2. Les manques repérés

Deux familles de problèmes sont à distinguer.

### 2.1. Films absents du catalogue (problème de sélection)

| Saga | Présents dans le catalogue | Absents | Raison |
|---|---|---|---|
| Matrix | Matrix (1999), Matrix Reloaded, Matrix Revolutions (2003) | Matrix Resurrections (2021) | note IMDb 5,6 (environ 293 000 votes) : sous le seuil de 6 |
| Taxi | Taxi (1998), Taxi 2 (2000) | Taxi 3, Taxi 4, Taxi 5 | notes IMDb 5,8, 5,6 et 4,6 : sous le seuil de 6 |
| Le Gendarme | Le Gendarme et les Extra-terrestres (1979, note 6,3) | Le Gendarme de Saint-Tropez (1964), Le Gendarme à New York (1965), Le Gendarme se marie (1968) | sortis avant 1970 |
| Le Gendarme (suite) | | Le Gendarme en balade (1970), Le Gendarme et les Gendarmettes (1982) | probablement la note ou le nombre de votes (à vérifier) |
| Les Tuche | aucun | Les Tuche (2011), Les Tuche 2 (2016), Les Tuche 3 (2018), Les Tuche 4 (2021), God Save the Tuche (2025) | double exclusion : notes IMDb sous 6 (5,5 pour le premier, 4,7 pour le troisième, 4,5 pour le quatrième, 4,6 pour God Save the Tuche) et nombre de votes très loin de 10 000 (environ 4 300 pour le premier, 1 600 pour le troisième) |

Les notes de Matrix Resurrections, de Taxi 3 à 5 et des Tuche ont été relevées
sur imdb.com (celle de Les Tuche 2 reste à vérifier).

### 2.1 bis. Un cas à part : les succès populaires français

Les Tuche montrent un biais du filtre, au-delà des sagas. Ces films ont eu un
grand succès en salles en France (environ 1,5 million d'entrées pour le premier,
4,6 millions pour Les Tuche 2, d'après AlloCiné), mais IMDb est un site
international, surtout anglophone : les comédies populaires françaises y
reçoivent peu de votes, et souvent des notes sévères. Le seuil de
10 000 votes écarte donc des films très connus du public français, alors que
le projet s'adresse à un cinéma d'Angers.

### 2.2. Films présents mais mal retrouvés (problème du moteur)

| Film de départ | Constat | Raison |
|---|---|---|
| Alien (1979) | Alien 3, Alien: Romulus et Alien: Covenant sont dans le top 5 ; Alien, la résurrection est 6ᵉ ; Aliens (1986) n'est que 20ᵉ | Aliens partage 7 mots-clés avec Alien, dont « xenomorph », mais IMDb le classe en Action, Adventure, Horror, sans Sci-Fi : il diffère d'Alien sur 3 genres |
| Astérix & Obélix : Mission Cléopâtre (2002) | 8 films Astérix dans le catalogue, mais seulement 2 dans les recommandations (Astérix & Obélix contre César, Astérix et la Surprise de César) ; un troisième (Les 12 Travaux d'Astérix) apparaît avec la durée à 0 | les dessins animés ont des genres (Animation) et des mots-clés trop différents de ceux des films en prises de vue réelles |

## 3. Décisions à prendre (en équipe)

### Option A : un fichier de sagas fait main

Un fichier `sagas.csv` (colonnes `saga` et `tconst`), tenu à la main pour
quelques dizaines de sagas « cultes ».

- Avantages : contrôle film par film, simple à expliquer, utilisable aussi
  dans l'appli (une ligne « Dans la même saga »).
- Inconvénients : travail manuel, liste forcément incomplète.
- Question : quelle source pour l'appartenance à une saga ? Piste : TMDB
  regroupe les films en « collections » (à vérifier : ce champ est-il présent
  dans le fichier TMDB utilisé ?).

### Option B : assouplir les seuils pour les films d'une saga

Si un film d'une saga est dans la sélection, on ajoute les autres films de la
saga avec des seuils plus bas, par exemple une note d'au moins 5 et un nombre
de votes suffisant.

- Récupérerait : Matrix Resurrections (5,6), Taxi 3 (5,8), Taxi 4 (5,6).
- Ne récupérerait pas : Taxi 5 (4,6), ni les Gendarme d'avant 1970.
- Garde-fou : limiter les très longues sagas (Star Trek, James Bond…).
- Suppose l'option A ou une autre source pour savoir qui appartient à une
  saga.

### Option C : revoir les critères généraux du catalogue

- Abaisser le seuil d'année (1960 au lieu de 1970, par exemple) : récupérerait
  les premiers Gendarme et de nombreux classiques des années 1960. Le public
  d'un cinéma de quartier à Angers peut être sensible à ces films.
- Conséquences à mesurer : taille du catalogue, part de films anciens dans les
  recommandations, cohérence avec l'étude de marché de l'équipe.

### Option C bis : un seuil de votes adapté aux films français

Le seuil de 10 000 votes pénalise les films français, moins notés sur IMDb.
On pourrait appliquer un seuil plus bas aux films dont la langue originale est
le français (par exemple 2 000 votes), voire assouplir aussi la note pour eux.

- Récupérerait : Les Tuche (4 300 votes) avec un seuil de votes abaissé, mais
  seulement si la note minimale est aussi abaissée (5,5) ; les suites (notes
  entre 4,5 et 4,7) resteraient exclues avec un seuil de note à 5.
- Plus généralement : de nombreuses comédies populaires françaises.
- Question de fond pour l'équipe : un cinéma d'Angers veut-il recommander des
  films populaires mais mal notés ? La note mesure la qualité perçue par les
  votants d'IMDb, pas le succès auprès du public français.
- Piste : une autre source de popularité en France (nombre d'entrées, notes
  AlloCiné), absente des données actuelles.

Pour inclure les Tuche à coup sûr, seule l'option A (ajout manuel) suffit,
puisque leurs notes sont trop basses pour tout seuil raisonnable.

### Option D : agir sur le moteur

- Ajouter un bloc « saga » au vecteur des films (une colonne 0/1 par saga,
  avec un poids), à partir du fichier de l'option A : les films d'une même
  saga se rapprocheraient fortement.
- Ajouter les résumés TMDB (`overview`) comme bloc TF-IDF : les noms des
  personnages (Ripley, Neo, Astérix…) relieraient naturellement les films
  d'une saga (voir le README, « Pour plus tard »).
- Baisser le poids des genres : Aliens remonterait, mais l'effet sur les
  autres films est à tester.

## 4. Proposition

À discuter, mais une combinaison simple semble réaliste avant la soutenance :

1. option A pour une courte liste de sagas importantes pour le public visé ;
2. option B pour ces sagas seulement (seuil de note abaissé à 5) ;
3. le reste (options C et D) noté comme pistes d'amélioration.
