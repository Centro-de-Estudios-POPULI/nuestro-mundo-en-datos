#!/usr/bin/env python3
"""
Mide cobertura de IDs sueltos (que pueden no estar en el catálogo de su fuente)
y los fusiona en data/coverage.json. Útil para indicadores emblemáticos que el
barrido por fuente no listó (p.ej. Índice de Capital Humano).
Uso: python sweep_extra_ids.py HD.HCI.OVRL SH.UHC.SRVS.CV.XD ...
"""
import json, os, sys, statistics, time, urllib.request, urllib.error

API = "https://api.worldbank.org/v2"
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "data"))
valid = set(json.load(open(os.path.join(DATA, "regions.json"), encoding="utf-8")))  # 217 ISO3 reales

def fetch(url, tries=4):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "populi-nmd/1.0"})
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.load(r)
        except Exception as e:
            last = e; time.sleep(1.2 * (i + 1))
    raise last

def measure(iid):
    d = fetch(f"{API}/country/all/indicator/{iid}?format=json&mrnev=1&per_page=400")
    rows = d[1] if isinstance(d, list) and len(d) > 1 and d[1] else []
    name = (rows[0].get("indicator", {}).get("value") if rows else iid) or iid
    years, seen = [], set()
    for r in rows:
        iso = r.get("countryiso3code")
        if iso in valid and r.get("value") is not None and iso not in seen:
            seen.add(iso)
            try: years.append(int(r["date"]))
            except (TypeError, ValueError): pass
    n = len(seen)
    return {"id": iid, "name": name, "topic": "Sin tema",
            "countries_with_data": n, "coverage_pct": round(100 * n / len(valid), 1),
            "latest_year_median": int(statistics.median(years)) if years else None,
            "latest_year_max": max(years) if years else None}

def main(ids):
    cov_path = os.path.join(DATA, "coverage.json")
    doc = json.load(open(cov_path, encoding="utf-8"))
    by_id = {r["id"]: r for r in doc["indicators"]}
    for iid in ids:
        try:
            rec = measure(iid)
            by_id[iid] = rec
            print(f"  {rec['coverage_pct']:5.1f}%  med {rec['latest_year_median']}  {iid:<20} {rec['name'][:50]}")
        except Exception as e:
            print(f"  ! {iid}: {e}")
    doc["indicators"] = list(by_id.values())
    doc["indicators_total"] = len(doc["indicators"])
    json.dump(doc, open(cov_path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print("Fusionado en coverage.json")

if __name__ == "__main__":
    main(sys.argv[1:])
