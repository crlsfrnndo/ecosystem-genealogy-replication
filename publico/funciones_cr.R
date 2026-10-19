# funciones_cr.R
# Reparacion y normalizacion del campo de referencias (CR) de este export de Scopus.
#
# EL PROBLEMA. En este export, Scopus usa ";" para separar tanto las referencias
# entre si como los autores dentro de cada referencia:
#   "Jacobides M.G.; Cennamo C.; Gawer A., Towards a theory of ecosystems, ...(2018); Moore J.F., ..."
# Bibliometrix parte CR por ";", asi que toda referencia de varios autores queda
# troceada: "JACOBIDES M.G.", "CENNAMO C." y "GAWER A., TOWARDS A THEORY..." pasan
# a ser tres referencias distintas, y la unica con titulo y anio empieza por el
# ULTIMO autor. Verificado sobre el corpus: 930.412 fragmentos que en realidad son
# 399.983 referencias (76,5 por registro). Esta es la causa de que histNetwork
# solo emparejara trabajos de un autor.
#
# reparar_cr()    une cada autor suelto con el fragmento siguiente y reconstruye
#                 la referencia completa. Usar sobre M$CR antes de cualquier analisis.
# normalizar_cr() reduce cada referencia a una clave "APELLIDO ANIO CUATRO PALABRAS
#                 DEL TITULO", para que las variantes de formato de una misma obra
#                 cuenten como una. Usar SOLO para cocitacion y acoplamiento: borra
#                 revista, volumen y paginas, que histNetwork necesita.
#
# Probado en R 4.3.3 sobre corpus_bibliometrix.csv: Jacobides et al. (2018) pasa
# de 9 apariciones con su primer autor a 1.081; Moore (1993) reune 1.182.

reparar_cr <- function(CR, sep = ";") {
  CR[is.na(CR)] <- ""
  fr  <- strsplit(CR, sep, fixed = TRUE)
  rid <- rep(seq_along(fr), lengths(fr))
  f   <- trimws(unlist(fr))
  ok  <- nchar(f) > 0
  f   <- f[ok]; rid <- rid[ok]
  fa  <- iconv(toupper(f), to = "ASCII//TRANSLIT", sub = "")
  # fragmento que es solo un autor: "APELLIDO I." o "DE LA CRUZ J.-P.", sin comas
  solo_autor <- grepl("^[A-Z' .-]+ ([A-Z]\\.-?)+$", fa, perl = TRUE) &
                !grepl(",", fa, fixed = TRUE)
  prev_rid  <- c(-1L, head(rid, -1))
  prev_solo <- c(FALSE, head(solo_autor, -1))
  inicio <- rid != prev_rid | !prev_solo     # empieza referencia nueva
  ref  <- cumsum(inicio)
  refs <- vapply(split(f, ref), paste, "", collapse = ", ")
  rec  <- rid[inicio]
  agg  <- vapply(split(refs, rec), paste, "", collapse = paste0(sep, " "))
  out  <- rep("", length(CR))
  out[as.integer(names(agg))] <- agg
  out
}

normalizar_ref <- function(r) {
  r <- iconv(toupper(trimws(r)), to = "ASCII//TRANSLIT", sub = "")
  m <- regexpr("\\((1[89]|20)[0-9]{2}\\)", r)
  anio <- ifelse(m > 0, substr(r, m + 1, m + 4), "")
  ap <- sub("^([A-Z' -]+?)\\s+([A-Z]\\.-?)+.*$", "\\1", r, perl = TRUE)
  ap[ap == r] <- sub("^([A-Z'-]+).*$", "\\1", r[ap == r], perl = TRUE)
  ap <- gsub("[^A-Z]", "", ap)
  segs <- strsplit(r, ",\\s*")
  tit <- vapply(segs, function(s) {
    s <- trimws(s)
    s <- s[!grepl("^([A-Z'-]+ )*[A-Z'-]+ ([A-Z]\\.-?)+$|^ET AL\\.?$", s, perl = TRUE) &
           nchar(s) > 0]
    if (length(s)) s[1] else ""
  }, "")
  pal <- strsplit(gsub("[^A-Z0-9 ]", " ", tit), "\\s+")
  t4  <- vapply(pal, function(w) paste(head(w[nchar(w) >= 3], 4), collapse = " "), "")
  ifelse(nchar(ap) == 0 | anio == "", r, trimws(paste(ap, anio, t4)))
}

normalizar_cr <- function(CR, sep = ";") {
  CR[is.na(CR)] <- ""
  fr  <- strsplit(CR, sep, fixed = TRUE)
  rid <- rep(seq_along(fr), lengths(fr))
  f   <- trimws(unlist(fr))
  ok  <- nchar(f) > 0
  k   <- normalizar_ref(f[ok]); rid <- rid[ok]
  agg <- vapply(split(k, rid), function(x) paste(unique(x), collapse = sep), "")
  out <- rep("", length(CR))
  out[as.integer(names(agg))] <- agg
  out
}
