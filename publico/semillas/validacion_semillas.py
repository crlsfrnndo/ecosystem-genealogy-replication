#!/usr/bin/env python3
"""
validacion_semillas.py — Respaldo empírico de las líneas y los autores semilla.

Tres comprobaciones sobre el export completo de Scopus (19.419 registros):

1. Rango de cada autor semilla. Para cada línea se toman los registros cuyo
   título nombra ese tipo de ecosistema (p. ej., "entrepreneurial ecosystem")
   y se ordenan los primeros autores de sus referencias por el número de
   registros que los citan. Se informa el puesto de cada semilla y su obra más
   citada en ese subconjunto.
2. Quitar una semilla a la vez (y una línea entera): cuántos registros del
   núcleo dejarían de cumplir la regla de dos semillas de una misma línea.
3. Cobertura: qué parte de los registros con un tipo de ecosistema en el
   título entra al núcleo, y cuántos títulos ecológicos entran.
4. Umbrales alternativos de la regla (una semilla, dos de cualquier línea,
   dos de una misma línea, tres de una misma línea).
El léxico ecológico estricto usa límites de palabra y omite términos que
producen coincidencias espurias en títulos organizacionales ("driver" contiene
"river"; "research streams").

Uso:  python3 semillas/validacion_semillas.py export_scopus.csv
Salidas en semillas/: rango_semillas.csv, quitar_semillas.csv, cobertura_regla.csv, umbrales_regla.csv
"""
import re, sys, unicodedata
from collections import Counter, defaultdict
import pandas as pd

sys.path.insert(0, ".")
from filtro_corpus import LINEAS, BIO_TITLE, ORG_TITLE, norm   # mismas semillas y léxicos

EXPORT = sys.argv[1]
OUT = "semillas"
TIPO_TITULO = {"negocios": r"business ecosyst", "innovacion": r"innovation ecosyst",
               "emprendimiento": r"entrepreneur\w* ecosyst", "plataforma": r"platform\w*[- ]?(based )?ecosyst",
               "servicio": r"service ecosyst", "software": r"software ecosyst",
               "conocimiento": r"knowledge ecosyst|knowledge-based ecosyst"}
NOMBRE = {  # apellido normalizado tal como aparece al inicio de la referencia
 "negocios": ["moore", "iansiti", "levien", "teece"],
 "innovacion": ["adner", "kapoor", "autio", "granstrand", "ritala", "oh"],
 "emprendimiento": ["isenberg", "spigel", "stam", "acs", "mason", "roundy", "audretsch", "malecki"],
 "plataforma": ["gawer", "cusumano", "parker", "van alstyne", "tiwana", "eisenmann", "jacobides", "boudreau"],
 "servicio": ["vargo", "lusch", "akaka", "chandler", "frow"],
 "software": ["bosch", "jansen", "messerschmitt", "manikas", "lungu"],
 "conocimiento": ["carayannis", "etzkowitz", "leydesdorff", "clarysse", "van de vrande"]}

def partir(s):
    partes = re.split(r"\((\d{4})\)\s*;\s*", s)
    it = iter(partes); prev = next(it, None); out = []
    for y in it:
        if re.fullmatch(r"\d{4}", y): out.append((prev, y)); prev = next(it, "")
        else: prev = y
    if prev:
        m = re.search(r"\((\d{4})\)\s*$", prev)
        if m: out.append((prev[:m.start()], m.group(1)))
    return out

def primer_autor(txt):
    t = txt.strip()
    m = re.match(r"((?:van der |van de |van |de la |de |von )?[a-z'\-]+)", t)
    return m.group(1) if m else None

def obra(txt, yr):
    segs = [s.strip() for s in txt.split(",")]
    tit = next((s for s in segs[1:] if len(s.split()) >= 3 and not re.match(r"^[a-z'\- ]+ ([a-z]\.-?)+$", s)), "")
    return f"{yr} {' '.join(tit.split()[:6])}"

df = pd.read_csv(EXPORT, dtype=str, usecols=["EID", "Title", "References"])
refs = df.References.fillna("").map(norm)
tit = df.Title.fillna("").map(norm)

# 1. rango de las semillas en los registros que nombran cada tipo en el título
filas = []
for linea, pat in TIPO_TITULO.items():
    sub = tit.str.contains(pat, regex=True)
    cnt, obras = Counter(), defaultdict(Counter)
    for r in refs[sub]:
        vistos, vistas = set(), set()
        for txt, yr in partir(r):
            a = primer_autor(txt)
            if not a: continue
            if a not in vistos: cnt[a] += 1; vistos.add(a)
            o = obra(txt, yr)
            if (a, o) not in vistas: obras[a][o] += 1; vistas.add((a, o))
    orden = [a for a, _ in cnt.most_common()]
    n = int(sub.sum())
    for s in NOMBRE[linea]:
        pos = orden.index(s) + 1 if s in cnt else None
        top = obras[s].most_common(1)[0] if obras[s] else ("", 0)
        filas.append(dict(linea=linea, registros_con_el_tipo_en_titulo=n, semilla=s,
                          puesto_primer_autor=pos, registros_que_lo_citan=cnt.get(s, 0),
                          pct_registros=round(cnt.get(s, 0) / n * 100, 1) if n else None,
                          obra_mas_citada=top[0], citas_obra=top[1]))
    filas.append(dict(linea=linea, registros_con_el_tipo_en_titulo=n, semilla="(10 primeros)",
                      obra_mas_citada="; ".join(f"{a} {c}" for a, c in cnt.most_common(10))))
R = pd.DataFrame(filas); R.to_csv(f"{OUT}/rango_semillas.csv", index=False)

