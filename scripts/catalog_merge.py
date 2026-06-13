#!/usr/bin/env python3
"""Helper: fusiona una categoría de indicadores (no-WB) en data/catalog.json."""
import json, os

def merge(DATA, category, indicators):
    p = os.path.join(DATA, "catalog.json")
    cat = json.load(open(p, encoding="utf-8"))
    cat["indicators"] = [i for i in cat["indicators"] if i.get("category") != category] + indicators
    cat["categories"] = [c for c in cat["categories"] if c["name"] != category]
    cat["categories"].append({"name": category, "count": len(indicators)})
    json.dump(cat, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"catalog.json: +{len(indicators)} en '{category}' (total {len(cat['indicators'])})")
