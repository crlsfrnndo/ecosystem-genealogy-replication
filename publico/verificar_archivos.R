# verificar_archivos.R
# Comprueba que cada archivo compartido llego completo, comparando tamano y huella
# MD5. Correrlo desde la raiz del repositorio, antes de cualquier analisis. Un
# archivo truncado no siempre produce error: read.csv lee las filas que hay y no
# avisa.
# Version del repositorio: lista los archivos compartidos (red_nodos.csv y
# lineas_por_documento.csv sin titulos). No incluye el corpus de Scopus.

esperado <- data.frame(
  archivo = c("metadatos_corpus.csv", "red_nodos.csv", "red_aristas.csv", "red_aristas_spc.csv", "sendero_principal.csv", "citacion_cruzada/lineas_por_documento.csv"),
  bytes   = c(439137, 479547, 476515, 2306291, 2855, 428241),
  md5     = c("c6957c4279b5ca80c3b13279c74d82c8", "5191dfe3916faa3fac742d94e80d3bb3", "05650c1ab1515b69c0cda42076a9c8c2", "42ad8663a032841fa2a895b68f9ff61f", "5f92fd82bc35e5757c547bee8798e9c5", "2ac827c16db271fc4024848ecf8dd2e9"),
  stringsAsFactors = FALSE
)

esperado$existe <- file.exists(esperado$archivo)
esperado$bytes_local <- ifelse(esperado$existe, file.size(esperado$archivo), NA)
esperado$md5_local <- ifelse(esperado$existe,
                             unname(tools::md5sum(esperado$archivo)), NA)
esperado$estado <- with(esperado, ifelse(!existe, "FALTA",
                        ifelse(bytes_local == 0, "VACIO",
                        ifelse(md5_local != md5, "INCOMPLETO o distinto", "ok"))))

cat("Carpeta:", getwd(), "\n\n")
print(esperado[, c("archivo", "bytes", "bytes_local", "estado")], row.names = FALSE)
if (all(esperado$estado == "ok")) cat("\nTodos los archivos estan completos.\n") else
  cat("\nReemplaza los archivos que no dicen 'ok' antes de seguir.\n")
