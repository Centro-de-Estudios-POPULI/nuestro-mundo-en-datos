/* Nuestro Mundo en Datos — tendencias globales ("Un mundo mejor") + hero spark */
(function () {
  "use strict";

  // dir: +1 = subir es mejor ; -1 = bajar es mejor
  const TRENDS = [
    { id: "SI.POV.DDAY",   title: "Pobreza extrema",        unit: "% (US$3,00/día)",          dir: -1 },
    { id: "SE.ADT.LITR.ZS",title: "Alfabetización adulta",  unit: "% de 15+ años",            dir: +1 },
    { id: "SP.DYN.IMRT.IN",title: "Mortalidad infantil",    unit: "por 1.000 nacidos",        dir: -1 },
    { id: "SP.DYN.LE00.IN",title: "Esperanza de vida",      unit: "años",                     dir: +1 },
    { id: "SH.DYN.MORT",   title: "Mortalidad de menores de 5", unit: "por 1.000 nacidos",    dir: -1 },
    { id: "EG.ELC.ACCS.ZS",title: "Acceso a electricidad",  unit: "% de la población",        dir: +1 },
    { id: "SH.H2O.BASW.ZS",title: "Agua potable básica",    unit: "% de la población",        dir: +1 },
    { id: "SP.DYN.TFRT.IN",title: "Fecundidad",             unit: "hijos por mujer",          dir: -1 },
  ];

  const fmt = v => {
    if (v == null || isNaN(v)) return "—";
    const a = Math.abs(v);
    let s = a >= 1e9 ? (v/1e9).toFixed(1)+" mil M" : a >= 1e6 ? (v/1e6).toFixed(1)+" M"
      : a >= 100 ? d3.format(",.0f")(v) : a >= 1 ? d3.format(",.1f")(v) : d3.format(",.2f")(v);
    return s.replace(/\B(?=(\d{3})+(?!\d))/g, " ").replace(".", ",");
  };
  const load = id => fetch(`data/indicators/${id}.json`).then(r => r.json());

  // serie mundial (WLD) -> [{year,val}]
  function worldSeries(j) {
    const arr = j.data.WLD; if (!arr) return [];
    return j.years.map((y, i) => ({ year: y, val: arr[i] }))
      .filter(d => d.val != null);
  }

  function sparkPath(series, w, h, pad) {
    const xs = d3.scaleLinear().domain(d3.extent(series, d => d.year)).range([pad, w - pad]);
    const ys = d3.scaleLinear().domain(d3.extent(series, d => d.val)).range([h - pad, pad]);
    const line = d3.line().x(d => xs(d.year)).y(d => ys(d.val)).curve(d3.curveMonotoneX);
    const area = d3.area().x(d => xs(d.year)).y0(h - pad).y1(d => ys(d.val)).curve(d3.curveMonotoneX);
    return { d: line(series), a: area(series) };
  }

  // ---- Tarjetas de tendencias ----
  const grid = d3.select("#trendGrid");
  Promise.all(TRENDS.map(t => load(t.id).then(j => ({ t, s: worldSeries(j) })).catch(() => null)))
    .then(items => {
      items.filter(x => x && x.s.length >= 2).forEach(({ t, s }) => {
        const first = s[0], last = s[s.length - 1];
        const delta = last.val - first.val;
        const good = (t.dir > 0 ? delta > 0 : delta < 0);
        const pct = first.val ? Math.round(Math.abs(delta / first.val) * 100) : null;

        const card = grid.append("div").attr("class", "trend-card");
        card.append("h4").text(t.title);
        card.append("div").attr("class", "tsub").text(`${t.unit} · mundo`);
        const v = card.append("div").attr("class", "tval");
        v.append("span").attr("class", "tnow").text(fmt(last.val));
        v.append("span").attr("class", `tdelta ${good ? "good" : "bad"}`)
          .text(`${delta > 0 ? "▲" : "▼"} ${pct != null ? pct + "%" : ""} desde ${first.year}`);

        const w = 300, h = 90, pad = 6;
        const sp = sparkPath(s, w, h, pad);
        const col = good ? "#1c7a4b" : "#C00000";
        const svg = card.append("svg").attr("viewBox", `0 0 ${w} ${h}`).attr("preserveAspectRatio", "none");
        const gid = "g_" + t.id.replace(/[^a-z0-9]/gi, "");
        svg.append("defs").append("linearGradient").attr("id", gid).attr("x1", 0).attr("y1", 0).attr("x2", 0).attr("y2", 1)
          .call(g => { g.append("stop").attr("offset", "0%").attr("stop-color", col).attr("stop-opacity", .18);
                       g.append("stop").attr("offset", "100%").attr("stop-color", col).attr("stop-opacity", 0); });
        svg.append("path").attr("d", sp.a).attr("fill", `url(#${gid})`);
        svg.append("path").attr("d", sp.d).attr("fill", "none").attr("stroke", col).attr("stroke-width", 2.2);
        const lastX = (w - pad), lastY = pad + (h - 2 * pad) *
          (1 - (last.val - d3.min(s, d => d.val)) / ((d3.max(s, d => d.val) - d3.min(s, d => d.val)) || 1));
        svg.append("circle").attr("cx", lastX).attr("cy", lastY).attr("r", 3).attr("fill", col);
      });
    });

})();
