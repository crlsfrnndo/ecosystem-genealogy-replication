# ecosystem-genealogy

Materiales de replicación del artículo **"One word, several lineages: A genealogy of the ecosystem concept and the place of Latin American research"**. English version: [README.md](README.md).

El estudio construye un corpus de citación sobre el uso de «ecosystem» en la literatura de negocios, ciencias de la decisión y ciencias sociales indexada en Scopus, y lo analiza con cocitación, acoplamiento bibliográfico y senderos de ruta principal (conteo de búsqueda, SPC).

> **Estado: versión previa.** Están todos los scripts del análisis; los de R aún no se han corrido sobre este repositorio (sección 3).

## 1. Política de datos

- Fuente: export de Scopus del **22 de septiembre de 2026**, 19.419 registros. El export y el archivo del corpus filtrado (`corpus_bibliometrix.csv`, 5.274 registros, 45 campos de Scopus) **no se redistribuyen**, porque las condiciones de Scopus restringen la redistribución de sus registros.
- Se comparten: identificadores de Scopus (EID), DOI, redes de citación derivadas, tablas de diagnóstico y tablas de resultados. `red_nodos.csv` y `citacion_cruzada/lineas_por_documento.csv` no traen títulos, nombres de autores ni revistas. Algunos títulos aparecen en `resultados/02`, `resultados/05` y `sendero_principal.csv`, y fragmentos breves de las referencias a obras semilla aparecen en `semillas/obras_semillas.csv` y `semillas/rango_semillas.csv`.
- Para reconstruir el corpus, descargue de Scopus los registros de `metadatos_corpus.csv` (columna `EID`) o repita la ecuación (los resultados pueden variar si Scopus cambió desde la fecha de descarga).

Ecuación de Scopus:

```
TITLE(ecosystem* AND NOT ("ecosystem service*" OR "ecosystem health" OR "ecosystem restoration" OR "marine ecosystem*" OR "forest ecosystem*" OR "aquatic ecosystem*" OR "coastal ecosystem*" OR "soil ecosystem*" OR "ecosystem function*")) AND (LIMIT-TO(subjarea,"BUSI") OR LIMIT-TO(subjarea,"DECI") OR LIMIT-TO(subjarea,"SOCI"))
```

## 2. Flujo de trabajo y archivos

Todos los scripts se corren **desde la raíz del repositorio**.

| Paso | Script | Salida | Requiere el corpus de Scopus | Estado |
|---|---|---|---|---|
| 1. Filtro del corpus (regla de obras semilla; capas núcleo y rescate) | `filtro_corpus.py` (capa núcleo), `rescate_entrantes.py` (capa de rescate) | `corpus_bibliometrix.csv`, `metadatos_corpus.csv` | sí | ambos scripts incluidos; `metadatos_corpus.csv` incluido (la regla también está en `docs/corpus_construction_notes_es.md`) |
| 2. Carga en bibliometrix, reparación y normalización de referencias, descriptivos | `cargar_en_bibliometrix.R`, `funciones_cr.R` | objetos de la sesión de R | sí | incluido |
| 3. Red interna de citación | `construir_red.py` | `red_nodos.csv`, `red_aristas.csv` | sí | incluido |
| 4. Comunidad (línea) de cada documento (Leiden) | `citacion_cruzada/comunidades.py` | `citacion_cruzada/lineas_por_documento.csv` | sí (solo títulos y autores, para el término del título y la marca de autor semilla) | incluido |
| 5. SPC y sendero principal | `red_citacion_en_R.R` | `sendero_principal.csv`, `red_aristas_spc.csv` | no | incluido |
| 6. Rutas clave, origen de los caminos y Figura 4 | `senderos/rutas_clave.R`, luego `senderos/figura_senderos.py` | `senderos/*.csv`, `senderos/senderos_ruta_clave.png` | no | incluido |
| 7. Cocitación corregida (Leiden) | `cocitacion/claves_cocitacion.R`, luego `cocitacion/cocitacion_leiden.py` | `cocitacion/*.csv` | el paso 7a sí | incluido; `cocitacion/claves_largas.csv` (archivo intermedio) no se comparte |
| 8. Validación de semillas | `semillas/validacion_semillas.py` | `semillas/*.csv` | sí (export crudo) | incluido, con sus salidas; importa `filtro_corpus.py` (ejecutar desde la raíz del repositorio) |
| 9. Recuento sin duplicados, afiliación latinoamericana, intermediación y regresiones (Tabla 5), sensibilidad | `sensibilidad/recuento_sin_duplicados.py`, `sensibilidad/sensibilidad.py` | `sensibilidad/*.csv` | sí | incluido, con sus salidas |
| 10. Citación cruzada, asortatividad, quién cita a quién, artículos integradores | `citacion_cruzada/citacion_cruzada.py` | `citacion_cruzada/asortatividad_por_periodo.csv`, `asortatividad_por_anio.csv`, `quien_cita_a_quien.csv`, `trafico_articulos_integradores.csv`, `asortatividad_anual.png` | no | incluido |
| 11. Exportación de las tablas de la primera pasada | `exportar_resultados.R` | `resultados/01` a `07` | sí | incluido |
| Verificación de integridad | `verificar_archivos.R` | consola | no | incluido (lista los archivos compartidos) |

