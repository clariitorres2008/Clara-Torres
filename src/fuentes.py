"""Lectura de datos tabulares desde CSV o JSON."""

import csv
import json
from abc import ABC, abstractmethod
from pathlib import Path


class ErrorLectura(Exception):
    """El archivo no existe, no se puede leer o no tiene la estructura esperada."""


class FuenteDatos(ABC):
    """Contrato común para cualquier fuente de datos tabulares."""

    def cargar(self, ruta) -> list[dict]:
        """Lee el archivo y devuelve una lista de registros (diccionarios)."""
        ruta = Path(ruta)
        if not ruta.is_file():
            raise ErrorLectura(f"No existe el archivo: {ruta}")
        try:
            registros = self._leer(ruta)
        except UnicodeDecodeError:
            raise ErrorLectura(f"{ruta} no está codificado en UTF-8") from None
        if not registros:
            raise ErrorLectura(f"{ruta} no contiene registros")
        for posicion, registro in enumerate(registros, start=1):
            registro["_registro"] = posicion
        return registros

    @abstractmethod
    def _leer(self, ruta: Path) -> list[dict]:
        """Lee el archivo concreto y devuelve los registros sin numerar."""


class FuenteCSV(FuenteDatos):
    """CSV con una fila de encabezado, separado por comas, en UTF-8."""

    def _leer(self, ruta: Path) -> list[dict]:
        with ruta.open(encoding="utf-8-sig", newline="") as archivo:
            lector = csv.DictReader(archivo)
            if not lector.fieldnames:
                raise ErrorLectura(f"{ruta} está vacío o no tiene encabezado")
            registros = []
            for fila in lector:
                sobrantes = fila.pop(None, None)
                if sobrantes:
                    fila["_columnas_extra"] = True
                registros.append(fila)
        return registros


class FuenteJSON(FuenteDatos):
    """JSON con una lista de objetos, uno por registro."""

    def _leer(self, ruta: Path) -> list[dict]:
        with ruta.open(encoding="utf-8") as archivo:
            try:
                contenido = json.load(archivo)
            except json.JSONDecodeError as error:
                raise ErrorLectura(
                    f"{ruta} no es un JSON válido (línea {error.lineno}, "
                    f"columna {error.colno}): {error.msg}"
                ) from None
        if isinstance(contenido, dict) and "registros" in contenido:
            contenido = contenido["registros"]
        if not isinstance(contenido, list):
            raise ErrorLectura(f"{ruta} debe contener una lista de objetos")
        for posicion, elemento in enumerate(contenido, start=1):
            if not isinstance(elemento, dict):
                raise ErrorLectura(f"{ruta}: el elemento {posicion} no es un objeto JSON")
        return contenido


FUENTES_POR_EXTENSION = {".csv": FuenteCSV, ".json": FuenteJSON}


def fuente_para_ruta(ruta) -> FuenteDatos:
    """Elige la fuente adecuada según la extensión del archivo."""
    extension = Path(ruta).suffix.lower()
    clase = FUENTES_POR_EXTENSION.get(extension)
    if clase is None:
        formatos = ", ".join(FUENTES_POR_EXTENSION)
        raise ErrorLectura(f"Formato no soportado: {ruta} (se aceptan {formatos})")
    return clase()
