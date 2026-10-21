"""Flujo de procesamiento: leer -> validar -> limpiar -> analizar -> comunicar."""

import csv
import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from .fuentes import fuente_para_ruta
from .modelo import ConsultaCatalogo, Pelicula
from .validaciones import (
    ErrorValidacion,
    normalizar_texto,
    parsear_generos,
    separar_titulo_anio,
    validar_id,
    validar_puntaje,
    validar_timestamp,
)

COLUMNAS_PELICULAS = ("movieId", "title", "genres")
COLUMNAS_VALORACIONES = ("userId", "movieId", "rating", "timestamp")
COLUMNAS_RECHAZOS = ("archivo", "registro", "codigo", "motivo", "datos")
COLUMNAS_LISTA = (
    "posicion", "movieId", "titulo", "anio", "generos", "cantidad_valoraciones", "media",
)


class ErrorEsquema(Exception):
    """A la tabla le faltan columnas necesarias para el análisis."""


class ErrorResultado(Exception):
    """El resultado no cumple una propiedad que debería cumplir siempre."""


@dataclass
class ResultadoPreparacion:
    """Lo que devuelve la etapa de preparación: catálogo listo y trazabilidad."""

    catalogo: dict[int, Pelicula]
    rechazos: list[dict] = field(default_factory=list)
    peliculas_leidas: int = 0
    valoraciones_leidas: int = 0
    valoraciones_validas: int = 0

    def resumen(self) -> dict:
        por_codigo = Counter((r["archivo"], r["codigo"]) for r in self.rechazos)
        return {
            "peliculas_leidas": self.peliculas_leidas,
            "peliculas_validas": len(self.catalogo),
            "valoraciones_leidas": self.valoraciones_leidas,
            "valoraciones_validas": self.valoraciones_validas,
            "rechazos": len(self.rechazos),
            "rechazos_por_motivo": {f"{a}/{c}": n for (a, c), n in sorted(por_codigo.items())},
        }


# --- Lectura e inspección ---------------------------------------------------

def normalizar_campos(registros: list[dict]) -> list[dict]:
    """Quita espacios en nombres de columna y en valores de texto."""
    normalizados = []
    for registro in registros:
        nuevo = {}
        for clave, valor in registro.items():
            clave = clave.strip() if isinstance(clave, str) else clave
            nuevo[clave] = valor.strip() if isinstance(valor, str) else valor
        normalizados.append(nuevo)
    return normalizados


def validar_esquema(registros: list[dict], columnas: tuple[str, ...], nombre: str) -> None:
    """Comprueba que estén las columnas necesarias."""
    presentes = set()
    for registro in registros:
        presentes.update(registro)
    faltantes = [c for c in columnas if c not in presentes]
    if faltantes:
        raise ErrorEsquema(
            f"Al archivo de {nombre} le faltan columnas: {', '.join(faltantes)}. "
            f"Se esperan: {', '.join(columnas)}"
        )


def cargar_tabla(ruta, columnas: tuple[str, ...], nombre: str) -> list[dict]:
    """Lee un CSV o JSON, normaliza los campos y valida el esquema."""
    registros = fuente_para_ruta(ruta).cargar(ruta)
    registros = normalizar_campos(registros)
    validar_esquema(registros, columnas, nombre)
    return registros


def crear_rechazo(archivo: str, registro: dict, error: ErrorValidacion) -> dict:
    """Arma el registro de un rechazo conservando los datos originales."""
    datos = {k: v for k, v in registro.items() if not str(k).startswith("_")}
    return {
        "archivo": archivo,
        "registro": registro.get("_registro", ""),
        "codigo": error.codigo,
        "motivo": str(error),
        "datos": json.dumps(datos, ensure_ascii=False),
    }


# --- Limpieza y transformación ---------------------------------------------

def construir_catalogo(registros: list[dict]) -> tuple[dict[int, Pelicula], list[dict]]:
    """Crea el índice {movieId: Pelicula} y registra los registros rechazados."""
    catalogo: dict[int, Pelicula] = {}
    rechazos: list[dict] = []
    for registro in registros:
        try:
            if registro.get("_columnas_extra"):
                raise ErrorValidacion("la fila tiene más columnas que el encabezado", "formato")
            id_pelicula = validar_id(registro.get("movieId"), "movieId")
            if id_pelicula in catalogo:
                raise ErrorValidacion(
                    f"movieId duplicado ({id_pelicula}); se conserva el primer registro",
                    "duplicado",
                )
            titulo, anio = separar_titulo_anio(registro.get("title"))
            generos = parsear_generos(registro.get("genres"))
        except ErrorValidacion as error:
            rechazos.append(crear_rechazo("peliculas", registro, error))
            continue
        catalogo[id_pelicula] = Pelicula(id_pelicula, titulo, anio, generos)
    return catalogo, rechazos


