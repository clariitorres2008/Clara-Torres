"""Genera la muestra de demostración en data/muestra/ (CSV y JSON equivalentes).

Uso (desde la raíz del proyecto):
    python scripts/generar_muestra.py
"""

import csv
import json
import random
from pathlib import Path

SEMILLA = 2026
CARPETA = Path(__file__).resolve().parent.parent / "data" / "muestra"

PELICULAS = [
    ("Toy Story (1995)", "Adventure|Animation|Children|Comedy|Fantasy", 4.0),
    ("Shawshank Redemption, The (1994)", "Crime|Drama", 4.5),
    ("Pulp Fiction (1994)", "Comedy|Crime|Drama|Thriller", 4.2),
    ("Forrest Gump (1994)", "Comedy|Drama|Romance|War", 4.1),
    ("Matrix, The (1999)", "Action|Sci-Fi|Thriller", 4.2),
    ("Silence of the Lambs, The (1991)", "Crime|Horror|Thriller", 4.1),
    ("Star Wars: Episode IV - A New Hope (1977)", "Action|Adventure|Sci-Fi", 4.2),
    ("Jurassic Park (1993)", "Action|Adventure|Sci-Fi|Thriller", 3.7),
    ("Titanic (1997)", "Drama|Romance", 3.4),
    ("Godfather, The (1972)", "Crime|Drama", 4.4),
    ("Fight Club (1999)", "Action|Crime|Drama|Thriller", 4.2),
    ("Lion King, The (1994)", "Adventure|Animation|Children|Drama|Musical|IMAX", 3.9),
    ("Spirited Away (Sen to Chihiro no kamikakushi) (2001)", "Adventure|Animation|Fantasy", 4.3),
    ("Amélie (Fabuleux destin d'Amélie Poulain, Le) (2001)", "Comedy|Romance", 4.0),
    ("Misérables, Les (1995)", "Drama|War", 3.6),
    ("Secret in Their Eyes, The (El secreto de sus ojos) (2009)", "Crime|Drama|Mystery|Romance|Thriller", 4.1),
    ("Wild Tales (2014)", "Comedy|Drama|Thriller", 4.0),
    ("Nine Queens (Nueve reinas) (2000)", "Crime|Thriller", 3.9),
    ("City of God (Cidade de Deus) (2002)", "Action|Adventure|Crime|Drama|Thriller", 4.2),
    ("Pan's Labyrinth (Laberinto del fauno, El) (2006)", "Drama|Fantasy|Thriller", 3.9),
    ("(500) Days of Summer (2009)", "Comedy|Drama|Romance", 3.7),
    ("Inception (2010)", "Action|Crime|Drama|Mystery|Sci-Fi|Thriller|IMAX", 4.1),
    ("Dark Knight, The (2008)", "Action|Crime|Drama|IMAX", 4.2),
    ("WALL·E (2008)", "Adventure|Animation|Children|Romance|Sci-Fi", 4.0),
    ("Up (2009)", "Adventure|Animation|Children|Drama", 3.9),
    ("Interstellar (2014)", "Sci-Fi|IMAX", 4.0),
    ("Mad Max: Fury Road (2015)", "Action|Adventure|Sci-Fi|Thriller", 3.9),
    ("Grand Budapest Hotel, The (2014)", "Comedy|Drama", 3.9),
    ("Whiplash (2014)", "Drama", 4.0),
    ("Get Out (2017)", "Horror", 3.8),
    ("Coco (2017)", "Adventure|Animation|Children", 3.9),
    ("Parasite (2019)", "Comedy|Drama", 4.3),
    ("Shrek (2001)", "Adventure|Animation|Children|Comedy|Fantasy|Romance", 3.6),
    ("Twilight (2008)", "Drama|Fantasy|Romance|Thriller", 2.6),
    ("Batman & Robin (1997)", "Action|Adventure|Fantasy|Thriller", 2.2),
    ("Catwoman (2004)", "Action|Crime|Fantasy", 2.0),
    ("Psycho (1960)", "Crime|Horror", 4.0),
    ("Metropolis (1927)", "Drama|Sci-Fi", 3.9),
    ("Casablanca (1942)", "Drama|Romance", 4.1),
    ("Cosmos", "(no genres listed)", 4.5),
    ("Hidden Gem Documentary (2016)", "Documentary", 5.0),
    ("Unrated Short Film (2018)", "Animation", 3.0),
]