Las salidas de los pasos 8 y 9 (`semillas/` y `sensibilidad/`) están incluidas: son tablas agregadas, regeneradas el 16 de octubre de 2026 con el export de Scopus del 22 de septiembre de 2026. Para volver a correr los scripts hace falta el export crudo (paso 8) o el corpus (paso 9); `sensibilidad/sensibilidad.py` necesita además `cocitacion/claves_largas.csv`, archivo intermedio que no se comparte.

## 3. Verificación de la red compartida

Al aplicar la regla de duplicados (título normalizado más año, se conserva el primer registro y las citas del registro eliminado pasan al conservado; es lo que hace `sensibilidad/recuento_sin_duplicados.py`) a `red_nodos.csv` y `red_aristas.csv` se obtienen las cifras del artículo: 5.262 documentos, 51.452 vínculos, 50.273 vínculos con año estrictamente creciente, 5.062 nodos en el grafo acíclico y 102.233.606 caminos fuente-sumidero. Los archivos compartidos contienen el corpus **antes** de quitar duplicados (5.274 nodos, 51.539 aristas). `duplicados_quitados.csv` lista los 12 registros quitados y el registro que conserva sus citas; `citacion_cruzada/citacion_cruzada.py` y `senderos/rutas_clave.R` lo aplican, de modo que las tablas de citación cruzada coinciden con el artículo (por ejemplo, 4.011 y 46.042 vínculos en 2014–2019 y 2020–2026). `red_aristas_spc.csv`, `sendero_principal.csv` y `senderos/rutas_clave_*.csv` se produjeron antes de esta regla; en las rutas clave, la matriz de origen de los caminos y los 20 vínculos de mayor SPC son idénticos con y sin duplicados (comprobado con una implementación independiente en Python el 19 de octubre de 2026), y `rutas_clave.R` aún no se ha corrido con la regla. El sendero principal de 14 nodos, de Adner (2006) a Joel et al. (2026), se reproduce con los archivos compartidos. La comprobación se hizo con una implementación independiente en Python. Los scripts de Python de los pasos 3, 4, 8, 9 y 10 y `senderos/figura_senderos.py` se corrieron el 16 de octubre de 2026 con los archivos del repositorio y el corpus de Scopus: reproducen la red compartida, la asignación de líneas, las tablas de citación cruzada y las figuras (archivos idénticos; `red_nodos.csv` solo difiere en el fin de línea), las cifras de la Tabla 1, y la Tabla 5 y las cifras sobre América Latina del artículo. Los scripts de R aún no se han corrido sobre este repositorio.

## 4. Notas sobre archivos específicos

