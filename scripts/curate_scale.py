"""
curate_scale.py — Añade a catalog.json el tipo de escala y la valencia de cada
indicador, para que los mapas (web + motor de imágenes) elijan paleta y
clasificación de forma coherente y honesta.

Campos que escribe por indicador:
  scale     : "divergente" (centrado en 0) | "secuencial"
  direction : "mejor" (más alto = mejor) | "peor" (más alto = peor) | "neutro"
  family    : rampa de marca POPULI -> "verde" | "calido" | "azul" | "divergente"

Convención de color (decisión 2026-06-15, "valencia: oscuro = peor"):
  - oscuro = valor ALTO siempre (honesto);
  - el MATIZ codifica la valencia:  mejor->verde, peor->calido, neutro->azul,
    divergente->rampa divergente anclada en 0.

Uso:
    python scripts/curate_scale.py           # DRY-RUN: imprime la clasificación
    python scripts/curate_scale.py --write    # escribe catalog.json (+ .bak)
"""
import json
import sys
from pathlib import Path
from collections import Counter

CATALOG = Path(__file__).resolve().parent.parent / "data" / "catalog.json"

# --- 10 divergentes genuinos (centrados en 0) ----------------------------- #
DIVERGENTE = {
    "GOV_WGI_VA.EST", "GOV_WGI_PV.EST", "GOV_WGI_GE.EST",
    "GOV_WGI_RQ.EST", "GOV_WGI_RL.EST", "GOV_WGI_CC.EST",   # gobernanza WGI
    "NY.GDP.PCAP.KD.ZG", "NY.GDP.MKTP.KD.ZG", "SP.POP.GROW",  # crecimientos
    "SM.POP.NETM",                                            # migración neta
}

# --- más alto = PEOR (rampa cálida/roja, oscuro = alerta) ------------------ #
PEOR = {
    # mortalidad / salud adversa
    "SP.DYN.IMRT.IN", "SH.DYN.MORT", "SH.DYN.NMRT", "SH.STA.MMRT", "SP.DYN.CDRT.IN",
    "SH.STA.SUIC.P5", "VC.IHR.PSRC.P5", "SH.TBS.INCD", "SH.DYN.AIDS.ZS", "SH.DYN.NCOM.ZS",
    # nutrición adversa
    "SN.ITK.DEFC.ZS", "SH.STA.STNT.ZS", "SH.STA.WAST.ZS", "SH.STA.OWAD.ZS",
    "SH.PRG.ANEM", "SH.STA.ODFC.ZS",
    # pobreza y desigualdad
    "SI.POV.DDAY", "SI.POV.LMIC", "SI.POV.UMIC", "SI.POV.GAPS", "SI.POV.LMIC.GP",
    "SI.POV.UMIC.GP", "SI.POV.NAHC", "SI.POV.GINI", "SI.DST.50MD",
    # desempleo y empleo vulnerable
    "SL.UEM.TOTL.ZS", "SL.UEM.1524.ZS", "SL.UEM.TOTL.FE.ZS", "SL.UEM.TOTL.MA.ZS",
    "SL.UEM.ADVN.ZS", "SL.UEM.BASC.ZS", "SL.UEM.NEET.ZS", "SL.EMP.VULN.ZS",
    # inflación
    "FP.CPI.TOTL.ZG", "NY.GDP.DEFL.KD.ZG",
    # ambiente adverso
    "EN.GHG.CO2.PC.CE.AR5", "EN.GHG.ALL.PC.CE.AR5", "EN.GHG.CO2.MT.CE.AR5",
    "EN.GHG.CH4.MT.CE.AR5", "EN.ATM.PM25.MC.M3", "EN.ATM.PM25.MC.ZS",
    "ER.H2O.FWTL.ZS", "EG.ELC.FOSL.ZS",
    # otros donde más = peor
    "GC.DOD.TOTL.GD.ZS", "SP.ADO.TFRT", "SE.PRM.ENRL.TC.ZS",
}

