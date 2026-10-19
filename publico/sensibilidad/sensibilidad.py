#!/usr/bin/env python3
"""
sensibilidad.py — Pruebas de sensibilidad del artículo (7 oct 2026).

Replica los resultados principales sobre el corpus completo (5.274 registros) y
los recalcula en tres versiones:

  sin_duplicados  quita 12 registros duplicados (mismo título normalizado y año;
                  se conserva el primero del archivo, como la línea comentada de
                  cargar_en_bibliometrix.R). Las citas que recibía el registro
                  quitado pasan al conservado.
  nucleo          sin duplicados y sin la capa de rescate por citación entrante.
  articulos       sin duplicados y solo artículos de revista (Article y Review).

En todas se conserva la partición original en comunidades (la pregunta es si
los documentos excluidos producen el resultado). Además se vuelve a correr
Leiden sobre cada subred y se informa su concordancia con la partición
original (NMI).

Uso, desde la carpeta corpus_depurado:
    python3 sensibilidad/sensibilidad.py [ruta a claves_largas.csv]
Requiere: pandas, numpy, scipy, python-igraph, leidenalg, scikit-learn, statsmodels
Salidas en sensibilidad/: resumen_sensibilidad.csv, modelos_al_sensibilidad.csv,
senderos_k20_<version>.csv
"""
import re, sys, warnings
from collections import defaultdict, deque
import numpy as np, pandas as pd, igraph as ig, leidenalg as la, scipy.sparse as sp
from sklearn.metrics import normalized_mutual_info_score as nmi
import statsmodels.formula.api as smf
import statsmodels.api as sm
warnings.filterwarnings("ignore")

CLAVES = sys.argv[1] if len(sys.argv) > 1 else "cocitacion/claves_largas.csv"
OUT = "sensibilidad"
LINEAS = ["Emprendimiento", "Estrategia y plataformas", "Innovacion", "Servicio", "Digital y datos"]
PAISES_AL = {"Argentina", "Bolivia", "Brazil", "Chile", "Colombia", "Costa Rica", "Cuba",
             "Dominican Republic", "Ecuador", "El Salvador", "Guatemala", "Honduras", "Mexico",
             "Nicaragua", "Panama", "Paraguay", "Peru", "Puerto Rico", "Uruguay", "Venezuela"}

# ------------------------------------------------------------------ datos
N = pd.read_csv("red_nodos.csv").sort_values("id").reset_index(drop=True)
A = pd.read_csv("red_aristas.csv").drop_duplicates()
L = pd.read_csv("citacion_cruzada/lineas_por_documento.csv")
M = pd.read_csv("metadatos_corpus.csv", dtype=str)
CB = pd.read_csv("corpus_bibliometrix.csv", dtype=str,
                usecols=["EID", "Title", "Year", "Affiliations", "Document Type"])
assert (CB.EID.values == N.EID.values).all()
if "titulo" not in N.columns:   # el red_nodos.csv compartido no trae titulos
    N["titulo"] = CB.Title.values
N = N.merge(L[["EID", "linea_comunidad", "linea_titulo", "autor_semilla"]], on="EID", how="left")
N = N.merge(M[["EID", "capa"]], on="EID", how="left").sort_values("id").reset_index(drop=True)
N["linea"] = N.linea_comunidad.where(N.linea_comunidad.isin(LINEAS))      # 5 líneas; resto NaN
N["g"] = N.linea_comunidad.fillna("otra o aislado")                       # grupo para intermediación

def paises(s):
    return {a.split(",")[-1].strip() for a in s.split(";") if a.strip()} if isinstance(s, str) else set()
P = CB.Affiliations.map(paises)
N["al"] = P.map(lambda p: bool(p & PAISES_AL)).values
N["al_mixto"] = P.map(lambda p: bool(p & PAISES_AL) and bool(p - PAISES_AL)).values
N["al_solo"] = N.al & ~N.al_mixto

# duplicados: misma regla que cargar_en_bibliometrix.R
kdup = [re.sub("[^a-z]", "", str(t).lower()) + "|" + str(y) for t, y in zip(CB.Title, CB.Year)]
CB["kdup"] = kdup
primero = CB.groupby("kdup").cumcount() == 0
conservado = {k: i for i, k in zip(CB.index[primero], CB.kdup[primero])}
QUITAR = {i: conservado[CB.kdup[i]] for i in CB.index[~primero]}             # quitado -> conservado

