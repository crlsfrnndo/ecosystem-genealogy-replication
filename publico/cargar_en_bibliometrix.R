# cargar_en_bibliometrix.R  — version 4 (5 oct 2026)
# Corpus depurado: genealogia del concepto de ecosistema.
#
# Correcciones acumuladas:
#  v2  No se hace merge de los metadatos dentro de M: el merge devuelve un
#      data.frame plano y rompe el objeto de bibliometrix. Los diagnosticos se
#      consultan aparte con match().
#  v2  convert2df no construye PP (paginas) a partir de este CSV; se arma aqui.
#      Sin PP, histNetwork falla con "Column `PP` doesn't exist".
#  v3  El LCS de histNetwork viene sin nombres; la tabla por documento es
#      hist_res$histData. El data.frame(SR = names(hist_res$LCS)) de v2 fallaba.
#  v3  histNetwork SOLO empareja documentos de un autor en este export (ver
#      seccion 6). Su histPlot NO es el sendero principal del estudio; ese se
#      calcula en red_citacion_en_R.R.
#  v3  El cruce con metadatos_corpus.csv se hace sin distinguir mayusculas:
#      bibliometrix pasa casi todos los campos a mayusculas.
#  v3  Paso 0: verificacion de archivos, por las copias vacias o truncadas.
#  v4  CAUSA REAL del sesgo de un autor: en este export ";" separa referencias Y
#      autores dentro de cada referencia, y bibliometrix trocea toda referencia
#      de varios autores. reparar_cr() (funciones_cr.R) la reconstruye antes de
#      cualquier analisis. Requiere funciones_cr.R en la carpeta.
#  v4  La cocitacion se colgaba: 405.435 "referencias" distintas y 110 millones
#      de pares. Ahora corre sobre referencias reparadas y normalizadas, con las
#      1.000 mas citadas (unos 935.000 pares).

library(bibliometrix)

# ------------------------------------------------- 0. Verificar los archivos
# Compara tamano y huella MD5 de cada CSV contra los originales.
if (file.exists("verificar_archivos.R")) source("verificar_archivos.R")

# ---------------------------------------------------------------- 1. Cargar
# Si el archivo esta partido en trozos, convert2df acepta un vector y los une:
# M <- convert2df(sprintf("corpus_parte%d.csv", 1:5), dbsource="scopus", format="csv")
M <- convert2df("corpus_bibliometrix.csv", dbsource = "scopus", format = "csv")

cat("Registros:", nrow(M), "\n")

# ---------------------------------------- 1b. Reparar el campo de referencias
# Une cada autor suelto con su referencia. Antes: 930.412 fragmentos. Despues:
# 399.963 referencias, 76,5 por registro. Tarda unos 15 segundos.
source("funciones_cr.R")
n_antes <- sum(lengths(strsplit(M$CR[!is.na(M$CR)], ";", fixed = TRUE)))
M$CR <- reparar_cr(M$CR)
n_desp  <- sum(lengths(strsplit(M$CR[M$CR != ""], ";", fixed = TRUE)))
cat("CR: fragmentos", n_antes, "-> referencias", n_desp, "\n")

# ------------------------------------------------------- 2. Diagnostico previo
# histNetwork necesita PP (paginas) y J9 para reconstruir las etiquetas con las
# que compara cada registro contra las cadenas de CR. Comprobar que existan
# ANTES de llamarla.
necesarios <- c("AU", "PY", "SO", "J9", "VL", "PP", "DI", "TC", "CR", "SR")
faltan <- setdiff(necesarios, names(M))
cat("Campos que faltan:", if (length(faltan)) paste(faltan, collapse = ", ") else "ninguno", "\n")

# CONFIRMADO: convert2df NO construye PP a partir de este CSV. Deja Page.start y
# Page.end dentro del objeto con esos nombres y no las combina. Se arma aqui.
if (!"PP" %in% names(M) && all(c("Page.start", "Page.end") %in% names(M))) {
  M$PP <- ifelse(is.na(M$Page.start) | M$Page.start == "", "",
                 paste(trimws(M$Page.start), trimws(M$Page.end), sep = "-"))
  cat("PP construido. No vacios:", sum(M$PP != ""), "de", nrow(M), "\n")
}
if (!"J9" %in% names(M) && "JI" %in% names(M)) M$J9 <- M$JI

# TC y PY deben ser numericos. El aviso "NAs introduced by coercion" que puede
# aparecer dentro de histNetwork viene de las paginas vacias (27% del corpus,
# sobre todo libros y capitulos) y es esperable.
M$TC <- as.numeric(M$TC)
M$PY <- as.numeric(M$PY)
cat("TC con NA:", sum(is.na(M$TC)), " PY con NA:", sum(is.na(M$PY)), "\n")

