# Catálogo de películas con listas de selección

**Autora:** Clara Torres — Programación Orientada a Datos, Licenciatura en Ciencia de Datos, UCA (2026)
**Trabajo Práctico 2 – Individual**

Aplicación de consola en Python que permite buscar películas por título, género y año, ver su ficha y generar listas ordenadas por valoración que exigen un **mínimo configurable de opiniones**, para que una película con una sola calificación de 5 estrellas no aparezca automáticamente entre las mejor respaldadas.

---

## 1. Problema, usuario y solución

**Problema.** Quien arma una lista de películas (para un ciclo de cine, una clase, un club de cine o una recomendación) suele ordenar por valoración media. Pero la media de una película con 1 o 2 opiniones no es comparable con la de una que tiene cientos: la primera puede quedar arriba por azar. Además, los archivos de origen tienen títulos con el año pegado, varios géneros por película y registros con errores (calificaciones fuera de escala, referencias a películas que no existen, duplicados), y hacer este trabajo a mano no es repetible.

**Usuario.** Una persona que organiza un ciclo de cine, docentes que preparan una actividad o cualquiera que quiera una lista de películas filtrada y respaldada por suficientes opiniones.

**Solución propuesta.** Un programa de consola que:

1. lee un catálogo de películas y un archivo de calificaciones (en CSV o JSON);
2. valida y limpia los datos, y guarda los registros rechazados con su motivo;
3. permite **buscar** por texto del título, género y rango de años;
4. muestra la **ficha** de una película por su identificador;
5. genera una **lista ordenada** por valoración media con un mínimo de valoraciones y un límite de resultados, y la exporta a CSV o JSON.

**Resultado e interpretación.** La lista muestra posición, título, año, géneros, cantidad de valoraciones (`n`) y media (escala de 0.5 a 5 estrellas). Una película figura en la lista sólo si tiene al menos `--minimo` valoraciones; a igual media, queda primero la que tiene más valoraciones (más respaldada). La media describe la opinión de los usuarios del dataset, no una "calidad objetiva".

**Alcance de la primera versión.**

| Incluye | Queda fuera |
|---|---|
| Búsqueda por texto (sin distinguir mayúsculas ni tildes), género y años | Recomendaciones personalizadas o aprendizaje automático |
| Ficha por `movieId` | Interfaz gráfica o web |
| Lista con mínimo de valoraciones, límite y desempate documentado | Etiquetas (`tags.csv`) y enlaces (`links.csv`) de MovieLens |
| Lectura CSV y JSON, registro de rechazos, exportación CSV/JSON | Medias ponderadas o bayesianas (ver limitaciones) |

## 2. Datos

Detalle completo en [`data/README.md`](data/README.md).

- **Fuente de referencia:** MovieLens *ml-latest-small*, GroupLens Research, Universidad de Minnesota. <https://grouplens.org/datasets/movielens/latest/> (consulta: 21/10/2026). Uso permitido con fines de investigación/educativos, sin uso comercial y sin implicar respaldo de la Universidad de Minnesota; se cita Harper y Konstan (2015).
- **Muestra incluida en el repositorio:** `data/muestra/` contiene una **muestra de demostración** en formato MovieLens, en CSV y JSON equivalentes: 46 registros de películas (títulos, años y géneros reales; `movieId` propios de la muestra) y 446 calificaciones **sintéticas** generadas con semilla fija por `scripts/generar_muestra.py`, con 12 registros con errores intencionales. Los datos reales de MovieLens no se suben al repositorio (ver `data/README.md`).
- **Unidad de análisis:** en `movies`, cada fila es **una película**; en `ratings`, cada fila es **una calificación de un usuario a una película en un momento**. El resultado de la aplicación tiene una fila por película.
- **Variables:** `movieId`, `title` (incluye el año), `genres` (separados por `|`), `userId`, `rating` (0.5–5.0 en pasos de 0.5) y `timestamp` (segundos Unix, UTC).

## 3. Instalación

Requiere **Python 3.10 o superior**. Sólo usa la biblioteca estándar (`csv`, `json`, `re`, `argparse`, `dataclasses`, `unittest`), por lo que no hay que instalar paquetes.

