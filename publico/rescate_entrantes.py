#!/usr/bin/env python3
"""
rescate_entrantes.py — Segundo criterio de pertenencia: citacion ENTRANTE.

La regla de filtro_corpus.py mira hacia atras (a quien cita el documento) y por
eso no puede admitir un texto fundacional, que es anterior a la literatura que
lo cita. Este script mira hacia adelante: un documento pertenece si el nucleo
lo cita. Resuelve los casos tipo Adner (2006), invisible para la primera regla
porque Scopus no entrega su lista de referencias.

Indexa las referencias de los registros del nucleo por (primer apellido, anio) y
verifica la coincidencia por solapamiento de palabras del titulo, lo que evita
las colisiones de apellidos frecuentes.

Uso:  python3 rescate_entrantes.py export_scopus.csv nucleo.csv ./salida
"""
import sys, re, unicodedata, pandas as pd
from collections import defaultdict, Counter

UMBRAL = 5   # citas entrantes minimas desde el nucleo
STOP = set("the a an of and or in on for to with from as by at is are be new into".split())

def norm(s):
    return unicodedata.normalize("NFKD", str(s).lower()).encode("ascii","ignore").decode("ascii")

def toks(s):
    return {w for w in re.findall(r"[a-z]{4,}", s) if w not in STOP}

def partir_referencias(s):
    """Las referencias de Scopus terminan en (AAAA); se parte por ese patron."""
    partes = re.split(r"\((\d{4})\)\s*;\s*", s)
    it = iter(partes); prev = next(it, None); out = []
    for y in it:
        if re.fullmatch(r"\d{4}", y):
            out.append((prev, y)); prev = next(it, "")
        else:
            prev = y
    return out

def main(export, nucleo_csv, out):
    eids = set(pd.read_csv(nucleo_csv, usecols=["EID"], dtype=str)["EID"])
    idx = defaultdict(Counter)
    for ch in pd.read_csv(export, usecols=["EID","References"], dtype=str, chunksize=2000):
        for eid, rf in zip(ch.EID, ch.References):
            if eid not in eids or not isinstance(rf, str): continue
            vistos = set()
            for txt, yr in partir_referencias(norm(rf)):
                mm = re.match(r"\s*([a-z][a-z'\-]{2,})", txt)
                if not mm: continue
                k = (mm.group(1), yr); tk = frozenset(toks(txt))
                if (k, tk) in vistos: continue
                vistos.add((k, tk)); idx[k][tk] += 1

    df = pd.read_csv(export, dtype=str)
    def puntaje(r):
        a = norm(r["Authors"]) if isinstance(r["Authors"], str) else ""
        mm = re.match(r"\s*([a-z][a-z'\-]{2,})", a); y = str(r["Year"])[:4]
        if not mm or not re.fullmatch(r"\d{4}", y): return 0
        c = idx.get((mm.group(1), y))
        if not c: return 0
        tt = toks(norm(r["Title"]) if isinstance(r["Title"], str) else "")
        if len(tt) < 2: return 0
        return sum(n for tk, n in c.items()
                   if len(tt & tk) >= 3 or (len(tt & tk) >= 2 and len(tt & tk) >= 0.6*len(tt)))
    df["citas_entrantes"] = df.apply(puntaje, axis=1)
    resc = df[(~df.EID.isin(eids)) & (df.citas_entrantes >= UMBRAL)].sort_values(
        "citas_entrantes", ascending=False)
    import os; os.makedirs(out, exist_ok=True)
    resc.to_csv(f"{out}/rescate_por_citacion_entrante.csv", index=False)
    print("rescatados:", len(resc))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "./salida")
