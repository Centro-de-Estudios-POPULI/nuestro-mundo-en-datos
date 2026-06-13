/* Nuestro Mundo en Datos — scatter de correlaciones (estilo Gapminder) */
(function () {
  "use strict";

  const REGION_COLORS = {
    "Asia Oriental y Pacífico": "#E8743B",
    "Europa y Asia Central": "#1B9E77",
    "América Latina y el Caribe": "#8B1A1A",
    "Oriente Medio y Norte de África": "#D4A017",
    "América del Norte": "#3B6CB7",
    "Asia Meridional": "#9C27B0",
    "África Subsahariana": "#5B8C2A",
  };

  const svg = d3.select("#scSvg");
  const tip = d3.select("#scTip");
  const cache = {};                       // id -> {years, data}
  const S = { ind: null, regions: null, pop: null, xId: null, yId: null,
              xData: null, yData: null, years: [], year: null,
              xLog: false, yLog: false, off: new Set(), playing: null };
  let G = null;   // grupos SVG persistentes (para transiciones)

  const fmt = v => {
    if (v == null || isNaN(v)) return "s/d";
    const a = Math.abs(v);
    let s = a >= 1e9 ? (v/1e9).toFixed(1)+" mil M" : a >= 1e6 ? (v/1e6).toFixed(1)+" M"
      : a >= 1000 ? d3.format(",.0f")(v) : a >= 1 ? d3.format(",.1f")(v) : d3.format(",.2f")(v);
    return s.replace(/\B(?=(\d{3})+(?!\d))/g, " ").replace(".", ",");
  };
  const load = id => cache[id] ? Promise.resolve(cache[id])
    : fetch(`data/indicators/${id}.json`).then(r => r.json()).then(j => (cache[id] = j));

  Promise.all([
    fetch("data/catalog.json").then(r => r.json()),
    fetch("data/regions.json").then(r => r.json()),
    load("SP.POP.TOTL")
  ]).then(([cat, regions, pop]) => {
    S.ind = cat; S.regions = regions; S.pop = pop;
    fillSelect("scX", cat, "NY.GDP.PCAP.CD");
    fillSelect("scY", cat, "SP.DYN.LE00.IN");
    buildRegionLegend();
    bind();
    reloadAxes();
  }).catch(e => console.error("scatter:", e));

  function fillSelect(elId, cat, def) {
    const sel = document.getElementById(elId);
    const byCat = d3.group(cat.indicators, d => d.category);
    cat.categories.forEach(c => {
      const og = document.createElement("optgroup"); og.label = c.name;
      (byCat.get(c.name) || []).forEach(d => {
        const o = document.createElement("option");
        o.value = d.id; o.textContent = d.name; if (d.id === def) o.selected = true;
        og.appendChild(o);
      });
      sel.appendChild(og);
    });
  }

  function buildRegionLegend() {
    const box = d3.select("#scLegend").html("");
    Object.keys(REGION_COLORS).forEach(r => {
      const it = box.append("div").attr("class", "ri").on("click", () => {
        if (S.off.has(r)) S.off.delete(r); else S.off.add(r);
        it.classed("off", S.off.has(r)); render();
      });
      it.append("span").attr("class", "sw").style("background", REGION_COLORS[r]);
      it.append("span").text(r);
    });
  }

  function bind() {
    document.getElementById("scX").addEventListener("change", e => { S.xId = e.target.value; reloadAxes(); });
    document.getElementById("scY").addEventListener("change", e => { S.yId = e.target.value; reloadAxes(); });
    document.getElementById("scLogX").addEventListener("change", e => { S.xLog = e.target.checked; render(); });
    document.getElementById("scLogY").addEventListener("change", e => { S.yLog = e.target.checked; render(); });
    document.getElementById("scYear").addEventListener("input", e => { S.year = S.years[+e.target.value]; render(); });
    document.getElementById("scPlay").addEventListener("click", function () {
      if (S.playing) { clearInterval(S.playing); S.playing = null; this.classList.remove("on"); this.textContent = "▶"; return; }
      this.classList.add("on"); this.textContent = "❚❚";
      const sl = document.getElementById("scYear");
      S.playing = setInterval(() => {
        let v = +sl.value + 1; if (v > +sl.max) v = 0;
        sl.value = v; S.year = S.years[v]; render();
      }, 700);
    });
    window.addEventListener("resize", () => clearTimeout(S._rz) || (S._rz = setTimeout(render, 150)));
  }

  function reloadAxes() {
    S.xId = document.getElementById("scX").value;
    S.yId = document.getElementById("scY").value;
    Promise.all([load(S.xId), load(S.yId)]).then(([x, y]) => {
      S.xData = x; S.yData = y;
      // años comunes con al menos un país que tenga x, y y población
      const common = x.years.filter(yr => y.years.includes(yr) && S.pop.years.includes(yr));
      const counts = common.map(yr => {
        const xi = x.years.indexOf(yr), yi = y.years.indexOf(yr), pi = S.pop.years.indexOf(yr);
        let n = 0;
        for (const iso in S.regions)
          if (x.data[iso]?.[xi] != null && y.data[iso]?.[yi] != null && S.pop.data[iso]?.[pi] != null) n++;
        return n;
      });
      S.years = common.filter((yr, i) => counts[i] > 0);
      const maxC = Math.max(...counts);
      let pos = S.years.length - 1;
      for (let p = S.years.length - 1; p >= 0; p--)
        if (counts[common.indexOf(S.years[p])] >= 0.6 * maxC) { pos = p; break; }
      const sl = document.getElementById("scYear");
      sl.min = 0; sl.max = S.years.length - 1; sl.value = pos;
      S.year = S.years[pos];
      // dominios globales (ejes fijos durante la animación)
      S.xExt = globalExtent(x); S.yExt = globalExtent(y);
      S.popExt = globalExtent(S.pop);
      render();
    });
  }

  function globalExtent(j) {
    let lo = Infinity, hi = -Infinity;
    for (const iso in S.regions) {
      const arr = j.data[iso]; if (!arr) continue;
      for (const v of arr) if (v != null) { if (v < lo) lo = v; if (v > hi) hi = v; }
    }
    return [lo, hi];
  }

  function render() {
    if (!S.xData || !S.yData || S.year == null) return;
    const node = svg.node(), W = node.clientWidth || 820, H = node.clientHeight || 460;
    const m = { t: 18, r: 20, b: 50, l: 68 };
    svg.attr("viewBox", `0 0 ${W} ${H}`);
    if (!G) {
      const g = svg.append("g");
      G = { ax: g.append("g").attr("class", "sc-axis"), ay: g.append("g").attr("class", "sc-axis"),
            bub: g.append("g"),
            lx: svg.append("text").attr("class", "sc-axislabel").attr("text-anchor", "middle"),
            ly: svg.append("text").attr("class", "sc-axislabel").attr("text-anchor", "middle").attr("transform", "rotate(-90)") };
    }
    const xMeta = S.ind.indicators.find(d => d.id === S.xId);
    const yMeta = S.ind.indicators.find(d => d.id === S.yId);

    // datos del año actual, filtrados por región y validez
    const xi = S.xData.years.indexOf(S.year), yi = S.yData.years.indexOf(S.year), pi = S.pop.years.indexOf(S.year);
    const rows = [];
    for (const iso in S.regions) {
      const reg = S.regions[iso].region;
      if (S.off.has(reg)) continue;
      const xv = S.xData.data[iso]?.[xi], yv = S.yData.data[iso]?.[yi], pv = S.pop.data[iso]?.[pi];
      if (xv == null || yv == null || pv == null) continue;
      if ((S.xLog && xv <= 0) || (S.yLog && yv <= 0)) continue;
      rows.push({ iso, reg, name: S.regions[iso].name, xv, yv, pv });
    }
    rows.sort((a, b) => b.pv - a.pv);   // grandes detrás
    document.getElementById("scYearLabel").textContent = S.year;
    if (!rows.length) { G.bub.selectAll("circle").remove(); return; }

    // dominios ADAPTADOS a los datos visibles del año (con margen) -> sin zonas vacías
    const pad = (e, f) => { const d = (e[1] - e[0]) || Math.abs(e[0]) || 1; return [e[0] - d * f, e[1] + d * f]; };
    const mkScale = (ext, log, range) => log && ext[0] > 0
      ? d3.scaleLog().domain(ext).range(range).nice()
      : d3.scaleLinear().domain(pad(ext, 0.05)).range(range).nice();
    const x = mkScale(d3.extent(rows, d => d.xv), S.xLog, [m.l, W - m.r]);
    const y = mkScale(d3.extent(rows, d => d.yv), S.yLog, [H - m.b, m.t]);
    const r = d3.scaleSqrt().domain([0, S.popExt[1]]).range([2, Math.min(40, W / 22)]);

    G.ax.attr("transform", `translate(0,${H - m.b})`).transition().duration(450).call(d3.axisBottom(x).ticks(W / 110, "~s"));
    G.ay.attr("transform", `translate(${m.l},0)`).transition().duration(450).call(d3.axisLeft(y).ticks(H / 60, "~s"));
    G.lx.attr("x", (W + m.l) / 2).attr("y", H - 8).text(`${xMeta.name} (${xMeta.unit})`);
    G.ly.attr("x", -(H - m.b) / 2).attr("y", 16).text(`${yMeta.name} (${yMeta.unit})`);

    G.bub.selectAll("circle.bubble").data(rows, d => d.iso).join(
      enter => enter.append("circle").attr("class", "bubble")
        .attr("cx", d => x(d.xv)).attr("cy", d => y(d.yv)).attr("fill", d => REGION_COLORS[d.reg] || "#999")
        .attr("r", 0).call(en => en.transition().duration(350).attr("r", d => r(d.pv))),
      update => update.attr("fill", d => REGION_COLORS[d.reg] || "#999")
        .call(up => up.transition().duration(550).attr("cx", d => x(d.xv)).attr("cy", d => y(d.yv)).attr("r", d => r(d.pv))),
      exit => exit.transition().duration(250).attr("r", 0).remove()
    ).on("mousemove", (ev, d) => {
      tip.style("opacity", 1).style("left", (ev.clientX + 14) + "px").style("top", (ev.clientY + 14) + "px")
        .html(`<b>${d.name}</b><div>${xMeta.name}: <b>${fmt(d.xv)}</b></div>` +
              `<div>${yMeta.name}: <b>${fmt(d.yv)}</b></div>` +
              `<div class="y">Población: ${fmt(d.pv)} · ${S.year}</div>`);
    }).on("mouseleave", () => tip.style("opacity", 0));
  }
})();
