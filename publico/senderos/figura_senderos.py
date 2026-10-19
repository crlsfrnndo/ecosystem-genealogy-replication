#!/usr/bin/env python3
"""
figura_senderos.py — Figura 4: red de senderos de ruta clave (20 rutas,
búsqueda global).

Dibuja los documentos y las aristas de la red de ruta clave que calcula
senderos/rutas_clave.R. Cada punto es un documento, el color es su comunidad
de citación y el grosor de la flecha crece con la raíz cuadrada del SPC.
Las posiciones verticales están fijadas a mano por documento (id de
red_nodos.csv) para que las etiquetas no se superpongan.

Entradas: senderos/rutas_clave_aristas.csv, senderos/rutas_clave_nodos.csv
Salida:   senderos/senderos_ruta_clave.png

No requiere el corpus de Scopus. Uso, desde la raíz del repositorio y después
de correr senderos/rutas_clave.R:
    python3 senderos/figura_senderos.py

Recuperado del espacio de trabajo de la sesión de análisis (fig_kr.py, 6 oct
2026) y adaptado para leer las tablas del repositorio en lugar del archivo
temporal de la sesión.
"""
import math
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
from matplotlib.lines import Line2D

AR = pd.read_csv("senderos/rutas_clave_aristas.csv")
ND = pd.read_csv("senderos/rutas_clave_nodos.csv")
AR = AR[(AR.modo == "global") & (AR.k == 20)]
en = {(int(u), int(v)) for u, v in zip(AR.desde_id, AR.hacia_id)}
spc = {(int(u), int(v)): s for u, v, s in zip(AR.desde_id, AR.hacia_id, AR.spc)}
nn = {x for e in en for x in e}
anio = dict(zip(ND.id, ND.anio)); com = dict(zip(ND.id, ND.comunidad)); lab = dict(zip(ND.id, ND.etiqueta))

COL = {"Estrategia y plataformas": "#2a78d6", "Emprendimiento": "#eb6834", "Innovacion": "#1baf7a", "Servicio": "#8a8a85"}
INK, MUTED, GRID, SURF = "#1f1f1d", "#5f5f5a", "#e6e6e2", "#fcfcfb"
# id del documento: (posición vertical, etiqueta 'a' arriba, 'b' abajo o 'r' a la derecha)
Y = {39: (8.7, 'a'), 49: (7.6, 'b'), 90: (9.5, 'a'), 160: (8.2, 'b'), 123: (7.0, 'b'), 244: (8.2, 'a'), 320: (6.4, 'a'),
     538: (6.9, 'b'), 465: (8.8, 'a'), 704: (7.7, 'b'), 1020: (7.7, 'a'), 1282: (7.7, 'b'),
     9: (5.2, 'b'), 19: (5.6, 'a'), 78: (4.6, 'a'), 88: (4.6, 'b'), 204: (4.6, 'a'), 65: (3.9, 'b'),
     8: (0.5, 'b'), 67: (2.0, 'b'), 268: (2.0, 'b'), 390: (2.8, 'a'), 409: (0.5, 'b'), 482: (0.5, 'a'), 494: (3.3, 'a'),
     498: (2.0, 'b'), 682: (2.0, 'a'), 1103: (2.0, 'b'), 1579: (2.0, 'a'),
     2209: (3.3, 'a'), 2099: (2.0, 'b'), 3040: (2.7, 'r'), 3457: (2.0, 'b'), 3591: (3.3, 'a'), 3985: (3.3, 'b'),
     4532: (2.0, 'a'), 4786: (2.0, 'b'), 4686: (3.3, 'a')}
assert set(Y) == nn, f"documentos sin posición o sobrantes: {set(Y) ^ nn}"


def corta(x):
    return f"{lab[x].split(',')[0].split()[0]} {anio[x]}"


fix = {4532: "Bonomi Santos 2025", 65: "Hanna 2011"}
fig, ax = plt.subplots(figsize=(13.5, 7.2), dpi=200)
fig.patch.set_facecolor(SURF); ax.set_facecolor(SURF)
for yr in range(2006, 2027, 2):
    ax.axvline(yr, color=GRID, lw=0.8, zorder=0)
for y0, y1, nm in ((6.0, 10.0, "Estrategia y plataformas"), (3.6, 6.0, "Innovación"), (0.0, 3.6, "Emprendimiento")):
    ax.text(2004.35, (y0 + y1) / 2, nm, rotation=90, ha="center", va="center", fontsize=9.5, color=MUTED)
ax.axhline(6.0, color=GRID, lw=0.8, ls=(0, (3, 3))); ax.axhline(3.6, color=GRID, lw=0.8, ls=(0, (3, 3)))
mx = max(spc[e] for e in en)
for u, v in sorted(en, key=lambda e: spc[e]):
    w = 0.6 + 3.0 * math.sqrt(spc[(u, v)] / mx)
    ax.add_patch(FancyArrowPatch((anio[u], Y[u][0]), (anio[v], Y[v][0]), arrowstyle="-|>", mutation_scale=7,
                                 lw=w, color="#a3a39d", shrinkA=6, shrinkB=6, zorder=1,
                                 connectionstyle=f"arc3,rad={0.28 if (u, v) == (19, 90) else 0.0}"))
for x in nn:
    ax.scatter(anio[x], Y[x][0], s=70, color=COL[com[x]], edgecolor=SURF, linewidth=2, zorder=3)
    t = fix.get(x, corta(x)); pos = Y[x][1]
    if pos == 'r':
        ax.text(anio[x] + 0.22, Y[x][0], t, ha="left", va="center", fontsize=7.6, color=INK, zorder=4)
    else:
        up = pos == 'a'
        ax.text(anio[x], Y[x][0] + (0.28 if up else -0.28), t, ha="center", va="bottom" if up else "top",
                fontsize=7.6, color=INK, zorder=4)
ax.set_xlim(2003.8, 2026.9); ax.set_ylim(-0.3, 10.2)
ax.set_xticks(range(2006, 2027, 2)); ax.tick_params(axis="x", colors=MUTED, labelsize=9, length=0)
ax.set_yticks([])
for s in ax.spines.values():
    s.set_visible(False)
ax.set_title("Senderos de ruta clave: 20 rutas, búsqueda global", loc="left", fontsize=13, color=INK, pad=26)
ax.text(0, 1.035, "Cada punto es un documento del corpus; el color indica su comunidad de citación y el grosor de la "
        "flecha, el conteo de búsqueda (SPC).", transform=ax.transAxes, fontsize=9, color=MUTED)
h = [Line2D([], [], marker="o", ls="", markersize=7, markerfacecolor=c, markeredgecolor=SURF, label=n)
     for n, c in (("Estrategia y plataformas", COL["Estrategia y plataformas"]), ("Innovación", COL["Innovacion"]),
                  ("Emprendimiento", COL["Emprendimiento"]), ("Servicio", COL["Servicio"]))]
ax.legend(handles=h, loc="lower right", frameon=False, fontsize=8.5, labelcolor=INK, ncol=4, bbox_to_anchor=(1.0, -0.12))
plt.tight_layout(); plt.savefig("senderos/senderos_ruta_clave.png", facecolor=SURF)
print("escrito senderos/senderos_ruta_clave.png")
