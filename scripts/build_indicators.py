#!/usr/bin/env python3
"""
Genera los JSON compactos por indicador para el atlas.

Toma IDs de indicador del WB (WDI) y, por cada uno, descarga la serie historica
completa y la reempaqueta al formato compacto que consume el motor D3:

    {"indicator","name","unit","source","years":[...],"data":{ISO3:[valores...]}}

Uso:
    python build_indicators.py NY.GDP.PCAP.CD SP.DYN.LE00.IN ...
    python build_indicators.py --from-catalog   # lee data/catalog.json
"""
import json, os, sys, time, urllib.request, urllib.error

API = "https://api.worldbank.org/v2"
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "data"))
OUT = os.path.join(DATA, "indicators")

def fetch(url, tries=4):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "populi-nmd/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as e:
            last = e
            time.sleep(1.2 * (i + 1))
    raise last

def build_one(ind_id):
    d = fetch(f"{API}/country/all/indicator/{ind_id}?format=json&per_page=20000")
    if not isinstance(d, list) or len(d) < 2 or not d[1]:
        print(f"  ! sin datos: {ind_id}")
        return None
    rows = d[1]
    meta = rows[0].get("indicator", {})
    name = meta.get("value", ind_id)
    years = sorted({int(r["date"]) for r in rows})
    yi = {y: i for i, y in enumerate(years)}
    data = {}
    for r in rows:
        iso = r.get("countryiso3code")
        if not iso:
            continue
        v = r.get("value")
        arr = data.setdefault(iso, [None] * len(years))
        arr[yi[int(r["date"])]] = round(v, 3) if isinstance(v, (int, float)) else None
    # descarta entidades totalmente vacias
    data = {k: v for k, v in data.items() if any(x is not None for x in v)}
    compact = {
        "indicator": ind_id,
        "name": name,
        "source": "World Bank — World Development Indicators",
        "years": years,
        "data": data,
    }
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f"{ind_id}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(compact, fh, ensure_ascii=False, separators=(",", ":"))
    kb = os.path.getsize(path) / 1024
    print(f"  ok {ind_id}: {len(data)} paises, {years[0]}-{years[-1]}, {kb:.1f} KB")
    return path

def main(argv):
    if "--from-catalog" in argv:
        with open(os.path.join(DATA, "catalog.json"), encoding="utf-8") as fh:
            cat = json.load(fh)
        ids = [i["id"] for i in cat["indicators"]]
    else:
        ids = [a for a in argv if not a.startswith("--")]
    if not ids:
        print("Indica al menos un ID o usa --from-catalog")
        return
    print(f"Generando {len(ids)} indicador(es)...")
    for i in ids:
        build_one(i)

if __name__ == "__main__":
    main(sys.argv[1:])
