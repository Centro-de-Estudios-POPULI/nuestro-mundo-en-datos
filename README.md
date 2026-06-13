# Nuestro Mundo en Datos

Atlas interactivo de **mapas coropléticos mundiales en español**, para investigadores,
periodistas y curiosos del mundo hispano. Cientos de indicadores globales con render
editorial (D3 + TopoJSON), buscador por temas y línea de tiempo.

Un proyecto del **Centro de Estudios POPULI**.

## Por qué

Iniciativas como **[Our World in Data](https://ourworldindata.org)**,
**[Gapminder](https://www.gapminder.org)** y los grandes índices globales
(**[Banco Mundial](https://data.worldbank.org)**, **[V-Dem](https://v-dem.net)**, etc.)
transformaron el acceso público a los datos del mundo — pero casi siempre en inglés.
Pese a lo extendido del idioma, sigue siendo una barrera real para millones de
hispanohablantes. *Nuestro Mundo en Datos* retoma esa misión y la traduce —
literal y editorialmente — al español, con las debidas referencias y crédito a
quienes la inspiraron.

## Cómo funciona

```
scripts/
  coverage_sweep.py    Mide cobertura por país de TODO el catálogo WDI -> data/coverage.json
  build_indicators.py  Descarga la API del WB y reempaqueta a JSON compacto (~50 KB/indicador)
data/
  world-110m.topojson  Mapa base del mundo (una vez, cacheado)
  coverage.json        Evidencia de cobertura para curar el catálogo
  catalog.json         Índice curado de indicadores (id, nombre, tema, fuente)
  indicators/*.json    Un archivo por indicador, carga diferida
src/                   Motor D3 de coropleta (proyección, escala, leyenda, timeline, tooltip)
index.html             Explorador con buscador + categorías
.github/workflows/     Refresco automático de datos
```

**Peso / rendimiento:** los datos se pre-generan en formato compacto y se sirven con
gzip. El visitante descarga solo el indicador del mapa que abre (~50 KB con historia
completa) más el mapa base (~105 KB, cacheado). Funciona en GitHub Pages, sin backend.

## Fuentes y atribución

- **Banco Mundial — World Development Indicators** ([data.worldbank.org](https://data.worldbank.org)) · CC BY 4.0
- *(en hoja de ruta)* **V-Dem** — Varieties of Democracy
- *(en hoja de ruta)* otros índices mundiales

Inspirado en Our World in Data y Gapminder.

## Estado

🚧 En construcción. Fase 0 (barrido de cobertura) → curaduría del catálogo → motor de mapa.
