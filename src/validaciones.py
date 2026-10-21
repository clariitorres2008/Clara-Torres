"""Reglas de validación y conversión de campos individuales."""

import math
import re
import unicodedata

RE_ENTERO_NO_NEGATIVO = re.compile(r"\d+")

# Título con el año entre paréntesis al final, p. ej. "Toy Story (1995)" o "Babylon 5 (1994-1998)"
RE_TITULO_ANIO = re.compile(
    r"^(?P<titulo>.+?)\s*\((?P<anio>\d{4})(?:\s*[-–]\s*(?:\d{4})?)?\)\s*$"
)

ANIO_MINIMO = 1874
ANIO_MAXIMO = 2030

PUNTAJE_MINIMO = 0.5
PUNTAJE_MAXIMO = 5.0

SIN_GENEROS = "(no genres listed)"


class ErrorValidacion(ValueError):
    """Un valor no cumple una regla del dominio."""

    def __init__(self, mensaje: str, codigo: str = "invalido"):
        super().__init__(mensaje)
        self.codigo = codigo


def es_faltante(valor) -> bool:
    """True si el valor está ausente: None (null en JSON) o texto vacío."""
    return valor is None or (isinstance(valor, str) and valor.strip() == "")


def validar_id(valor, campo: str) -> int:
    """Convierte un identificador a entero positivo (movieId, userId)."""
    if es_faltante(valor):
        raise ErrorValidacion(f"{campo} faltante", "faltante")
    if isinstance(valor, bool):
        raise ErrorValidacion(f"{campo} inválido: {valor!r}", "id_invalido")
    texto = str(valor).strip()
    if not RE_ENTERO_NO_NEGATIVO.fullmatch(texto):
        raise ErrorValidacion(
            f"{campo} inválido: {valor!r} (se espera un entero positivo)",
            "id_invalido",
        )
    numero = int(texto)
    if numero == 0:
        raise ErrorValidacion(f"{campo} inválido: debe ser mayor que cero", "id_invalido")
    return numero


def validar_timestamp(valor) -> int:
    """Convierte un timestamp Unix (segundos desde 1970-01-01 UTC) a entero."""
    if es_faltante(valor):
        raise ErrorValidacion("timestamp faltante", "faltante")
    texto = str(valor).strip()
    if isinstance(valor, bool) or not RE_ENTERO_NO_NEGATIVO.fullmatch(texto):
        raise ErrorValidacion(f"timestamp inválido: {valor!r}", "formato")
    return int(texto)


def separar_titulo_anio(titulo_crudo) -> tuple[str, int | None]:
    """Separa "Toy Story (1995)" en ("Toy Story", 1995); sin año devuelve (titulo, None)."""
    if es_faltante(titulo_crudo):
        raise ErrorValidacion("título faltante", "faltante")
    texto = " ".join(str(titulo_crudo).split())
    coincidencia = RE_TITULO_ANIO.match(texto)
    if coincidencia is None:
        return texto, None
    anio = int(coincidencia.group("anio"))
    if not ANIO_MINIMO <= anio <= ANIO_MAXIMO:
        raise ErrorValidacion(
            f"año fuera de rango en el título: {anio} "
            f"(se acepta {ANIO_MINIMO}-{ANIO_MAXIMO})",
            "anio_fuera_de_rango",
        )
    return coincidencia.group("titulo"), anio


def parsear_generos(valor) -> tuple[str, ...]:
    """Convierte "Action|Comedy" en ("Action", "Comedy")."""
    if es_faltante(valor) or str(valor).strip() == SIN_GENEROS:
        return ()
    generos = []
    for parte in str(valor).split("|"):
        genero = parte.strip()
        if genero and genero not in generos:
            generos.append(genero)
    return tuple(generos)


def validar_puntaje(valor) -> float:
    """Convierte una calificación y comprueba la escala 0.5-5.0 en pasos de 0.5."""
    if es_faltante(valor):
        raise ErrorValidacion("puntaje faltante", "faltante")
    if isinstance(valor, bool):
        raise ErrorValidacion(f"puntaje no numérico: {valor!r}", "formato")
    try:
        puntaje = float(str(valor).strip())
    except ValueError:
        raise ErrorValidacion(f"puntaje no numérico: {valor!r}", "formato") from None
    if not math.isfinite(puntaje):
        raise ErrorValidacion(f"puntaje no numérico: {valor!r}", "formato")
    if not PUNTAJE_MINIMO <= puntaje <= PUNTAJE_MAXIMO:
        raise ErrorValidacion(
            f"puntaje fuera de escala: {puntaje} "
            f"(se acepta {PUNTAJE_MINIMO}-{PUNTAJE_MAXIMO})",
            "fuera_de_escala",
        )
    if not math.isclose(puntaje * 2, round(puntaje * 2)):
        raise ErrorValidacion(
            f"puntaje {puntaje} no es múltiplo de media estrella", "fuera_de_escala"
        )
    return puntaje


def normalizar_texto(texto: str) -> str:
    """Pasa a minúsculas y quita tildes."""
    descompuesto = unicodedata.normalize("NFKD", texto)
    sin_tildes = "".join(c for c in descompuesto if not unicodedata.combining(c))
    return " ".join(sin_tildes.casefold().split())
