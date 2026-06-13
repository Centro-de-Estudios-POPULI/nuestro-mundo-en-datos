# -*- coding: utf-8 -*-
"""
fill_missing_defs.py — Completa a mano las definiciones (def) y fuentes (org) en
español de los indicadores que el Banco Mundial NO entrega traducidas vía su API
/v2/es/. Traducciones fieles a la metadata oficial en inglés (api.worldbank.org).

Uso:  python scripts/fill_missing_defs.py
Idempotente: solo rellena los 21 ids del diccionario; no toca el resto del catálogo.
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG = os.path.join(ROOT, "data", "catalog.json")

# Fuentes reutilizables
JMP = ("Programa Conjunto OMS/UNICEF de Monitoreo del Abastecimiento de Agua, "
       "Saneamiento e Higiene (JMP).")
EDGAR = ("Base de Datos Comunitaria de GEI EDGAR, Centro Común de Investigación (JRC) "
         "de la Comisión Europea; Agencia Internacional de Energía (AIE).")
NACC = ("Estadísticas oficiales de los países y bancos centrales; archivos de Cuentas "
        "Nacionales de la OCDE; estimaciones del personal del Banco Mundial.")
WGI = "Indicadores Mundiales de Gobernanza (WGI), Banco Mundial."

# Intro común para los seis WGI; cada dimensión agrega su párrafo específico.
WGI_INTRO = ("Indicador de los Indicadores Mundiales de Gobernanza (WGI) del Banco Mundial, "
             "que resumen la percepción sobre la calidad de la gobernanza a partir de numerosas "
             "encuestas a empresas, ciudadanos y expertos. ")
WGI_SCALE = (" El valor (estimate) expresa la puntuación del país en unidades de una distribución "
             "normal estándar, aproximadamente entre -2,5 y +2,5 (a mayor valor, mejor gobernanza).")

DEFS = {
"NE.CON.PRVT.ZS": (
    "Gasto en bienes y servicios realizado por los hogares y las instituciones sin fines de lucro "
    "que sirven a los hogares (ISFLSH) para la satisfacción directa de necesidades humanas, "
    "individuales o colectivas. Se expresa como porcentaje del producto interno bruto (PIB), es "
    "decir, del ingreso total generado por la producción de bienes y servicios en un territorio "
    "económico durante un período contable.", NACC),
"NV.SRV.TOTL.ZS": (
    "Las actividades de servicios corresponden a las divisiones 45 a 99 de la CIIU (Rev. 4) e "
    "incluyen comercio mayorista y minorista, reparación de vehículos, hoteles y restaurantes, "
    "transporte, almacenamiento y comunicaciones, intermediación financiera, actividades "
    "inmobiliarias y empresariales, administración pública y defensa, seguridad social obligatoria, "
    "educación, salud y trabajo social, otros servicios comunitarios y personales, y los hogares con "
    "personas empleadas. El valor agregado es el aporte de cada sector a la economía: el valor total "
    "de la producción menos el consumo intermedio de bienes y servicios usados para generarla. Se "
    "expresa como porcentaje del producto interno bruto (PIB).", NACC),
"SH.XPD.CHEX.PC.CD": (
    "Gasto corriente en salud por persona, en dólares estadounidenses corrientes. Incluye los bienes "
    "y servicios sanitarios consumidos durante cada año.",
    "Base de Datos Mundial de Gasto en Salud, Organización Mundial de la Salud (OMS)."),
"SH.H2O.BASW.ZS": (
    "Porcentaje de personas que usan al menos servicios básicos de agua potable; abarca tanto a "
    "quienes acceden a servicios básicos como a quienes cuentan con servicios gestionados de forma "
    "segura. El servicio básico se define como agua potable proveniente de una fuente mejorada cuyo "
    "tiempo de recolección no supere los 30 minutos de ida y vuelta. Las fuentes mejoradas incluyen "
    "agua por tubería, pozos entubados o perforaciones, pozos excavados protegidos, manantiales "
    "protegidos y agua envasada o suministrada.", JMP),
"SH.STA.BASS.ZS": (
    "Porcentaje de personas que usan al menos servicios básicos de saneamiento, es decir, "
    "instalaciones mejoradas no compartidas con otros hogares; abarca tanto a quienes acceden a "
    "servicios básicos como a quienes cuentan con servicios gestionados de forma segura. Las "
    "instalaciones mejoradas incluyen inodoros conectados a alcantarillado, fosas sépticas o letrinas "
    "de pozo; letrinas de pozo mejoradas con ventilación, inodoros composteros y letrinas de pozo con "
    "losa.", JMP),
"SI.DST.50MD": (
    "Porcentaje de la población que vive en hogares cuyo ingreso o consumo per cápita es inferior a "
    "la mitad de la mediana nacional. La mediana se mide en paridad de poder adquisitivo (PPA) de "
    "2021 mediante la Plataforma de Pobreza y Desigualdad del Banco Mundial. En algunos países no se "
    "reporta por tratarse de datos agrupados o confidenciales. El año de referencia es aquel en que "
    "se recolectó la encuesta de hogares subyacente.",
    "Plataforma de Pobreza y Desigualdad, Banco Mundial (datos de encuestas de hogares de organismos "
    "estadísticos nacionales)."),
"EN.GHG.CO2.PC.CE.AR5": (
    "Emisiones anuales totales de dióxido de carbono (CO₂) —uno de los seis gases de efecto "
    "invernadero del Protocolo de Kioto— provenientes de los sectores de agricultura, energía, "
    "residuos e industria, excluyendo el uso de la tierra, cambio de uso de la tierra y silvicultura "
    "(LULUCF), expresadas en CO₂ equivalente y divididas por la población. Se excluyen los flujos de "
    "LULUCF por tener mayor incertidumbre.", EDGAR),
"EN.GHG.ALL.PC.CE.AR5": (
    "Emisiones anuales totales de los seis gases de efecto invernadero del Protocolo de Kioto (CO₂, "
    "metano (CH₄), óxido nitroso (N₂O), hidrofluorocarbonos (HFC), perfluorocarbonos (PFC) y "
    "hexafluoruro de azufre (SF₆)) de los sectores de energía, industria, residuos y agricultura, "
    "expresadas en CO₂ equivalente y divididas por la población. Se excluyen los flujos de LULUCF por "
    "tener mayor incertidumbre.", EDGAR),
"EN.GHG.CO2.MT.CE.AR5": (
    "Emisiones anuales de dióxido de carbono (CO₂) —uno de los seis gases de efecto invernadero del "
    "Protocolo de Kioto— de los sectores de agricultura, energía, residuos e industria, excluyendo "
    "LULUCF. Se expresan en CO₂ equivalente usando los factores de Potencial de Calentamiento Global "
    "(PCG) del Quinto Informe de Evaluación del IPCC (AR5).", EDGAR),
"EN.GHG.CH4.MT.CE.AR5": (
    "Emisiones anuales de metano (CH₄) —uno de los seis gases de efecto invernadero del Protocolo de "
    "Kioto— de los sectores de agricultura, energía, residuos e industria, excluyendo LULUCF. Se "
    "expresan en CO₂ equivalente usando los factores de Potencial de Calentamiento Global (PCG) del "
    "Quinto Informe de Evaluación del IPCC (AR5).", EDGAR),
"GOV_WGI_VA.EST": (
    WGI_INTRO + "«Voz y rendición de cuentas» capta la percepción sobre el grado en que los "
    "ciudadanos pueden participar en la elección de su gobierno, así como la libertad de expresión, "
    "la libertad de asociación y la existencia de medios de comunicación libres." + WGI_SCALE, WGI),
"GOV_WGI_PV.EST": (
    WGI_INTRO + "«Estabilidad política y ausencia de violencia» mide la percepción sobre la "
    "probabilidad de inestabilidad política o de violencia por motivos políticos, incluido el "
    "terrorismo." + WGI_SCALE, WGI),
"GOV_WGI_GE.EST": (
    WGI_INTRO + "«Efectividad del gobierno» capta la percepción sobre la calidad de los servicios "
    "públicos, la calidad de la función pública y su grado de independencia de las presiones "
    "políticas, la calidad de la formulación e implementación de políticas, y la credibilidad del "
    "compromiso del gobierno con dichas políticas." + WGI_SCALE, WGI),
"GOV_WGI_RQ.EST": (
    WGI_INTRO + "«Calidad regulatoria» capta la percepción sobre la capacidad del gobierno para "
    "formular e implementar políticas y regulaciones sólidas que permitan y promuevan el desarrollo "
    "del sector privado." + WGI_SCALE, WGI),
"GOV_WGI_RL.EST": (
    WGI_INTRO + "«Estado de derecho» capta la percepción sobre el grado en que los agentes confían y "
    "respetan las reglas de la sociedad, en particular la calidad del cumplimiento de los contratos, "
    "los derechos de propiedad, la policía y los tribunales, así como la probabilidad de delitos y "
    "violencia." + WGI_SCALE, WGI),
"GOV_WGI_CC.EST": (
    WGI_INTRO + "«Control de la corrupción» capta la percepción sobre el grado en que el poder "
    "público se ejerce para beneficio privado, incluidas tanto la corrupción menor como la de gran "
    "escala, así como la «captura» del Estado por las élites y los intereses privados." + WGI_SCALE, WGI),
"IQ.SPI.OVRL": (
    "Puntuación general de los Indicadores de Desempeño Estadístico (SPI), una medida compuesta del "
    "desempeño de cada país en cinco pilares: uso de datos, servicios de datos, productos de datos, "
    "fuentes de datos e infraestructura de datos. Los SPI reemplazan al Índice de Capacidad "
    "Estadística (SCI) que el Banco Mundial publicaba desde 2004, ampliando la medición a áreas como "
    "el uso de datos, los datos administrativos y geoespaciales, y la infraestructura estadística. La "
    "escala va de 0 a 100.",
    "Indicadores de Desempeño Estadístico (SPI), Banco Mundial."),
"HD.HCI.OVRL": (
    "El Índice de Capital Humano (ICH) calcula el aporte de la salud y la educación a la "
    "productividad de los trabajadores. La puntuación final va de 0 a 1 y mide la productividad como "
    "futuro trabajador de un niño nacido hoy, en relación con el ideal de salud plena y educación "
    "completa.",
    "Cálculos del personal del Banco Mundial según la metodología del Proyecto de Capital Humano "
    "(Banco Mundial, 2018)."),
"SH.STA.OWAD.ZS": (
    "Prevalencia de sobrepeso: porcentaje de adultos de 18 años o más cuyo Índice de Masa Corporal "
    "(IMC) supera los 25 kg/m². El IMC es un índice simple de peso para la talla: el peso en "
    "kilogramos dividido por el cuadrado de la estatura en metros.",
    "Organización Mundial de la Salud (OMS), Observatorio Mundial de la Salud."),
"SH.H2O.SMDW.ZS": (
    "Porcentaje de personas que usan agua potable de una fuente mejorada accesible en el lugar de "
    "uso, disponible cuando se necesita y libre de contaminación fecal y química prioritaria. Las "
    "fuentes mejoradas incluyen agua por tubería, pozos entubados o perforaciones, pozos excavados "
    "protegidos, manantiales protegidos y agua envasada o suministrada.", JMP),
"SH.STA.SMSS.ZS": (
    "Porcentaje de personas que usan instalaciones de saneamiento mejoradas, no compartidas con "
    "otros hogares, en las que las excretas se eliminan de forma segura in situ o se transportan y "
    "tratan fuera del sitio. Las instalaciones mejoradas incluyen inodoros conectados a "
    "alcantarillado, fosas sépticas o letrinas de pozo; letrinas de pozo mejoradas con ventilación, "
    "inodoros composteros y letrinas de pozo con losa.", JMP),
}


def main():
    with open(CATALOG, encoding="utf-8") as f:
        cat = json.load(f)
    by_id = {d["id"]: d for d in cat["indicators"]}
    updated, missing = [], []
    for iid, (definition, org) in DEFS.items():
        if iid not in by_id:
            missing.append(iid)
            continue
        item = by_id[iid]
        item["def"] = definition
        if not (item.get("org") or "").strip():
            item["org"] = org
        updated.append(iid)
    with open(CATALOG, "w", encoding="utf-8") as f:
        json.dump(cat, f, ensure_ascii=False, indent=2)
    remaining = [d["id"] for d in cat["indicators"] if not (d.get("def") or "").strip()]
    print(f"Definiciones actualizadas: {len(updated)}")
    if missing:
        print(f"IDs no encontrados en el catálogo: {missing}")
    print(f"Indicadores que SIGUEN sin def: {len(remaining)} {remaining}")


if __name__ == "__main__":
    main()
