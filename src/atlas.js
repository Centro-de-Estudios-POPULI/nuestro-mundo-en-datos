/* Nuestro Mundo en Datos — motor de mapas coropléticos (D3 v7) */
(function () {
  "use strict";

  const PAD = 6;
  const svg = d3.select("#map");
  const gMap = svg.append("g");
  const tip = d3.select("#tip");
  // ---- formato de números (español) ----
  // compacto para la leyenda (termómetro): 150k · 100M · 1,4 mil M · 12,3 B
  function fmtTick(v, suf) {
    if (v == null || isNaN(v)) return "";
    let u = "";
    const a = Math.abs(v);
    if (a >= 1e12) { v /= 1e12; u = " B"; }
    else if (a >= 1e9) { v /= 1e9; u = " mil M"; }
    else if (a >= 1e6) { v /= 1e6; u = "M"; }
    else if (a >= 1e3) { v /= 1e3; u = "k"; }
    const sa = Math.abs(v);
    const d = u ? 1 : (sa >= 100 ? 0 : sa >= 1 ? 1 : 2);
    let s = v.toFixed(d);
    if (s.indexOf(".") >= 0) s = s.replace(/0+$/, "").replace(/\.$/, "");
    return s.replace(".", ",") + u + (suf || "");
  }
  // completo para el tooltip: miles con "." y decimal con "," (1.234,5);
  // de un millón en adelante usa el compacto para no alargar.
  function fmt(v) {
    if (v == null || isNaN(v)) return "s/d";
    const a = Math.abs(v);
    if (a >= 1e6) return fmtTick(v);
    const dd = a >= 100 ? 0 : a >= 1 ? 1 : 2;
    return d3.format(`,.${dd}f`)(v).replace(/,/g, "·").replace(".", ",").replace(/·/g, ".");
  }

  const state = {
    catalog: null, crosswalk: null, countries: null, sphere: null,
    nameById: {}, ind: null, data: null, year: null, latest: false, playing: null, color: null
  };

  // Proyección Natural Earth (editorial, baja distorsión)
  const projection = d3.geoNaturalEarth1();
  const path = d3.geoPath(projection);

  // Zoom / paneo
  const zoom = d3.zoom().scaleExtent([1, 8]).on("zoom", e => gMap.attr("transform", e.transform));
  svg.call(zoom);

  Promise.all([
    fetch("data/catalog.json").then(r => r.json()),
    fetch("data/iso-crosswalk.json").then(r => r.json()),
    fetch("data/world-110m.topojson").then(r => r.json()),
    fetch("data/regions.json").then(r => r.json())
  ]).then(([catalog, crosswalk, topo, regions]) => {
    state.catalog = catalog;
    state.crosswalk = crosswalk;
    state.regions = regions;
    const geo = topojson.feature(topo, topo.objects.countries);
    state.countries = geo.features;
    state.sphere = { type: "Sphere" };
    // ISO3 por geometría (vía crosswalk numérico; Kosovo por nombre) + nombre en español
    state.countries.forEach(f => {
      const num = f.id != null ? String(parseInt(f.id, 10)) : null;
      let iso = num && crosswalk[num] ? crosswalk[num] : null;
      if (!iso && f.properties && f.properties.name === "Kosovo") iso = "XKX";
      f.iso3 = iso;
      f.nameEs = (iso && regions[iso] && regions[iso].name) || (f.properties && f.properties.name);
    });
    sizeMap();
    drawBase();
    buildSidebar();
    window.addEventListener("resize", () => { clearTimeout(state._rz); state._rz = setTimeout(sizeMap, 150); });
    document.getElementById("indSub").textContent =
      `${catalog.indicators.length} indicadores · 217 países · elige uno para ver el mapa`;
  }).catch(err => {
    document.getElementById("indTitle").textContent = "No se pudieron cargar los datos";
    document.getElementById("indSub").textContent =
      "Si abriste el archivo con doble clic, sírvelo con un servidor local (ver README).";
    console.error(err);
  });

  // Ajusta el viewBox y la proyección al tamaño real del contenedor (sin franjas ni recortes)
  function sizeMap() {
    const wrap = document.querySelector(".mapwrap");
    if (!wrap) return;
    const w = Math.max(320, Math.round(wrap.clientWidth));
    const h = Math.max(240, Math.round(wrap.clientHeight));
    svg.attr("viewBox", `0 0 ${w} ${h}`);
    projection.fitExtent([[PAD, PAD], [w - PAD, h - PAD]], state.sphere);
    gMap.attr("transform", null);
    svg.call(zoom.transform, d3.zoomIdentity);
    gMap.select("path.sphere").attr("d", path(state.sphere));
    gMap.selectAll("path.country").attr("d", path);
  }

  function drawBase() {
    gMap.append("path").attr("class", "sphere").attr("d", path(state.sphere));
    gMap.selectAll("path.country").data(state.countries).join("path")
      .attr("class", "country nodata").attr("d", path)
      .on("mousemove", onHover).on("mouseleave", () => tip.style("opacity", 0));
  }

  // ---------- Sidebar ----------
  function buildSidebar() {
    const byCat = d3.group(state.catalog.indicators, d => d.category);
    const host = d3.select("#catlist");
    state.catalog.categories.forEach(c => {
      const items = byCat.get(c.name) || [];
      const box = host.append("div").attr("class", "cat").attr("data-cat", c.name);
      box.append("h3").html(`<span>${c.name}</span><span class="n">${items.length}</span>`)
        .on("click", function () {
          const sib = this.parentNode.querySelectorAll(".ind");
          sib.forEach(el => el.style.display = el.style.display === "none" ? "" : "none");
        });
      items.forEach(d => {
        box.append("div").attr("class", "ind").attr("data-id", d.id).attr("data-name", d.name.toLowerCase())
          .html(`<span>${d.name}</span><span class="cov">${Math.round(d.coverage_pct)}%</span>`)
          .on("click", () => selectIndicator(d.id));
      });
    });
    document.getElementById("q").addEventListener("input", onSearch);
    document.getElementById("menuBtn").addEventListener("click", () =>
      document.getElementById("nav").classList.toggle("open"));
    document.querySelectorAll(".nav-mobile a").forEach(a =>
      a.addEventListener("click", () => document.getElementById("nav").classList.remove("open")));
  }

  function onSearch(e) {
    const q = e.target.value.trim().toLowerCase();
    document.querySelectorAll(".ind").forEach(el => {
      el.style.display = !q || el.dataset.name.includes(q) ? "" : "none";
    });
    document.querySelectorAll(".cat").forEach(cat => {
      const any = [...cat.querySelectorAll(".ind")].some(el => el.style.display !== "none");
      cat.style.display = any ? "" : "none";
    });
  }

  // ---------- Selección de indicador ----------
  function selectIndicator(id) {
    const meta = state.catalog.indicators.find(d => d.id === id);
    document.querySelectorAll(".ind").forEach(el => el.classList.toggle("active", el.dataset.id === id));
    fetch(`data/indicators/${id}.json`).then(r => r.json()).then(raw => {
      state.ind = meta; state.data = raw;
      buildColor(raw, meta);
      // conteo de entidades con dato por año -> año por defecto reciente y "poblado"
      const counts = raw.years.map((y, i) =>
        Object.values(raw.data).reduce((a, arr) => a + (arr[i] != null ? 1 : 0), 0));
      state.sliderYears = raw.years.filter((y, i) => counts[i] > 0);
      const maxC = Math.max(...counts);
      const nAny = Object.values(raw.data).filter(arr => arr.some(v => v != null)).length;
      let pos = state.sliderYears.length - 1;
      for (let p = state.sliderYears.length - 1; p >= 0; p--) {
        if (counts[raw.years.indexOf(state.sliderYears[p])] >= 0.5 * maxC) { pos = p; break; }
      }
      // datos de encuesta (sin un año bien cubierto) -> "último disponible" automático
      const autoLatest = (maxC / nAny) < 0.6;
      state.latest = autoLatest;
      document.getElementById("latest").checked = autoLatest;
      const sl = document.getElementById("yr");
      sl.disabled = autoLatest; document.getElementById("playBtn").disabled = autoLatest;
      sl.min = 0; sl.max = state.sliderYears.length - 1; sl.value = pos;
      state.year = state.sliderYears[pos];
      document.getElementById("controls").style.display = "";
      document.getElementById("legend").style.display = "";
      document.getElementById("indTitle").textContent = meta.name;
      document.getElementById("indSub").textContent =
        `${meta.unit} · ${meta.category} · cobertura ${Math.round(meta.coverage_pct)}%`;
      document.getElementById("indSrc").textContent =
        "Fuente: " + (meta.org || state.catalog.source_default);
      const db = document.getElementById("defBox");
      if (meta.def) {
        document.getElementById("defText").textContent = meta.def;
        document.getElementById("defOrg").textContent = meta.org ? "Organización fuente: " + meta.org : "";
        db.style.display = ""; db.open = false;
      } else { db.style.display = "none"; }
      sizeMap();
      render();
    });
  }

  // ---- escala de color: rampas de marca POPULI ----
  const RAMPS = {
    calido:     ["#F6E6BE", "#E6B24A", "#CF7B33", "#B23A2C", "#8B1A1A", "#5E1010"],
    rojo:       ["#F3D9D2", "#D98E80", "#BC4B3F", "#8B1A1A", "#5E1010"],
    azul:       ["#E6EAEF", "#A9B7C6", "#647D97", "#3A516B", "#22344A"],
    verde:      ["#E3EDEA", "#9AC4B9", "#4F9E90", "#2C7468", "#16504A"],
    divergente: ["#3A516B", "#7E94A8", "#EFE7D6", "#CB7A6D", "#8B1A1A"],
  };
  const NBINS = 7;
  const rampColors = (name, n) => {
    const ip = d3.interpolateRgbBasis(RAMPS[name] || RAMPS.calido);
    return d3.range(n).map(i => ip(n === 1 ? 0.5 : i / (n - 1)));
  };

  // scale "divergente" -> anclada en 0 (slate-crema-rojo); si no, secuencial por
  // cuantiles con la familia de marca del indicador (verde/calido/azul) según valencia.
  function buildColor(raw, meta) {
    // SOLO países reales: excluir los agregados del Banco Mundial (Mundo, regiones y
    // grupos de ingreso: WLD, HIC, EUU, OED…). No se dibujan en el mapa, pero
    // contaminaban la escala/leyenda (p. ej. población mundial = 8,1 mil M).
    const reg = state.regions || {};
    const vals = [];
    for (const k in raw.data) {
      if (!(k in reg)) continue;
      for (const v of raw.data[k]) if (v != null) vals.push(v);
    }
    vals.sort(d3.ascending);
    const ext = [vals[0], vals[vals.length - 1]];
    if (meta.scale === "divergente") {
      const m = Math.max(Math.abs(ext[0]), Math.abs(ext[1])) || 1;
      const cols = rampColors("divergente", 7);          // índice 3 = crema (cero)
      const t = [-m * .5, -m * .2, -m * .05, m * .05, m * .2, m * .5];
      state.color = { type: "div", cols, dom: [-m, m], of: v => cols[d3.bisect(t, v)] };
    } else {
      const cols = rampColors(meta.family || "calido", NBINS);
      const q = d3.scaleQuantile().domain(vals).range(d3.range(NBINS));
      state.color = { type: "seq", cols, dom: ext,
                      edges: [ext[0], ...q.quantiles(), ext[1]], of: v => cols[q(v)] };
    }
    buildLegend(meta);
  }

  function buildLegend(meta) {
    const c = state.color;
    const suf = (meta.unit && meta.unit.indexOf("%") >= 0) ? "%" : "";
    const bins = d3.select("#legendBins").html("");
    c.cols.forEach(col => bins.append("span").style("background", col));
    // marcas de valor SOBRE la barra, alineadas a cada borde de bin
    const ticks = c.type === "div" ? [c.dom[0], 0, c.dom[1]] : c.edges;
    const td = d3.select("#legendTicks").html("");
    const n = ticks.length;
    ticks.forEach((d, i) => {
      const sp = td.append("span").text(fmtTick(d, suf))
        .style("left", (n === 1 ? 50 : (i / (n - 1)) * 100) + "%");
      if (i === 0) sp.style("transform", "translateX(0)");
      else if (i === n - 1) sp.style("transform", "translateX(-100%)");
    });
  }

  // ---------- Render ----------
  function valueFor(iso) {
    const raw = state.data;
    if (!iso || !raw.data[iso]) return { v: null, y: null };
    const arr = raw.data[iso];
    if (state.latest) {
      for (let i = arr.length - 1; i >= 0; i--) if (arr[i] != null) return { v: arr[i], y: raw.years[i] };
      return { v: null, y: null };
    }
    const idx = raw.years.indexOf(state.year);
    return { v: arr[idx], y: state.year };
  }

  function render() {
    const meta = state.ind;
    document.getElementById("yrLabel").textContent = state.latest ? "—" : state.year;
    gMap.selectAll("path.country")
      .each(function (f) { f._cur = valueFor(f.iso3); })
      .attr("class", f => "country" + (f._cur.v == null ? " nodata" : ""))
      .transition().duration(250)
      .attr("fill", f => f._cur.v == null ? null : state.color.of(f._cur.v));
  }

  // Mini serie histórica del país (estilo Our World in Data)
  function sparkSVG(iso, curYear) {
    const arr = state.data && state.data.data[iso];
    if (!arr) return "";
    const pts = [];
    state.data.years.forEach((yr, i) => { if (arr[i] != null) pts.push([yr, arr[i]]); });
    if (pts.length < 2) return "";
    const W = 214, H = 46, pad = 5;
    const xe = d3.extent(pts, d => d[0]), ye = d3.extent(pts, d => d[1]);
    const sx = v => xe[1] === xe[0] ? W / 2 : pad + (W - 2 * pad) * (v - xe[0]) / (xe[1] - xe[0]);
    const sy = v => ye[1] === ye[0] ? H / 2 : H - pad - (H - 2 * pad) * (v - ye[0]) / (ye[1] - ye[0]);
    let d = "";
    pts.forEach((p, i) => d += (i ? "L" : "M") + sx(p[0]).toFixed(1) + " " + sy(p[1]).toFixed(1) + " ");
    let dot = "";
    if (curYear != null) {
      const cp = pts.find(p => p[0] === curYear);
      if (cp) dot = `<circle cx="${sx(cp[0]).toFixed(1)}" cy="${sy(cp[1]).toFixed(1)}" r="2.7" fill="#fff" stroke="#D4A017" stroke-width="1.2"/>`;
    }
    return `<svg class="tipspark" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}">` +
           `<path d="${d}" fill="none" stroke="#D4A017" stroke-width="1.7" stroke-linejoin="round"/>${dot}</svg>` +
           `<div class="tiprange"><span>${pts[0][0]}</span><span>${pts[pts.length - 1][0]}</span></div>`;
  }

  function onHover(ev, f) {
    const meta = state.ind;
    if (!meta) return;
    const cur = f._cur || valueFor(f.iso3);
    const { v, y } = cur;
    const name = f.nameEs || f.properties.name || f.iso3 || "—";
    const head = `<b>${name}</b>` + (v == null
      ? `<span class="y">sin dato</span>`
      : `<span class="v">${fmt(v, meta.unit)}</span> <span style="font-size:11px;opacity:.7">${meta.unit}</span>` +
        `<div class="y">${state.latest ? "último dato: " + y : "año " + y}</div>`);
    tip.style("opacity", 1)
      .style("left", (ev.clientX + 14) + "px").style("top", (ev.clientY + 14) + "px")
      .html(head + sparkSVG(f.iso3, v == null ? null : y));
  }

  // ---------- Controles ----------
  document.getElementById("yr").addEventListener("input", e => {
    state.year = state.sliderYears[+e.target.value]; render();
  });
  document.getElementById("latest").addEventListener("change", e => {
    state.latest = e.target.checked;
    document.getElementById("yr").disabled = state.latest;
    document.getElementById("playBtn").disabled = state.latest;
    render();
  });
  document.getElementById("playBtn").addEventListener("click", function () {
    if (state.playing) { clearInterval(state.playing); state.playing = null; this.classList.remove("on"); this.textContent = "▶"; return; }
    this.classList.add("on"); this.textContent = "❚❚";
    const sl = document.getElementById("yr");
    state.playing = setInterval(() => {
      let v = +sl.value + 1; if (v > +sl.max) v = 0;
      sl.value = v; state.year = state.sliderYears[v]; render();
    }, 650);
  });
})();
