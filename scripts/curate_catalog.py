#!/usr/bin/env python3
"""
Catalogo curado (editorial) AMPLIADO, cruzado con la cobertura real medida.
Whitelist de indicadores interpretables con nombres/unidades en espanol,
re-categorizados por significado real. Incluye WDI (fuente 2) + WGI gobernanza
(fuente 3) + bloque generado de estructura por edad (quinquenal por sexo).

Salida: data/catalog.json  + reporte de verificacion (faltantes / baja cobertura).
"""
import json, os, urllib.request
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "data"))
cov = {r["id"]: r for r in json.load(open(os.path.join(DATA, "coverage.json"), encoding="utf-8"))["indicators"]}

def fetch_defs(sources=(2, 3)):
    """Definiciones del Banco Mundial: sourceNote (cómo se calcula) + organización fuente."""
    defs = {}
    for src in sources:
        try:
            req = urllib.request.Request(
                f"https://api.worldbank.org/v2/es/indicator?format=json&source={src}&per_page=3000",
                headers={"User-Agent": "populi-nmd/1.0"})
            d = json.load(urllib.request.urlopen(req, timeout=90))
            for r in d[1]:
                defs[r["id"]] = {
                    "def": (r.get("sourceNote") or "").strip(),
                    "org": (r.get("sourceOrganization") or "").strip(),
                }
        except Exception as e:
            print("  ! sin definiciones de fuente", src, ":", e)
    return defs

DEFS = fetch_defs()
print(f"Definiciones descargadas: {len(DEFS)}")

