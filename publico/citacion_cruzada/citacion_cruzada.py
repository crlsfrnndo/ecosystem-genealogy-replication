#!/usr/bin/env python3
"""
citacion_cruzada.py — Paso 10: aislamiento entre líneas y artículos integradores.

Aplica la regla de duplicados (título normalizado más año; se conserva el primer
registro y las citas del quitado pasan al conservado), de modo que las cifras
corresponden al corpus del artículo (5.262 documentos, 50.273 citas con año
creciente). La lista de los 12 registros está en duplicados_quitados.csv.

Usa solo las citas con año estrictamente creciente (el documento que cita es
posterior al citado), la misma regla del sendero principal.

  - Asortatividad nominal (Newman, 2003) por periodo y por año, con las líneas
    definidas por la comunidad de citación y, como control, por el término
    del título; versión con todas las citas y versión sin las citas a
    documentos de autores semilla.
  - Matriz de quién cita a quién (porcentaje de las citas de cada línea).
  - Procedencia de las citas que reciben los artículos integradores.
  - Figura de la serie anual.

Entradas: red_nodos.csv, red_aristas.csv, duplicados_quitados.csv,
          citacion_cruzada/lineas_por_documento.csv
Salidas:  citacion_cruzada/asortatividad_por_periodo.csv
          citacion_cruzada/asortatividad_por_anio.csv
          citacion_cruzada/quien_cita_a_quien.csv
          citacion_cruzada/trafico_articulos_integradores.csv
          citacion_cruzada/asortatividad_anual.png

No requiere el corpus de Scopus. Uso, desde la raíz del repositorio:
    python3 citacion_cruzada/citacion_cruzada.py

Recuperado del espacio de trabajo de la sesión de análisis (cruz3.py,
cruz4.py y graf.py, 6 oct 2026) y adaptado para leer los archivos del
repositorio. Los artículos integradores se identifican por EID porque
red_nodos.csv no trae títulos.
"""
import warnings
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")
LINEAS = ["Emprendimiento", "Estrategia y plataformas", "Innovacion", "Servicio", "Digital y datos"]

N = pd.read_csv("red_nodos.csv").sort_values("id").reset_index(drop=True)
A = pd.read_csv("red_aristas.csv")
D = pd.read_csv("duplicados_quitados.csv")                                # 12 duplicados (EID quitado -> EID conservado)
_id = dict(zip(N.EID, N.id))
quitar = {_id[a]: _id[b] for a, b in zip(D.EID_quitado, D.EID_conservado)}
A = A[~A.desde.isin(quitar)].copy()                                      # el duplicado no cita
A["hacia"] = A.hacia.map(lambda h: quitar.get(h, h))                     # las citas a un duplicado pasan al conservado
A = A[A.desde != A.hacia].drop_duplicates().reset_index(drop=True)
L = pd.read_csv("citacion_cruzada/lineas_por_documento.csv")
assert (L.EID.values == N.EID.values).all()
linea = L.linea_comunidad.where(L.linea_comunidad.isin(LINEAS)).values   # "otra o aislado" -> sin línea
titulo = L.linea_titulo.values
semilla = L.autor_semilla.astype(bool).values
anio = N.anio.values

E = A.copy()
E["y"] = anio[E.desde]; E["y_c"] = anio[E.hacia]
E["li"] = linea[E.desde]; E["lj"] = linea[E.hacia]
E["ti"] = titulo[E.desde]; E["tj"] = titulo[E.hacia]
E["semilla_citado"] = semilla[E.hacia]
E = E[E.y > E.y_c]                        # año estrictamente creciente
E["periodo"] = E.y.map(lambda y: "hasta 2013" if y <= 2013 else ("2014-2019" if y <= 2019 else "2020-2026"))
VERSIONES = [("todas", E), ("sin semillas", E[~E.semilla_citado])]


