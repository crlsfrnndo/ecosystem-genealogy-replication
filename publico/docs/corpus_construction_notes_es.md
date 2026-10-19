# Depuración del corpus núcleo — genealogía del concepto de ecosistema

Entrada: export de Scopus, 19.419 registros.
Fecha del procesamiento: 22 de septiembre de 2026.

## Regla de pertenencia

Conexión de citación, no léxico de título. Un documento pertenece al corpus si
cita al menos **dos obras semilla de una misma línea**. Las semillas están
declaradas en `filtro_corpus.py` y son editables.

| Línea | Semillas |
|---|---|
| negocios | Moore, Iansiti, Levien, Teece |
| innovación | Adner, Kapoor, Autio, Granstrand, Ritala, Oh |
| emprendimiento | Isenberg, Spigel, Stam, Acs, Mason, Roundy, Audretsch, Malecki |
| plataforma | Gawer, Cusumano, Parker, Van Alstyne, Tiwana, Eisenmann, Jacobides, Boudreau |
| servicio | Vargo, Lusch, Akaka, Chandler, Frow |
| software | Bosch, Jansen, Messerschmitt, Manikas, Lungu |
| conocimiento | Carayannis, Etzkowitz, Leydesdorff, Clarysse, Van de Vrande |

Semillas ecológicas de control: Tansley, Odum, Costanza, MEA, Daily, De Groot,
Tilman, Loreau, Chapin. **Holling y Folke quedan fuera** de esa lista: son
compartidos con la literatura de resiliencia organizacional y producirían
falsos positivos.

## Resultado

| Archivo | N | Qué es |
|---|---:|---|
| `nucleo.csv` | 5.006 | Pertenece al corpus. Columnas Scopus completas más diagnóstico. |
| `revision.csv` | 3.103 | Zona gris: una sola semilla, o título organizacional sin semillas. Revisión manual, ordenada por citas recibidas. |
| `sin_referencias.csv` | 1.090 | Scopus no entrega lista de referencias. La regla no aplica. Revisión manual obligatoria: aquí está Adner (2006), 1.590 citas. |
| `fuera_metadatos.csv` | 10.220 | Descartados. Solo metadatos, sin referencias ni resumen. |
| `nucleo_periodo_x_linea.csv` | — | Tabla periodo × línea dominante. |
| `diagnostico.csv` | — | Conteos por decisión y línea. |

## Columnas de diagnóstico añadidas

`L_<linea>` semillas citadas de cada línea · `semillas_max` máximo por línea ·
`lineas_tocadas` líneas con al menos una semilla · `linea_dominante` ·
`cita_bio` cita semilla ecológica · `n_refs` · `titulo_org` · `titulo_bio` ·
`decision`.

`linea_dominante` es un indicador de diagnóstico, **no** la asignación de línea
del estudio. Esa sigue saliendo de detección de comunidades sobre la red de
citación directa, como fija el libro de códigos §1.

## Controles ejecutados

- Contaminación ecológica remanente en el núcleo: 23 de 5.006, y la mayoría son
  falsas marcas del léxico, no ecología real.
- Registros que entran al núcleo solo por citar a Moore, sin ninguna otra
  semilla: **0**. La prueba de canonización no queda condicionada por la regla
  de pertenencia.
- Cabecera del núcleo por citas: Jacobides et al. (3.016), Adner (2.626),
  Adner y Kapoor (2.338), Gawer y Cusumano (1.914), Stam (1.866),
  Spigel (1.861), Carayannis y Campbell (1.790).

## Límite estructural

El núcleo tiene 0 registros anteriores a 2000, 8 en 2000–2006 y 139 en
2007–2013. La regla no puede operar donde todavía no hay nada que citar, y
Scopus no entrega referencias del material antiguo, de HBR ni de libros. Las
capas de prehistoria y canon siguen siendo curadas a mano, y el sendero
principal debe construirse con referencias citadas como nodos no fuente.

## Advertencia sobre la operación 2

La regla obliga a que todo documento del corpus comparta al menos dos
referencias con otros, lo que impone un piso a la conectividad entre líneas y
sesga la matriz de citación cruzada hacia la coevolución. Calcular esa matriz
**excluyendo a los autores semilla** de las referencias, y reportar ambas
versiones.

## Reproducir

```
python3 filtro_corpus.py export_scopus.csv ./salida
```

---