# (id, nombre_es, unidad, tipo)  tipo: rel = relativo (mapeable) / abs = magnitud
CAT = OrderedDict()
CAT["Economía y crecimiento"] = [
    ("NY.GDP.PCAP.CD",      "PIB per cápita", "US$ corrientes", "rel"),
    ("NY.GDP.PCAP.PP.CD",   "PIB per cápita (PPA)", "US$ internacionales", "rel"),
    ("NY.GDP.PCAP.KD",      "PIB per cápita (constante)", "US$ de 2015", "rel"),
    ("NY.GNP.PCAP.CD",      "INB per cápita (método Atlas)", "US$ corrientes", "rel"),
    ("NY.GNP.PCAP.PP.CD",   "INB per cápita (PPA)", "US$ internacionales", "rel"),
    ("NY.GDP.PCAP.KD.ZG",   "Crecimiento del PIB per cápita", "% anual", "rel"),
    ("NY.GDP.MKTP.KD.ZG",   "Crecimiento del PIB", "% anual", "rel"),
    ("FP.CPI.TOTL.ZG",      "Inflación (precios al consumidor)", "% anual", "rel"),
    ("NY.GDP.DEFL.KD.ZG",   "Inflación (deflactor del PIB)", "% anual", "rel"),
    ("NE.GDI.TOTL.ZS",      "Formación bruta de capital", "% del PIB", "rel"),
    ("NY.GNS.ICTR.ZS",      "Ahorro bruto", "% del PIB", "rel"),
    ("NE.CON.PRVT.ZS",      "Consumo de los hogares", "% del PIB", "rel"),
    ("NV.AGR.TOTL.ZS",      "Valor agregado agrícola", "% del PIB", "rel"),
    ("NV.IND.TOTL.ZS",      "Valor agregado industrial", "% del PIB", "rel"),
    ("NV.IND.MANF.ZS",      "Valor agregado manufacturero", "% del PIB", "rel"),
    ("NV.SRV.TOTL.ZS",      "Valor agregado de servicios", "% del PIB", "rel"),
    ("NY.GDP.MKTP.CD",      "PIB total", "US$ corrientes", "abs"),
    ("NY.GDP.MKTP.PP.CD",   "PIB total (PPA)", "US$ internacionales", "abs"),
    ("GC.DOD.TOTL.GD.ZS",   "Deuda del gobierno central", "% del PIB", "rel"),
]
CAT["Población y demografía"] = [
    ("SP.POP.TOTL",         "Población total", "personas", "abs"),
    ("SP.POP.GROW",         "Crecimiento poblacional", "% anual", "rel"),
    ("EN.POP.DNST",         "Densidad poblacional", "hab./km²", "rel"),
    ("SP.URB.TOTL.IN.ZS",   "Población urbana", "% del total", "rel"),
    ("SP.RUR.TOTL.ZS",      "Población rural", "% del total", "rel"),
    ("SP.DYN.TFRT.IN",      "Tasa de fecundidad", "hijos por mujer", "rel"),
    ("SP.DYN.CBRT.IN",      "Tasa bruta de natalidad", "por 1.000 personas", "rel"),
    ("SP.ADO.TFRT",         "Fecundidad adolescente", "por 1.000 mujeres 15-19", "rel"),
    ("SP.POP.DPND",         "Razón de dependencia (total)", "% pob. en edad de trabajar", "rel"),
    ("SP.POP.DPND.YG",      "Razón de dependencia (jóvenes)", "% pob. en edad de trabajar", "rel"),
    ("SP.POP.DPND.OL",      "Razón de dependencia (mayores)", "% pob. en edad de trabajar", "rel"),
    ("SP.POP.TOTL.FE.ZS",   "Población femenina", "% del total", "rel"),
    ("SP.POP.BRTH.MF",      "Razón de sexos al nacer", "varones por mujer", "rel"),
    ("SP.POP.0014.TO.ZS",   "Población de 0 a 14 años", "% del total", "rel"),
    ("SP.POP.1564.TO.ZS",   "Población de 15 a 64 años", "% del total", "rel"),
    ("SP.POP.65UP.TO.ZS",   "Población de 65 años y más", "% del total", "rel"),
    ("SM.POP.NETM",         "Migración neta", "personas", "abs"),
    ("SM.POP.TOTL.ZS",      "Stock de migrantes internacionales", "% de la población", "rel"),
]
CAT["Salud"] = [
    ("SP.DYN.LE00.IN",      "Esperanza de vida al nacer", "años", "rel"),
    ("SP.DYN.LE00.FE.IN",   "Esperanza de vida (mujeres)", "años", "rel"),
    ("SP.DYN.LE00.MA.IN",   "Esperanza de vida (hombres)", "años", "rel"),
    ("SP.DYN.IMRT.IN",      "Mortalidad infantil", "por 1.000 nacidos vivos", "rel"),
    ("SH.DYN.MORT",         "Mortalidad de menores de 5 años", "por 1.000 nacidos vivos", "rel"),
    ("SH.DYN.NMRT",         "Mortalidad neonatal", "por 1.000 nacidos vivos", "rel"),
    ("SH.STA.MMRT",         "Mortalidad materna", "por 100.000 nacidos vivos", "rel"),
    ("SP.DYN.CDRT.IN",      "Tasa bruta de mortalidad", "por 1.000 personas", "rel"),
    ("SH.MED.PHYS.ZS",      "Médicos", "por 1.000 personas", "rel"),
    ("SH.MED.BEDS.ZS",      "Camas de hospital", "por 1.000 personas", "rel"),
    ("SH.XPD.CHEX.GD.ZS",   "Gasto en salud", "% del PIB", "rel"),
    ("SH.XPD.CHEX.PC.CD",   "Gasto en salud per cápita", "US$ corrientes", "rel"),
    ("SH.H2O.BASW.ZS",      "Acceso a agua potable básica", "% de la población", "rel"),
    ("SH.STA.BASS.ZS",      "Acceso a saneamiento básico", "% de la población", "rel"),
    ("SH.STA.ODFC.ZS",      "Defecación al aire libre", "% de la población", "rel"),
    ("SH.IMM.MEAS",         "Inmunización contra sarampión", "% de niños 12-23 m", "rel"),
    ("SH.IMM.IDPT",         "Inmunización DPT", "% de niños 12-23 m", "rel"),
    ("SH.TBS.INCD",         "Incidencia de tuberculosis", "por 100.000 personas", "rel"),
    ("SH.DYN.AIDS.ZS",      "Prevalencia de VIH (15-49)", "% de la población", "rel"),
    ("SH.STA.SUIC.P5",      "Tasa de mortalidad por suicidio", "por 100.000 personas", "rel"),
]
CAT["Educación"] = [
    ("SE.PRM.ENRR",         "Matrícula en primaria", "% bruto", "rel"),
    ("SE.SEC.ENRR",         "Matrícula en secundaria", "% bruto", "rel"),
    ("SE.TER.ENRR",         "Matrícula en educación terciaria", "% bruto", "rel"),
    ("SE.PRE.ENRR",         "Matrícula en preprimaria", "% bruto", "rel"),
    ("SE.ADT.LITR.ZS",      "Alfabetización (adultos)", "% de 15 años y más", "rel"),
    ("SE.ADT.1524.LT.ZS",   "Alfabetización (jóvenes 15-24)", "% del grupo", "rel"),
    ("SE.XPD.TOTL.GD.ZS",   "Gasto público en educación", "% del PIB", "rel"),
    ("SE.PRM.CMPT.ZS",      "Finalización de la primaria", "% del grupo etario", "rel"),
    ("SE.ENR.PRIM.FM.ZS",   "Paridad de género en primaria", "índice (M/H)", "rel"),
    ("SE.PRM.ENRL.TC.ZS",   "Alumnos por docente (primaria)", "alumnos/docente", "rel"),
]
CAT["Empleo y protección social"] = [
    ("SL.UEM.TOTL.ZS",      "Desempleo (total)", "% de la fuerza laboral", "rel"),
    ("SL.UEM.1524.ZS",      "Desempleo juvenil (15-24)", "% de la fuerza laboral joven", "rel"),
    ("SL.UEM.TOTL.FE.ZS",   "Desempleo (mujeres)", "% de la fuerza laboral femenina", "rel"),
    ("SL.UEM.TOTL.MA.ZS",   "Desempleo (hombres)", "% de la fuerza laboral masculina", "rel"),
    ("SL.UEM.ADVN.ZS",      "Desempleo con educación avanzada", "% de ese grupo", "rel"),
    ("SL.UEM.BASC.ZS",      "Desempleo con educación básica", "% de ese grupo", "rel"),
    ("SL.TLF.CACT.ZS",      "Participación laboral (total)", "% de 15 años y más", "rel"),
    ("SL.TLF.CACT.FE.ZS",   "Participación laboral (mujeres)", "% de mujeres 15+", "rel"),
    ("SL.TLF.CACT.MA.ZS",   "Participación laboral (hombres)", "% de hombres 15+", "rel"),
    ("SL.TLF.CACT.FM.ZS",   "Participación laboral mujer/hombre", "razón %", "rel"),
    ("SL.EMP.TOTL.SP.ZS",   "Relación empleo-población", "% de 15 años y más", "rel"),
    ("SL.EMP.VULN.ZS",      "Empleo vulnerable", "% del empleo total", "rel"),
    ("SL.EMP.SELF.ZS",      "Trabajo por cuenta propia", "% del empleo total", "rel"),
    ("SL.EMP.MPYR.ZS",      "Empleadores", "% del empleo total", "rel"),
    ("SL.EMP.WORK.ZS",      "Asalariados", "% del empleo total", "rel"),
    ("SL.FAM.WORK.ZS",      "Trabajadores familiares", "% del empleo total", "rel"),
    ("SL.AGR.EMPL.ZS",      "Empleo en agricultura", "% del empleo total", "rel"),
    ("SL.IND.EMPL.ZS",      "Empleo en industria", "% del empleo total", "rel"),
    ("SL.SRV.EMPL.ZS",      "Empleo en servicios", "% del empleo total", "rel"),
    ("SL.UEM.NEET.ZS",      "Jóvenes que ni estudian ni trabajan", "% de jóvenes", "rel"),
    ("SL.TLF.TOTL.IN",      "Fuerza laboral total", "personas", "abs"),
]
CAT["Pobreza y desigualdad"] = [
    ("SI.POV.GINI",         "Índice de Gini", "0-100", "rel"),
    ("SI.POV.DDAY",         "Pobreza extrema (US$3,00/día PPA 2021)", "% de la población", "rel"),
    ("SI.POV.LMIC",         "Pobreza (US$4,20/día PPA 2021)", "% de la población", "rel"),
    ("SI.POV.UMIC",         "Pobreza (US$8,30/día PPA 2021)", "% de la población", "rel"),
    ("SI.POV.GAPS",         "Brecha de pobreza (US$3,00/día)", "%", "rel"),
    ("SI.POV.LMIC.GP",      "Brecha de pobreza (US$4,20/día)", "%", "rel"),
    ("SI.POV.UMIC.GP",      "Brecha de pobreza (US$8,30/día)", "%", "rel"),
    ("SI.POV.NAHC",         "Pobreza (línea nacional)", "% de la población", "rel"),
    ("SI.DST.FRST.10",      "Ingreso del 10% más pobre", "% del ingreso", "rel"),
    ("SI.DST.02ND.20",      "Ingreso del 2.º quintil", "% del ingreso", "rel"),
    ("SI.DST.03RD.20",      "Ingreso del 3.º quintil", "% del ingreso", "rel"),
    ("SI.DST.04TH.20",      "Ingreso del 4.º quintil", "% del ingreso", "rel"),
    ("SI.DST.05TH.20",      "Ingreso del 20% más rico", "% del ingreso", "rel"),
    ("SI.DST.10TH.10",      "Ingreso del 10% más rico", "% del ingreso", "rel"),
    ("SI.DST.50MD",         "Población bajo el 50% de la mediana", "% de la población", "rel"),
]
CAT["Medio ambiente y clima"] = [
    ("EN.GHG.CO2.PC.CE.AR5","Emisiones de CO₂ per cápita", "t por persona", "rel"),
    ("EN.GHG.ALL.PC.CE.AR5","Emisiones de GEI per cápita", "t CO₂e por persona", "rel"),
    ("EN.GHG.CO2.MT.CE.AR5","Emisiones de CO₂ (total)", "Mt CO₂e", "abs"),
    ("EN.GHG.CH4.MT.CE.AR5","Emisiones de metano (total)", "Mt CO₂e", "abs"),
    ("AG.LND.FRST.ZS",      "Superficie forestal", "% del territorio", "rel"),
    ("ER.LND.PTLD.ZS",      "Áreas protegidas terrestres", "% del territorio", "rel"),
    ("ER.MRN.PTMR.ZS",      "Áreas protegidas marinas", "% de aguas territoriales", "rel"),
    ("ER.PTD.TOTL.ZS",      "Áreas protegidas (terr. y marinas)", "% del territorio", "rel"),
    ("EN.ATM.PM25.MC.M3",   "Contaminación del aire (PM2.5)", "µg/m³", "rel"),
    ("EN.ATM.PM25.MC.ZS",   "Población expuesta a PM2.5 sobre OMS", "% de la población", "rel"),
    ("ER.H2O.FWTL.ZS",      "Extracción de agua dulce", "% de recursos internos", "rel"),
    ("ER.H2O.INTR.PC",      "Recursos de agua dulce per cápita", "m³ por persona", "rel"),
    ("AG.LND.AGRI.ZS",      "Tierra agrícola", "% del territorio", "rel"),
    ("AG.LND.ARBL.ZS",      "Tierra cultivable", "% del territorio", "rel"),
]
CAT["Energía"] = [
    ("EG.ELC.ACCS.ZS",      "Acceso a electricidad", "% de la población", "rel"),
    ("EG.CFT.ACCS.ZS",      "Acceso a combustibles limpios para cocinar", "% de la población", "rel"),
    ("EG.FEC.RNEW.ZS",      "Energía renovable", "% del consumo final", "rel"),
    ("EG.ELC.RNEW.ZS",      "Electricidad de fuentes renovables", "% de la generación", "rel"),
    ("EG.ELC.HYRO.ZS",      "Electricidad hidroeléctrica", "% de la generación", "rel"),
    ("EG.ELC.FOSL.ZS",      "Electricidad de combustibles fósiles", "% de la generación", "rel"),
    ("EG.ELC.NUCL.ZS",      "Electricidad nuclear", "% de la generación", "rel"),
    ("EG.USE.PCAP.KG.OE",   "Uso de energía per cápita", "kg equiv. petróleo", "rel"),
    ("EG.USE.ELEC.KH.PC",   "Consumo eléctrico per cápita", "kWh por persona", "rel"),
    ("NY.GDP.TOTL.RT.ZS",   "Rentas de recursos naturales", "% del PIB", "rel"),
]
CAT["Comercio y sector externo"] = [
    ("TG.VAL.TOTL.GD.ZS",   "Comercio de mercancías", "% del PIB", "rel"),
    ("NE.EXP.GNFS.ZS",      "Exportaciones de bienes y servicios", "% del PIB", "rel"),
    ("NE.IMP.GNFS.ZS",      "Importaciones de bienes y servicios", "% del PIB", "rel"),
    ("BX.KLT.DINV.WD.GD.ZS","Inversión extranjera directa (entradas)", "% del PIB", "rel"),
    ("BM.KLT.DINV.WD.GD.ZS","Inversión extranjera directa (salidas)", "% del PIB", "rel"),
    ("BX.TRF.PWKR.DT.GD.ZS","Remesas recibidas", "% del PIB", "rel"),
    ("PA.NUS.FCRF",         "Tipo de cambio oficial", "LCU por US$", "rel"),
    ("FI.RES.TOTL.MO",      "Reservas internacionales", "meses de importaciones", "rel"),
    ("TX.VAL.TECH.MF.ZS",   "Exportaciones de alta tecnología", "% de exp. manufactureras", "rel"),
    ("FD.AST.PRVT.GD.ZS",   "Crédito al sector privado", "% del PIB", "rel"),
]
CAT["Tecnología e innovación"] = [
    ("IT.NET.USER.ZS",      "Usuarios de internet", "% de la población", "rel"),
    ("IT.CEL.SETS.P2",      "Suscripciones de telefonía móvil", "por 100 personas", "rel"),
    ("IT.NET.BBND.P2",      "Banda ancha fija", "por 100 personas", "rel"),
    ("IT.MLT.MAIN.P2",      "Telefonía fija", "por 100 personas", "rel"),
    ("GB.XPD.RSDV.GD.ZS",   "Gasto en investigación y desarrollo", "% del PIB", "rel"),
    ("IP.JRN.ARTC.SC",      "Artículos científicos y técnicos", "publicaciones", "abs"),
    ("IP.PAT.RESD",         "Solicitudes de patentes (residentes)", "solicitudes", "abs"),
]
CAT["Gobernanza y sociedad"] = [
    ("GOV_WGI_VA.EST",      "Voz y rendición de cuentas", "estimación −2,5 a 2,5", "rel"),
    ("GOV_WGI_PV.EST",      "Estabilidad política y ausencia de violencia", "estimación −2,5 a 2,5", "rel"),
    ("GOV_WGI_GE.EST",      "Efectividad del gobierno", "estimación −2,5 a 2,5", "rel"),
    ("GOV_WGI_RQ.EST",      "Calidad regulatoria", "estimación −2,5 a 2,5", "rel"),
    ("GOV_WGI_RL.EST",      "Estado de derecho", "estimación −2,5 a 2,5", "rel"),
    ("GOV_WGI_CC.EST",      "Control de la corrupción", "estimación −2,5 a 2,5", "rel"),
    ("VC.IHR.PSRC.P5",      "Homicidios intencionales", "por 100.000 personas", "rel"),
    ("SG.GEN.PARL.ZS",      "Mujeres en el parlamento", "% de escaños", "rel"),
    ("MS.MIL.XPND.GD.ZS",   "Gasto militar", "% del PIB", "rel"),
    ("MS.MIL.TOTL.P1",      "Personal de las fuerzas armadas", "personas", "abs"),
    ("IQ.SPI.OVRL",         "Desempeño de los sistemas estadísticos", "índice 0-100", "rel"),
]
CAT["Desarrollo humano y bienestar"] = [
    ("HD.HCI.OVRL",         "Índice de Capital Humano", "escala 0 a 1", "rel"),
    ("SN.ITK.DEFC.ZS",      "Prevalencia de subalimentación", "% de la población", "rel"),
    ("SH.STA.STNT.ZS",      "Desnutrición crónica infantil (talla baja)", "% de menores de 5", "rel"),
    ("SH.STA.WAST.ZS",      "Emaciación infantil (bajo peso para la talla)", "% de menores de 5", "rel"),
    ("SH.STA.OWAD.ZS",      "Sobrepeso en adultos", "% de adultos", "rel"),
    ("SH.H2O.SMDW.ZS",      "Agua potable gestionada de forma segura", "% de la población", "rel"),
    ("SH.STA.SMSS.ZS",      "Saneamiento gestionado de forma segura", "% de la población", "rel"),
    ("SP.REG.BRTH.ZS",      "Registro de nacimientos", "% de menores de 5", "rel"),
    ("SH.DYN.NCOM.ZS",      "Mortalidad por enfermedades no transmisibles (30-70 a.)", "% (probabilidad)", "rel"),
    ("SH.PRG.ANEM",         "Anemia en mujeres embarazadas", "% de embarazadas", "rel"),
]