```bash
git clone https://github.com/clariitorres2008/Clara-Torres.git
cd Clara-Torres
python -m venv .venv                 # opcional
# Windows: .venv\Scripts\activate    |    Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt      # no instala nada: documenta que no hay dependencias
```

Todos los comandos se ejecutan **desde la carpeta raíz del proyecto**. En Windows puede ser `py` en lugar de `python`.

## 4. Uso

```bash
python -m src.main --help                 # ayuda general
python -m src.main lista --help           # ayuda de un comando
```

| Comando | Qué hace | Ejemplo |
|---|---|---|
| `lista` | Lista ordenada por media con mínimo de valoraciones; se exporta | `python -m src.main lista --genero Drama --desde 2000 --minimo 5 --limite 5` |
| `buscar` | Búsqueda por título, género y años | `python -m src.main buscar --texto "the" --genero Sci-Fi` |
| `ficha` | Ficha de una película por id | `python -m src.main ficha --id 1` |
| `generos` | Géneros disponibles y cantidad de películas | `python -m src.main generos` |

Opciones comunes:

- `--peliculas RUTA` y `--valoraciones RUTA`: archivos de entrada `.csv` o `.json` (el formato se elige por la extensión). Por defecto, `data/muestra/movies.csv` y `data/muestra/ratings.json`, es decir, se leen **un CSV y un JSON** en la misma ejecución.
- `--rechazos RUTA`: dónde se guardan los registros rechazados (por defecto `outputs/rechazos.csv`).
- Filtros de `buscar` y `lista`: `--texto`, `--genero`, `--desde`, `--hasta`.
- Sólo `lista`: `--minimo` (por defecto 3), `--limite` (por defecto 10), `--salida` (por defecto `outputs/lista.csv`; con extensión `.json` exporta en JSON).

Con los datos reales de MovieLens (después de descargarlos según `data/README.md`):

```bash
python -m src.main lista --peliculas data/raw/ml-latest-small/movies.csv --valoraciones data/raw/ml-latest-small/ratings.csv --minimo 50 --limite 20
```

## 5. Ejemplo de resultado

`python -m src.main lista --genero Drama --desde 2000 --minimo 5 --limite 5`

```text
Datos: 42/46 películas válidas, 438/446 valoraciones válidas. Rechazos: 12 (detalle en outputs/rechazos.csv)
  - peliculas/anio_fuera_de_rango: 1
  - peliculas/duplicado: 1
  - peliculas/faltante: 1
  - peliculas/id_invalido: 1
  - valoraciones/duplicado: 2
  - valoraciones/faltante: 1
  - valoraciones/formato: 1
  - valoraciones/fuera_de_escala: 2
  - valoraciones/id_invalido: 1
  - valoraciones/referencia_inexistente: 1

Lista (género Drama, años 2000-...; mínimo de valoraciones: 5; límite: 5):
  12 película(s) coinciden con los filtros; 0 quedan fuera por no alcanzar el mínimo.

  #      id  título                                         año     n  media  géneros
  1      23  Dark Knight, The                              2008    13   4.35  Action, Crime, Drama, IMAX
  2      16  Secret in Their Eyes, The (El secreto de sus… 2009    12   4.25  Crime, Drama, Mystery, Romance, Thriller
  3      25  Up                                            2009    10   4.25  Adventure, Animation, Children, Drama
  4      32  Parasite                                      2019    14   4.18  Comedy, Drama
  5      22  Inception                                     2010    13   4.08  Action, Crime, Drama, Mystery, Sci-Fi, Thriller, IMAX
```

**Cómo leerlo:** las posiciones 2 y 3 empatan en media (4.25); queda primero la de más valoraciones (12 contra 10). El efecto del mínimo se ve sin filtros: con `--minimo 1`, *Hidden Gem Documentary* (2 valoraciones de 5.0) y *Cosmos* (1 valoración de 5.0) encabezan la lista; con `--minimo 3` quedan fuera y la lista la encabezan películas con 10 o más opiniones. Recordá que estas calificaciones son sintéticas: el ejemplo demuestra el funcionamiento, no describe preferencias reales.

## 6. Flujo de procesamiento

