"""Pruebas de las reglas de campo, incluida la expresión regular del año."""

import unittest

from src.validaciones import (
    ErrorValidacion,
    normalizar_texto,
    parsear_generos,
    separar_titulo_anio,
    validar_id,
    validar_puntaje,
)


class TestSepararTituloAnio(unittest.TestCase):
    def test_caso_normal(self):
        self.assertEqual(separar_titulo_anio("Toy Story (1995)"), ("Toy Story", 1995))

    def test_parentesis_dentro_del_titulo(self):
        self.assertEqual(
            separar_titulo_anio("Secret in Their Eyes, The (El secreto de sus ojos) (2009)"),
            ("Secret in Their Eyes, The (El secreto de sus ojos)", 2009),
        )
        self.assertEqual(separar_titulo_anio("(500) Days of Summer (2009)"),
                         ("(500) Days of Summer", 2009))

    def test_rango_de_anios_de_series(self):
        self.assertEqual(separar_titulo_anio("Babylon 5 (1994-1998)"), ("Babylon 5", 1994))

    def test_titulo_sin_anio_se_conserva(self):
        self.assertEqual(separar_titulo_anio("Cosmos"), ("Cosmos", None))
        self.assertEqual(separar_titulo_anio("Rocky (1976) Remastered"), ("Rocky (1976) Remastered", None))

    def test_espacios_extra(self):
        self.assertEqual(separar_titulo_anio("  Up   (2009)  "), ("Up", 2009))

    def test_anio_con_forma_valida_pero_fuera_de_rango(self):
        with self.assertRaises(ErrorValidacion) as ctx:
            separar_titulo_anio("Movie From The Future (2099)")
        self.assertEqual(ctx.exception.codigo, "anio_fuera_de_rango")

    def test_titulo_faltante(self):
        for valor in ("", "   ", None):
            with self.assertRaises(ErrorValidacion):
                separar_titulo_anio(valor)


class TestValidarId(unittest.TestCase):
    def test_validos_desde_csv_y_json(self):
        self.assertEqual(validar_id("12", "movieId"), 12)
        self.assertEqual(validar_id(12, "movieId"), 12)

    def test_invalidos(self):
        for valor in ("abc", "-3", "1.5", "0", 12.0, True, "", None):
            with self.subTest(valor=valor), self.assertRaises(ErrorValidacion):
                validar_id(valor, "movieId")


class TestValidarPuntaje(unittest.TestCase):
    def test_validos(self):
        self.assertEqual(validar_puntaje("3.5"), 3.5)
        self.assertEqual(validar_puntaje(4), 4.0)
        self.assertEqual(validar_puntaje("0.5"), 0.5)
        self.assertEqual(validar_puntaje(5.0), 5.0)

    def test_fuera_de_escala_o_mal_formado(self):
        for valor in ("6.0", "0", "0.25", "3.7", "muy buena", "nan", "", None, False):
            with self.subTest(valor=valor), self.assertRaises(ErrorValidacion):
                validar_puntaje(valor)


class TestOtrosCampos(unittest.TestCase):
    def test_generos(self):
        self.assertEqual(parsear_generos("Action|Comedy"), ("Action", "Comedy"))
        self.assertEqual(parsear_generos("(no genres listed)"), ())
        self.assertEqual(parsear_generos("Drama||Drama"), ("Drama",))

    def test_normalizar_texto(self):
        self.assertEqual(normalizar_texto("  Misérables,  LES "), "miserables, les")


if __name__ == "__main__":
    unittest.main()
