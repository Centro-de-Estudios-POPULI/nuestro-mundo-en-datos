"""
build_owid.py — Descarga indicadores de Our World in Data (catálogo
scripts/owid_indicadores.json) e incorpora cada uno al atlas:

  · baja el CSV completo por slug (?csvType=full&useColumnShortNames=true),
  · se queda SOLO con países reales (columna `code` ∈ regions.json) → descarta
    agregados (World, regiones, grupos de ingreso) y no-países,
  · escribe data/indicators/<id>.json con el esquema del atlas
    {indicator, name, source, years:[], data:{ISO3:[...]}},
  · agrega/actualiza la entrada en data/catalog.json (con scale/direction/family)
    y crea las categorías nuevas que falten.

Idempotente: re-ejecutar actualiza en lugar de duplicar. Hace backup catalog.json.owidbak.

Uso:
    python scripts/build_owid.py                 # todos los del catálogo OWID
    python scripts/build_owid.py <slug|id> ...   # solo esos
"""
import csv
import io
import json
import sys
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
IND = DATA / "indicators"
CAT = DATA / "catalog.json"
OWID = ROOT / "scripts" / "owid_indicadores.json"
CSV_URL = "https://ourworldindata.org/grapher/{slug}.csv?csvType=full&useColumnShortNames=true"
META_COLS = {"entity", "code", "year", "owid_region"}


def fetch_csv(slug):
    url = CSV_URL.format(slug=slug)
    # OWID está tras Cloudflare: requiere User-Agent de navegador (urllib es bloqueado con 403)
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/csv,*/*", "Accept-Language": "es,en;q=0.8",
    })
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read().decode("utf-8")


def to_num(s):
    s = (s or "").strip()
    if s == "":
        return None
    try:
        f = float(s)
        return int(f) if f.is_integer() else round(f, 4)
    except ValueError:
        return None


def build_one(meta, valid_iso):
    rows = list(csv.reader(io.StringIO(fetch_csv(meta["owid_slug"]))))
    header = [h.strip().lower() for h in rows[0]]
    ci, yi = header.index("code"), header.index("year")
    vi = next(i for i, h in enumerate(header) if h not in META_COLS)
    valname = header[vi]

    by_iso, years_set = {}, set()
    for r in rows[1:]:
        if len(r) <= max(ci, yi, vi):
            continue
        code = r[ci].strip()
        if code not in valid_iso:                 # solo países reales
            continue
        y, v = to_num(r[yi]), to_num(r[vi])
        if y is None or v is None:
            continue
        by_iso.setdefault(code, {})[int(y)] = v
        years_set.add(int(y))

    years = sorted(years_set)
    yidx = {y: i for i, y in enumerate(years)}
    data = {}
    for iso, yv in by_iso.items():
        arr = [None] * len(years)
        for y, v in yv.items():
            arr[yidx[y]] = v
        data[iso] = arr

    out = {
        "indicator": meta["id"],
        "name": meta["name"],
        "source": f"{meta.get('org', 'Our World in Data')} — vía Our World in Data",
        "years": years,
        "data": data,
    }
    y0, y1 = (years[0], years[-1]) if years else (None, None)
    return out, len(data), y0, y1, valname


def catalog_entry(meta, ncty, y1, valid_n):
    return {
        "id": meta["id"], "name": meta["name"], "unit": meta["unit"],
        "category": meta["category"], "type": meta.get("type", "rel"),
        "coverage_pct": round(100 * ncty / valid_n, 1),
        "latest_year_median": y1, "latest_year_max": y1,
        "wb_name": meta["owid_slug"], "def": meta.get("def", ""), "org": meta.get("org", ""),
        "scale": meta["scale"], "direction": meta["direction"], "family": meta["family"],
    }


def main():
    owid = json.loads(OWID.read_text(encoding="utf-8"))
    catalog = json.loads(CAT.read_text(encoding="utf-8"))
    valid_iso = set(json.loads((DATA / "regions.json").read_text(encoding="utf-8")).keys())
    valid_n = len(valid_iso)

    args = set(sys.argv[1:])
    items = owid["indicadores"]
    if args:
        items = [x for x in items if x["owid_slug"] in args or x["id"] in args]

    IND.mkdir(parents=True, exist_ok=True)
    cur = {d["id"]: d for d in catalog["indicators"]}
    cat_names = {c["name"] for c in catalog["categories"]}
    built = 0

    for meta in items:
        if meta.get("categorico"):
            print(f"SKIP {meta['id']}: categórico (necesita leyenda discreta) — se incorpora aparte")
            continue
        try:
            out, ncty, y0, y1, valname = build_one(meta, valid_iso)
        except Exception as e:
            print(f"ERROR {meta['id']}: {type(e).__name__}: {e}")
            continue
        if ncty < 10:
            print(f"SKIP {meta['id']}: solo {ncty} países con dato")
            continue
        (IND / f"{meta['id']}.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
        cur[meta["id"]] = catalog_entry(meta, ncty, y1, valid_n)
        if meta["category"] not in cat_names:
            catalog["categories"].append({"name": meta["category"], "count": 0})
            cat_names.add(meta["category"])
        built += 1
        print(f"OK   {meta['id']:<52} {ncty:>3} países  {y0}-{y1}  col='{valname}'")

    # reordenar: primero lo no-OWID (orden original), luego los OWID (orden del catálogo OWID)
    owid_ids = {m["id"] for m in owid["indicadores"]}
    non_owid = [d for d in catalog["indicators"] if d["id"] not in owid_ids]
    owid_present = [cur[m["id"]] for m in owid["indicadores"] if m["id"] in cur]
    catalog["indicators"] = non_owid + owid_present

    cnt = Counter(d["category"] for d in catalog["indicators"])
    for c in catalog["categories"]:
        c["count"] = cnt.get(c["name"], 0)

    CAT.with_suffix(".json.owidbak").write_text(CAT.read_text(encoding="utf-8"), encoding="utf-8")
    CAT.write_text(json.dumps(catalog, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n{built} indicadores OWID incorporados. "
          f"catalog.json -> {len(catalog['indicators'])} indicadores, {len(catalog['categories'])} categorías.")


if __name__ == "__main__":
    main()