def acumular_valoraciones(
    catalogo: dict[int, Pelicula], registros: list[dict]
) -> tuple[int, list[dict]]:
    """Valida las calificaciones y las suma a cada película del catálogo."""
    if any(p.cantidad for p in catalogo.values()):
        raise ValueError("El catálogo ya tiene valoraciones: acumular dos veces duplicaría opiniones")

    vigentes: dict[tuple[int, int], tuple[int, float, dict]] = {}
    rechazos: list[dict] = []
    for registro in registros:
        try:
            if registro.get("_columnas_extra"):
                raise ErrorValidacion("la fila tiene más columnas que el encabezado", "formato")
            usuario = validar_id(registro.get("userId"), "userId")
            id_pelicula = validar_id(registro.get("movieId"), "movieId")
            puntaje = validar_puntaje(registro.get("rating"))
            momento = validar_timestamp(registro.get("timestamp"))
            if id_pelicula not in catalogo:
                raise ErrorValidacion(
                    f"movieId {id_pelicula} no existe en el catálogo", "referencia_inexistente"
                )
        except ErrorValidacion as error:
            rechazos.append(crear_rechazo("valoraciones", registro, error))
            continue

        clave = (usuario, id_pelicula)
        anterior = vigentes.get(clave)
        if anterior is None:
            vigentes[clave] = (momento, puntaje, registro)
        elif momento > anterior[0]:
            rechazos.append(crear_rechazo("valoraciones", anterior[2], ErrorValidacion(
                f"valoración duplicada del usuario {usuario} para la película {id_pelicula}; "
                "se reemplaza por una más reciente", "duplicado")))
            vigentes[clave] = (momento, puntaje, registro)
        else:
            rechazos.append(crear_rechazo("valoraciones", registro, ErrorValidacion(
                f"valoración duplicada del usuario {usuario} para la película {id_pelicula}; "
                "ya existe una igual o más reciente", "duplicado")))

    for (_, id_pelicula), (_, puntaje, _) in vigentes.items():
        catalogo[id_pelicula].agregar_valoracion(puntaje)

    rechazos.sort(key=lambda r: r["registro"] if isinstance(r["registro"], int) else 0)
    return len(vigentes), rechazos


def preparar_catalogo(ruta_peliculas, ruta_valoraciones) -> ResultadoPreparacion:
    """Ejecuta lectura, validación y limpieza de ambas tablas."""
    registros_peliculas = cargar_tabla(ruta_peliculas, COLUMNAS_PELICULAS, "películas")
    registros_valoraciones = cargar_tabla(ruta_valoraciones, COLUMNAS_VALORACIONES, "valoraciones")

    catalogo, rechazos_peliculas = construir_catalogo(registros_peliculas)
    validas, rechazos_valoraciones = acumular_valoraciones(catalogo, registros_valoraciones)

    resultado = ResultadoPreparacion(
        catalogo=catalogo,
        rechazos=rechazos_peliculas + rechazos_valoraciones,
        peliculas_leidas=len(registros_peliculas),
        valoraciones_leidas=len(registros_valoraciones),
        valoraciones_validas=validas,
    )
    verificar_conservacion(resultado)
    return resultado


# --- Operaciones de la aplicación ------------------------------------------

def generos_disponibles(catalogo: dict[int, Pelicula]) -> list[tuple[str, int]]:
    """Lista de (género, cantidad de películas), ordenada por nombre."""
    conteo = Counter(g for p in catalogo.values() for g in p.generos)
    return sorted(conteo.items(), key=lambda item: normalizar_texto(item[0]))


def validar_genero_conocido(catalogo: dict[int, Pelicula], genero: str | None) -> None:
    """Verifica que el género exista en el catálogo."""
    if not genero:
        return
    conocidos = [g for g, _ in generos_disponibles(catalogo)]
    if normalizar_texto(genero) not in {normalizar_texto(g) for g in conocidos}:
        raise ErrorValidacion(
            f"Género desconocido: {genero!r}. Disponibles: {', '.join(conocidos)}", "parametro"
        )


