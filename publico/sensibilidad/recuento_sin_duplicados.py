#!/usr/bin/env python3
"""
recuento_sin_duplicados.py — Recalcula las cifras descriptivas que cita el
artículo, sobre el corpus completo (5.274) y sin los 12 duplicados (5.262).

La primera columna sirve de control: debe reproducir las cifras ya publicadas
en el borrador. La segunda da las cifras definitivas. Se conserva la partición
original en comunidades; las citas a un duplicado quitado pasan al registro
conservado.

Uso, desde la carpeta corpus_depurado:  python3 sensibilidad/recuento_sin_duplicados.py
Salidas: sensibilidad/recuento_sin_duplicados.csv y sensibilidad/tabla3_sin_duplicados.csv
"""
import re, warnings
from collections import defaultdict
import numpy as np, pandas as pd
import statsmodels.formula.api as smf, statsmodels.api as sm
warnings.filterwarnings("ignore")

LINEAS = ["Emprendimiento", "Estrategia y plataformas", "Innovacion", "Servicio", "Digital y datos"]
PAISES_AL = {"Argentina", "Bolivia", "Brazil", "Chile", "Colombia", "Costa Rica", "Cuba",
             "Dominican Republic", "Ecuador", "El Salvador", "Guatemala", "Honduras", "Mexico",
             "Nicaragua", "Panama", "Paraguay", "Peru", "Puerto Rico", "Uruguay", "Venezuela"}

N = pd.read_csv("red_nodos.csv").sort_values("id").reset_index(drop=True)
A = pd.read_csv("red_aristas.csv").drop_duplicates()
L = pd.read_csv("citacion_cruzada/lineas_por_documento.csv")
M = pd.read_csv("metadatos_corpus.csv", dtype=str)
CB = pd.read_csv("corpus_bibliometrix.csv", dtype=str,
                 usecols=["EID", "Title", "Year", "Affiliations", "Language of Original Document"])
assert (CB.EID.values == N.EID.values).all()
if "titulo" not in N.columns:   # el red_nodos.csv compartido no trae titulos
    N["titulo"] = CB.Title.values
N = N.merge(L[["EID", "linea_comunidad", "linea_titulo"]], on="EID", how="left")
N = N.merge(M[["EID", "capa"]], on="EID", how="left").sort_values("id").reset_index(drop=True)
N["linea"] = N.linea_comunidad.where(N.linea_comunidad.isin(LINEAS))
N["g"] = N.linea_comunidad.fillna("otra o aislado")
N["idioma"] = CB["Language of Original Document"].values
P = CB.Affiliations.map(lambda s: {a.split(",")[-1].strip() for a in s.split(";") if a.strip()}
                        if isinstance(s, str) else set())
N["paises"] = P.values
N["al"] = P.map(lambda p: bool(p & PAISES_AL)).values
N["al_mixto"] = P.map(lambda p: bool(p & PAISES_AL) and bool(p - PAISES_AL)).values
N["al_solo"] = N.al & ~N.al_mixto
CB["kdup"] = [re.sub("[^a-z]", "", str(t).lower()) + "|" + str(y) for t, y in zip(CB.Title, CB.Year)]
primero = CB.groupby("kdup").cumcount() == 0
cons = {k: i for i, k in zip(CB.index[primero], CB.kdup[primero])}
QUITAR = {i: cons[CB.kdup[i]] for i in CB.index[~primero]}
TITULO = {"Emprendimiento": "emprendimiento", "Innovacion": "innovacion", "Servicio": "servicio"}  # etiqueta del título

def version(nombre):
    keep = set(N.id); E = A.copy()
    if nombre == "sin_duplicados":
        E = E[~E.desde.isin(QUITAR)]
        E["hacia"] = E.hacia.map(lambda h: QUITAR.get(h, h))
        keep -= set(QUITAR)
    E = E[E.desde.isin(keep) & E.hacia.isin(keep) & (E.desde != E.hacia)].drop_duplicates()
    return sorted(keep), E.reset_index(drop=True)

def asort(df, a, b):
    t = pd.crosstab(df[a], df[b]); cats = sorted(set(t.index) | set(t.columns))
    t = t.reindex(index=cats, columns=cats, fill_value=0); e = t.values / t.values.sum()
    s = (e.sum(1) * e.sum(0)).sum()
    return (np.trace(e) - s) / (1 - s), 1 - np.trace(e)

