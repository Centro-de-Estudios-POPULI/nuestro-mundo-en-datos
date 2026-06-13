#!/usr/bin/env python3
"""
Crosswalk codigo numerico ISO/M49 (el que usa world-atlas/TopoJSON) -> ISO3
(el que usa el Banco Mundial). Necesario para unir geometria con datos en D3.

Fuente: dataset 'country-codes' de Datahub (CSV estable). Una sola request.
Salida: data/iso-crosswalk.json  ->  {"840":"USA","68":"BOL",...}
"""
import csv, io, json, os, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "data"))
CSV_URL = "https://raw.githubusercontent.com/datasets/country-codes/master/data/country-codes.csv"

def main():
    req = urllib.request.Request(CSV_URL, headers={"User-Agent": "populi-nmd/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        text = r.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    cw = {}
    for row in reader:
        num = (row.get("ISO3166-1-numeric") or "").strip()
        iso3 = (row.get("ISO3166-1-Alpha-3") or "").strip()
        if num and iso3:
            cw[str(int(num))] = iso3        # "840" -> "USA"  (sin ceros a la izq.)
    os.makedirs(DATA, exist_ok=True)
    path = os.path.join(DATA, "iso-crosswalk.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(cw, fh, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    print(f"Crosswalk: {len(cw)} paises -> {path}")

if __name__ == "__main__":
    main()
