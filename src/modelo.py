"""Clases del dominio: la película del catálogo y la consulta de quien usa el programa."""

from dataclasses import dataclass

from .validaciones import (
    ANIO_MAXIMO,
    ANIO_MINIMO,
    ErrorValidacion,
    normalizar_texto,
    validar_puntaje,
)


@dataclass
class Pelicula:
    """Una película del catálogo con sus valoraciones acumuladas."""

    id: int
    titulo: str
    anio: int | None
    generos: tuple[str, ...]
    cantidad: int = 0
    suma: float = 0.0

    def agregar_valoracion(self, puntaje: float) -> None:
        """Suma una calificación."""
        puntaje = validar_puntaje(puntaje)
        self.cantidad += 1
        self.suma += puntaje

    @property
    def media(self) -> float | None:
        """Media de las calificaciones, o None si todavía no tiene ninguna."""
        if self.cantidad == 0:
            return None
        return self.suma / self.cantidad

    def tiene_genero(self, genero: str) -> bool:
        """True si la película pertenece al género (sin distinguir mayúsculas)."""
        buscado = normalizar_texto(genero)
        return any(normalizar_texto(g) == buscado for g in self.generos)

    @property
    def titulo_completo(self) -> str:
        """Título con el año entre paréntesis, si se conoce."""
        return f"{self.titulo} ({self.anio})" if self.anio is not None else self.titulo

    def a_fila(self) -> dict:
        """Representación plana para exportar a CSV o JSON."""
        return {
            "movieId": self.id,
            "titulo": self.titulo,
            "anio": self.anio if self.anio is not None else "",
            "generos": "|".join(self.generos),
            "cantidad_valoraciones": self.cantidad,
            "media": round(self.media, 3) if self.media is not None else "",
        }


@dataclass(frozen=True)
class ConsultaCatalogo:
    """Filtros que elige quien usa el programa, ya validados."""

    texto: str = ""
    genero: str | None = None
    anio_desde: int | None = None
    anio_hasta: int | None = None
    minimo_valoraciones: int = 1
    limite: int | None = None

    def __post_init__(self):
        object.__setattr__(self, "texto", (self.texto or "").strip())
        genero = (self.genero or "").strip() or None
        object.__setattr__(self, "genero", genero)

        for nombre in ("anio_desde", "anio_hasta"):
            valor = getattr(self, nombre)
            if valor is not None and not (ANIO_MINIMO <= valor <= ANIO_MAXIMO):
                raise ErrorValidacion(
                    f"{nombre} debe estar entre {ANIO_MINIMO} y {ANIO_MAXIMO}", "parametro"
                )
        if (
            self.anio_desde is not None
            and self.anio_hasta is not None
            and self.anio_desde > self.anio_hasta
        ):
            raise ErrorValidacion(
                f"El año desde ({self.anio_desde}) es mayor que el año hasta ({self.anio_hasta})",
                "parametro",
            )
        if self.minimo_valoraciones < 1:
            raise ErrorValidacion("El mínimo de valoraciones debe ser al menos 1", "parametro")
        if self.limite is not None and self.limite < 1:
            raise ErrorValidacion("El límite debe ser al menos 1", "parametro")

    @property
    def filtra_por_anio(self) -> bool:
        return self.anio_desde is not None or self.anio_hasta is not None

    def coincide(self, pelicula: Pelicula) -> bool:
        """True si la película cumple texto, género y rango de años."""
        if self.texto and normalizar_texto(self.texto) not in normalizar_texto(pelicula.titulo):
            return False
        if self.genero and not pelicula.tiene_genero(self.genero):
            return False
        if self.filtra_por_anio:
            if pelicula.anio is None:
                return False
            if self.anio_desde is not None and pelicula.anio < self.anio_desde:
                return False
            if self.anio_hasta is not None and pelicula.anio > self.anio_hasta:
                return False
        return True

    def cumple_minimo(self, pelicula: Pelicula) -> bool:
        """True si la película tiene suficientes valoraciones para entrar en la lista."""
        return pelicula.cantidad >= self.minimo_valoraciones

    def describir(self) -> str:
        """Descripción legible de los filtros, para encabezar los resultados."""
        partes = []
        if self.texto:
            partes.append(f'título contiene "{self.texto}"')
        if self.genero:
            partes.append(f"género {self.genero}")
        if self.filtra_por_anio:
            desde = self.anio_desde if self.anio_desde is not None else "..."
            hasta = self.anio_hasta if self.anio_hasta is not None else "..."
            partes.append(f"años {desde}-{hasta}")
        return ", ".join(partes) if partes else "sin filtros"
