# rutas_clave.R — Senderos de ruta clave (key-route main path) y origen de los caminos
#
# Solo R base: no necesita igraph ni otros paquetes. Correr desde la carpeta del
# proyecto (donde estan red_nodos.csv, red_aristas.csv y citacion_cruzada/).
#
# Metodo. Las aristas van de la obra citada a la que cita y se exige anio
# estrictamente creciente, de modo que ordenar los nodos por anio ya es un orden
# topologico. El conteo de busqueda (SPC, Hummon y Doreian 1989) de una arista es
# el numero de caminos fuente-sumidero que pasan por ella. Las rutas clave (Liu y
# Lu 2012) son las k aristas de mayor SPC; cada una se extiende hacia atras hasta
# una fuente y hacia adelante hasta un sumidero.
#   - busqueda "global": el camino con mayor SPC acumulado (Liu, Lu y Ho 2019);
#   - busqueda "local": en cada paso, la arista de mayor SPC.
# La union de esos caminos es la red de senderos de ruta clave.
#
# Origen de los caminos: de todos los caminos fuente-sumidero que terminan en una
# comunidad, que parte empieza en documentos de cada comunidad.
#
# Duplicados: se aplica la regla de duplicados (duplicados_quitados.csv: 12 registros;
# las citas de un duplicado quitado pasan al registro conservado), de modo que las
# cifras corresponden al corpus del articulo (5.262 documentos, 50.273 aristas).
#
# Salidas (en senderos/): rutas_clave_aristas.csv, rutas_clave_nodos.csv,
# origen_caminos.csv

nodos   <- read.csv("red_nodos.csv", stringsAsFactors = FALSE)
aristas <- read.csv("red_aristas.csv", stringsAsFactors = FALSE)
lin     <- read.csv("citacion_cruzada/lineas_por_documento.csv", stringsAsFactors = FALSE)
nodos$comunidad <- lin$linea_comunidad[match(nodos$EID, lin$EID)]

dup <- read.csv("duplicados_quitados.csv", stringsAsFactors = FALSE)
id_de <- setNames(nodos$id, nodos$EID)
quitar <- setNames(id_de[dup$EID_conservado], id_de[dup$EID_quitado])   # id quitado -> id conservado
aristas <- aristas[!(aristas$desde %in% as.integer(names(quitar))), ]   # el duplicado no cita
i <- match(as.character(aristas$hacia), names(quitar))
aristas$hacia[!is.na(i)] <- quitar[i[!is.na(i)]]                         # las citas pasan al conservado
aristas <- aristas[aristas$desde != aristas$hacia, ]

anio <- setNames(nodos$anio, nodos$id)
e <- unique(data.frame(from = aristas$hacia, to = aristas$desde))   # citado -> citante
e <- e[!is.na(anio[as.character(e$from)]) & !is.na(anio[as.character(e$to)]) &
       anio[as.character(e$from)] < anio[as.character(e$to)], ]
V <- sort(unique(c(e$from, e$to)))
ix <- function(x) match(x, V)
e$f <- ix(e$from); e$t <- ix(e$to)
ya <- anio[as.character(V)]; ye_t <- ya[e$t]; ye_f <- ya[e$f]
anios <- sort(unique(ya))
cat("aristas:", nrow(e), " nodos:", length(V), "\n")

tiene_in  <- tabulate(e$t, length(V)) > 0
tiene_out <- tabulate(e$f, length(V)) > 0

# caminos desde las fuentes (fw) y hacia los sumideros (bw)
fw <- ifelse(tiene_in, 0, 1)
for (y in anios) { s <- ye_t == y; if (any(s)) { a <- tapply(fw[e$f[s]], e$t[s], sum); fw[as.integer(names(a))] <- a } }
bw <- ifelse(tiene_out, 0, 1)
for (y in rev(anios)) { s <- ye_f == y; if (any(s)) { a <- tapply(bw[e$t[s]], e$f[s], sum); bw[as.integer(names(a))] <- a } }
e$spc <- fw[e$f] * bw[e$t]
cat("caminos fuente-sumidero:", format(sum(bw[!tiene_in]), big.mark = ","), "\n")

