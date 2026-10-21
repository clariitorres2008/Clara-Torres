"""Pruebas de la lógica de la aplicación y de las propiedades del resultado."""

import unittest

from src.modelo import ConsultaCatalogo, Pelicula
from src.pipeline import (
    ErrorEsquema,
    ErrorResultado,
    acumular_valoraciones,
    buscar_titulos,
    construir_catalogo,
    generar_lista,
    validar_esquema,
    verificar_lista,
)
from src.validaciones import ErrorValidacion


def pelis(*filas):
    return [{"movieId": i, "title": t, "genres": g} for i, t, g in filas]


def vals(*filas):
    return [{"userId": u, "movieId": m, "rating": r, "timestamp": ts} for u, m, r, ts in filas]


PELICULAS = pelis(
    ("1", "Toy Story (1995)", "Animation|Comedy"),
    ("2", "Heat (1995)", "Action|Crime|Thriller"),
    ("3", "Cosmos", "(no genres listed)"),
    ("4", "Misérables, Les (1995)", "Drama|War"),
)


class TestCatalogo(unittest.TestCase):
    def test_media_y_conteo(self):
        catalogo, _ = construir_catalogo(PELICULAS)
        validas, rechazos = acumular_valoraciones(catalogo, vals((1, "1", "3.0", 10), (2, "1", "5.0", 11)))
        self.assertEqual((validas, rechazos), (2, []))
        self.assertEqual(catalogo[1].cantidad, 2)
        self.assertEqual(catalogo[1].media, 4.0)

    def test_pelicula_sin_valoraciones_tiene_media_desconocida(self):
        catalogo, _ = construir_catalogo(PELICULAS)
        self.assertIsNone(catalogo[3].media)

    def test_movieid_duplicado_conserva_el_primero(self):
        catalogo, rechazos = construir_catalogo(PELICULAS + pelis(("1", "Otra (2000)", "Drama")))
        self.assertEqual(catalogo[1].titulo, "Toy Story")
        self.assertEqual([r["codigo"] for r in rechazos], ["duplicado"])

    def test_referencia_inexistente_no_altera_conteos(self):
        catalogo, _ = construir_catalogo(PELICULAS)
        validas, rechazos = acumular_valoraciones(catalogo, vals((1, "1", "4.0", 1), (1, "99", "5.0", 2)))
        self.assertEqual(validas, 1)
        self.assertEqual(rechazos[0]["codigo"], "referencia_inexistente")
        self.assertEqual(sum(p.cantidad for p in catalogo.values()), 1)

    def test_valoracion_duplicada_no_se_cuenta_dos_veces(self):
        catalogo, _ = construir_catalogo(PELICULAS)
        validas, rechazos = acumular_valoraciones(catalogo, vals((1, "1", "1.0", 10), (1, "1", "5.0", 20)))
        self.assertEqual(validas, 1)
        self.assertEqual(catalogo[1].cantidad, 1)
        self.assertEqual(catalogo[1].media, 5.0)
        self.assertEqual(rechazos[0]["codigo"], "duplicado")

    def test_acumular_dos_veces_no_duplica_opiniones(self):
        catalogo, _ = construir_catalogo(PELICULAS)
        filas = vals((1, "1", "4.0", 1))
        acumular_valoraciones(catalogo, filas)
        with self.assertRaises(ValueError):
            acumular_valoraciones(catalogo, filas)

    def test_conservacion_leidas_igual_validas_mas_rechazadas(self):
        catalogo, _ = construir_catalogo(PELICULAS)
        filas = vals((1, "1", "4.0", 1), (1, "2", "9", 1), (2, "2", "", 1),
                     (2, "1", "3.5", 1), (2, "1", "3.0", 0))
        validas, rechazos = acumular_valoraciones(catalogo, filas)
        self.assertEqual(validas + len(rechazos), len(filas))
        self.assertEqual(sum(p.cantidad for p in catalogo.values()), validas)

    def test_esquema_incompleto(self):
        with self.assertRaises(ErrorEsquema):
            validar_esquema([{"movieId": 1, "title": "x"}], ("movieId", "title", "genres"), "películas")