# --- Bloque generado: estructura por edad quinquenal por sexo (para pirámides) ---
RANGOS = ["0004","0509","1014","1519","2024","2529","3034","3539",
          "4044","4549","5054","5559","6064","6569","7074","7579"]
def etiqueta_rango(r):
    a, b = int(r[:2]), int(r[2:])
    return f"{a}-{b} años"
edad = []
for r in RANGOS:
    for sx, sxes in (("FE", "mujeres"), ("MA", "hombres")):
        iid = f"SP.POP.{r}.{sx}.5Y"
        edad.append((iid, f"Población {etiqueta_rango(r)} ({sxes})", "% de su sexo", "rel"))
# 80+ y mas, por sexo (formato distinto)
for sx, sxes in (("FE", "mujeres"), ("MA", "hombres")):
    edad.append((f"SP.POP.80UP.{sx}.5Y", f"Población 80 años y más ({sxes})", "% de su sexo", "rel"))
CAT["Estructura por edad (pirámide)"] = edad

# ---- Construccion + verificacion ----
out = {"source_default": "Banco Mundial — Indicadores del Desarrollo Mundial (WDI) y Worldwide Governance Indicators (WGI)",
       "categories": [], "indicators": []}
missing, weak = [], []
for cat, items in CAT.items():
    n_ok = 0
    for (iid, name_es, unit, kind) in items:
        rec = cov.get(iid)
        if rec is None:
            missing.append((cat, iid, name_es))
            continue
        c = rec["coverage_pct"]; y = rec.get("latest_year_median")
        if c < 60:
            weak.append((cat, iid, name_es, c, y))
        dd = DEFS.get(iid, {})
        out["indicators"].append({
            "id": iid, "name": name_es, "unit": unit, "category": cat,
            "type": kind, "coverage_pct": c, "latest_year_median": y,
            "latest_year_max": rec.get("latest_year_max"), "wb_name": rec["name"],
            "def": dd.get("def", ""), "org": dd.get("org", ""),
        })
        n_ok += 1
    out["categories"].append({"name": cat, "count": n_ok})

with open(os.path.join(DATA, "catalog.json"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=1)

total = len(out["indicators"])
print(f"CATALOGO CURADO AMPLIADO: {total} indicadores en {len(CAT)} categorias\n")
for c in out["categories"]:
    print(f"  {c['count']:3d}  {c['name']}")
covs = [i["coverage_pct"] for i in out["indicators"]]
print(f"\nCobertura promedio: {sum(covs)/len(covs):.1f}%  |  >=90%: {sum(1 for x in covs if x>=90)}/{total}  |  >=80%: {sum(1 for x in covs if x>=80)}/{total}")
if missing:
    print(f"\n[!] IDs no encontrados ({len(missing)}) -> se omiten, revisar:")
    for cat, iid, n in missing:
        print(f"      {iid:<22} {n}  ({cat})")
if weak:
    print(f"\n[!] Cobertura < 60% ({len(weak)}):")
    for cat, iid, n, c, y in weak:
        print(f"      {c:5.1f}% {y}  {iid:<20} {n}")
print(f"\nGuardado: {os.path.join(DATA,'catalog.json')}")
