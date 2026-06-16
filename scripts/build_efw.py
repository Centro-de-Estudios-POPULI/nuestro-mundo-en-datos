"""
build_efw.py — Incorpora el Índice de Libertad Económica del Mundo (Fraser
Institute, EFW) al atlas, desde el repo hermano populi-libertad-economica.

Fuente: data/efw_panel_map.json  = { "<año>": { ISO3: {s, a1, a2, a3, a4, a5} } }
  s = índice general (0–10) · a1..a5 = las 5 áreas.

Crea 6 indicadores (índice general + 5 áreas), filtra a países reales (regions.json),
escribe data/indicators/EFW.*.json y actualiza catalog.json (categoría 'Libertad económica').
Curaduría: más alto = más libre = mejor -> verde. Idempotente, con backup .efwbak.
"""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
IND = DATA / "indicators"
CAT = DATA / "catalog.json"
EFW_SRC = ROOT.parent / "populi-libertad-economica" / "data" / "efw_panel_map.json"

ORG = "Fraser Institute — Economic Freedom of the World (informe anual 2025)"
CATEGORY = "Libertad económica"

METRICS = [
    ("s", "EFW.SUMMARY", "Índice de Libertad Económica",
     "Índice de Libertad Económica del Mundo (Fraser Institute): mide cuánto las políticas e "
     "instituciones de un país favorecen la libertad de elección, el intercambio voluntario y los "
     "mercados, de 0 a 10 (más libre)."),
    ("a1", "EFW.A1", "Libertad económica: Tamaño del Gobierno",
     "Área 1 del EFW: peso del gasto público, los impuestos y las empresas estatales. Un valor alto "
     "indica menor intervención del Estado (más libertad)."),
    ("a2", "EFW.A2", "Libertad económica: Sistema Legal y Derechos de Propiedad",
     "Área 2 del EFW: calidad del sistema legal y protección de los derechos de propiedad. Un valor "
     "alto indica instituciones más sólidas."),
    ("a3", "EFW.A3", "Libertad económica: Solidez del Dinero",
     "Área 3 del EFW: estabilidad monetaria y libertad para usar monedas. Un valor alto indica menor "
     "inflación y mayor libertad monetaria."),
    ("a4", "EFW.A4", "Libertad económica: Libertad de Comercio Internacional",
     "Área 4 del EFW: apertura al comercio exterior (aranceles, barreras y controles de capital). Un "
     "valor alto indica mayor libertad para comerciar."),
    ("a5", "EFW.A5", "Libertad económica: Regulación",
     "Área 5 del EFW: regulación del crédito, el trabajo y los negocios. Un valor alto indica "
     "regulaciones menos restrictivas."),
]


def main():
    panel = json.loads(EFW_SRC.read_text(encoding="utf-8"))
    valid = set(json.loads((DATA / "regions.json").read_text(encoding="utf-8")).keys())
    years = sorted(int(y) for y in panel.keys())
    catalog = json.loads(CAT.read_text(encoding="utf-8"))
    cur = {d["id"]: d for d in catalog["indicators"]}
    cat_names = {c["name"] for c in catalog["categories"]}
    IND.mkdir(parents=True, exist_ok=True)

    for key, iid, name, dfn in METRICS:
        data = {}
        for yi, y in enumerate(years):
            for iso, rec in panel[str(y)].items():
                if iso not in valid:
                    continue
                v = rec.get(key)
                if v is None:
                    continue
                data.setdefault(iso, [None] * len(years))[yi] = v
        ncty = len(data)
        out = {"indicator": iid, "name": name,
               "source": f"{ORG} — vía Centro de Estudios POPULI",
               "years": years, "data": data}
        (IND / f"{iid}.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
        y1 = max((years[i] for iso in data for i in range(len(years)) if data[iso][i] is not None),
                 default=years[-1])
        cur[iid] = {
            "id": iid, "name": name, "unit": "índice 0–10", "category": CATEGORY, "type": "rel",
            "coverage_pct": round(100 * ncty / len(valid), 1),
            "latest_year_median": y1, "latest_year_max": y1,
            "wb_name": iid, "def": dfn, "org": ORG,
            "scale": "secuencial", "direction": "mejor", "family": "verde",
        }
        print(f"OK {iid:<14} {ncty:>3} países  {years[0]}-{years[-1]}")

    if CATEGORY not in cat_names:
        catalog["categories"].append({"name": CATEGORY, "count": 0})
    efw_ids = [m[1] for m in METRICS]
    base = [d for d in catalog["indicators"] if d["id"] not in efw_ids]
    catalog["indicators"] = base + [cur[i] for i in efw_ids]
    cnt = Counter(d["category"] for d in catalog["indicators"])
    for c in catalog["categories"]:
        c["count"] = cnt.get(c["name"], 0)

    CAT.with_suffix(".json.efwbak").write_text(CAT.read_text(encoding="utf-8"), encoding="utf-8")
    CAT.write_text(json.dumps(catalog, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nEFW incorporado. catalog.json -> {len(catalog['indicators'])} indicadores, "
          f"{len(catalog['categories'])} categorías.")


if __name__ == "__main__":
    main()
