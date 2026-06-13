#!/usr/bin/env python3
"""
Mapa ISO3 -> region e ingreso (para colorear burbujas del scatter tipo Gapminder).
Fuente: endpoint de paises del Banco Mundial. Traduce regiones/ingreso al espanol.
Salida: data/regions.json -> {"BOL":{"name":"Bolivia","region":"América Latina y el Caribe","income":"Ingreso mediano bajo"}, ...}
"""
import json, os, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "data"))

REGION_ES = {
    "East Asia & Pacific": "Asia Oriental y Pacífico",
    "Europe & Central Asia": "Europa y Asia Central",
    "Latin America & Caribbean": "América Latina y el Caribe",
    "Middle East & North Africa": "Oriente Medio y Norte de África",
    "Middle East, North Africa, Afghanistan & Pakistan": "Oriente Medio y Norte de África",
    "North America": "América del Norte",
    "South Asia": "Asia Meridional",
    "Sub-Saharan Africa": "África Subsahariana",
}
INCOME_ES = {
    "High income": "Ingreso alto",
    "Upper middle income": "Ingreso mediano alto",
    "Lower middle income": "Ingreso mediano bajo",
    "Low income": "Ingreso bajo",
}

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "populi-nmd/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def main():
    # nombres de países en español (API del Banco Mundial en /es/)
    es_names, page = {}, 1
    while True:
        d = fetch(f"https://api.worldbank.org/v2/es/country?format=json&per_page=300&page={page}")
        meta, rows = d[0], d[1]
        for c in rows:
            es_names[c["id"]] = c["name"]
        if page >= meta["pages"]:
            break
        page += 1

    out, page = {}, 1
    while True:
        d = fetch(f"https://api.worldbank.org/v2/country?format=json&per_page=300&page={page}")
        meta, rows = d[0], d[1]
        for c in rows:
            reg = (c.get("region", {}).get("value") or "").strip()
            if reg == "Aggregates" or not reg:
                continue
            out[c["id"]] = {
                "name": es_names.get(c["id"], c["name"]),   # nombre en español
                "region": REGION_ES.get(reg, reg),
                "income": INCOME_ES.get(c.get("incomeLevel", {}).get("value"), "—"),
            }
        if page >= meta["pages"]:
            break
        page += 1
    with open(os.path.join(DATA, "regions.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    from collections import Counter
    print(f"regions.json: {len(out)} paises")
    for r, n in Counter(v["region"] for v in out.values()).most_common():
        print(f"  {n:3d}  {r}")

if __name__ == "__main__":
    main()