- `resultados/03` y `resultados/04` (Walktrap sobre las 100 referencias más cocitadas y los 200 documentos más acoplados) producen un grupo muy grande y son exploratorios. La cocitación corregida está en `cocitacion/`.
- `resultados/06` y `resultados/07` usan `linea_dominante`, que es una etiqueta de diagnóstico y no la asignación de línea del estudio. La asignación está en `citacion_cruzada/lineas_por_documento.csv` (`linea_comunidad`).
- `resultados/02_lcs_top50.csv` viene de `histNetwork` y omite obras sin DOI o con referencias sin emparejar; la medida de referencia son las `citas_internas` de `red_nodos.csv`.
- `metadatos_corpus.csv`: `capa` toma los valores nucleo 5006, rescate 268. `criterio` toma los valores 1_nucleo (5006); 2_revision (179); 3_sin_referencias (43); 4_fuera (46).
- `red_aristas.csv`: `desde` es el nodo que cita y `hacia` el nodo citado (ids de `red_nodos.csv`).
- `citacion_cruzada/intermediacion_resultados.csv` es una primera pasada de los modelos sobre América Latina, con el corpus antes de quitar duplicados y con una especificación anterior de la proporción de referencias a otras líneas; su script no se conservó y el archivo se mantiene como registro. La Tabla 5 del artículo sale de `sensibilidad/recuento_sin_duplicados.py` (salida `sensibilidad/tabla3_sin_duplicados.csv`).
- `citacion_cruzada/trafico_articulos_integradores.csv` cubre a Adner (2017), Jacobides et al. (2018), Kapoor (2018), Granstrand y Holgersson (2020) y Shipilov y Gawer (2020), que `citacion_cruzada.py` identifica por EID. Thomas y Autio (2020) no está en el corpus.
- Tablas del artículo y sus archivos: Tabla 1, dos últimas columnas: `semillas/cobertura_por_semilla.csv`; Tabla 5: `sensibilidad/tabla3_sin_duplicados.csv` (versión `sin_duplicados`); Tablas S1 y S2: `semillas/obras_semillas.csv`, `semillas/quitar_semillas.csv`, `semillas/rango_semillas.csv` y `semillas/umbrales_regla.csv`; Tabla S3: `sensibilidad/resumen_sensibilidad.csv`; cifras descriptivas del corpus y de América Latina: `sensibilidad/recuento_sin_duplicados.csv`.

## 5. Requisitos

R 4.4.1 con `bibliometrix` 4.3.0 e `igraph`; Python 3.11 con `pandas`, `numpy`, `scipy`, `python-igraph`, `leidenalg`, `scikit-learn`, `statsmodels` y `matplotlib`. `rutas_clave.R` solo usa R base. Registre las versiones de los paquetes con `sessionInfo()` y `pip freeze` al correr el código. Los pasos de Python se comprobaron con pandas 3.0.2, numpy 2.4.4, python-igraph 1.0.0, leidenalg 0.12.0, statsmodels 0.15.0 y matplotlib 3.10.9; con otras versiones de igraph o leidenalg la numeración de las comunidades puede cambiar, y `comunidades.py` avisa si los tamaños no coinciden con los del artículo.

Cambios respecto de los scripts de trabajo: `red_citacion_en_R.R` selecciona las columnas que existen en el archivo de nodos compartido; los dos scripts de `sensibilidad/` toman el título del corpus cuando `red_nodos.csv` no lo trae; `construir_red.py`, `citacion_cruzada/comunidades.py`, `citacion_cruzada/citacion_cruzada.py` y `senderos/figura_senderos.py` se recuperaron del espacio de trabajo del análisis y se adaptaron para leer y escribir los archivos del repositorio (`citacion_cruzada.py` identifica los artículos integradores por EID porque `red_nodos.csv` no trae títulos). Los comentarios están en español.

## 6. Licencia

Código: MIT (`LICENSE`). Tablas y figuras derivadas: CC BY 4.0 (`LICENSE-DATA.md`). Los registros de Scopus siguen sujetos a las condiciones de Elsevier y de las editoriales.

## 7. Cómo citar

Véase `CITATION.cff`. El DOI se asignará con Zenodo al publicar la versión.