def asort(df, a, b):
    """Asortatividad nominal, proporción observada de citas cruzadas y proporción esperada al azar."""
    t = pd.crosstab(df[a], df[b]); cats = sorted(set(t.index) | set(t.columns))
    t = t.reindex(index=cats, columns=cats, fill_value=0); e = t.values / t.values.sum()
    s = (e.sum(1) * e.sum(0)).sum()
    return (np.trace(e) - s) / (1 - s), 1 - np.trace(e), 1 - s


# ---- asortatividad por periodo
filas = []
for version, df in VERSIONES:
    for nivel, (a, b) in [("comunidades", ("li", "lj")), ("titulo", ("ti", "tj"))]:
        d = df.dropna(subset=[a, b])
        for p in ["hasta 2013", "2014-2019", "2020-2026"]:
            s = d[d.periodo == p]; r, cross, exp = asort(s, a, b)
            filas.append(dict(version=version, nivel=nivel, periodo=p, aristas=len(s), asortatividad=round(r, 3),
                              cruce_observado=round(cross, 3), cruce_azar=round(exp, 3)))
R = pd.DataFrame(filas); R.to_csv("citacion_cruzada/asortatividad_por_periodo.csv", index=False)
print(R.to_string(index=False))

# ---- serie anual (año del documento que cita)
filas = []
for y in range(2014, 2027):
    s = E[E.y == y]; dc = s.dropna(subset=["li", "lj"]); dcs = dc[~dc.semilla_citado]
    filas.append(dict(anio=y, aristas=len(dc), comunidades=round(asort(dc, "li", "lj")[0], 3),
                      comunidades_sin_semillas=round(asort(dcs, "li", "lj")[0], 3) if len(dcs) >= 100 else np.nan,
                      titulo=round(asort(s, "ti", "tj")[0], 3)))
S = pd.DataFrame(filas); S.to_csv("citacion_cruzada/asortatividad_por_anio.csv", index=False)
print(S.to_string(index=False))

# ---- quién cita a quién
filas = []
for p in ["2014-2019", "2020-2026"]:
    for version, df in VERSIONES:
        d = df[df.periodo == p].dropna(subset=["li", "lj"])
        t = pd.crosstab(d.li, d.lj).reindex(index=LINEAS, columns=LINEAS).fillna(0).astype(int)
        pct = t.div(t.sum(1).replace(0, np.nan), axis=0) * 100
        for li in LINEAS:
            for lj in LINEAS:
                filas.append(dict(periodo=p, version=version, linea_que_cita=li, linea_citada=lj,
                                  citas=int(t.loc[li, lj]), pct_de_la_fila=round(float(pct.loc[li, lj]), 1)))
pd.DataFrame(filas).to_csv("citacion_cruzada/quien_cita_a_quien.csv", index=False)

# ---- procedencia de las citas que reciben los artículos integradores
INTEGRADORES = [("Adner 2017", "2-s2.0-85004107267"), ("Jacobides 2018", "2-s2.0-85046829494"),
                ("Kapoor 2018", "2-s2.0-85064429503"), ("Granstrand 2020", "2-s2.0-85076204140"),
                ("Shipilov y Gawer 2020", "2-s2.0-85078293022")]
# Thomas y Autio (2020) no está en el corpus. Cobben et al. (2022) no se incluyó en el análisis original.
pos = {e: i for i, e in enumerate(N.EID)}
filas = []
for et, eid in INTEGRADORES:
    i = pos[eid]; propia = linea[i]
    d = E[E.hacia == i].dropna(subset=["li"])
    v = d.li.value_counts(normalize=True) * 100
    filas.append(dict(articulo=et, linea_propia=propia, citas=len(d), pct_desde_otras_lineas=round(100 - v.get(propia, 0), 1),
                      **{f"desde_{o}": round(v.get(o, 0), 1) for o in LINEAS}))
