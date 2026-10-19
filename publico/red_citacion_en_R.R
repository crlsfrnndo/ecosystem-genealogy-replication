# red_citacion_en_R.R  — version 2 (29 sept 2026)
#
# CORRECCION de la version 1: enumeraba caminos con all_simple_paths, que es un
# problema exponencial y no termina sobre 50.000 aristas. El conteo de busqueda
# de Hummon y Doreian NO se calcula enumerando caminos: se calcula por
# programacion dinamica sobre el orden topologico, en tiempo lineal. Asi esta
# aqui, y corre en segundos.
#
# POR QUE ESTA RED Y NO histNetwork. Con el CR crudo, histNetwork solo empareja
# documentos de UN AUTOR (los 20 primeros por LCS eran los 20 de un autor;
# Jacobides et al. 2018, con 1.203 citas internas, quedaba bajo 59). La causa,
# identificada el 5 oct 2026: en este export ";" separa las referencias Y los
# autores dentro de cada referencia, y bibliometrix trocea toda referencia de
# varios autores. funciones_cr.R lo repara; si tras la reparacion histNetwork
# empareja bien, las dos redes deberian coincidir.
#
# Esta red no tiene ese problema: parte las referencias por su cierre "(anio);",
# no por cada ";", y empareja por apellido del primer autor, anio y palabras del
# titulo. Cubre 387.003 de las 399.963 referencias reales del corpus (97%).
# En los casos que bibliometrix si resolvia, los dos metodos coinciden dentro de
# un 10%: Adner 2017 (1.031 aqui, 1.123 en bibliometrix), Stam 2015 (955 / 922),
# Spigel 2017 (920 / 905).

library(igraph)

nodos   <- read.csv("red_nodos.csv",   stringsAsFactors = FALSE)
aristas <- read.csv("red_aristas.csv", stringsAsFactors = FALSE)

# Orientar citado -> citante, para que el tiempo corra hacia adelante, y exigir
# anio estrictamente creciente. Eso deja un DAG sin necesidad de romper ciclos a
# posteriori y descarta solo el 2% de las aristas (las del mismo anio).
anio <- setNames(nodos$anio, nodos$id)
ar <- data.frame(from = aristas$hacia, to = aristas$desde)   # citado -> citante
ar <- ar[!is.na(anio[as.character(ar$from)]) &
         !is.na(anio[as.character(ar$to)]) &
         anio[as.character(ar$from)] < anio[as.character(ar$to)], ]
cat("aristas utiles:", nrow(ar), "de", nrow(aristas), "\n")

g <- graph_from_data_frame(ar, directed = TRUE)
stopifnot(is_dag(g))

# ---------------------------------------- Conteo de busqueda (SPC), O(V+E)
topo <- topo_sort(g, mode = "out")
fin  <- degree(g, mode = "in")
fout <- degree(g, mode = "out")

# caminos desde las fuentes hasta cada nodo
f <- ifelse(fin == 0, 1, 0); names(f) <- V(g)$name
for (v in topo) {
  if (fin[v] > 0) f[v] <- sum(f[neighbors(g, v, mode = "in")])
}
# caminos desde cada nodo hasta los sumideros
b <- ifelse(fout == 0, 1, 0); names(b) <- V(g)$name
for (v in rev(topo)) {
  if (fout[v] > 0) b[v] <- sum(b[neighbors(g, v, mode = "out")])
}
# SPC de cada arista = caminos que entran al origen x caminos que salen del destino
el <- as_edgelist(g, names = FALSE)
E(g)$spc <- f[el[, 1]] * b[el[, 2]]
cat("caminos fuente-sumidero:", format(sum(E(g)$spc), scientific = TRUE), "\n")

# ------------------------------------------------- Sendero principal
# Desde la arista de mayor SPC, avanzar y retroceder siguiendo el maximo local.
e0 <- which.max(E(g)$spc)
cam <- as.vector(el[e0, ])
repeat {
  sal <- incident(g, cam[length(cam)], mode = "out")
  if (length(sal) == 0) break
  mej <- sal[which.max(sal$spc)]
  cam <- c(cam, head_of(g, mej))
}
repeat {
  ent <- incident(g, cam[1], mode = "in")
  if (length(ent) == 0) break
  mej <- ent[which.max(ent$spc)]
  cam <- c(tail_of(g, mej), cam)
}
sp <- data.frame(orden = seq_along(cam), id = as.integer(V(g)$name[cam]))
sp <- merge(sp, nodos[, intersect(c("id", "etiqueta", "anio", "autores", "titulo", "fuente", "citas_internas"), names(nodos))],
            by = "id", all.x = TRUE)
print(sp[order(sp$orden), intersect(c("orden", "anio", "etiqueta", "autores", "titulo"), names(sp))])

# Dibujo, ordenado por anio en el eje vertical
sub <- induced_subgraph(g, cam)
V(sub)$label <- nodos$etiqueta[match(as.integer(V(sub)$name), nodos$id)]
plot(sub, vertex.size = 5, edge.arrow.size = 0.4, vertex.label.cex = 0.7,
     layout = layout_as_tree(sub, root = 1, flip.y = FALSE))

# Los resultados ya calculados estan en sendero_principal.csv y
# red_aristas_spc.csv, por si se quiere comparar contra esta corrida.

# ------------------------------- Citacion cruzada entre lineas (operacion 2)
meta <- read.csv("metadatos_corpus.csv", stringsAsFactors = FALSE)
nodos$linea <- meta$linea_dominante[match(nodos$EID, meta$EID)]
lin <- setNames(nodos$linea, nodos$id)
cruz <- table(desde = lin[as.character(ar$to)], hacia = lin[as.character(ar$from)])
print(cruz)
# Repetir excluyendo a los autores semilla de las referencias antes de emparejar,
# por el piso de conectividad que impone la regla de pertenencia, y reportar ambas.