def buscar_pelicula(catalogo: dict[int, Pelicula], id_pelicula: int) -> Pelicula | None:
    """Devuelve la película con ese id o None si no existe."""
    return catalogo.get(id_pelicula)


def buscar_titulos(catalogo: dict[int, Pelicula], consulta: ConsultaCatalogo) -> list[Pelicula]:
    """Películas que cumplen los filtros, ordenadas alfabéticamente."""
    encontradas = [p for p in catalogo.values() if consulta.coincide(p)]
    return sorted(encontradas, key=lambda p: (normalizar_texto(p.titulo), p.id))


def clave_orden_lista(pelicula: Pelicula) -> tuple:
    """Media descendente, más valoraciones, título y movieId."""
    return (-pelicula.media, -pelicula.cantidad, normalizar_texto(pelicula.titulo), pelicula.id)


def generar_lista(catalogo: dict[int, Pelicula], consulta: ConsultaCatalogo) -> list[Pelicula]:
    """Lista ordenada de películas con al menos `minimo_valoraciones` calificaciones."""
    candidatas = [p for p in buscar_titulos(catalogo, consulta) if consulta.cumple_minimo(p)]
    candidatas.sort(key=clave_orden_lista)
    if consulta.limite is not None:
        candidatas = candidatas[: consulta.limite]
    return candidatas


# --- Verificación del resultado ---------------------------------------------

def verificar_conservacion(resultado: ResultadoPreparacion) -> None:
    """Toda calificación válida debe estar contada exactamente una vez."""
    total = sum(p.cantidad for p in resultado.catalogo.values())
    if total != resultado.valoraciones_validas:
        raise ErrorResultado(
            f"Se contaron {total} valoraciones pero hay {resultado.valoraciones_validas} válidas"
        )
    if resultado.valoraciones_validas + sum(
        1 for r in resultado.rechazos if r["archivo"] == "valoraciones"
    ) != resultado.valoraciones_leidas:
        raise ErrorResultado("Valoraciones leídas != válidas + rechazadas")


def verificar_lista(lista: list[Pelicula], consulta: ConsultaCatalogo) -> None:
    """Comprueba propiedades que la lista debe cumplir siempre."""
    for pelicula in lista:
        if not consulta.cumple_minimo(pelicula):
            raise ErrorResultado(f"{pelicula.titulo_completo} no alcanza el mínimo de valoraciones")
        if not consulta.coincide(pelicula):
            raise ErrorResultado(f"{pelicula.titulo_completo} no cumple los filtros")
        if not 0.5 <= pelicula.media <= 5.0:
            raise ErrorResultado(f"Media fuera de escala en {pelicula.titulo_completo}")
    claves = [clave_orden_lista(p) for p in lista]
    if claves != sorted(claves):
        raise ErrorResultado("La lista no respeta el orden documentado")
    if len({p.id for p in lista}) != len(lista):
        raise ErrorResultado("La lista tiene películas repetidas")
    if consulta.limite is not None and len(lista) > consulta.limite:
        raise ErrorResultado("La lista supera el límite pedido")


# --- Comunicación del resultado --------------------------------------------

def lista_a_filas(lista: list[Pelicula]) -> list[dict]:
    return [{"posicion": i, **p.a_fila()} for i, p in enumerate(lista, start=1)]


def guardar_tabla(filas: list[dict], columnas: tuple[str, ...], ruta) -> Path:
    """Guarda filas en CSV o JSON según la extensión (crea la carpeta si falta)."""
    ruta = Path(ruta)
    extension = ruta.suffix.lower()
    if extension not in (".csv", ".json"):
        raise ErrorValidacion(f"La salida debe ser .csv o .json: {ruta}", "parametro")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    if extension == ".csv":
        with ruta.open("w", encoding="utf-8", newline="") as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=columnas, extrasaction="ignore")
            escritor.writeheader()
            escritor.writerows(filas)
    else:
        with ruta.open("w", encoding="utf-8") as archivo:
            json.dump([{c: f.get(c, "") for c in columnas} for f in filas],
                      archivo, ensure_ascii=False, indent=2)
            archivo.write("\n")
    return ruta


def guardar_rechazos(rechazos: list[dict], ruta) -> Path:
    return guardar_tabla(rechazos, COLUMNAS_RECHAZOS, ruta)
