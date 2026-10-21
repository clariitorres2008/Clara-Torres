"""Convierte un CSV (por ejemplo, el movies.csv real de MovieLens) a JSON equivalente.

Uso (desde la raíz del proyecto):
    python scripts/csv_a_json.py data/raw/ml-latest-small/movies.csv data/raw/movies.json
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.fuentes import FuenteCSV  # noqa: E402


def convertir_valor(valor: str):
    if valor == "":
        return None
    for tipo in (int, float):
        try:
            return tipo(valor)
        except ValueError:
            pass
    return valor


def main(origen: str, destino: str) -> None:
    registros = FuenteCSV().cargar(origen)
    salida = [
        {k: convertir_valor(v) for k, v in r.items() if not k.startswith("_")}
        for r in registros
    ]
    Path(destino).parent.mkdir(parents=True, exist_ok=True)
    with open(destino, "w", encoding="utf-8") as archivo:
        json.dump(salida, archivo, ensure_ascii=False)
    print(f"{len(salida)} registros escritos en {destino}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Uso: python scripts/csv_a_json.py ORIGEN.csv DESTINO.json")
    main(sys.argv[1], sys.argv[2])