K = pd.read_csv(CLAVES).drop_duplicates()
K = K[K.clave.str.match(r"^[A-Z]{2,}\s+(1[89]|20)\d\d\b", na=False)]
G0 = pd.read_csv("cocitacion/grupos_cocitacion.csv")
CLAVES_MOORE = set(K.clave[K.clave.str.startswith("MOORE 1993")])     # todas las variantes, como en la cocitación

def idx(etiqueta, palabra):
    m = N[(N.etiqueta == etiqueta) & N.titulo.str.contains(palabra, case=False, na=False)]
    return int(m.id.iloc[0])
CLAVE_NODOS = {
    "Adner 2006": idx("Adner R., 2006", "Match your innovation"),
    "Cohen 2006": idx("Cohen B., 2006", "Sustainable valley"),
    "Malecki 2011": idx("Malecki E.J., 2011", "Connecting local"),
    "Pitelis 2012": idx("Pitelis C., 2012", "Clusters"),
    "Stam 2015": idx("Stam E., 2015", "regional policy"),
    "Mack y Mayer 2016": idx("Mack E., 2016", "evolutionary dynamics"),
    "Theodoraki y Messeghem 2017": idx("Theodoraki C., 2017", "entrepreneurial support"),
    "Malecki 2018": idx("Malecki E.J., 2018", "Entrepreneurship and entrepreneurial ecosystems"),
    "Adner 2017": idx("Adner R., 2017", "Ecosystem as structure"),
    "Jacobides et al. 2018": idx("Jacobides M.G., 2018", "Towards a theory"),
    "Granstrand y Holgersson 2020": idx("Granstrand O., 2020", "conceptual review"),
    "Shipilov y Gawer 2020": idx("Shipilov A., 2020", "Integrating research"),
}

# ------------------------------------------------------------------ versiones
def version(nombre):
    keep = set(N.id)
    E = A.copy()
    if nombre != "completo":
        E = E[~E.desde.isin(QUITAR)]                                   # el duplicado no cita
        E["hacia"] = E.hacia.map(lambda h: QUITAR.get(h, h))           # citas al conservado
        keep -= set(QUITAR)
    if nombre == "nucleo":
        keep &= set(N.id[N.capa == "nucleo"])
    if nombre == "articulos":
        keep &= set(N.id[N.tipo.isin(["Article", "Review"])])
    E = E[E.desde.isin(keep) & E.hacia.isin(keep) & (E.desde != E.hacia)].drop_duplicates()
    return keep, E.reset_index(drop=True)

# ------------------------------------------------------------------ medidas
def asort(df, a, b):
    t = pd.crosstab(df[a], df[b]); cats = sorted(set(t.index) | set(t.columns))
    t = t.reindex(index=cats, columns=cats, fill_value=0); e = t.values / t.values.sum()
    s = (e.sum(1) * e.sum(0)).sum()
    return (np.trace(e) - s) / (1 - s), 1 - np.trace(e), 1 - s

def temporal(E):
    T = E.copy()
    T["y"] = N.anio.values[T.desde]; T["yc"] = N.anio.values[T.hacia]
    T = T[T.y > T.yc]
    T["li"] = N.linea.values[T.desde]; T["lj"] = N.linea.values[T.hacia]
    T["ti"] = N.linea_titulo.values[T.desde]; T["tj"] = N.linea_titulo.values[T.hacia]
    T["semilla"] = N.autor_semilla.values[T.hacia].astype(bool)
    return T