# Adenda — segundo criterio: citación entrante (22 sept 2026)

La regla anterior mira hacia atrás y por eso no puede admitir un texto
fundacional, que es anterior a la literatura que lo cita. `rescate_entrantes.py`
añade el criterio inverso: **un documento pertenece si el núcleo lo cita**.

Indexa las referencias de los 5.006 registros del núcleo por (primer apellido,
año) y verifica cada coincidencia por solapamiento de palabras del título. La
verificación de título es indispensable: sin ella, apellidos frecuentes
—Wang, Zhang, Chen, Liu— producen cientos de falsos positivos.

## Resultado

`rescate_por_citacion_entrante.csv`, 268 registros con 5 o más citas entrantes
verificadas: 179 venían de `revision`, 46 de `fuera`, 43 de `sin_referencias`.

Los mejor conectados son exactamente el canon que la primera regla no veía:

| Registro | Citas entrantes |
|---|---:|
| Adner (2006), *Match your innovation strategy to your innovation ecosystem*, HBR | 715 |
| Moore (2006), *Business Ecosystems and the View from the Firm*, Antitrust Bulletin | 203 |
| Isenberg (2016), *Applying the ecosystem metaphor to entrepreneurship* | 94 |
| Fetters et al. (2010), *The development of university-based entrepreneurship ecosystems* | 57 |
| Iansiti y Richards (2006), *The Information Technology Ecosystem* | 57 |
| Jansen, Brinkkemper y Cusumano (2013), *Software ecosystems* | 51 |
| Gobble (2014), *Charting the innovation ecosystem* | 50 |
| Mars, Bronstein y Lusch (2012), *The value of a metaphor* | 48 |
| Holgersson et al. (2022), *The Forces of Ecosystem Evolution* | 45 |
| Corallo, Passiante y Prencipe (2007), *The digital business ecosystem* | 37 |

## Lo que el rescate NO resuelve

| Periodo | Núcleo | Rescate | Total |
|---|---:|---:|---:|
| ≤1999 | 0 | 3 | 3 |
| 2000–06 | 8 | 8 | 16 |
| 2007–13 | 139 | 30 | 169 |
| 2014–19 | 927 | 102 | 1.029 |
| 2020–26 | 3.932 | 125 | 4.057 |

El hueco anterior a 2000 sigue vacío. No es un problema de filtrado sino de
recuperación: ese material nunca entró al export porque no lleva la palabra
*ecosystem* en el título. Se resuelve con búsqueda por referencia citada, no
con otro filtro.

## Cautelas

- El rescate es una **capa declarada aparte**, no se funde en silencio con el
  núcleo. Su criterio de pertenencia es distinto y debe reportarse como tal.
- Una sola iteración. Iterar hasta convergencia haría crecer el corpus por bola
  de nieve alrededor de lo que el núcleo ya cita.
- El umbral de 5 es una decisión, no un hallazgo. Con 10 quedan 127 registros;
  con 3, 441.

## Reproducir

```
python3 rescate_entrantes.py export_scopus.csv salida/nucleo.csv ./salida
```

---

# Adenda — archivo para Bibliometrix (22 sept 2026)

`corpus_bibliometrix.csv` es la lista definitiva: **5.274 registros**, la suma del
núcleo (5.006) y del rescate por citación entrante (268). Conserva las 45
columnas del export de Scopus en su orden original, en UTF-8 sin BOM, de modo que `convert2df(file, dbsource = "scopus", format = "csv")` lo lee
sin ajustes. Ningún campo de los que bibliometrix mapea falta.

**Salvedad confirmada en R 4.3.3.** `convert2df` no construye `PP`, el campo de
páginas que `histNetwork` exige: deja `Page.start` y `Page.end` en el objeto con
esos nombres y no las combina. Es un hueco del importador de bibliometrix, no
del archivo, y `cargar_en_bibliometrix.R` lo arma en dos líneas. Sin eso,
`histNetwork` falla con «Column `PP` doesn't exist».

| Archivo | N | Para qué |
|---|---:|---|
| `corpus_bibliometrix.csv` | 5.274 | Corpus completo, las dos capas |
| `corpus_bibliometrix_nucleo.csv` | 5.006 | Versión conservadora, solo citación saliente |
| `metadatos_corpus.csv` | 5.274 | Diagnósticos por EID, para adjuntar en R |
| `duplicados_a_revisar.csv` | 23 | Grupos de mismo título y año, sin resolver |
| `cargar_en_bibliometrix.R` | — | Carga, limpiezas y las operaciones del diseño |