F = pd.DataFrame(filas); F.to_csv("citacion_cruzada/trafico_articulos_integradores.csv", index=False)
print(F[["articulo", "linea_propia", "citas", "pct_desde_otras_lineas"]].to_string(index=False))
d = E.dropna(subset=["li", "lj"]).assign(fuera=lambda x: x.li != x.lj)
gr = d.groupby("hacia").agg(citas=("fuera", "size"), fuera=("fuera", "mean")); gr = gr[gr.citas >= 50]
print(f"referencia: {len(gr)} documentos con 50 o más citas internas; mediana de citas desde otras líneas "
      f"{gr.fuera.median() * 100:.1f}% (p75 {gr.fuera.quantile(.75) * 100:.1f}%)")

# ---- figura de la serie anual
INK, INK2, MUTED, GRID, BG = "#0b0b0b", "#52514e", "#8a8984", "#e6e5e0", "#fcfcfb"
series = [("comunidades", "Comunidades", "#2a78d6", "Líneas = comunidades de la red de citación"),
          ("comunidades_sin_semillas", "Comunidades, sin semillas", "#eb6834", "Ídem, sin las citas a autores semilla"),
          ("titulo", "Término del título", "#1baf7a", "Líneas = término que el autor usa en el título")]
fig, ax = plt.subplots(figsize=(9.6, 5.6), dpi=200); fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
for y, lab, ha, dx in [(2017, "Adner\n2017", "right", -0.1), (2018, "Jacobides\net al. 2018", "left", 0.1),
                       (2020, "Granstrand y\nHolgersson 2020", "left", 0.1)]:
    ax.axvline(y, color=MUTED, lw=1, ls=(0, (3, 3)), zorder=1)
    ax.text(y + dx, 0.06, lab, color=INK2, fontsize=7.5, va="bottom", ha=ha)
for col, lab, c, leg in series:
    d = S.dropna(subset=[col])
    ax.plot(d.anio, d[col], color=c, lw=2, zorder=3, solid_capstyle="round", label=leg)
    ax.scatter(d.anio, d[col], s=34, color=c, edgecolor=BG, linewidth=1.5, zorder=4)
    yl = d[col].iloc[-1]; off = {"comunidades": 0.018, "comunidades_sin_semillas": -0.03, "titulo": 0}[col]
    ax.text(2026.25, yl + off, lab, color=INK, fontsize=8, va="center")
ax.axhline(0, color=INK2, lw=1, zorder=2)
ax.text(2013.75, 0.012, "0 = las líneas se citan al azar", color=INK2, fontsize=7.5, va="bottom")
ax.set_xlim(2013.6, 2029.2); ax.set_ylim(-0.02, 0.85)
ax.set_xticks(range(2014, 2027, 2)); ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8])
ax.tick_params(colors=INK2, labelsize=8.5, length=0)
ax.grid(axis="y", color=GRID, lw=0.8); ax.set_axisbelow(True)
for s_ in ax.spines.values():
    s_.set_visible(False)
ax.set_ylabel("Asortatividad (1 = cada línea solo se cita a sí misma)", color=INK2, fontsize=8.5)
fig.text(0.075, 0.955, "Las líneas se citan cada vez más a sí mismas", fontsize=13, color=INK, weight="bold")
fig.text(0.075, 0.915, "Asortatividad de la red de citación interna, por año del documento que cita. 2014–2026.",
         fontsize=9, color=INK2)
leg = ax.legend(loc="upper left", bbox_to_anchor=(0.0, 1.06), ncol=3, frameon=False, fontsize=7.8,
                handlelength=1.8, columnspacing=1.6)
for t in leg.get_texts():
    t.set_color(INK)
fig.text(0.075, 0.02, "Los puntos de 2014 a 2016 se basan en menos de 300 citas por año; desde 2018, en más de 1.100. "
         "Líneas verticales: artículos integradores.", fontsize=7.5, color=INK2)
plt.subplots_adjust(left=0.085, right=0.985, top=0.84, bottom=0.1)
plt.savefig("citacion_cruzada/asortatividad_anual.png", facecolor=BG)
print("escritos los archivos de citacion_cruzada/")
