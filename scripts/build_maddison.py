#!/usr/bin/env python3
"""
Maddison Project Database 2023 -> JSON compactos + catálogo.
PIB per cápita histórico (desde 1820) y población histórica.
Fuente: GGDC, Universidad de Groningen (CC BY 4.0).
"""
import pandas as pd, json, os, statistics, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "data"))
OUT = os.path.join(DATA, "indicators")
SRCDIR = os.path.join(DATA, "sources")
XLSX = os.path.join(SRCDIR, "mpd2023web.xlsx")
URL = "https://dataverse.nl/api/access/datafile/421302"
ORG = "Groningen Growth and Development Centre, Universidad de Groningen"
SOURCE = "Maddison Project Database 2023 (Bolt y van Zanden)"
YEAR_MIN = 1800
regions = set(json.load(open(os.path.join(DATA, "regions.json"), encoding="utf-8")))

import sys; sys.path.insert(0, HERE)
from catalog_merge import merge
from descarga import descargar

def ensure():
    os.makedirs(SRCDIR, exist_ok=True)
    if not os.path.exists(XLSX):
        print("Descargando Maddison…")
        descargar(URL, XLSX)

def series(df, col, scale=1, rnd=2, as_int=False):
    piv = df.pivot_table(index="countrycode", columns="year", values=col, aggfunc="first")
    years = [int(y) for y in piv.columns]
    data = {}
    for cc, row in piv.iterrows():
        arr = []
        for v in row.tolist():
            if pd.isna(v): arr.append(None)
            else: arr.append(int(round(v * scale)) if as_int else round(v * scale, rnd))
        if any(v is not None for v in arr):
            data[cc] = arr
    return years, data

def meta_of(iid, name, unit, years, data, kind, defn):
    last = []
    for cc, arr in data.items():
        if cc in regions:
            for i in range(len(arr) - 1, -1, -1):
                if arr[i] is not None: last.append(years[i]); break
    n = sum(1 for cc in data if cc in regions)
    return {"id": iid, "name": name, "unit": unit, "category": "Largo plazo · Maddison Project",
            "type": kind, "coverage_pct": round(100 * n / len(regions), 1),
            "latest_year_median": int(statistics.median(last)) if last else None,
            "latest_year_max": max(last) if last else None,
            "wb_name": name, "def": defn, "org": ORG, "source": SOURCE}

def write(iid, name, years, data):
    os.makedirs(OUT, exist_ok=True)
    obj = {"indicator": iid, "name": name, "source": SOURCE, "years": years, "data": data}
    json.dump(obj, open(os.path.join(OUT, iid + ".json"), "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))

def main():
    ensure()
    df = pd.read_excel(XLSX, sheet_name="Full data")
    df = df[df["year"] >= YEAR_MIN]
    metas = []

    y, d = series(df, "gdppc", rnd=1)
    write("MPD.GDPPC", "PIB per cápita (histórico)", y, d)
    metas.append(meta_of("MPD.GDPPC", "PIB per cápita (histórico)", "US$ internacionales de 2011",
        y, d, "rel", "PIB per cápita real en dólares internacionales de 2011, empalmado por el Maddison "
        "Project para permitir comparaciones de niveles de ingreso en el muy largo plazo (desde 1820, y "
        "antes para algunos países)."))

    y, d = series(df, "pop", scale=1000, as_int=True)   # Maddison: población en miles
    write("MPD.POP", "Población (histórica)", y, d)
    metas.append(meta_of("MPD.POP", "Población (histórica)", "personas",
        y, d, "abs", "Población total con cobertura histórica de largo plazo estimada por el Maddison Project."))

    merge(DATA, "Largo plazo · Maddison Project", metas)
    for m in metas:
        print(f"  {m['id']}: cobertura {m['coverage_pct']}% · hasta {m['latest_year_max']}")

if __name__ == "__main__":
    main()