class TestBusquedaYLista(unittest.TestCase):
    def setUp(self):
        self.catalogo, _ = construir_catalogo(PELICULAS)
        acumular_valoraciones(self.catalogo, vals(
            (1, "1", "4.0", 1), (2, "1", "4.0", 1), (3, "1", "4.0", 1),
            (1, "2", "4.0", 1), (2, "2", "4.0", 1),
            (1, "3", "5.0", 1),
            (1, "4", "3.0", 1), (2, "4", "4.0", 1), (3, "4", "5.0", 1),
        ))

    def test_busqueda_sin_tildes_ni_mayusculas(self):
        resultado = buscar_titulos(self.catalogo, ConsultaCatalogo(texto="MISERABLES"))
        self.assertEqual([p.id for p in resultado], [4])

    def test_busqueda_sin_coincidencias(self):
        self.assertEqual(buscar_titulos(self.catalogo, ConsultaCatalogo(texto="zzz")), [])

    def test_varios_generos_no_duplican_resultados(self):
        resultado = buscar_titulos(self.catalogo, ConsultaCatalogo())
        self.assertEqual(len(resultado), len({p.id for p in resultado}))
        self.assertEqual([p.id for p in buscar_titulos(self.catalogo, ConsultaCatalogo(genero="crime"))], [2])

    def test_filtro_de_anio_excluye_anio_desconocido(self):
        con_rango = buscar_titulos(self.catalogo, ConsultaCatalogo(anio_desde=1990))
        self.assertNotIn(3, [p.id for p in con_rango])
        self.assertIn(3, [p.id for p in buscar_titulos(self.catalogo, ConsultaCatalogo())])

    def test_minimo_excluye_peliculas_con_pocas_valoraciones(self):
        lista = generar_lista(self.catalogo, ConsultaCatalogo(minimo_valoraciones=2))
        self.assertNotIn(3, [p.id for p in lista])
        self.assertEqual(generar_lista(self.catalogo, ConsultaCatalogo(minimo_valoraciones=1))[0].id, 3)

    def test_desempate_documentado(self):
        lista = generar_lista(self.catalogo, ConsultaCatalogo(minimo_valoraciones=2))
        self.assertEqual([p.id for p in lista], [4, 1, 2])

    def test_limite(self):
        lista = generar_lista(self.catalogo, ConsultaCatalogo(limite=2))
        self.assertEqual(len(lista), 2)

    def test_verificar_lista_detecta_orden_incorrecto(self):
        consulta = ConsultaCatalogo(minimo_valoraciones=2)
        lista = generar_lista(self.catalogo, consulta)
        verificar_lista(lista, consulta)
        with self.assertRaises(ErrorResultado):
            verificar_lista(list(reversed(lista)), consulta)


class TestConsultaCatalogo(unittest.TestCase):
    def test_parametros_invalidos(self):
        for parametros in ({"anio_desde": 2010, "anio_hasta": 2000}, {"minimo_valoraciones": 0},
                           {"limite": 0}, {"anio_desde": 1500}):
            with self.subTest(**parametros), self.assertRaises(ErrorValidacion):
                ConsultaCatalogo(**parametros)

    def test_describir(self):
        consulta = ConsultaCatalogo(texto=" star ", genero="Sci-Fi", anio_desde=1977)
        self.assertEqual(consulta.texto, "star")
        self.assertEqual(consulta.describir(), 'título contiene "star", género Sci-Fi, años 1977-...')

    def test_pelicula_rechaza_puntaje_invalido(self):
        pelicula = Pelicula(1, "Up", 2009, ("Drama",))
        with self.assertRaises(ErrorValidacion):
            pelicula.agregar_valoracion(7)
        self.assertEqual(pelicula.cantidad, 0)


if __name__ == "__main__":
    unittest.main()