## Cobertura de campos

| Campo | Cobertura |
|---|---:|
| Referencias (CR) | 99% (43 sin lista) |
| Afiliaciones (C1) | 99% |
| Palabras clave de autor (DE) | 85% |
| DOI | 94% |
| Palabras clave de índice (ID) | 37% |

La cobertura baja de ID limita el análisis de co-palabras sobre términos de
indexación; conviene apoyarlo en DE, o en títulos y resúmenes. Los 43 registros
sin referencias son la capa de rescate, que por definición carece de ellas.

Rango temporal: 1995–2027. Los diez registros de 2027 son artículos en prensa.

## Tres cosas que hay que decidir antes de analizar

1. **Duplicados.** 23 registros en 11 grupos de mismo título y año. Casi todos
   son capítulos de IGI Global reeditados en varias compilaciones, más un par de
   registros doblemente indexados por Scopus. No los eliminé: la decisión de qué
   versión conservar es del autor. `duplicados_a_revisar.csv` los lista.
2. **Espacios en el nombre de la revista.** Seis fuentes traen espacios al borde
   y se cuentan dos veces: 1.545 fuentes distintas en crudo, 1.541 al limpiarlas.
   No toqué el archivo, para que siga siendo un export fiel; el script de R
   aplica el `trimws`.
3. **Erratas, retractados y editoriales.** 3 erratas, 2 retractados, 46
   editoriales y 18 notas. El script excluye erratas y retractados; las
   editoriales quedan porque en esta literatura varias son piezas sustantivas.

## Advertencia sobre la capa de rescate

Las dos capas tienen criterios de pertenencia distintos y la metodología las
reporta por separado. El archivo completo las mezcla por comodidad operativa,
pero la columna `capa` permite separarlas en cualquier momento, y
`corpus_bibliometrix_nucleo.csv` da la versión conservadora. Conviene correr al
menos una operación con ambos archivos y verificar que el resultado no depende
de esa decisión.

## Corrección de codificación (verificada en R 4.3.3)

Los cuatro CSV se escriben **sin BOM**. Con BOM, `read.csv` renombra la primera
columna a `X...Authors` y el mapeo de campos de bibliometrix falla sin avisar;
y `read.csv(..., fileEncoding = "UTF-8-BOM")` devuelve cero filas sobre este
archivo. Sin BOM, R lee 5.274 filas, 45 columnas, `Authors` como primer nombre,
5.231 registros con referencias, acentos
intactos y cruce por EID completo con `metadatos_corpus.csv`.

Efecto lateral: al abrir estos CSV con doble clic en Excel los acentos salen
mal. Hay que entrar por Datos, Obtener datos, Desde texto, y elegir UTF-8.

---

# Adenda — separador de referencias (5 oct 2026)

**Hallazgo.** En este export, Scopus usa `;` para separar las referencias entre sí
y también los autores dentro de cada referencia
(`Jacobides M.G.; Cennamo C.; Gawer A., Towards a theory of ecosystems, …`).
Al partir por `;`, bibliometrix trocea toda referencia de varios autores: los
autores quedan como "referencias" sueltas y la que conserva título y año empieza
por el último autor.

| Medida | Crudo, partido por `;` | Reparado |
|---|---:|---:|
| Elementos en CR | 930.412 | 399.963 |
| Por registro | 178 | 76,5 |
| Distintos (texto exacto) | 405.443 | 284.326 |
| Distintos tras normalizar | — | 201.716 |

**Corrección.** La cifra de 176 referencias por registro que figuraba más
arriba contaba fragmentos, no referencias; la real es 76,5. La red propia de
`red_aristas.csv` parte por el cierre «(año);» y cubre 387.003 de las 399.963
referencias, el 97%.

**Consecuencias.** Esto explica el sesgo de un autor de `histNetwork` y la
fragmentación de la cocitación. `funciones_cr.R` trae `reparar_cr()`, que
reconstruye las referencias, y `normalizar_cr()`, que reduce las variantes de
formato de una misma obra a una clave (Moore 1993 pasaba de 237 variantes a una
que reúne 1.182 citas). `cargar_en_bibliometrix.R` v4 aplica ambas.