# --- más alto = MEJOR (rampa verde/teal, oscuro = bueno) ------------------- #
MEJOR = {
    # salud / agua / saneamiento positivos
    "SP.DYN.LE00.IN", "SP.DYN.LE00.FE.IN", "SP.DYN.LE00.MA.IN",
    "SH.MED.PHYS.ZS", "SH.MED.BEDS.ZS", "SH.IMM.MEAS", "SH.IMM.IDPT", "SP.REG.BRTH.ZS",
    "SH.H2O.BASW.ZS", "SH.STA.BASS.ZS", "SH.H2O.SMDW.ZS", "SH.STA.SMSS.ZS",
    "SH.XPD.CHEX.GD.ZS", "SH.XPD.CHEX.PC.CD",
    # educación
    "SE.ADT.LITR.ZS", "SE.ADT.1524.LT.ZS", "SE.PRM.ENRR", "SE.SEC.ENRR", "SE.TER.ENRR",
    "SE.PRE.ENRR", "SE.PRM.CMPT.ZS", "SE.XPD.TOTL.GD.ZS",
    # ingreso / productividad / capital humano
    "NY.GDP.PCAP.CD", "NY.GDP.PCAP.PP.CD", "NY.GDP.PCAP.KD", "NY.GNP.PCAP.CD",
    "NY.GNP.PCAP.PP.CD", "HD.HCI.OVRL", "MPD.GDPPC", "PWT.GDPPC", "PWT.GDPWK",
    "PWT.HC", "PWT.CTFP", "SI.DST.FRST.10",
    # energía / acceso
    "EG.ELC.ACCS.ZS", "EG.CFT.ACCS.ZS", "EG.FEC.RNEW.ZS", "EG.ELC.RNEW.ZS",
    # tecnología e innovación
    "IT.NET.USER.ZS", "IT.CEL.SETS.P2", "IT.NET.BBND.P2", "IT.MLT.MAIN.P2",
    "GB.XPD.RSDV.GD.ZS", "IP.JRN.ARTC.SC", "IP.PAT.RESD", "TX.VAL.TECH.MF.ZS",
    # ambiente positivo
    "AG.LND.FRST.ZS", "ER.LND.PTLD.ZS", "ER.MRN.PTMR.ZS", "ER.PTD.TOTL.ZS",
    # gobernanza / finanzas / inversión / empleo formal
    "SG.GEN.PARL.ZS", "IQ.SPI.OVRL", "FI.RES.TOTL.MO", "FD.AST.PRVT.GD.ZS",
    "SL.TLF.CACT.ZS", "SL.TLF.CACT.FE.ZS", "SL.EMP.TOTL.SP.ZS", "SL.EMP.WORK.ZS",
    "SL.EMP.MPYR.ZS", "NY.GNS.ICTR.ZS", "NE.GDI.TOTL.ZS",
}

FAMILY = {"mejor": "verde", "peor": "calido", "neutro": "azul", "divergente": "divergente"}


def clasifica(iid):
    if iid in DIVERGENTE:
        return "divergente", "divergente"
    if iid in PEOR:
        return "secuencial", "peor"
    if iid in MEJOR:
        return "secuencial", "mejor"
    return "secuencial", "neutro"


def main():
    write = "--write" in sys.argv
    cat = json.loads(CATALOG.read_text(encoding="utf-8"))
    cnt = Counter()
    grupos = {"divergente": [], "peor": [], "mejor": [], "neutro": []}
    for x in cat["indicators"]:
        scale, direction = clasifica(x["id"])
        x["scale"] = scale
        x["direction"] = direction
        x["family"] = FAMILY[direction]
        cnt[direction] += 1
        grupos[direction].append((x["id"], x["name"]))

    for k in ("divergente", "peor", "mejor", "neutro"):
        print(f"\n===== {k.upper()}  ({cnt[k]}) =====")
        for iid, name in grupos[k]:
            print(f"  {iid:<22} {name}")
    print(f"\nTOTAL: {sum(cnt.values())} indicadores")

    if write:
        bak = CATALOG.with_suffix(".json.bak")
        bak.write_text(CATALOG.read_text(encoding="utf-8"), encoding="utf-8")
        CATALOG.write_text(json.dumps(cat, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\nESCRITO catalog.json (backup en {bak.name})")
    else:
        print("\n(DRY-RUN — sin escribir; usa --write para aplicar)")


if __name__ == "__main__":
    main()