def medidas_red(keep, E, R):
    T = temporal(E)
    R["documentos"] = len(keep); R["vinculos"] = len(E); R["vinculos_temporales"] = len(T)
    R["nodos_dag"] = len(set(T.desde) | set(T.hacia))
    d = T.dropna(subset=["li", "lj"])
    for y in (2014, 2020, 2025):
        R[f"asortatividad_{y}"] = asort(d[d.y == y], "li", "lj")[0]
    p = d[d.y >= 2020]
    r, cruce, azar = asort(p, "li", "lj")
    R["asortatividad_2020_26"] = r; R["cruce_2020_26"] = cruce; R["cruce_azar_2020_26"] = azar
    R["asortatividad_2020_26_sin_semillas"] = asort(p[~p["semilla"]], "li", "lj")[0]
    dt = T.dropna(subset=["ti", "tj"])
    R["asort_titulo_2014"] = asort(dt[dt.y == 2014], "ti", "tj")[0]
    R["asort_titulo_2024"] = asort(dt[dt.y == 2024], "ti", "tj")[0]
    R["emprendimiento_se_cita_2020_26"] = (p[p.li == "Emprendimiento"].lj == "Emprendimiento").mean()
    # integradores
    d["fuera"] = d.li != d.lj
    g = d.groupby("hacia").agg(c=("fuera", "size"), f=("fuera", "mean"))
    R["mediana_otras_lineas_50mas"] = g[g.c >= 50].f.median()
    R["docs_50mas_citas"] = int((g.c >= 50).sum())
    for k in ("Adner 2017", "Jacobides et al. 2018", "Granstrand y Holgersson 2020"):
        i = CLAVE_NODOS[k]
        x = d[d.hacia == i]
        R[f"otras_lineas_{k}"] = (x.li != N.linea[i]).mean() if len(x) else np.nan
    # Leiden de nuevo sobre la subred
    ids = sorted(keep); pos = {n: j for j, n in enumerate(ids)}
    gr = ig.Graph(n=len(ids), edges=[(pos[a], pos[b]) for a, b in zip(E.desde, E.hacia)], directed=False)
    gr.simplify()
    part = la.find_partition(gr, la.ModularityVertexPartition, seed=42)
    m = np.array(part.membership)
    R["Q_leiden_nuevo"] = gr.modularity(m)
    orig = N.linea.values[ids]; ok = pd.notna(orig) & (np.array(gr.degree()) > 0)
    R["NMI_particion_original"] = nmi(orig[ok], m[ok])
    tam = pd.Series(m).value_counts()
    R["comunidades_grandes_nuevas"] = int((tam >= 0.01 * len(ids)).sum())
    return T

def medidas_cocitacion(keep, R):
    eids = set(N.EID[list(keep)])
    k = K[K.EID.isin(eids)]
    cnt = k.clave.value_counts(); top = cnt.index[:300]
    kk = k[k.clave.isin(top)]; docs = kk.EID.unique()
    di = {e: i for i, e in enumerate(docs)}; ri = {c: i for i, c in enumerate(top)}
    Am = sp.csr_matrix((np.ones(len(kk)), ([di[e] for e in kk.EID], [ri[c] for c in kk.clave])),
                       shape=(len(docs), 300))
    Cm = (Am.T @ Am).toarray(); c = np.diag(Cm).copy(); np.fill_diagonal(Cm, 0)
    iu = np.triu_indices(300, 1); ok = Cm[iu] >= 3
    S = Cm / np.outer(c, c) * c.sum()
    g = ig.Graph(n=300, edges=list(zip(iu[0][ok], iu[1][ok]))); g.es["weight"] = S[iu][ok]
    parts = [la.find_partition(g, la.RBConfigurationVertexPartition, weights="weight", seed=s)
             for s in range(30)]
    best = max(parts, key=lambda p: p.quality()); m = np.array(best.membership)
    R["NMI_min_semillas_cocit"] = min(nmi(m, p.membership) for p in parts)
    G = pd.DataFrame({"referencia": top, "grupo": m, "citas": c})
    cab = G.sort_values("citas", ascending=False).groupby("grupo").referencia.first()
    et = {gr: ("Estrategia" if r.startswith("MOORE") else
               "Emprendimiento" if r.startswith(("STAM", "SPIGEL", "ISENBERG")) else
               "Servicio" if r.startswith(("VARGO", "LUSCH")) else f"otro{gr}") for gr, r in cab.items()}
    G["base"] = G.grupo.map(et)
    R["grupos_cocitacion"] = int(G.grupo.nunique())
    R["tamanos_grupos"] = "/".join(str(x) for x in G.base.value_counts().reindex(
        ["Estrategia", "Emprendimiento", "Servicio"]).fillna(0).astype(int))
    base0 = G0.set_index("referencia").base
    com = G[G.referencia.isin(base0.index)]
    R["refs_comunes_con_original"] = len(com)
    R["NMI_bases_vs_original"] = nmi(base0[com.referencia].values, com.base.values)
    lin = dict(zip(N.EID, N.linea_comunidad))
    x = kk.merge(G[["referencia", "base"]], left_on="clave", right_on="referencia")
    x["lc"] = x.EID.map(lin)
    q = pd.crosstab(x.lc, x.base, normalize="index")
    R["innovacion_a_base_estrategia"] = q.loc["Innovacion", "Estrategia"]
    R["emprendimiento_a_base_propia"] = q.loc["Emprendimiento", "Emprendimiento"]
    R["emprendimiento_a_base_estrategia"] = q.loc["Emprendimiento", "Estrategia"]
    R["estrategia_a_base_propia"] = q.loc["Estrategia y plataformas", "Estrategia"]
    # citas a Moore (1993) en la comunidad de emprendimiento
    cita_moore = set(k.EID[k.clave.isin(CLAVES_MOORE)])
    e = N.loc[sorted(keep)]; e = e[e.linea_comunidad == "Emprendimiento"]
    per = pd.cut(e.anio, [0, 2013, 2016, 2019, 2030], labels=["hasta_2013", "2014_16", "2017_19", "2020_26"])
    for p_, s in e.groupby(per, observed=True):
        R[f"moore_emprendimiento_{p_}"] = s.EID.isin(cita_moore).mean()
        R[f"docs_emprendimiento_{p_}"] = len(s)

