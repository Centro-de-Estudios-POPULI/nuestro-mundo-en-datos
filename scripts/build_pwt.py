#!/usr/bin/env python3
"""
Penn World Table 11.0 -> JSON compactos + catálogo.
PIB per cápita PPA, productividad laboral, capital humano, horas trabajadas, PTF.
Fuente: Feenstra, Inklaar y Timmer (2015), GGDC, Universidad de Groningen (CC BY 4.0).
Versión 11.0 (oct-2025): 185 países, 1950-2023, dólares internacionales de 2021.
"""
import pandas as pd, json, os, statistics, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "data"))
OUT = os.path.join(DATA, "indicators")
SRCDIR = os.path.join(DATA, "sources")
XLSX = os.path.join(SRCDIR, "pwt1100.xlsx")
URL = "https://dataverse.nl/api/access/datafile/554105"
ORG = "Groningen Growth and Development Centre, Universidad de Groningen"
SOURCE = "Penn World Table 11.0 (Feenstra, Inklaar y Timmer)"
CATEGORY = "Productividad · Penn World Table"
regions = set(json.load(open(os.path.join(DATA, "regions.json"), encoding="utf-8")))

import sys; sys.path.insert(0, HERE)
from catalog_merge import merge
from descarga import descargar

def ensure():
    os.makedirs(SRCDIR, exist_ok=True)
    if not os.path.exists(XLSX):
        print("Descargando PWT…")
        descargar(URL, XLSX)

def series(df, col, rnd=2, as_int=False):
    piv = df.pivot_table(index="countrycode", columns="year", values=col, aggfunc="first")
    years = [int(y) for y in piv.columns]
    data = {}
    for cc, row in piv.iterrows():
        arr = []
        for v in row.tolist():
            if pd.isna(v): arr.append(None)
            else: arr.append(int(round(v)) if as_int else round(v, rnd))
        if any(v is not None for v in arr):
            data[cc] = arr
    return years, data

def meta_of(iid, name, unit, years, data, defn):
    last = []
    for cc, arr in data.items():
        if cc in regions:
            for i in range(len(arr) - 1, -1, -1):
                if arr[i] is not None: last.append(years[i]); break
    n = sum(1 for cc in data if cc in regions)
    return {"id": iid, "name": name, "unit": unit, "category": CATEGORY, "type": "rel",
            "coverage_pct": round(100 * n / len(regions), 1),
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
    df = pd.read_excel(XLSX, sheet_name="Data")
    # variables derivadas
    df["labsh_pct"] = df["labsh"] * 100
    metas = []

    # NOTA: se retiraron deliberadamente el PIB per cápita (rgdpo/pop) y el PIB por
    # trabajador (rgdpo/emp) de PWT. Ambos eran series DERIVADAS por nosotros (PWT no las
    # trae) y, medidas como PIB real lado-producción, generan artefactos en petro-economías
    # (p. ej. Emiratos en 1980 >> hoy). El PIB per cápita histórico lo cubre la serie NATIVA
    # del Maddison Project (MPD.GDPPC). Se conservan solo variables nativas de PWT.
    defs = [
        ("PWT.HC", "Índice de capital humano", "índice", "hc", 3, False,
         "Índice de capital humano por persona, basado en años de escolaridad (Barro-Lee) y los retornos a la educación (ecuación de Mincer)."),
        ("PWT.AVH", "Horas trabajadas al año por ocupado", "horas/año", "avh", 0, True,
         "Promedio anual de horas trabajadas por persona ocupada."),
        ("PWT.CTFP", "Productividad total de los factores (EE.UU.=1)", "índice (EE.UU.=1)", "ctfp", 3, False,
         "Nivel de productividad total de los factores a PPA corrientes, normalizado con Estados Unidos = 1."),
        ("PWT.LABSH", "Participación del trabajo en el ingreso", "% del PIB", "labsh_pct", 1, False,
         "Porción del ingreso nacional que remunera al trabajo (salarios y autoempleo), frente al capital."),
    ]
    for iid, name, unit, col, rnd, as_int, dfn in defs:
        y, d = series(df, col, rnd=rnd, as_int=as_int)
        write(iid, name, y, d)
        metas.append(meta_of(iid, name, unit, y, d, dfn))

    merge(DATA, CATEGORY, metas)
    for m in metas:
        print(f"  {m['id']}: cobertura {m['coverage_pct']}% · hasta {m['latest_year_max']}")

if __name__ == "__main__":
    main()
