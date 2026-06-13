/* Nuestro Mundo en Datos — motor de mapas coropléticos (D3 v7) */
(function () {
  "use strict";

  const PAD = 6;
  const svg = d3.select("#map");
  const gMap = svg.append("g");
  const tip = d3.select("#tip");
  const fmt = (v, unit) => {
    if (v == null || isNaN(v)) return "s/d";
    const abs = Math.abs(v);
    let s;
    if (abs >= 1e9) s = (v / 1e9).toFixed(1) + " mil M";
    else if (abs >= 1e6) s = (v / 1e6).toFixed(1) + " M";
    else if (abs >= 1000) s = d3.format(",.0f")(v);
    else if (abs >= 1) s = d3.format(",.1f")(v);
    else s = d3.format(",.2f")(v);
    return s.replace(/\B(?=(\d{3})+(?!\d))/g, " ").replace(".", ",");
  };

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
        `${meta.wb_name} — ${meta.source || state.catalog.source_default}`;
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

  // Escala de color: divergente si cruza 0; si no, secuencial por cuantiles
  function buildColor(raw, meta) {
    const vals = [];
    for (const k in raw.data) for (const v of raw.data[k]) if (v != null) vals.push(v);
    vals.sort(d3.ascending);
    const ext = [vals[0], vals[vals.length - 1]];
    const diverging = ext[0] < 0 && ext[1] > 0 && meta.type !== "abs";
    if (diverging) {
      const m = Math.max(Math.abs(ext[0]), Math.abs(ext[1]));
      const t = [-m, -m * .6, -m * .25, -m * .07, m * .07, m * .25, m * .6, m];
      const cols = d3.schemeRdBu[8].slice().reverse();
      state.color = { type: "div", thr: t, cols, of: v => cols[Math.min(7, d3.bisect(t, v))] , dom: [-m, m] };
    } else {
      const q = d3.scaleQuantile().domain(vals).range(d3.range(7));
      const scheme = d3.schemeYlGnBu[7];
      const breaks = q.quantiles();
      state.color = { type: "seq", breaks, cols: scheme, of: v => scheme[q(v)], dom: ext };
    }
    buildLegend(meta);
  }

  function buildLegend(meta) {
    const c = state.color;
    document.getElementById("legendTitle").textContent = `${meta.name} (${meta.unit})`;
    const bins = d3.select("#legendBins").html("");
    c.cols.forEach(col => bins.append("span").style("background", col));
    const ticks = c.type === "div"
      ? [c.dom[0], 0, c.dom[1]]
      : [c.dom[0], c.breaks[2], c.breaks[5], c.dom[1]];
    d3.select("#legendTicks").html("").selectAll("span").data(ticks).join("span")
      .text(d => fmt(d, meta.unit));
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
