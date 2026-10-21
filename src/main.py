"""Punto de entrada de la aplicación de consola.

Uso (desde la carpeta raíz del proyecto):
    python -m src.main lista --genero Drama --minimo 5 --limite 10
    python -m src.main buscar --texto "star wars"
    python -m src.main ficha --id 1
    python -m src.main generos
    python -m src.main --help
"""

import argparse
import sys

from .fuentes import ErrorLectura
from .modelo import ConsultaCatalogo
from .pipeline import (
    COLUMNAS_LISTA,
    ErrorEsquema,
    ErrorResultado,
    buscar_pelicula,
    buscar_titulos,
    generar_lista,
    generos_disponibles,
    guardar_rechazos,
    guardar_tabla,
    lista_a_filas,
    preparar_catalogo,
    validar_genero_conocido,
    verificar_lista,
)
from .validaciones import ErrorValidacion

RUTA_PELICULAS = "data/muestra/movies.csv"
RUTA_VALORACIONES = "data/muestra/ratings.json"
RUTA_RECHAZOS = "outputs/rechazos.csv"


def crear_parser() -> argparse.ArgumentParser:
    comunes = argparse.ArgumentParser(add_help=False)
    comunes.add_argument("--peliculas", default=RUTA_PELICULAS,
                         help=f"catálogo de películas, .csv o .json (por defecto {RUTA_PELICULAS})")
    comunes.add_argument("--valoraciones", default=RUTA_VALORACIONES,
                         help=f"calificaciones, .csv o .json (por defecto {RUTA_VALORACIONES})")
    comunes.add_argument("--rechazos", default=RUTA_RECHAZOS,
                         help=f"dónde guardar los registros rechazados (por defecto {RUTA_RECHAZOS})")

    filtros = argparse.ArgumentParser(add_help=False)
    filtros.add_argument("--texto", default="", help="texto a buscar en el título (sin distinguir mayúsculas ni tildes)")
    filtros.add_argument("--genero", help="género exacto, p. ej. Drama (ver el comando 'generos')")
    filtros.add_argument("--desde", type=int, help="año de estreno mínimo")
    filtros.add_argument("--hasta", type=int, help="año de estreno máximo")

    parser = argparse.ArgumentParser(
        prog="python -m src.main",
        description="Catálogo de películas: búsqueda, fichas y listas ordenadas por valoración.",
    )
    sub = parser.add_subparsers(dest="comando", required=True)

    p_buscar = sub.add_parser("buscar", parents=[comunes, filtros],
                              help="buscar películas por título, género y años")
    p_buscar.add_argument("--salida", help="exportar los resultados a .csv o .json")

    p_lista = sub.add_parser("lista", parents=[comunes, filtros],
                             help="lista ordenada por valoración con un mínimo de opiniones")
    p_lista.add_argument("--minimo", type=int, default=3, help="mínimo de valoraciones (por defecto 3)")
    p_lista.add_argument("--limite", type=int, default=10, help="cantidad máxima de películas (por defecto 10)")
    p_lista.add_argument("--salida", default="outputs/lista.csv",
                         help="archivo de salida .csv o .json (por defecto outputs/lista.csv)")

    p_ficha = sub.add_parser("ficha", parents=[comunes], help="ver la ficha de una película por id")
    p_ficha.add_argument("--id", type=int, required=True, help="movieId de la película")

    sub.add_parser("generos", parents=[comunes], help="listar los géneros disponibles")
    return parser


def imprimir_resumen(resumen: dict, ruta_rechazos) -> None:
    print(
        f"Datos: {resumen['peliculas_validas']}/{resumen['peliculas_leidas']} películas válidas, "
        f"{resumen['valoraciones_validas']}/{resumen['valoraciones_leidas']} valoraciones válidas. "
        f"Rechazos: {resumen['rechazos']} (detalle en {ruta_rechazos})"
    )
    for motivo, cantidad in resumen["rechazos_por_motivo"].items():
        print(f"  - {motivo}: {cantidad}")
    print()


