#!/usr/bin/env python3
"""
construir_red.py — Paso 3: red interna de citación del corpus.

Empareja cada referencia de cada documento con los documentos del corpus por
primer apellido, año y palabras del título, y escribe la red de citación
directa entre documentos del corpus.

Regla de emparejamiento (la misma del análisis original):
  - clave del documento: primer apellido del primer autor (normalizado, sin
    tildes) y año de publicación;
  - una referencia se separa en (texto, año) a partir de los "(AAAA)" de Scopus;
  - entre los documentos con la misma clave se elige el que comparte más
    palabras de título (palabras de 4 o más letras, sin palabras vacías), con
    al menos 3 palabras en común, o 2 si cubren el 60% de las palabras del
    título del candidato; se excluyen las autocitas del propio registro.

Entrada:  corpus_bibliometrix.csv (no se redistribuye; ver README, sección 1)
Salidas:  red_nodos.csv   id, EID, etiqueta, anio, DOI, tipo, citas_globales,
                          citas_internas, n_autores
          red_aristas.csv desde (documento que cita), hacia (documento citado)

Uso, desde la raíz del repositorio:
    python3 construir_red.py [corpus_bibliometrix.csv]

Recuperado del espacio de trabajo de la sesión de análisis (red.py, 28 sept
2026) y adaptado para leer y escribir en la raíz del repositorio.
"""
import re, sys, time, unicodedata, warnings
from collections import defaultdict
import pandas as pd

warnings.filterwarnings("ignore")
t0 = time.time()
CORPUS = sys.argv[1] if len(sys.argv) > 1 else "corpus_bibliometrix.csv"
df = pd.read_csv(CORPUS, dtype=str).reset_index(drop=True)


def norm(s):
    return unicodedata.normalize("NFKD", str(s).lower()).encode("ascii", "ignore").decode("ascii")


STOP = set("the a an of and or in on for to with from as by at is are be new into its their".split())


def toks(s):
    return {w for w in re.findall(r"[a-z]{4,}", s) if w not in STOP}


# --- índice de los documentos del corpus: (apellido, año) -> [(fila, palabras del título)]
idx = defaultdict(list)
for i, (au, yr, ti) in enumerate(zip(df["Authors"].fillna(""), df["Year"].fillna(""), df["Title"].fillna(""))):
    m = re.match(r"\s*([A-Za-zÀ-ÿ'\-]{3,})", str(au))
    y = str(yr)[:4]
    if not m or not re.fullmatch(r"\d{4}", y):
        continue
    idx[(norm(m.group(1)), y)].append((i, toks(norm(ti))))
print("claves de documento:", len(idx))


def partir(s):
    """Separa la cadena de referencias de Scopus en pares (texto, año)."""
    partes = re.split(r"\((\d{4})\)\s*;\s*", s)
    it = iter(partes); prev = next(it, None); out = []
    for y in it:
        if re.fullmatch(r"\d{4}", y):
            out.append((prev, y)); prev = next(it, "")
        else:
            prev = y
    if prev:
        m = re.search(r"\((\d{4})\)\s*$", prev)
        if m:
            out.append((prev[:m.start()], m.group(1)))
    return out


aristas = []; nref_tot = 0; sin_match = 0
for i, raw in enumerate(df["References"].fillna("")):
    if not raw:
        continue
    for txt, yr in partir(norm(raw)):
        nref_tot += 1
        m = re.match(r"\s*([a-z][a-z'\-]{2,})", txt)
        if not m:
            continue
        cand = idx.get((m.group(1), yr))
        if not cand:
            sin_match += 1; continue
        tt = toks(txt); mejor = None; mejor_n = 0
        for j, tj in cand:
            if j == i or not tj:
                continue
            inter = len(tt & tj)
            if inter > mejor_n and (inter >= 3 or (inter >= 2 and inter >= 0.6 * len(tj))):
                mejor, mejor_n = j, inter
        if mejor is not None:
            aristas.append((i, mejor))

E = pd.DataFrame(aristas, columns=["desde", "hacia"]).drop_duplicates()
print(f"referencias procesadas: {nref_tot:,}; aristas internas únicas: {len(E):,}")

# --- tabla de nodos
autores = df["Authors"].fillna("")
primer = autores.map(lambda s: s.split(";")[0].strip() or "NA")   # 5 registros sin autor
anio = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
kin = E.groupby("hacia").size()
N = pd.DataFrame({
    "id": range(len(df)),
    "EID": df["EID"],
    "etiqueta": [f"{a}, {y}" for a, y in zip(primer, anio)],
    "anio": anio,
    "DOI": df["DOI"],
    "tipo": df["Document Type"],
    "citas_globales": pd.to_numeric(df["Cited by"], errors="coerce").fillna(0).astype(int),
    "citas_internas": pd.Series(range(len(df))).map(kin).fillna(0).astype(int),
    "n_autores": autores.map(lambda s: len([x for x in s.split(";") if x.strip()])),
})
N.to_csv("red_nodos.csv", index=False)
E.to_csv("red_aristas.csv", index=False)   # orden de lectura: documento que cita, luego sus referencias
print(f"red_nodos.csv: {len(N):,} documentos; red_aristas.csv: {len(E):,} aristas; {time.time() - t0:.0f} s")
