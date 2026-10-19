#!/usr/bin/env python3
"""
filtro_corpus.py — Depuracion del corpus bibliometrico nucleo (Scopus)
Articulo: genealogia del concepto de ecosistema en estudios organizacionales.

Criterio de pertenencia: CONEXION DE CITACION, no lexico de titulo.
Un documento pertenece al corpus si cita al menos 2 obras semilla de UNA MISMA
linea. La regla es reportable, no depende de juicio y coincide con lo que las
operaciones 1, 2 y 5 necesitan (nodos conectados a la red).

Salidas:
  nucleo.csv            pertenece al corpus
  revision.csv          zona gris (1 semilla, o titulo organizacional sin semillas)
  sin_referencias.csv   Scopus no entrega lista de referencias -> revision manual obligatoria
  fuera.csv             descartados
  diagnostico.csv       tabla resumen
Uso:  python3 filtro_corpus.py export_scopus.csv ./salida
"""
import sys, re, unicodedata, pandas as pd

def norm(s):
    return unicodedata.normalize("NFKD", str(s).lower()).encode("ascii","ignore").decode("ascii")

# --- Semillas por linea. Editar aqui para replicar o ampliar. -----------------
LINEAS = {
 "negocios":       [r"moore j\.?f|moore, j", r"iansiti", r"levien", r"teece d|teece, d"],
 "innovacion":     [r"adner r|adner, r", r"kapoor r|kapoor, r", r"autio e|autio, e",
                    r"granstrand", r"ritala p|ritala, p", r"oh d|oh, d"],
 "emprendimiento": [r"isenberg", r"spigel", r"stam e|stam, e", r"acs z|acs, z",
                    r"mason c|mason, c", r"roundy", r"audretsch", r"malecki"],
 "plataforma":     [r"gawer", r"cusumano", r"parker g|parker, g", r"van alstyne",
                    r"tiwana", r"eisenmann", r"jacobides", r"boudreau k|boudreau, k"],
 "servicio":       [r"vargo", r"lusch", r"akaka", r"chandler j|chandler, j", r"frow p|frow, p"],
 "software":       [r"bosch j|bosch, j", r"jansen s|jansen, s", r"messerschmitt",
                    r"manikas", r"lungu m|lungu, m"],
 "conocimiento":   [r"carayannis", r"etzkowitz", r"leydesdorff", r"clarysse", r"van de vrande"],
}
# Semillas ecologicas. Holling y Folke NO se incluyen: son compartidas con la
# literatura de resiliencia organizacional y marcarian falsos positivos.
BIO_SEED = [r"tansley", r"odum", r"costanza", r"millennium ecosystem assessment",
            r"daily g|daily, g", r"de groot", r"tilman", r"loreau", r"chapin"]

ORG_TITLE = re.sub(r"\s*\n\s*","", r"""business ecosyst|innovation ecosyst|entrepreneur\w* ecosyst|
entrepreneurship ecosyst|platform ecosyst|platform-based ecosyst|digital ecosyst|software ecosyst|
service ecosyst|knowledge ecosyst|technology ecosyst|start-?up ecosyst|industrial ecosyst|
data ecosyst|information ecosyst|fintech ecosyst|financial ecosyst|iot ecosyst|mobile ecosyst|
value ecosyst|venture ecosyst|ecosystem strategy|ecosystems? as structure|theory of ecosystems|
ecosystem orchestrat|ecosystem governance|ecosystem business model|keystone""")
BIO_TITLE = re.sub(r"\s*\n\s*","", r"""terrestrial|freshwater|marine|mangrove|wetland|grassland|
savanna|tundra|peatland|riparian|estuar|coral|reef|seagrass|benthic|pelagic|microbial|soil|
rhizosphere|forest|woodland|rangeland|pasture|agroecosystem|agro-ecosystem|lake|river|stream|
watershed|catchment|lagoon|coastal|ocean|alpine|montane|desert|arid|karst|permafrost|glacier|
boreal|rainforest|biodivers|species richness|trophic|food web|carbon sequestr|nutrient cycl|
primary productiv|habitat|fauna|flora|vegetation|biomass|fisher|wildlife|pollinat|
invasive species|yellowstone|microbiom|microbiota|ecosystem service|ecosystem health|
ecosystem function|ecosystem restoration|ecological restoration""")

def main(src, out):
    pats  = {k:[re.compile(p) for p in v] for k,v in LINEAS.items()}
    biopat = re.compile("|".join(BIO_SEED))
    df = pd.read_csv(src, dtype=str)
    refs = df["References"].fillna("").map(norm)
    for k, ps in pats.items():
        df["L_"+k] = [sum(bool(p.search(r)) for p in ps) for r in refs]
    Lc = ["L_"+k for k in LINEAS]
    df["semillas_max"]   = df[Lc].max(axis=1)
    df["lineas_tocadas"] = (df[Lc] > 0).sum(axis=1)
    df["linea_dominante"]= df[Lc].idxmax(axis=1).str[2:].where(df.semillas_max>0, "")
    df["cita_bio"]       = [bool(biopat.search(r)) for r in refs]
    df["n_refs"]         = refs.str.count(";")
    t = df["Title"].fillna("").map(norm)
    df["titulo_org"] = t.str.contains(ORG_TITLE, regex=True, na=False)
    df["titulo_bio"] = t.str.contains(BIO_TITLE, regex=True, na=False)

    def decide(r):
        if r.semillas_max >= 2: return "1_nucleo"
        if r.n_refs == 0:       return "3_sin_referencias"
        if r.semillas_max == 1: return "2_revision"
        if r.titulo_org and not r.titulo_bio: return "2_revision"
        return "4_fuera"
    df["decision"] = df.apply(decide, axis=1)

    import os; os.makedirs(out, exist_ok=True)
    cb = pd.to_numeric(df["Cited by"], errors="coerce").fillna(0)
    for tag, name in [("1_nucleo","nucleo"),("2_revision","revision"),
                      ("3_sin_referencias","sin_referencias"),("4_fuera","fuera")]:
        sub = df[df.decision == tag].assign(_cb=cb).sort_values("_cb", ascending=False).drop(columns="_cb")
        sub.to_csv(f"{out}/{name}.csv", index=False)
        print(f"{name:18s} {len(sub):6d}")
    (df.groupby(["decision","linea_dominante"]).size().rename("n")
       .reset_index().to_csv(f"{out}/diagnostico.csv", index=False))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv)>2 else "./salida")