# 2. quitar una semilla a la vez
pats = {k: [re.compile(p) for p in v] for k, v in LINEAS.items()}
M = {k: pd.DataFrame({i: [bool(p.search(r)) for r in refs] for i, p in enumerate(ps)}) for k, ps in pats.items()}
cuenta = {k: m.sum(axis=1) for k, m in M.items()}
nucleo = pd.concat(cuenta, axis=1).max(axis=1) >= 2
filas = []
for k, m in M.items():
    otras = pd.concat({j: c for j, c in cuenta.items() if j != k}, axis=1).max(axis=1)
    for i, nombre in enumerate(NOMBRE[k]):
        sin = (cuenta[k] - m[i]).clip(lower=0)
        quedan = (pd.concat([otras, sin], axis=1).max(axis=1) >= 2)
        filas.append(dict(linea=k, semilla=nombre, registros_que_la_citan=int(m[i].sum()),
                          salen_del_nucleo=int((nucleo & ~quedan).sum())))
    quedan = otras >= 2
    filas.append(dict(linea=k, semilla="(línea entera)", registros_que_la_citan=int((cuenta[k] > 0).sum()),
                      salen_del_nucleo=int((nucleo & ~quedan).sum())))
Q = pd.DataFrame(filas); Q["pct_del_nucleo"] = (Q.salen_del_nucleo / nucleo.sum() * 100).round(2)
Q.to_csv(f"{OUT}/quitar_semillas.csv", index=False)

# 3. cobertura de la regla
org = tit.str.contains(ORG_TITLE, regex=True); bio = tit.str.contains(BIO_TITLE, regex=True)
tiene = refs.str.len() > 0
C = pd.DataFrame([
    dict(grupo="título con un tipo de ecosistema organizacional", registros=int(org.sum()),
         con_referencias=int((org & tiene).sum()), en_nucleo=int((org & nucleo).sum())),
    dict(grupo="título ecológico", registros=int(bio.sum()), con_referencias=int((bio & tiene).sum()),
         en_nucleo=int((bio & nucleo).sum())),
    dict(grupo="todo el export", registros=len(df), con_referencias=int(tiene.sum()), en_nucleo=int(nucleo.sum()))])
C.to_csv(f"{OUT}/cobertura_regla.csv", index=False)

# 4. umbrales alternativos, con léxico ecológico estricto
ESPURIOS = ("stream", "river", "desert", "arid", "habitat", "fauna", "flora")
BIO_ESTRICTO = r"\b(?:" + "|".join(t for t in BIO_TITLE.split("|") if t not in ESPURIOS) + r")"
bio2 = tit.str.contains(BIO_ESTRICTO, regex=True)
total = pd.concat(cuenta, axis=1).sum(axis=1); maximo = pd.concat(cuenta, axis=1).max(axis=1)
U = pd.DataFrame([dict(regla=n_, registros=int(r_.sum()),
                       pct_titulos_org_con_refs=round((r_ & org).sum() / (org & tiene).sum() * 100, 1),
                       titulos_ecologicos_estricto=int((r_ & bio2).sum()))
                  for n_, r_ in [("al menos 1 semilla", total >= 1), ("al menos 2, de cualquier línea", total >= 2),
                                 ("al menos 2 de una misma línea (regla)", maximo >= 2),
                                 ("al menos 3 de una misma línea", maximo >= 3)]])
U.to_csv(f"{OUT}/umbrales_regla.csv", index=False)
print(U.to_string(index=False))
pd.set_option("display.width", 250, "display.max_colwidth", 120, "display.max_rows", 200)
print(R.to_string(index=False)); print(Q.to_string(index=False)); print(C.to_string(index=False))

# 5. obra más citada de cada autor semilla (en cualquier posición de autoría),
#    en los registros con un tipo de ecosistema organizacional en el título
pats_aut = {(k, NOMBRE[k][i]): p for k, ps in pats.items() for i, p in enumerate(ps)}
obras_aut = defaultdict(Counter)
for r in refs[org]:
    vistas = set()
    for txt, yr in partir(r):
        a = primer_autor(txt) or "?"
        clave = f"{a} {obra(txt, yr)}"
        for kk, p in pats_aut.items():
            if p.search(txt) and (kk, clave) not in vistas:
                obras_aut[kk][clave] += 1; vistas.add((kk, clave))
O = pd.DataFrame([dict(linea=k, semilla=s_, obra_mas_citada=(obras_aut[(k, s_)].most_common(1) or [("", 0)])[0][0],
                       citas=(obras_aut[(k, s_)].most_common(1) or [("", 0)])[0][1]) for (k, s_) in pats_aut])
O.to_csv(f"{OUT}/obras_semillas.csv", index=False)
print(O.to_string(index=False))

# 6. porcentaje de los registros que nombran cada tipo en el título (con referencias)
#    que cita a cada autor semilla de su línea, en cualquier posición de autoría
filas = []
for k, pat in TIPO_TITULO.items():
    sub = tit.str.contains(pat, regex=True) & tiene
    m = M[k][sub.values]
    for i, s_ in enumerate(NOMBRE[k]):
        filas.append(dict(linea=k, registros_tipo_con_refs=int(sub.sum()), semilla=s_, pct_lo_cita=round(m[i].mean() * 100, 1)))
    filas.append(dict(linea=k, registros_tipo_con_refs=int(sub.sum()), semilla="(al menos una semilla)",
                      pct_lo_cita=round(m.any(axis=1).mean() * 100, 1)))
P = pd.DataFrame(filas); P.to_csv(f"{OUT}/cobertura_por_semilla.csv", index=False)
print(P.to_string(index=False))