def medidas_senderos(T, nombre, R):
    Ed = list(dict.fromkeys(zip(T.hacia, T.desde)))       # flujo: citado -> cita
    out = defaultdict(list); inn = defaultdict(list); V = set()
    for u, v in Ed: out[u].append(v); inn[v].append(u); V |= {u, v}
    gin = {n: len(inn[n]) for n in V}; q = deque(n for n in V if gin[n] == 0); topo = []
    while q:
        n = q.popleft(); topo.append(n)
        for w in out[n]:
            gin[w] -= 1
            if gin[w] == 0: q.append(w)
    f = {n: 1 if not inn[n] else 0 for n in V}
    for n in topo:
        if inn[n]: f[n] = sum(f[u] for u in inn[n])
    b = {n: 1 if not out[n] else 0 for n in V}
    for n in reversed(topo):
        if out[n]: b[n] = sum(b[w] for w in out[n])
    spc = {(u, v): f[u] * b[v] for u, v in Ed}
    fuentes = [n for n in topo if not inn[n]]
    R["caminos_fuente_sumidero"] = sum(f[n] for n in V if not out[n])
    orden = sorted(spc, key=spc.get, reverse=True)
    R["arista_mayor_spc"] = f"{N.etiqueta[orden[0][0]]} -> {N.etiqueta[orden[0][1]]}"
    ms = (CLAVE_NODOS["Malecki 2011"], CLAVE_NODOS["Stam 2015"])
    R["rango_Malecki2011_Stam2015"] = orden.index(ms) + 1 if ms in spc else np.nan
    # búsqueda global, k = 20
    bb, bbp = {}, {}
    for n in topo:
        if not inn[n]: bb[n], bbp[n] = 0, None
        else:
            u = max(inn[n], key=lambda u: spc[(u, n)] + bb[u]); bb[n], bbp[n] = spc[(u, n)] + bb[u], u
    ff, ffp = {}, {}
    for n in reversed(topo):
        if not out[n]: ff[n], ffp[n] = 0, None
        else:
            w = max(out[n], key=lambda w: spc[(n, w)] + ff[w]); ff[n], ffp[n] = spc[(n, w)] + ff[w], w
    nodos, aristas = set(), set()
    for u, v in orden[:20]:
        p = [u, v]
        while bbp[p[0]] is not None: p.insert(0, bbp[p[0]])
        while ffp[p[-1]] is not None: p.append(ffp[p[-1]])
        nodos |= set(p); aristas |= set(zip(p[:-1], p[1:]))
    R["nodos_ruta_clave_k20"] = len(nodos)
    for k_ in ("Cohen 2006", "Malecki 2011", "Stam 2015", "Mack y Mayer 2016",
               "Theodoraki y Messeghem 2017", "Malecki 2018", "Adner 2006"):
        R[f"en_k20_{k_}"] = CLAVE_NODOS[k_] in nodos
    # tronco propio: arista Malecki 2011 -> Stam 2015 dentro de la red k = 20
    R["en_k20_arista_Malecki2011_Stam2015"] = ms in aristas
    pd.DataFrame([{"desde": N.etiqueta[u], "hacia": N.etiqueta[v], "spc": spc[(u, v)],
                   "linea_desde": N.linea[u], "linea_hacia": N.linea[v]} for u, v in aristas]
                 ).sort_values("spc", ascending=False).to_csv(f"{OUT}/senderos_k20_{nombre}.csv", index=False)
    # origen de los caminos que terminan en emprendimiento
    bE = {}
    for n in reversed(topo):
        bE[n] = (1 if N.linea[n] == "Emprendimiento" else 0) if not out[n] else sum(bE[w] for w in out[n])
    tot = sum(bE[s] for s in fuentes)
    por = pd.Series({s: bE[s] / tot for s in fuentes})
    porl = por.groupby(N.linea.reindex(por.index).fillna("otra").values).sum()
    for l_ in ("Emprendimiento", "Innovacion", "Estrategia y plataformas"):
        R[f"origen_emprendimiento_desde_{l_}"] = porl.get(l_, 0)
    for k_ in ("Adner 2006", "Malecki 2011", "Cohen 2006", "Pitelis 2012"):
        R[f"origen_emprendimiento_desde_{k_}"] = por.get(CLAVE_NODOS[k_], 0)
    # fuente principal de esos caminos
    R["fuente_principal_emprendimiento"] = N.etiqueta[por.idxmax()]