# mejor predecesor / sucesor: global (SPC acumulado) y local (SPC de la arista)
mejor <- function(clave, valor, n) {   # para cada clave, la fila de mayor valor (primera en empate)
  o <- order(clave, -valor); o <- o[!duplicated(clave[o])]; r <- rep(NA_integer_, n); r[clave[o]] <- o; r
}
acc_b <- numeric(length(V)); pred_g <- rep(NA_integer_, length(V))
for (y in anios) {
  s <- which(ye_t == y); if (!length(s)) next
  val <- e$spc[s] + acc_b[e$f[s]]
  m <- mejor(e$t[s], val, length(V)); k <- which(!is.na(m))
  pred_g[k] <- e$f[s][m[k]]; acc_b[k] <- val[m[k]]
}
acc_f <- numeric(length(V)); suc_g <- rep(NA_integer_, length(V))
for (y in rev(anios)) {
  s <- which(ye_f == y); if (!length(s)) next
  val <- e$spc[s] + acc_f[e$t[s]]
  m <- mejor(e$f[s], val, length(V)); k <- which(!is.na(m))
  suc_g[k] <- e$t[s][m[k]]; acc_f[k] <- val[m[k]]
}
m <- mejor(e$t, e$spc, length(V)); pred_l <- ifelse(is.na(m), NA, e$f[m])
m <- mejor(e$f, e$spc, length(V)); suc_l <- ifelse(is.na(m), NA, e$t[m])

trazar <- function(u, v, pred, suc) {
  p <- c(u, v)
  while (!is.na(pred[p[1]])) p <- c(pred[p[1]], p)
  while (!is.na(suc[p[length(p)]])) p <- c(p, suc[p[length(p)]])
  p
}
orden <- order(-e$spc)
e$rango <- NA_integer_; e$rango[orden] <- seq_along(orden)

etq <- nodos$etiqueta[match(V, nodos$id)]; com <- nodos$comunidad[match(V, nodos$id)]
nod_out <- data.frame(id = V, etiqueta = etq, anio = ya, comunidad = com)
ar_out <- NULL
for (modo in c("global", "local")) {
  for (k in c(1, 5, 10, 20, 50)) {
    cams <- lapply(orden[1:k], function(i)
      if (modo == "global") trazar(e$f[i], e$t[i], pred_g, suc_g) else trazar(e$f[i], e$t[i], pred_l, suc_l))
    nn <- unique(unlist(cams))
    pares <- unique(do.call(rbind, lapply(cams, function(p) cbind(p[-length(p)], p[-1]))))
    fuentes <- unique(sapply(cams, `[`, 1))
    cat(sprintf("%-6s k=%2d: %3d nodos, %3d aristas | fuentes: %s\n", modo, k, length(nn), nrow(pares),
                paste(etq[fuentes][order(ya[fuentes])], collapse = "; ")))
    nod_out[[paste0(modo, "_k", k)]] <- seq_along(V) %in% nn
    ar_out <- rbind(ar_out, data.frame(modo = modo, k = k, desde = etq[pares[, 1]], hacia = etq[pares[, 2]],
                                       desde_id = V[pares[, 1]], hacia_id = V[pares[, 2]],
                                       comunidad_desde = com[pares[, 1]], comunidad_hacia = com[pares[, 2]]))
  }
}
ar_out$spc <- e$spc[match(paste(ix(ar_out$desde_id), ix(ar_out$hacia_id)), paste(e$f, e$t))]
ar_out$spc_relativo <- round(ar_out$spc / max(e$spc), 4)
nod_out <- nod_out[rowSums(nod_out[, grep("_k", names(nod_out))]) > 0, ]
write.csv(ar_out, "senderos/rutas_clave_aristas.csv", row.names = FALSE)
write.csv(nod_out[order(nod_out$anio), ], "senderos/rutas_clave_nodos.csv", row.names = FALSE)

cat("\nPrimeras 20 rutas clave:\n")
top <- orden[1:20]
print(data.frame(rango = 1:20, desde = etq[e$f[top]], hacia = etq[e$t[top]],
                 spc_relativo = round(e$spc[top] / e$spc[top[1]], 3)), row.names = FALSE)

# ---------------------------------------------- origen de los caminos
fuentes <- which(!tiene_in)
destinos <- c("Emprendimiento", "Estrategia y plataformas", "Innovacion", "Servicio")
orig <- sapply(destinos, function(C) {
  bC <- ifelse(tiene_out, 0, as.numeric(!is.na(com) & com == C))
  for (y in rev(anios)) { s <- ye_f == y; if (any(s)) { a <- tapply(bC[e$t[s]], e$f[s], sum); bC[as.integer(names(a))] <- a } }
  tapply(bC[fuentes], ifelse(is.na(com[fuentes]), "sin comunidad", com[fuentes]), sum) / sum(bC[fuentes]) * 100
})
orig <- round(orig, 1)
cat("\n% de los caminos que terminan en cada comunidad (columnas), segun la comunidad donde empiezan (filas)\n")
print(orig)
write.csv(orig, "senderos/origen_caminos.csv")
