#!/usr/bin/env python3
"""
Barrido de cobertura del catalogo World Development Indicators (WDI, source=2).

Para cada indicador del WDI mide cuantos PAISES reales (no agregados) tienen
un dato reciente, y la recencia (anio mediano del ultimo dato disponible).
Salida -> data/coverage.json  + resumen por consola.

Solo stdlib. Paraleliza con hilos y reintenta ante errores transitorios.
"""
import json, os, sys, time, urllib.request, urllib.error, statistics
from concurrent.futures import ThreadPoolExecutor, as_completed

API = "https://api.worldbank.org/v2"
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "data"))
WORKERS = 12
RETRIES = 4

def fetch(url, tries=RETRIES):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "populi-nmd/1.0"})
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.load(r)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as e:
            last = e
            time.sleep(1.2 * (i + 1))
    raise last

def real_countries():
    """ISO3 de paises reales (excluye agregados region=Aggregates)."""
    out = {}
    page = 1
    while True:
        d = fetch(f"{API}/country?format=json&per_page=300&page={page}")
        meta, rows = d[0], d[1]
        for c in rows:
            if c.get("region", {}).get("value") != "Aggregates":
                out[c["id"]] = {  # id = ISO3
                    "name": c["name"],
                    "region": c.get("region", {}).get("value"),
                    "income": c.get("incomeLevel", {}).get("value"),
                }
        if page >= meta["pages"]:
            break
        page += 1
    return out

def all_indicators(source=2):
    """Catalogo de indicadores de una fuente (2=WDI, 3=WGI gobernanza, ...)."""
    d = fetch(f"{API}/indicator?format=json&source={source}&per_page=2000")
    meta, rows = d[0], d[1]
    inds = []
    for r in rows:
        topics = r.get("topics") or []
        topic = topics[0].get("value", "").strip() if topics else "Sin tema"
        inds.append({
            "id": r["id"],
            "name": r["name"],
            "topic": topic,
            "source_note": (r.get("sourceNote") or "")[:400],
        })
    return inds

def coverage(ind, valid_iso):
    """Cobertura de un indicador: paises con ultimo dato disponible (mrnev=1)."""
    url = f"{API}/country/all/indicator/{ind['id']}?format=json&mrnev=1&per_page=400"
    try:
        d = fetch(url)
    except Exception as e:
        return {**ind, "error": str(e), "countries_with_data": 0, "coverage_pct": 0.0, "latest_year_median": None}
    rows = d[1] if isinstance(d, list) and len(d) > 1 and d[1] else []
    years = []
    seen = set()
    for r in rows:
        iso = r.get("countryiso3code")
        if iso in valid_iso and r.get("value") is not None and iso not in seen:
            seen.add(iso)
            try:
                years.append(int(r["date"]))
            except (TypeError, ValueError):
                pass
    n = len(seen)
    return {
        **ind,
        "countries_with_data": n,
        "coverage_pct": round(100 * n / len(valid_iso), 1),
        "latest_year_median": int(statistics.median(years)) if years else None,
        "latest_year_max": max(years) if years else None,
    }

def main():
    # Args: --sources 2,3   (default 2) ; --merge (fusiona con coverage.json existente)
    sources = [2]
    merge = "--merge" in sys.argv
    for i, a in enumerate(sys.argv):
        if a == "--sources" and i + 1 < len(sys.argv):
            sources = [int(s) for s in sys.argv[i + 1].split(",")]

    t0 = time.time()
    print("Cargando paises reales...", flush=True)
    countries = real_countries()
    valid = set(countries)
    print(f"  paises reales: {len(valid)}", flush=True)

    inds = []
    for src in sources:
        s = all_indicators(src)
        print(f"  indicadores fuente {src}: {len(s)}", flush=True)
        inds += s

    print(f"Midiendo cobertura ({WORKERS} hilos)...", flush=True)
    results = []
    done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(coverage, ind, valid): ind for ind in inds}
        for f in as_completed(futs):
            results.append(f.result())
            done += 1
            if done % 100 == 0:
                print(f"  {done}/{len(inds)}  ({time.time()-t0:.0f}s)", flush=True)

    cov_path = os.path.join(DATA, "coverage.json")
    if merge and os.path.exists(cov_path):
        prev = json.load(open(cov_path, encoding="utf-8"))["indicators"]
        by_id = {r["id"]: r for r in prev}
        for r in results:
            by_id[r["id"]] = r      # nuevos sobrescriben/añaden
        results = list(by_id.values())
        print(f"  fusionado con previo -> {len(results)} indicadores totales", flush=True)

    results.sort(key=lambda r: (-r["coverage_pct"], -(r.get("countries_with_data") or 0)))

    out = {
        "countries_total": len(valid),
        "indicators_total": len(results),
        "indicators": results,
    }
    os.makedirs(DATA, exist_ok=True)
    with open(cov_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))

    # ---- Resumen ----
    def cnt(th): return sum(1 for r in results if r["coverage_pct"] >= th)
    print("\n===== RESUMEN COBERTURA =====", flush=True)
    print(f"Paises base: {len(valid)} | Indicadores: {len(results)} | t={time.time()-t0:.0f}s")
    for th in (95, 90, 80, 70, 50):
        print(f"  >= {th}% cobertura: {cnt(th)} indicadores")

    # Conteo por tema entre los de alta cobertura (>=80%) y recientes (>=2018)
    from collections import Counter
    strong = [r for r in results if r["coverage_pct"] >= 80 and (r.get("latest_year_median") or 0) >= 2015]
    by_topic = Counter(r["topic"] for r in strong)
    print(f"\nIndicadores 'fuertes' (>=80% cobertura y dato mediano >=2015): {len(strong)}")
    for topic, c in by_topic.most_common():
        print(f"  {c:4d}  {topic}")

    print("\nTOP 25 por cobertura:")
    for r in results[:25]:
        print(f"  {r['coverage_pct']:5.1f}%  {r.get('latest_year_median')}  {r['id']:<22}  {r['name'][:60]}")

    print(f"\nGuardado: {os.path.join(DATA, 'coverage.json')}")

if __name__ == "__main__":
    main()
