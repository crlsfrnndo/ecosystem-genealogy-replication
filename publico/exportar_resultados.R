# exportar_resultados.R
# Guarda en la carpeta "resultados" los numeros que hacen falta para interpretar.
# Correr al final, en la MISMA sesion de R en que corrieron
# cargar_en_bibliometrix.R y red_citacion_en_R.R (usa los objetos que dejaron).
# Cada bloque revisa que su objeto exista; si falta, lo salta y avisa.

dir.create("resultados", showWarnings = FALSE)
guardar <- function(x, f) {
  write.csv(x, file.path("resultados", f), row.names = FALSE, fileEncoding = "UTF-8")
  cat("guardado:", f, "\n")
}
falta <- function(obj) cat("no encontrado:", obj, "- se salta\n")

# 1. Resumen general de bibliometrix
if (exists("res")) {
  writeLines(capture.output(summary(res, k = 30, pause = FALSE)),
             "resultados/01_resumen_biblioanalysis.txt")
  cat("guardado: 01_resumen_biblioanalysis.txt\n")
} else falta("res")

# 2. histNetwork tras la reparacion: 50 primeros por LCS y su numero de autores
if (exists("hist_res") && exists("M")) {
  hd  <- hist_res$histData
  top <- head(hd[order(-hd$LCS), ], 50)
  top$n_autores <- lengths(strsplit(M$AU[match(toupper(top$DOI), toupper(M$DI))], ";"))
  guardar(top[, intersect(c("Paper", "Title", "DOI", "Year", "LCS", "GCS", "n_autores"),
                          names(top))], "02_lcs_top50.csv")
} else falta("hist_res")

# 3. Cocitacion: grupos entre las 100 referencias mas cocitadas
if (exists("cocit")) {
  net <- networkPlot(cocit, n = 100, normalize = "association", cluster = "walktrap",
                     type = "fruchterman", Title = "Cocitacion", verbose = FALSE)
  if (!is.null(net$cluster_res)) guardar(net$cluster_res, "03_cocitacion_grupos.csv")
} else falta("cocit")

# 4. Acoplamiento: grupos entre los 200 documentos mas acoplados
if (exists("acopl")) {
  net2 <- networkPlot(acopl, n = 200, normalize = "salton", cluster = "walktrap",
                      type = "fruchterman", Title = "Acoplamiento", verbose = FALSE)
  if (!is.null(net2$cluster_res)) guardar(net2$cluster_res, "04_acoplamiento_grupos.csv")
} else falta("acopl")

# 5. Sendero principal de la red propia (red_citacion_en_R.R)
if (exists("sp")) guardar(sp[order(sp$orden), ], "05_sendero_principal.csv") else falta("sp")

# 6. Citacion cruzada entre lineas (red_citacion_en_R.R)
if (exists("cruz")) guardar(as.data.frame(cruz), "06_citacion_cruzada.csv") else falta("cruz")

# 7. Registros por periodo, linea y capa
if (exists("M") && exists("capa") && exists("linea")) {
  per <- cut(M$PY, c(0, 1999, 2006, 2013, 2019, 2100),
             labels = c("<=1999", "2000-06", "2007-13", "2014-19", "2020-26"))
  guardar(as.data.frame(table(periodo = per, linea = linea, capa = capa)),
          "07_periodo_linea_capa.csv")
} else falta("capa / linea")

cat("\nListo. Los archivos estan en:", normalizePath("resultados"), "\n")

packageVersion("bibliometrix")
