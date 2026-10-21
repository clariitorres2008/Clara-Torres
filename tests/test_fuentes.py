"""Pruebas de lectura: CSV, JSON y errores de archivo."""

import tempfile
import unittest
from pathlib import Path

from src.fuentes import ErrorLectura, FuenteCSV, FuenteJSON, fuente_para_ruta


class TestFuentes(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def escribir(self, nombre, contenido):
        ruta = self.dir / nombre
        ruta.write_text(contenido, encoding="utf-8")
        return ruta

    def test_csv_normal(self):
        ruta = self.escribir("m.csv", 'movieId,title,genres\n1,"Matrix, The (1999)",Action\n')
        registros = FuenteCSV().cargar(ruta)
        self.assertEqual(registros, [{"movieId": "1", "title": "Matrix, The (1999)",
                                      "genres": "Action", "_registro": 1}])

    def test_json_normal_y_con_clave_registros(self):
        lista = self.escribir("a.json", '[{"movieId": 1, "title": "Up (2009)"}]')
        envuelto = self.escribir("b.json", '{"fuente": "x", "registros": [{"movieId": 1, "title": "Up (2009)"}]}')
        self.assertEqual(FuenteJSON().cargar(lista), FuenteJSON().cargar(envuelto))

    def test_csv_fila_con_columnas_de_mas_queda_marcada(self):
        ruta = self.escribir("m.csv", "movieId,title,genres\n1,Up (2009),Drama,EXTRA\n")
        self.assertTrue(FuenteCSV().cargar(ruta)[0]["_columnas_extra"])

    def test_archivo_inexistente(self):
        with self.assertRaises(ErrorLectura):
            FuenteCSV().cargar(self.dir / "no_existe.csv")

    def test_archivos_vacios_no_se_aceptan(self):
        with self.assertRaises(ErrorLectura):
            FuenteCSV().cargar(self.escribir("vacio.csv", ""))
        with self.assertRaises(ErrorLectura):
            FuenteCSV().cargar(self.escribir("solo_encabezado.csv", "movieId,title,genres\n"))
        with self.assertRaises(ErrorLectura):
            FuenteJSON().cargar(self.escribir("vacio.json", "[]"))

    def test_json_mal_formado_o_con_otra_estructura(self):
        with self.assertRaises(ErrorLectura) as ctx:
            FuenteJSON().cargar(self.escribir("roto.json", '[{"movieId": 1,'))
        self.assertIn("línea", str(ctx.exception))
        with self.assertRaises(ErrorLectura):
            FuenteJSON().cargar(self.escribir("objeto.json", '{"movieId": 1}'))
        with self.assertRaises(ErrorLectura):
            FuenteJSON().cargar(self.escribir("numeros.json", "[1, 2, 3]"))

    def test_eleccion_de_fuente_por_extension(self):
        self.assertIsInstance(fuente_para_ruta("x.CSV"), FuenteCSV)
        self.assertIsInstance(fuente_para_ruta("x.json"), FuenteJSON)
        with self.assertRaises(ErrorLectura):
            fuente_para_ruta("x.xlsx")


if __name__ == "__main__":
    unittest.main()
