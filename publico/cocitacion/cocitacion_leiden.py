#!/usr/bin/env python3
"""
cocitacion_leiden.py — Paso 2 de la cocitacion corregida.

Por que no networkPlot: entre las referencias mas citadas casi todas se citan
juntas al menos una vez, de modo que la red es casi completa (en la salida de
bibliometrix, 47 de las 100 referencias estaban unidas a las otras 99) y el
agrupamiento devuelve un solo bloque. Aqui los grupos se buscan sobre la FUERZA
de los vinculos (fuerza de asociacion, van Eck y Waltman 2009) con Leiden.

Entrada: cocitacion/claves_largas.csv (de claves_cocitacion.R) y
         citacion_cruzada/lineas_por_documento.csv
Uso:     python3 cocitacion/cocitacion_leiden.py      (desde la carpeta del proyecto)
Requiere: pandas, numpy, scipy, python-igraph, leidenalg, scikit-learn
"""
import pandas as pd, numpy as np, igraph as ig, leidenalg as la, scipy.sparse as sp
from sklearn.metrics import normalized_mutual_info_score as nmi

TOP, MIN_COCIT, SEMILLAS = 300, 3, 30
NOMBRES = None  # se asignan abajo segun el miembro mas citado de cada grupo

k = pd.read_csv("cocitacion/claves_largas.csv").drop_duplicates()
k = k[k.clave.str.match(r"^[A-Z]{2,}\s+(1[89]|20)\d\d\b")]   # descarta claves sin apellido ni anio
L = pd.read_csv("citacion_cruzada/lineas_por_documento.csv")[["EID", "anio", "linea_comunidad"]]
cnt = k.clave.value_counts()

def agrupar(top_n):
    top = cnt.index[:top_n]; kk = k[k.clave.isin(top)]; docs = kk.EID.unique()
    di = {e: i for i, e in enumerate(docs)}; ri = {c: i for i, c in enumerate(top)}
    A = sp.csr_matrix((np.ones(len(kk)), ([di[e] for e in kk.EID], [ri[c] for c in kk.clave])),
                      shape=(len(docs), top_n))
    C = (A.T @ A).toarray(); c = np.diag(C).copy(); np.fill_diagonal(C, 0)
    iu = np.triu_indices(top_n, 1); keep = C[iu] >= MIN_COCIT
    S = C / np.outer(c, c) * c.sum()                           # fuerza de asociacion
    g = ig.Graph(n=top_n, edges=list(zip(iu[0][keep], iu[1][keep]))); g.es["weight"] = S[iu][keep]
    parts = [la.find_partition(g, la.RBConfigurationVertexPartition, weights="weight", seed=s)
             for s in range(SEMILLAS)]
    best = max(parts, key=lambda p: p.quality()); m = np.array(best.membership)
    return top, m, c, g.density(), g.modularity(m, weights="weight"), min(nmi(m, p.membership) for p in parts)

print("Robustez al tamano de la red")
for n_ in (200, 300, 500):
    _, m, _, dens, Q, st = agrupar(n_)
    print(f"  {n_} referencias: densidad {dens:.2f}, grupos {np.bincount(m).tolist()}, Q {Q:.3f}, NMI minima {st:.2f}")

top, m, c, *_ = agrupar(TOP)
g = pd.DataFrame({"referencia": top, "grupo": m, "citas": c.astype(int)})
g["anio_ref"] = g.referencia.str.extract(r"\s(\d{4})")[0].astype(int)
cab = g.sort_values("citas", ascending=False).groupby("grupo").referencia.first()
etiq = {gr: ("Estrategia, innovacion y plataformas" if r.startswith("MOORE") else
             "Emprendimiento y desarrollo regional" if r.startswith(("STAM", "SPIGEL", "ISENBERG")) else
             "Logica de servicio" if r.startswith(("VARGO", "LUSCH")) else f"grupo {gr}")
        for gr, r in cab.items()}
g["base"] = g.grupo.map(etiq)
g.sort_values(["grupo", "citas"], ascending=[True, False]).to_csv("cocitacion/grupos_cocitacion.csv", index=False)

kk = k[k.clave.isin(top)].merge(g[["referencia", "base"]], left_on="clave", right_on="referencia").merge(L, on="EID", how="left")
kk["linea_comunidad"] = kk.linea_comunidad.fillna("sin comunidad")
q = pd.crosstab(kk.linea_comunidad, kk.base, normalize="index").mul(100).round(1)
q.to_csv("cocitacion/base_por_linea.csv")
kk["periodo"] = pd.cut(kk.anio, [0, 2013, 2016, 2019, 2030], labels=["<=2013", "2014-16", "2017-19", "2020-26"])
p = pd.crosstab([kk.linea_comunidad, kk.periodo], kk.base, normalize="index").mul(100).round(1)
p = p.join(kk.groupby(["linea_comunidad", "periodo"], observed=True).EID.nunique().rename("documentos"))
p.to_csv("cocitacion/base_por_linea_y_periodo.csv")
print("\n% de las citas de cada linea que van a cada base\n", q.round(0).to_string())
print("\nPor periodo\n", p.round(0).to_string())