# ------------------------------------------------- 3. Limpiezas recomendadas
M$SO <- trimws(gsub("\\s+", " ", M$SO))          # seis revistas con espacios al borde
M <- M[!M$DT %in% c("ERRATUM", "RETRACTED"), ]   # 5 registros

# Duplicados: 23 registros en 11 grupos, listados en duplicados_a_revisar.csv.
# Revisar antes de activar esta linea.
# M <- M[!duplicated(paste(tolower(gsub("[^a-z]", "", tolower(M$TI))), M$PY)), ]

# --------------------------------------- 4. Diagnosticos, SIN tocar M
meta  <- read.csv("metadatos_corpus.csv", stringsAsFactors = FALSE)
clave <- if ("UT" %in% names(M)) M$UT else M$EID
pos   <- match(toupper(trimws(clave)), toupper(trimws(meta$EID)))
cat("Registros cruzados con metadatos:", sum(!is.na(pos)), "de", nrow(M), "\n")
capa  <- meta$capa[pos]
linea <- meta$linea_dominante[pos]

table(capa, useNA = "ifany")     # nucleo / rescate
table(linea)                     # diagnostico, NO la asignacion de linea del estudio
table(cut(M$PY, c(0, 1999, 2006, 2013, 2019, 2100),
          labels = c("<=1999", "2000-06", "2007-13", "2014-19", "2020-26")), linea)

# ---------------------------------------------------- 5. Descriptivos
res <- biblioAnalysis(M, sep = ";")
summary(res, k = 20, pause = FALSE)

# ------------------------------- 6. Red de citacion directa (histNetwork)
# ANTECEDENTE. Sin la reparacion del paso 1b, histNetwork solo emparejaba
# documentos de UN AUTOR: los 20 primeros por LCS eran los 20 de un autor y
# Jacobides et al. (2018), con 1.203 citas internas reales, quedaba por debajo
# de 59. La causa era el troceo de las referencias de varios autores, que la
# reparacion corrige. Lo que no se ha comprobado es que histNetwork empareje
# bien DESPUES de reparar: la tabla n_autores de abajo lo dice. Si en los 20
# primeros aparecen trabajos de varios autores, el sesgo quedo corregido.
#
# Mientras eso no se compruebe, el sendero principal del estudio es el de
# red_citacion_en_R.R, sobre la red propia (51.539 aristas), que no depende de
# bibliometrix.
hist_res <- histNetwork(M, min.citations = 10, sep = ";")

# histData es la tabla por documento: una fila por registro, con LCS y GCS.
# Su nrow es el tamano del corpus y no dice nada sobre la red.
hd <- hist_res$histData
cat("documentos citados dentro del corpus:", sum(hd$LCS > 0), "\n")
head(hd[order(-hd$LCS), c("Paper", "Year", "LCS", "GCS")], 20)

# Comprobacion del sesgo: numero de autores de los 20 primeros por LCS.
# Si todos tienen 1, el sesgo esta presente en tu corrida.
top20 <- head(hd[order(-hd$LCS), ], 20)
n_aut <- lengths(strsplit(M$AU[match(toupper(top20$DOI), toupper(M$DI))], ";"))
table(n_autores = n_aut)

histPlot(hist_res, n = 40, size = 5, labelsize = 4)   # solo como comparacion

# ------------------------------------------- 7. Cocitacion y acoplamiento
# Estas redes cuentan cadenas de CR identicas, y una misma obra aparece con
# formatos distintos: Moore (1993) figura con 237 variantes en el CSV crudo, y la
# mas frecuente reune solo 487 de sus 1.357 citas. Por eso se arman sobre una
# COPIA de M con las referencias normalizadas (apellido, anio y cuatro palabras
# del titulo). M queda intacto para histNetwork, que necesita revista y paginas.
# Normalizar tarda alrededor de un minuto.
Mc <- M
Mc$CR <- normalizar_cr(M$CR)

# Sin filtro, la cocitacion cruza 200.000 referencias entre si y no termina.
# Con n = 1000 se toman las 1.000 mas citadas: unos 935.000 pares, segundos.
cocit <- biblioNetwork(Mc, analysis = "co-citation", network = "references",
                       n = 1000, sep = ";")
networkPlot(cocit, n = 50, Title = "Red de cocitacion", type = "fruchterman",
            size.cex = TRUE, remove.multiple = FALSE, labelsize = 0.7)

# El acoplamiento produce una matriz documento x documento (5.269 x 5.269) y no
# tiene el problema de tamano de la cocitacion. Las referencias citadas una sola
# vez no aportan acoplamiento, asi que no hace falta filtrar.
acopl <- biblioNetwork(Mc, analysis = "coupling", network = "references", sep = ";")

# ------------------------------------------------------------ 8. Interfaz
# biblioshiny()
