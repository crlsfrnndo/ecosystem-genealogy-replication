# ecosystem-genealogy

Replication materials for the article **"One word, several lineages: A genealogy of the ecosystem concept and the place of Latin American research"**. Spanish version: [README_es.md](README_es.md).

The study builds a citation corpus on the use of "ecosystem" in business, decision-sciences and social-science literature indexed in Scopus, and analyses it with co-citation, bibliographic coupling and main-path (search path count, SPC) methods.

> **Status: pre-release.** All analysis scripts are included; the R scripts have not yet been run on this repository (section 3).

## 1. Data policy

- Source: Scopus export of **22 September 2026**, 19,419 records. The raw export and the filtered corpus file (`corpus_bibliometrix.csv`, 5,274 records, 45 Scopus fields) are **not redistributed**, because the Scopus terms restrict redistribution of its records.
- Shared: Scopus identifiers (EID), DOIs, derived citation networks, diagnostic tables and result tables. `red_nodos.csv` and `citacion_cruzada/lineas_por_documento.csv` have no titles, author names or source titles. A few titles appear in the result tables `resultados/02`, `resultados/05` and `sendero_principal.csv`, and short fragments of the references to seed works appear in `semillas/obras_semillas.csv` and `semillas/rango_semillas.csv`.
- To rebuild the corpus, retrieve the records listed in `metadatos_corpus.csv` (column `EID`) from Scopus, or run the query again (results may differ if Scopus has changed since the download date).

Scopus query:

```
TITLE(ecosystem* AND NOT ("ecosystem service*" OR "ecosystem health" OR "ecosystem restoration" OR "marine ecosystem*" OR "forest ecosystem*" OR "aquatic ecosystem*" OR "coastal ecosystem*" OR "soil ecosystem*" OR "ecosystem function*")) AND (LIMIT-TO(subjarea,"BUSI") OR LIMIT-TO(subjarea,"DECI") OR LIMIT-TO(subjarea,"SOCI"))
```

## 2. Pipeline and files

All scripts are run **from the repository root**. The first five columns are in the order of the analysis.

| Step | Script | Output | Needs the Scopus corpus | Status |
|---|---|---|---|---|
| 1. Corpus filter (seed-citation rule; core and rescue layers) | `filtro_corpus.py` (core layer), `rescate_entrantes.py` (rescue layer) | `corpus_bibliometrix.csv`, `metadatos_corpus.csv` | yes | both scripts included; `metadatos_corpus.csv` included (rule also described in `docs/corpus_construction_notes_es.md`) |
| 2. Load in bibliometrix, repair and normalise references, descriptives | `cargar_en_bibliometrix.R`, `funciones_cr.R` | objects in the R session | yes | included |
| 3. Internal citation network | `construir_red.py` | `red_nodos.csv`, `red_aristas.csv` | yes | included |
| 4. Community (line) of each document (Leiden) | `citacion_cruzada/comunidades.py` | `citacion_cruzada/lineas_por_documento.csv` | yes (titles and authors only, for the title term and the seed-author flag) | included |
| 5. SPC and main path | `red_citacion_en_R.R` | `sendero_principal.csv`, `red_aristas_spc.csv` | no | included |
| 6. Key-route paths, origin of paths and Figure 4 | `senderos/rutas_clave.R`, then `senderos/figura_senderos.py` | `senderos/*.csv`, `senderos/senderos_ruta_clave.png` | no | included |
| 7. Corrected co-citation (Leiden) | `cocitacion/claves_cocitacion.R`, then `cocitacion/cocitacion_leiden.py` | `cocitacion/*.csv` | step 7a yes | included; `cocitacion/claves_largas.csv` (intermediate file) is not shared |
| 8. Seed validation | `semillas/validacion_semillas.py` | `semillas/*.csv` | yes (raw export) | included, with its outputs; imports `filtro_corpus.py` (run from the repository root) |
| 9. Recount without duplicates, Latin American affiliation, brokerage and regressions (Table 5), sensitivity | `sensibilidad/recuento_sin_duplicados.py`, `sensibilidad/sensibilidad.py` | `sensibilidad/*.csv` | yes | included, with its outputs |
| 10. Cross-citation, assortativity, who cites whom, integrator articles | `citacion_cruzada/citacion_cruzada.py` | `citacion_cruzada/asortatividad_por_periodo.csv`, `asortatividad_por_anio.csv`, `quien_cita_a_quien.csv`, `trafico_articulos_integradores.csv`, `asortatividad_anual.png` | no | included |
| 11. Export of first-pass tables | `exportar_resultados.R` | `resultados/01` to `07` | yes | included |
| Integrity check of files | `verificar_archivos.R` | console | no | included (lists the shared files) |

The outputs of steps 8 and 9 (`semillas/` and `sensibilidad/`) are included: they are aggregate tables, regenerated on 16 October 2026 with the Scopus export of 22 September 2026. Running the scripts again requires the raw export (step 8) or the corpus (step 9); `sensibilidad/sensibilidad.py` also needs `cocitacion/claves_largas.csv`, an intermediate file that is not shared.

## 3. Verification of the shared network