def medidas_al(keep, E, nombre):
    g = dict(zip(N.id, N.g))
    cites, citedby = defaultdict(set), defaultdict(set)
    for a, b in zip(E.desde, E.hacia): cites[a].add(b); citedby[b].add(a)
    filas = []
    for i in keep:
        br = 0
        for a in cites[i]:
            for c in citedby[i]:
                if a in cites[c]: continue
                if g[a] != g[c]: br += 1                     # portero + representante + enlace
        filas.append(dict(id=i, kin=len(citedby[i]), kout=len(cites[i]), entre_lineas=br))
    D = pd.DataFrame(filas).merge(N[["id", "anio", "g", "tipo", "al", "al_solo", "al_mixto"]], on="id")
    D = D[(D.anio >= 2013) & (D.anio <= 2025)].copy()
    D["lk"] = np.log1p(D.kout); D["br1"] = (D.entre_lineas > 0).astype(int)
    for v in ("al", "al_solo", "al_mixto"): D[v] = D[v].astype(int)
    fe = "C(anio) + C(g) + C(tipo) + lk"
    res = []
    def fit(y, x, fam, medida):
        m = smf.glm(f"{y} ~ {x} + {fe}", data=D, family=fam).fit(cov_type="HC1")
        for v in x.split(" + "):
            b, se = m.params[v], m.bse[v]
            res.append(dict(version=nombre, N=len(D), N_AL=int(D.al.sum()), medida=medida, grupo=v,
                            efecto=np.exp(b), ic95_inf=np.exp(b - 1.96 * se), ic95_sup=np.exp(b + 1.96 * se)))
    fit("kin", "al", sm.families.Poisson(), "citas recibidas (razon de tasas)")
    fit("br1", "al", sm.families.Binomial(), "alguna intermediacion entre lineas (odds ratio)")
    fit("kin", "al_solo + al_mixto", sm.families.Poisson(), "citas recibidas (razon de tasas)")
    fit("br1", "al_solo + al_mixto", sm.families.Binomial(), "alguna intermediacion entre lineas (odds ratio)")
    return res

# ------------------------------------------------------------------ ejecución
resumen, modelos = {}, []
for nombre in ("completo", "sin_duplicados", "nucleo", "articulos"):
    keep, E = version(nombre)
    R = {}
    T = medidas_red(keep, E, R)
    medidas_cocitacion(keep, R)
    medidas_senderos(T, nombre, R)
    modelos += medidas_al(keep, E, nombre)
    resumen[nombre] = R
    print(f"{nombre}: {R['documentos']} documentos, {R['vinculos']} vínculos", flush=True)

pd.DataFrame(resumen).to_csv(f"{OUT}/resumen_sensibilidad.csv")
pd.DataFrame(modelos).round(4).to_csv(f"{OUT}/modelos_al_sensibilidad.csv", index=False)
pd.set_option("display.width", 200, "display.max_rows", 200)
print(pd.DataFrame(resumen).to_string())
print(pd.DataFrame(modelos).round(2).to_string(index=False))
