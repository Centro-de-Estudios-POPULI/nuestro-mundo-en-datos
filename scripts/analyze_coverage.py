#!/usr/bin/env python3
"""
Analisis exploratorio de data/coverage.json para fundamentar la curaduria.
Por cada tema muestra los mejores candidatos 'limpios' (sin desagregaciones por
sexo/edad/quinquenio que inflan el catalogo con redundancia).
"""
import json, os, re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "data"))
cov = json.load(open(os.path.join(DATA, "coverage.json"), encoding="utf-8"))
inds = cov["indicators"]

# Patrones de desagregacion que generan redundancia (los excluimos del reporte limpio)
NOISE = re.compile(
    r"(\.FE|\.MA)(\.|$)"          # por sexo
    r"|\.\d{4}\."                  # rangos de edad tipo .0014. .0509.
    r"|\.\d{2}\.5Y"               # quinquenios .5Y
    r"|\.5Y$"
)
# Palabras que delatan desagregacion en el nombre
NOISE_NAME = re.compile(r"ages \d|, male|, female|quintile|, rural|, urban", re.I)

def is_clean(r):
    return not NOISE.search(r["id"]) and not NOISE_NAME.search(r["name"])

by_topic = defaultdict(list)
for r in inds:
    if r["coverage_pct"] >= 70 and (r.get("latest_year_median") or 0) >= 2012:
        by_topic[r["topic"]].append(r)

print("TEMA: candidatos limpios (cob>=70%, mediana>=2012) / totales fuertes\n")
order = ["Economy & Growth","Health","Education","Environment","Climate Change",
         "Energy & Mining","Social Protection & Labor","Private Sector",
         "Financial Sector","Infrastructure","Agriculture & Rural Development",
         "Public Sector","Urban Development","Poverty","Science & Technology"]
for topic in order:
    rows = by_topic.get(topic, [])
    clean = [r for r in rows if is_clean(r)]
    clean.sort(key=lambda r: -r["coverage_pct"])
    print(f"\n===== {topic}  (limpios {len(clean)} / total {len(rows)}) =====")
    for r in clean[:16]:
        print(f"  {r['coverage_pct']:5.1f}%  {r.get('latest_year_median')}  {r['id']:<20} {r['name'][:62]}")
