#!/usr/bin/env python3
"""
comunidades.py — Paso 4: línea (comunidad) de cada documento.

1. Detecta comunidades en la red de citación directa, tratada como no dirigida
   y sin aristas repetidas, con el algoritmo de Leiden (modularidad, semilla
   42). Compara la partición con otras cuatro semillas (información mutua
   normalizada).
2. Nombra las cinco comunidades grandes según sus documentos más citados y los
   términos de sus títulos. Las demás comunidades y los documentos aislados
   quedan como "otra o aislado".
3. Añade dos variables de control: el término de ecosistema del título
   (linea_titulo) y si algún autor del documento es autor semilla
   (autor_semilla).

Entradas: red_nodos.csv, red_aristas.csv y corpus_bibliometrix.csv (este
          último solo para títulos y autores; no se redistribuye)
Salida:   citacion_cruzada/lineas_por_documento.csv
          EID, etiqueta, anio, linea_comunidad, linea_titulo, autor_semilla,
          citas_internas

Uso, desde la raíz del repositorio:
    python3 citacion_cruzada/comunidades.py [corpus_bibliometrix.csv]

Requiere python-igraph y leidenalg. El análisis original usó igraph 1.0.0 y
leidenalg 0.12.0; con otras versiones la numeración de las comunidades puede
cambiar, y el script avisa si los tamaños no coinciden con los del artículo.

Recuperado del espacio de trabajo de la sesión de análisis (cruz1.py, 6 oct
2026) y adaptado para leer los archivos del repositorio.
"""
import os, re, sys, unicodedata, warnings
import numpy as np, pandas as pd
import igraph as ig, leidenalg as la

warnings.filterwarnings("ignore")
CORPUS = sys.argv[1] if len(sys.argv) > 1 else "corpus_bibliometrix.csv"

N = pd.read_csv("red_nodos.csv").sort_values("id").reset_index(drop=True)
A = pd.read_csv("red_aristas.csv")
CB = pd.read_csv(CORPUS, dtype=str, usecols=["EID", "Title", "Authors"])
assert (CB.EID.values == N.EID.values).all(), "el corpus y red_nodos.csv deben tener el mismo orden"
print("nodos", len(N), "aristas", len(A))


def norm(s):
    return unicodedata.normalize("NFKD", str(s).lower()).encode("ascii", "ignore").decode("ascii")


# ---- 1. comunidades (Leiden, modularidad) sobre la red no dirigida
g = ig.Graph(n=len(N), edges=list(zip(A.desde, A.hacia)), directed=False)
g.simplify()
part = la.find_partition(g, la.ModularityVertexPartition, seed=42)
memb = np.array(part.membership)
print("modularidad Q:", round(g.modularity(memb), 3))
nmi = [ig.compare_communities(memb, la.find_partition(g, la.ModularityVertexPartition, seed=s).membership,
                              method="nmi") for s in [1, 7, 99, 2026]]
print("NMI frente a otras semillas:", [round(x, 3) for x in nmi])
com = memb.copy()
com[np.array(g.degree()) == 0] = -1          # aislados

# ---- 2. nombres de las comunidades grandes (leidenalg numera por tamaño)
NOMBRES = {0: "Emprendimiento", 1: "Estrategia y plataformas", 2: "Innovacion", 3: "Servicio", 4: "Digital y datos"}
ESPERADO = {"Emprendimiento": 1699, "Estrategia y plataformas": 1660, "Innovacion": 1047, "Servicio": 498,
            "Digital y datos": 156}
N["linea_comunidad"] = [NOMBRES.get(c, "otra o aislado") for c in com]
tam = N.linea_comunidad.value_counts()
print(tam.to_string())
if any(tam.get(k, 0) != v for k, v in ESPERADO.items()):
    print("AVISO: los tamaños no coinciden con los del artículo; revise los nombres con los documentos más citados:")
for c in range(5):
    s = N[com == c].sort_values("citas_internas", ascending=False).head(4)
    print(f"  comunidad {c} ({NOMBRES[c]}):", "; ".join(s.etiqueta))

# ---- 3. término del título y autor semilla
T = CB.Title.fillna("").map(norm)
REGLAS = [("emprendimiento", r"entrepreneur\w* ecosyst|start-?up ecosyst|startup ecosyst|venture ecosyst"),
          ("innovacion", r"innovation ecosyst"),
          ("plataforma", r"platform\w*[- ]?(based )?ecosyst"),
          ("negocios", r"business ecosyst"),
          ("servicio", r"service ecosyst"),
          ("digital/software", r"digital ecosyst|software ecosyst|data ecosyst|iot ecosyst|technolog\w* ecosyst"),
          ("conocimiento", r"knowledge ecosyst|university ecosyst|academic ecosyst|research ecosyst"),
          ("industrial", r"industrial ecosyst")]


def etiq(t):
    for k, p in REGLAS:
        if re.search(p, t):
            return k
    return "generico" if "ecosyst" in t else "sin termino"


N["linea_titulo"] = T.map(etiq).values
SEM = [r"\bmoore j", r"\biansiti", r"\blevien", r"\bteece d", r"\badner r", r"\bkapoor r", r"\bautio e",
       r"\bgranstrand", r"\britala p", r"\boh d", r"\bisenberg", r"\bspigel", r"\bstam e", r"\bacs z", r"\bmason c",
       r"\broundy", r"\baudretsch", r"\bmalecki", r"\bgawer", r"\bcusumano", r"\bparker g", r"\bvan alstyne",
       r"\btiwana", r"\beisenmann", r"\bjacobides", r"\bboudreau k", r"\bvargo", r"\blusch", r"\bakaka",
       r"\bchandler j", r"\bfrow p", r"\bbosch j", r"\bjansen s", r"\bmesserschmitt", r"\bmanikas", r"\blungu m",
       r"\bcarayannis", r"\betzkowitz", r"\bleydesdorff", r"\bclarysse", r"\bvan de vrande"]
sp = re.compile("|".join(SEM))
N["autor_semilla"] = CB.Authors.fillna("").map(lambda s: bool(sp.search(norm(s)))).values
print("documentos de autor semilla:", int(N.autor_semilla.sum()))

os.makedirs("citacion_cruzada", exist_ok=True)
N[["EID", "etiqueta", "anio", "linea_comunidad", "linea_titulo", "autor_semilla", "citas_internas"]].to_csv(
    "citacion_cruzada/lineas_por_documento.csv", index=False)
print("escrito citacion_cruzada/lineas_por_documento.csv")
