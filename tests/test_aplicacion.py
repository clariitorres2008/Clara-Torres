"""Pruebas de punta a punta con la muestra de data/muestra/."""

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from src.main import main
from src.pipeline import preparar_catalogo

MUESTRA = Path(__file__).resolve().parent.parent / "data" / "muestra"


def ejecutar(*argumentos):
    """Corre la aplicación capturando la salida; devuelve (código, stdout, stderr)."""
    salida, errores = io.StringIO(), io.StringIO()
    with redirect_stdout(salida), redirect_stderr(errores):
        codigo = main(list(argumentos))
    return codigo, salida.getvalue(), errores.getvalue()


class TestEquivalenciaCSVJSON(unittest.TestCase):
    def test_csv_y_json_producen_el_mismo_catalogo(self):
        desde_csv = preparar_catalogo(MUESTRA / "movies.csv", MUESTRA / "ratings.csv")
        desde_json = preparar_catalogo(MUESTRA / "movies.json", MUESTRA / "ratings.json")
        self.assertEqual(desde_csv.catalogo, desde_json.catalogo)
        self.assertEqual(desde_csv.resumen(), desde_json.resumen())
        clave = lambda r: (r["archivo"], r["registro"], r["codigo"])
        self.assertEqual([clave(r) for r in desde_csv.rechazos], [clave(r) for r in desde_json.rechazos])

    def test_muestra_cumple_el_minimo_de_observaciones(self):
        resultado = preparar_catalogo(MUESTRA / "movies.csv", MUESTRA / "ratings.csv")
        self.assertGreaterEqual(resultado.valoraciones_validas, 50)


class TestAplicacion(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def comunes(self):
        return ["--rechazos", str(self.dir / "rechazos.csv")]

    def test_lista_es_reproducible(self):
        for nombre in ("a.csv", "b.csv"):
            codigo, _, _ = ejecutar("lista", "--minimo", "3", "--salida", str(self.dir / nombre), *self.comunes())
            self.assertEqual(codigo, 0)
        self.assertEqual((self.dir / "a.csv").read_text(encoding="utf-8"),
                         (self.dir / "b.csv").read_text(encoding="utf-8"))
        self.assertTrue((self.dir / "rechazos.csv").exists())

    def test_ficha_existente_e_inexistente(self):
        codigo, salida, _ = ejecutar("ficha", "--id", "1", *self.comunes())
        self.assertEqual(codigo, 0)
        self.assertIn("Toy Story", salida)
        codigo, salida, _ = ejecutar("ficha", "--id", "12345", *self.comunes())
        self.assertEqual(codigo, 1)
        self.assertIn("No existe", salida)

    def test_busqueda_sin_resultados_responde_explicitamente(self):
        codigo, salida, _ = ejecutar("buscar", "--texto", "pelicula que no existe", *self.comunes())
        self.assertEqual(codigo, 0)
        self.assertIn("No hay películas", salida)

    def test_errores_de_uso_dan_mensaje_comprensible(self):
        codigo, _, errores = ejecutar("lista", "--desde", "2010", "--hasta", "2000", *self.comunes())
        self.assertEqual(codigo, 1)
        self.assertIn("mayor que el año hasta", errores)
        codigo, _, errores = ejecutar("lista", "--genero", "Dramaa", *self.comunes())
        self.assertEqual(codigo, 1)
        self.assertIn("Género desconocido", errores)

    def test_archivo_inexistente_no_se_oculta(self):
        codigo, _, errores = ejecutar("generos", "--peliculas", str(self.dir / "nada.csv"), *self.comunes())
        self.assertEqual(codigo, 1)
        self.assertIn("No existe el archivo", errores)


if __name__ == "__main__":
    unittest.main()