```
cargar_tabla()            leer CSV/JSON (FuenteCSV / FuenteJSON) → normalizar_campos() → validar_esquema()
construir_catalogo()      validar id, título/año (regex), géneros → {movieId: Pelicula} + rechazos
acumular_valoraciones()   validar ids, escala, timestamp, referencia, duplicados → cantidad/suma por película + rechazos
verificar_conservacion()  leídas = válidas + rechazadas; suma de conteos = válidas
ConsultaCatalogo          valida los parámetros de la consulta
buscar_titulos() / generar_lista() → verificar_lista()
guardar_tabla() / guardar_rechazos()    exportar resultados y rechazos (CSV o JSON)
```

## 7. Organización del código

```
Clara-Torres/
├── README.md
├── requirements.txt
├── .gitignore
├── src/
│   ├── main.py           # CLI (argparse): recibe la operación, coordina y muestra/guarda resultados
│   ├── fuentes.py        # FuenteDatos (abstracta) → FuenteCSV, FuenteJSON; fuente_para_ruta()
│   ├── validaciones.py   # expresiones regulares y reglas de cada campo (id, título/año, puntaje…)
│   ├── modelo.py         # clases del dominio: Pelicula y ConsultaCatalogo
│   └── pipeline.py       # limpieza, catálogo, búsqueda, lista, verificaciones y exportación
├── tests/                # unittest: validaciones, fuentes, lógica y aplicación completa
├── scripts/
│   ├── generar_muestra.py   # regenera data/muestra/ (semilla fija)
│   └── csv_a_json.py        # convierte un CSV real a JSON equivalente
└── data/
    ├── README.md
    └── muestra/          # movies.csv, movies.json, ratings.csv, ratings.json
```

`outputs/` se crea al ejecutar y no se versiona (las salidas se regeneran con los comandos).

### Conceptos del curso y por qué se usan

- **Funciones con responsabilidad única.** Lectura (`cargar_tabla`), validación (`validar_esquema`, `validar_puntaje`…), transformación (`construir_catalogo`, `acumular_valoraciones`) y producción de resultados (`generar_lista`, `guardar_tabla`) están separadas. La lógica recibe datos ya cargados, sin saber de qué formato vinieron.
- **Abstracción de fuentes.** `FuenteDatos` define el contrato `cargar(ruta) → list[dict]` y hace las comprobaciones comunes (archivo inexistente, codificación, archivo sin registros, numeración `_registro`); `FuenteCSV` y `FuenteJSON` sólo implementan `_leer()`. Gracias a eso `main.py` elige la fuente por extensión y el resto del programa no cambia; agregar otro formato sería una subclase nueva.
- **Clases del dominio.** `Pelicula` reúne los datos de una película y su comportamiento: acumula valoraciones (cantidad y suma, sin guardar cada calificación), calcula la media, responde si tiene un género y se exporta como fila. `ConsultaCatalogo` (inmutable) representa los filtros elegidos por el usuario, **los valida al crearse** (por ejemplo, año desde ≤ año hasta, mínimo ≥ 1) y decide si una película coincide o alcanza el mínimo.
- **Expresión regular.** `RE_TITULO_ANIO` en `validaciones.py` separa el año del final del título: `^(?P<titulo>.+?)\s*\((?P<anio>\d{4})(?:\s*[-–]\s*(?:\d{4})?)?\)\s*$`. Exige que el paréntesis con cuatro dígitos esté **al final**, por eso funciona con títulos como *(500) Days of Summer (2009)* o *Secret in Their Eyes, The (El secreto de sus ojos) (2009)*, y acepta rangos de series como *(1994-1998)*. Como la regex sólo garantiza "cuatro dígitos", se complementa con una comprobación de rango (1874–2030): *(2099)* tiene forma de año pero se rechaza. Otra regex (`\d+`) valida los identificadores: rechaza `-4`, `1.5` o `abc`.
- **Errores comprensibles.** `ErrorLectura`, `ErrorEsquema`, `ErrorValidacion` (con un `codigo` para agrupar rechazos) y `ErrorResultado`. `main.py` los captura y muestra `Error: …` con código de salida 1; nunca se ocultan fallas de lectura.

## 8. Decisiones de limpieza

Cada registro rechazado se guarda en `outputs/rechazos.csv` con archivo, número de registro, código, motivo y datos originales.

