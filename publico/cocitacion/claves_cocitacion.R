# claves_cocitacion.R
# Paso 1 de la cocitacion corregida. Repara y normaliza las referencias con
# funciones_cr.R y escribe una fila por (documento, referencia normalizada).
# Correr desde la carpeta del proyecto, donde estan corpus_bibliometrix.csv y
# funciones_cr.R. Tarda alrededor de un minuto. Salida: claves_largas.csv
source("funciones_cr.R")
d <- read.csv("corpus_bibliometrix.csv", stringsAsFactors = FALSE)
n <- normalizar_cr(reparar_cr(toupper(d$References)))
s <- strsplit(n, ";", fixed = TRUE)
out <- data.frame(EID = rep(d$EID, lengths(s)), clave = unlist(s), stringsAsFactors = FALSE)
out <- out[nchar(out$clave) > 0, ]
write.csv(out, "cocitacion/claves_largas.csv", row.names = FALSE)
cat("pares documento-referencia:", nrow(out), " referencias distintas:", length(unique(out$clave)), "\n")