def imprimir_tabla(filas: list[dict], con_posicion: bool) -> None:
    encabezado = f"{'#':>3}  " if con_posicion else ""
    print(f"{encabezado}{'id':>6}  {'título':<45} {'año':>4}  {'n':>4}  {'media':>5}  géneros")
    for fila in filas:
        prefijo = f"{fila['posicion']:>3}  " if con_posicion else ""
        titulo = fila["titulo"] if len(fila["titulo"]) <= 45 else fila["titulo"][:44] + "…"
        anio = fila["anio"] if fila["anio"] != "" else "?"
        media = f"{fila['media']:.2f}" if fila["media"] != "" else "-"
        generos = fila["generos"].replace("|", ", ") or "(sin géneros)"
        print(f"{prefijo}{fila['movieId']:>6}  {titulo:<45} {anio:>4}  "
              f"{fila['cantidad_valoraciones']:>4}  {media:>5}  {generos}")


def ejecutar(args) -> int:
    """Coordina la lectura, la operación pedida y la salida. Devuelve el código de salida."""
    consulta = None
    if args.comando in ("buscar", "lista"):
        consulta = ConsultaCatalogo(
            texto=args.texto,
            genero=args.genero,
            anio_desde=args.desde,
            anio_hasta=args.hasta,
            minimo_valoraciones=getattr(args, "minimo", 1),
            limite=getattr(args, "limite", None),
        )

    preparado = preparar_catalogo(args.peliculas, args.valoraciones)
    guardar_rechazos(preparado.rechazos, args.rechazos)
    imprimir_resumen(preparado.resumen(), args.rechazos)
    catalogo = preparado.catalogo

    if args.comando == "generos":
        for genero, cantidad in generos_disponibles(catalogo):
            print(f"{genero:<20} {cantidad:>5} películas")
        return 0

    if args.comando == "ficha":
        pelicula = buscar_pelicula(catalogo, args.id)
        if pelicula is None:
            print(f"No existe una película con id {args.id} en el catálogo válido.")
            return 1
        media = f"{pelicula.media:.2f}" if pelicula.media is not None else "sin valoraciones"
        print(f"Película {pelicula.id}: {pelicula.titulo}")
        print(f"  Año:          {pelicula.anio if pelicula.anio is not None else 'desconocido'}")
        print(f"  Géneros:      {', '.join(pelicula.generos) or '(sin géneros)'}")
        print(f"  Valoraciones: {pelicula.cantidad}")
        print(f"  Media:        {media}")
        return 0

    validar_genero_conocido(catalogo, consulta.genero)

    if args.comando == "buscar":
        encontradas = buscar_titulos(catalogo, consulta)
        print(f"Búsqueda ({consulta.describir()}): {len(encontradas)} película(s)")
        filas = [p.a_fila() for p in encontradas]
        if filas:
            imprimir_tabla(filas, con_posicion=False)
        else:
            print("No hay películas que coincidan con la búsqueda.")
        if args.salida:
            columnas = tuple(c for c in COLUMNAS_LISTA if c != "posicion")
            print(f"\nResultados guardados en {guardar_tabla(filas, columnas, args.salida)}")
        return 0

    # comando "lista"
    lista = generar_lista(catalogo, consulta)
    verificar_lista(lista, consulta)
    candidatas = buscar_titulos(catalogo, consulta)
    excluidas = sum(1 for p in candidatas if not consulta.cumple_minimo(p))
    print(f"Lista ({consulta.describir()}; mínimo de valoraciones: {consulta.minimo_valoraciones}; "
          f"límite: {consulta.limite}):")
    print(f"  {len(candidatas)} película(s) coinciden con los filtros; "
          f"{excluidas} quedan fuera por no alcanzar el mínimo.\n")
    filas = lista_a_filas(lista)
    if filas:
        imprimir_tabla(filas, con_posicion=True)
    else:
        print("Ninguna película cumple los filtros y el mínimo de valoraciones.")
    print(f"\nLista guardada en {guardar_tabla(filas, COLUMNAS_LISTA, args.salida)}")
    return 0


def main(argv=None) -> int:
    args = crear_parser().parse_args(argv)
    try:
        return ejecutar(args)
    except (ErrorLectura, ErrorEsquema, ErrorValidacion, ErrorResultado) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