| Situación | Decisión | Código |
|---|---|---|
| Columna requerida ausente en todo el archivo | Se detiene el programa (archivo equivocado) | — (`ErrorEsquema`) |
| `movieId` / `userId` vacío, negativo, decimal o no numérico | Se rechaza el registro | `id_invalido` / `faltante` |
| `movieId` repetido en el catálogo | Se conserva el **primero** y se rechazan los siguientes | `duplicado` |
| Título vacío | Se rechaza | `faltante` |
| Título sin año al final | Se **conserva** con año desconocido; queda excluido sólo si se filtra por años | — |
| Año fuera de 1874–2030 | Se rechaza | `anio_fuera_de_rango` |
| Sin géneros (`(no genres listed)` o vacío) | Se conserva con lista de géneros vacía | — |
| Puntaje vacío o no numérico | Se rechaza (un faltante **no** se convierte en 0) | `faltante` / `formato` |
| Puntaje fuera de 0.5–5.0 o no múltiplo de 0.5 | Se rechaza | `fuera_de_escala` |
| Calificación de una película que no está en el catálogo válido | Se rechaza y no altera conteos | `referencia_inexistente` |
| Mismo usuario califica la misma película más de una vez | Se conserva la **más reciente** (mayor `timestamp`; si empatan, la primera) | `duplicado` |
| Fila CSV con más columnas que el encabezado | Se rechaza | `formato` |

**Desempate de la lista:** media descendente → más valoraciones → título alfabético (sin tildes ni mayúsculas) → `movieId`. Como `movieId` es único, el orden es siempre el mismo y la salida es reproducible.

## 9. Pruebas

```bash
python -m unittest -v
```

46 pruebas en `tests/` (biblioteca `unittest`). Entre ellas:

- **Casos normales:** valoraciones 3 y 5 dan media 4.0 y conteo 2; búsqueda sin tildes (`MISERABLES` encuentra *Misérables, Les*); ficha existente.
- **Entradas inválidas y casos límite:** puntajes `6.0`, `0.25`, `3.7`, `"muy buena"`, vacío; ids `-3`, `1.5`, `abc`; año 2099; JSON mal formado o que no es lista; archivo vacío o inexistente; parámetros contradictorios (`--desde 2010 --hasta 2000`); género inexistente; búsqueda sin coincidencias; película sin valoraciones.
- **Propiedades del resultado:** las lecturas CSV y JSON equivalentes producen **el mismo catálogo y los mismos rechazos**; valoraciones leídas = válidas + rechazadas; un duplicado o una referencia inexistente no cambian los conteos; una película con varios géneros aparece una sola vez; la lista respeta mínimo, límite y orden; dos ejecuciones iguales generan archivos idénticos.

## 10. Interpretación y limitaciones

- **El mínimo de valoraciones es un corte, no un ajuste.** Una película con 49 valoraciones queda fuera con `--minimo 50`, aunque esté muy cerca. Una mejora posible sería una media bayesiana que "acerque" a la media general las películas con pocas opiniones.
- **Sesgo de selección del dataset.** En MovieLens califican usuarios que eligieron ver y puntuar esas películas, y en *ml-latest-small* todos tienen al menos 20 calificaciones. Predominan películas en inglés y populares: las conclusiones no generalizan a "el público".
- **Datos de demostración sintéticos.** Las calificaciones de `data/muestra/` se generaron con un modelo simple para mostrar el funcionamiento; sus medias no representan opiniones reales.
- **Títulos.** MovieLens advierte que los títulos se cargan a mano y pueden tener errores; un título sin año al final queda con año desconocido. El año es el de estreno indicado en el título.
- **Géneros.** Son los de MovieLens (en inglés) y una película puede tener varios; el filtro por género pide coincidencia exacta del nombre (sin distinguir mayúsculas).
- **Rango de años fijo (1874–2030)** para que el análisis sea reproducible; habría que actualizarlo en versiones futuras.

## Referencias

- Harper, F. M. y Konstan, J. A. (2015). *The MovieLens Datasets: History and Context*. ACM Transactions on Interactive Intelligent Systems, 5(4), 19:1–19:19. <https://doi.org/10.1145/2827872>
- GroupLens Research. *MovieLens Latest Datasets* y README de *ml-latest-small*. <https://grouplens.org/datasets/movielens/latest/>
- Python Software Foundation. Documentación de `csv`, `json`, `re`, `argparse`, `dataclasses` y `unittest`.