Applying the duplicate rule (normalised title plus year, keep the first record, move the citations of the removed record to the kept one; this is what `sensibilidad/recuento_sin_duplicados.py` does) to `red_nodos.csv` and `red_aristas.csv` gives the figures of the article: 5,262 documents, 51,452 links, 50,273 links with strictly increasing year, 5,062 nodes in the acyclic graph and 102,233,606 source-sink paths. The files as shared contain the corpus **before** duplicate removal (5,274 nodes, 51,539 edges). `duplicados_quitados.csv` lists the 12 removed records and the record that keeps their citations; `citacion_cruzada/citacion_cruzada.py` and `senderos/rutas_clave.R` apply it, so the cross-citation tables match the article (for example, 4,011 and 46,042 links in 2014–2019 and 2020–2026). `red_aristas_spc.csv`, `sendero_principal.csv` and `senderos/rutas_clave_*.csv` were produced before this rule; for the key routes, the origin-of-paths matrix and the 20 highest-SPC links are identical with and without duplicates (checked with an independent Python implementation on 19 October 2026), and `rutas_clave.R` has not yet been run with the rule. The 14-node main path from Adner (2006) to Joel et al. (2026) is reproduced from the shared files. This check was done with an independent Python implementation. The Python scripts of steps 3, 4, 8, 9 and 10 and `senderos/figura_senderos.py` were run on 16 October 2026 with the repository files and the Scopus corpus: they reproduce the shared network, the line assignment, the cross-citation tables and the figures (identical files; `red_nodos.csv` differs only in line endings), the figures of Table 1, and Table 5 and the Latin American figures of the article. The R scripts have not yet been run on this repository.

## 4. Notes on specific files

- `resultados/03` and `resultados/04` (Walktrap on the 100 most co-cited references and the 200 most coupled documents) give one very large group and are exploratory. The corrected co-citation is in `cocitacion/`.
- `resultados/06` and `resultados/07` use `linea_dominante`, which is a diagnostic label and not the line assignment of the study. The assignment is in `citacion_cruzada/lineas_por_documento.csv` (`linea_comunidad`).
- `resultados/02_lcs_top50.csv` comes from `histNetwork` and omits works without DOI or with unmatched references; use `citas_internas` in `red_nodos.csv` as the reference measure.
- `metadatos_corpus.csv`: `capa` takes the values nucleo 5006, rescate 268. `criterio` takes the values 1_nucleo (5006); 2_revision (179); 3_sin_referencias (43); 4_fuera (46).
- `red_aristas.csv`: `desde` is the citing node and `hacia` the cited node (ids of `red_nodos.csv`).
- `citacion_cruzada/intermediacion_resultados.csv` is a first pass of the Latin American models, on the corpus before duplicate removal and with an earlier specification of the share of references to other lines; its script was not preserved and the file is kept for the record. Table 5 of the article comes from `sensibilidad/recuento_sin_duplicados.py` (output `sensibilidad/tabla3_sin_duplicados.csv`).
- `citacion_cruzada/trafico_articulos_integradores.csv` covers Adner (2017), Jacobides et al. (2018), Kapoor (2018), Granstrand and Holgersson (2020) and Shipilov and Gawer (2020), which `citacion_cruzada.py` identifies by EID. Thomas and Autio (2020) is not in the corpus.
- Tables of the article and their files: Table 1, last two columns: `semillas/cobertura_por_semilla.csv`; Table 5: `sensibilidad/tabla3_sin_duplicados.csv` (version `sin_duplicados`); Tables S1 and S2: `semillas/obras_semillas.csv`, `semillas/quitar_semillas.csv`, `semillas/rango_semillas.csv` and `semillas/umbrales_regla.csv`; Table S3: `sensibilidad/resumen_sensibilidad.csv`; descriptive figures of the corpus and of Latin America: `sensibilidad/recuento_sin_duplicados.csv`.

## 5. Requirements

R 4.4.1 with `bibliometrix` 4.3.0 and `igraph`; Python 3.11 with `pandas`, `numpy`, `scipy`, `python-igraph`, `leidenalg`, `scikit-learn`, `statsmodels` and `matplotlib`. `rutas_clave.R` only needs base R. Record package versions with `sessionInfo()` and `pip freeze` when you run the code. The Python steps were checked with pandas 3.0.2, numpy 2.4.4, python-igraph 1.0.0, leidenalg 0.12.0, statsmodels 0.15.0 and matplotlib 3.10.9; with other versions of igraph or leidenalg the numbering of the communities may change, and `comunidades.py` warns if the community sizes differ from those of the article.

Changes with respect to the working scripts: `red_citacion_en_R.R` selects the columns that exist in the shared node file; the two Python scripts in `sensibilidad/` take the title from the corpus when `red_nodos.csv` has none; `construir_red.py`, `citacion_cruzada/comunidades.py`, `citacion_cruzada/citacion_cruzada.py` and `senderos/figura_senderos.py` were recovered from the analysis workspace and adapted to read and write the repository files (`citacion_cruzada.py` identifies the integrator articles by EID because `red_nodos.csv` has no titles). Comments are in Spanish.

## 6. Licence

Code: MIT (`LICENSE`). Derived tables and figures: CC BY 4.0 (`LICENSE-DATA.md`). Scopus records remain subject to the terms of Elsevier and the publishers.

## 7. How to cite

See `CITATION.cff`. A DOI will be assigned through Zenodo at release.