res, tablas = {}, []
for nombre in ("completo", "sin_duplicados"):
    keep, E = version(nombre); D = N.loc[keep].copy(); R = {}
    # ---------------- corpus
    R["documentos"] = len(D); R["nucleo"] = int((D.capa == "nucleo").sum()); R["rescate"] = int((D.capa == "rescate").sum())
    for t in ("Article", "Book chapter", "Conference paper", "Review"):
        R[f"tipo_{t}"] = int((D.tipo == t).sum())
    R["tipo_otros"] = len(D) - sum(R[f"tipo_{t}"] for t in ("Article", "Book chapter", "Conference paper", "Review"))
    R["pct_articulos"] = R["tipo_Article"] / len(D)
    R["pct_ingles"] = (D.idioma == "English").mean()
    R["docs_hasta_1999"] = int((D.anio <= 1999).sum()); R["docs_2000_06"] = int(D.anio.between(2000, 2006).sum())
    R["docs_2007_13"] = int(D.anio.between(2007, 2013).sum()); R["docs_2014_19"] = int(D.anio.between(2014, 2019).sum())
    R["docs_desde_2020"] = int((D.anio >= 2020).sum()); R["pct_desde_2020"] = R["docs_desde_2020"] / len(D)
    R["docs_2027"] = int((D.anio == 2027).sum())
    n06, n25 = (D.anio == 2006).sum(), (D.anio == 2025).sum()
    R["tasa_crecimiento_2006_2025"] = (n25 / n06) ** (1 / 19) - 1
    # ---------------- red
    kin = E.groupby("hacia").size(); kout = E.groupby("desde").size()
    D["kin"] = D.id.map(kin).fillna(0).astype(int); D["kout"] = D.id.map(kout).fillna(0).astype(int)
    R["vinculos"] = len(E); R["aislados"] = int(((D.kin + D.kout) == 0).sum())
    for l_ in LINEAS: R[f"comunidad_{l_}"] = int((D.linea == l_).sum())
    R["otra_o_aislado"] = int(D.linea.isna().sum())
    for l_, pat in TITULO.items():
        s = D[D.linea == l_]; R[f"titulo_{l_}"] = (s.linea_titulo == pat).mean()
    T = E.copy(); T["y"] = N.anio.values[T.desde]; T["yc"] = N.anio.values[T.hacia]; T = T[T.y > T.yc]
    T["li"] = N.linea.values[T.desde]; T["lj"] = N.linea.values[T.hacia]
    R["vinculos_temporales"] = len(T); R["nodos_dag"] = len(set(T.desde) | set(T.hacia))
    d = T.dropna(subset=["li", "lj"])
    R["citas_hasta_2013"] = int((T.y <= 2013).sum())
    r, c = asort(d[d.y <= 2013], "li", "lj"); R["asort_hasta_2013"] = r; R["cruce_hasta_2013"] = c
    r, c = asort(d[d.y.between(2014, 2019)], "li", "lj"); R["asort_2014_19"] = r; R["cruce_2014_19"] = c
    for y in range(2014, 2027):
        R[f"asort_{y}"] = asort(d[d.y == y], "li", "lj")[0]; R[f"citas_{y}"] = int((d.y == y).sum())
    R["citas_internas_media_AL"] = D[D.al].kin.mean(); R["citas_internas_media_resto"] = D[~D.al].kin.mean()
    rk = D.sort_values("kin", ascending=False).reset_index(drop=True)
    R["puesto_Gomes_2018"] = int(rk.index[rk.titulo.str.contains("Unpacking the innovation ecosystem construct", case=False, na=False)][0] + 1)
    # ---------------- América Latina
    R["docs_AL"] = int(D.al.sum()); R["pct_AL"] = D.al.mean(); R["AL_mixtos"] = int(D.al_mixto.sum())
    R["AL_primer_anio"] = int(D[D.al].anio.min())
    for a, b, et in ((0, 2013, "hasta_2013"), (2014, 2019, "2014_19"), (2020, 2030, "2020_26")):
        s = D[D.anio.between(a, b)]; R[f"pct_AL_{et}"] = s.al.mean(); R[f"docs_AL_{et}"] = int(s.al.sum())
    for p_ in ("Brazil", "Mexico", "Chile", "Colombia", "Argentina", "Ecuador", "Peru", "Costa Rica"):
        R[f"pais_{p_}"] = int(D.paises.map(lambda x: p_ in x).sum())
    R["paises_AL_distintos"] = len(set().union(*D.paises) & PAISES_AL)
    for l_ in LINEAS[:4]: R[f"pct_AL_en_{l_}"] = D[D.linea == l_].al.mean()
    # intermediación y modelos
    g = dict(zip(N.id, N.g)); al = dict(zip(N.id, N.al))
    cites, citedby = defaultdict(set), defaultdict(set)
    for a, b in zip(E.desde, E.hacia): cites[a].add(b); citedby[b].add(a)
    f = []
    for i in keep:
        br = sum(1 for a in cites[i] for c in citedby[i] if a not in cites[c] and g[a] != g[c])
        f.append(dict(id=i, entre_lineas=br, in_cross=sum(g[x] != g[i] for x in citedby[i]),
                      out_cross=sum(g[x] != g[i] for x in cites[i]), n_lineas=len({g[x] for x in cites[i]}),
                      in_from_al=sum(al[x] for x in citedby[i])))
    D = D.merge(pd.DataFrame(f), on="id")
    R["pct_citas_AL_desde_AL"] = D[D.al].in_from_al.sum() / D[D.al].kin.sum()
    R["peso_AL_entre_los_que_citan"] = D[(D.kout > 0) & (D.anio >= 2014)].al.mean()
    S = D[D.anio.between(2013, 2025)].copy()
    S["lk"] = np.log1p(S.kout); S["br1"] = (S.entre_lineas > 0).astype(int)
    S["c1"] = (S.kin > 0).astype(int); S["cx1"] = (S.in_cross > 0).astype(int)
    for v in ("al", "al_solo", "al_mixto"): S[v] = S[v].astype(int)
    R["N_modelos"] = len(S); R["N_AL"] = int(S.al.sum()); R["N_AL_solo"] = int(S.al_solo.sum()); R["N_AL_mixto"] = int(S.al_mixto.sum())
    R["pct_citado_AL"] = S[S.al == 1].c1.mean(); R["pct_citado_resto"] = S[S.al == 0].c1.mean()
    R["pct_citado_otra_linea_AL"] = S[S.al == 1].cx1.mean(); R["pct_citado_otra_linea_resto"] = S[S.al == 0].cx1.mean()
    fe = "C(anio) + C(g) + C(tipo)"
    def fit(y, x, fam, medida, lk=True, data=None, w=None):
        dat = S if data is None else data
        frm = f"{y} ~ {x} + {fe}" + (" + lk" if lk else "")
        m = smf.glm(frm, data=dat, family=fam, var_weights=w).fit(cov_type="HC1")
        for v in x.split(" + "):
            b, se = m.params[v], m.bse[v]
            tablas.append(dict(version=nombre, medida=medida, grupo=v, efecto=np.exp(b),
                               ic95_inf=np.exp(b - 1.96 * se), ic95_sup=np.exp(b + 1.96 * se), p=m.pvalues[v]))
    Po, Bi = sm.families.Poisson(), sm.families.Binomial()
    for x in ("al", "al_solo + al_mixto"):
        fit("kin", x, Po, "citas recibidas (RT)")
        fit("in_cross", x, Po, "citas desde otra linea (RT)")
        fit("br1", x, Bi, "alguna intermediacion entre lineas (OR)")
        fit("entre_lineas", x, Po, "volumen de intermediacion (RT)")
    fit("c1", "al", Bi, "recibe alguna cita (OR)")
    fit("kout", "al", Po, "referencias internas (RT)", lk=False)
    fit("n_lineas", "al", Po, "lineas citadas (RT)")
    Sx = S[S.kout > 0].copy(); Sx["prop"] = Sx.out_cross / Sx.kout
    # proporción ya normalizada por el número de referencias: sin control lk; el peso es el número de
    # referencias (var_weights), de modo que el error estándar robusto se calcula por documento
    fit("prop", "al", Bi, "referencias a otra linea (OR)", lk=False, data=Sx, w=Sx.kout)
    res[nombre] = R
    print(nombre, "listo", flush=True)

out = pd.DataFrame(res); out["cambia"] = out.completo.astype(str) != out.sin_duplicados.astype(str)
out.to_csv("sensibilidad/recuento_sin_duplicados.csv")
tb = pd.DataFrame(tablas); tb.to_csv("sensibilidad/tabla3_sin_duplicados.csv", index=False)
pd.set_option("display.width", 220, "display.max_rows", 300)
print(out.to_string())
print(tb.round(3).to_string(index=False))