VALORACIONES_FIJAS = {
    "Cosmos": [5.0],
    "Hidden Gem Documentary (2016)": [5.0, 5.0],
    "Unrated Short Film (2018)": [],
}

USUARIOS = 25
PROBABILIDAD_DE_CALIFICAR = 0.45
INICIO, FIN = 1420070400, 1537747200

PELICULAS_CON_ERRORES = [
    {"movieId": "12", "title": "Lion King, The (2019)", "genres": "Adventure|Animation"},
    {"movieId": "abc", "title": "Movie With Bad Id (2001)", "genres": "Drama"},
    {"movieId": "90", "title": "", "genres": "Drama"},
    {"movieId": "91", "title": "Movie From The Future (2099)", "genres": "Sci-Fi"},
]


def redondear_media_estrella(valor: float) -> float:
    return min(5.0, max(0.5, round(valor * 2) / 2))


def generar():
    rng = random.Random(SEMILLA)
    peliculas = [
        {"movieId": str(i), "title": t, "genres": g}
        for i, (t, g, _) in enumerate(PELICULAS, start=1)
    ]
    ids = {p["title"]: int(p["movieId"]) for p in peliculas}

    valoraciones = []
    for usuario in range(1, USUARIOS + 1):
        sesgo = rng.gauss(0, 0.3)
        for titulo, _, calidad in PELICULAS:
            if titulo in VALORACIONES_FIJAS:
                continue
            if rng.random() < PROBABILIDAD_DE_CALIFICAR:
                puntaje = redondear_media_estrella(calidad + sesgo + rng.gauss(0, 0.7))
                valoraciones.append([usuario, ids[titulo], puntaje, rng.randint(INICIO, FIN)])
    for titulo, puntajes in VALORACIONES_FIJAS.items():
        for usuario, puntaje in enumerate(puntajes, start=1):
            valoraciones.append([usuario, ids[titulo], puntaje, rng.randint(INICIO, FIN)])
    valoraciones.sort(key=lambda v: (v[0], v[1]))

    u, m, _, ts = valoraciones[0]
    errores = [
        [3, 2, "6.0", 1500000000],
        [3, 5, "3.7", 1500000000],
        [4, 2, "", 1500000000],
        [4, 3, "muy buena", 1500000000],
        [5, 999, "4.0", 1500000000],
        ["-4", 1, "3.0", 1500000000],
        [u, m, "1.0", ts - 1000],
        [u, m, "2.0", ts + 1000],
    ]

    CARPETA.mkdir(parents=True, exist_ok=True)

    # --- películas ---
    filas_peliculas = peliculas + PELICULAS_CON_ERRORES
    with (CARPETA / "movies.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["movieId", "title", "genres"])
        w.writeheader()
        w.writerows(filas_peliculas)
    json_peliculas = [
        {**p, "movieId": int(p["movieId"]) if p["movieId"].isdigit() else p["movieId"]}
        for p in filas_peliculas
    ]
    with (CARPETA / "movies.json").open("w", encoding="utf-8") as f:
        json.dump(json_peliculas, f, ensure_ascii=False, indent=1)
        f.write("\n")

    # --- valoraciones ---
    filas_csv = [[str(c) if not isinstance(c, float) else f"{c:.1f}" for c in v] for v in valoraciones]
    filas_csv += [[str(c) for c in e] for e in errores]
    with (CARPETA / "ratings.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["userId", "movieId", "rating", "timestamp"])
        w.writerows(filas_csv)

    def a_json(valor):
        if valor == "":
            return None
        if isinstance(valor, (int, float)):
            return valor
        try:
            return int(valor)
        except ValueError:
            try:
                return float(valor)
            except ValueError:
                return valor

    claves = ["userId", "movieId", "rating", "timestamp"]
    json_valoraciones = [dict(zip(claves, (a_json(c) for c in fila))) for fila in valoraciones + errores]
    for registro in json_valoraciones:
        if isinstance(registro["rating"], int):
            registro["rating"] = float(registro["rating"])
    with (CARPETA / "ratings.json").open("w", encoding="utf-8") as f:
        json.dump(json_valoraciones, f, ensure_ascii=False, indent=1)
        f.write("\n")

    print(f"Muestra generada en {CARPETA}: {len(filas_peliculas)} películas, "
          f"{len(valoraciones) + len(errores)} valoraciones (incluye registros con errores).")


if __name__ == "__main__":
    generar()
