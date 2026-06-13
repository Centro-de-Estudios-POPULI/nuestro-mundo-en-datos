/* Hero interactivo — partículas tipo constelación (adaptado de galeria-populi) + contadores */
(function () {
  "use strict";

  // ---- Partículas ----
  const canvas = document.getElementById("particles");
  if (canvas) {
    const host = canvas.parentElement, ctx = canvas.getContext("2d");
    const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
    const RGB = "255,255,255", ACC = "212,160,23", CONNECT = 140, MR = 170;
    let w = 0, h = 0, parts = [], raf = 0;
    const mouse = { x: -9999, y: -9999 };

    function resize() {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = host.offsetWidth; h = host.offsetHeight;
      canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    function make() {
      const n = w < 768 ? 30 : 64; parts = [];
      for (let i = 0; i < n; i++) {
        const b = Math.random() * 0.35 + 0.12;
        parts.push({ x: Math.random()*w, y: Math.random()*h, vx: (Math.random()-.5)*.4,
          vy: (Math.random()-.5)*.4, r: Math.random()*1.8+.8, base: b, alpha: b, gold: Math.random()<.18 });
      }
    }
    function frame() {
      ctx.clearRect(0, 0, w, h);
      for (let i = 0; i < parts.length; i++) {
        const p = parts[i], dx = mouse.x-p.x, dy = mouse.y-p.y, dist = Math.hypot(dx, dy);
        if (dist < MR) { const f = ((MR-dist)/MR)*0.008; p.vx += dx*f; p.vy += dy*f; p.alpha = p.base + (1-dist/MR)*0.4; }
        else p.alpha += (p.base-p.alpha)*0.02;
        p.vx *= 0.99; p.vy *= 0.99; p.x += p.vx; p.y += p.vy;
        if (p.x < 0) p.x = w; if (p.x > w) p.x = 0; if (p.y < 0) p.y = h; if (p.y > h) p.y = 0;
        ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI*2);
        ctx.fillStyle = "rgba(" + (p.gold ? ACC : RGB) + "," + p.alpha + ")"; ctx.fill();
        for (let j = i+1; j < parts.length; j++) {
          const p2 = parts[j], d = Math.hypot(p.x-p2.x, p.y-p2.y);
          if (d < CONNECT) {
            let la = (1-d/CONNECT)*0.13;
            const mx = (p.x+p2.x)/2, my = (p.y+p2.y)/2, md = Math.hypot(mouse.x-mx, mouse.y-my);
            if (md < MR) la += (1-md/MR)*0.13;
            ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(p2.x, p2.y);
            ctx.strokeStyle = "rgba(" + RGB + "," + la + ")"; ctx.lineWidth = 0.6; ctx.stroke();
          }
        }
      }
      raf = requestAnimationFrame(frame);
    }
    resize(); make();
    if (reduce) { for (const p of parts) { ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI*2);
      ctx.fillStyle = "rgba(" + (p.gold ? ACC : RGB) + "," + p.base + ")"; ctx.fill(); } }
    else raf = requestAnimationFrame(frame);
    host.addEventListener("mousemove", e => { const r = canvas.getBoundingClientRect(); mouse.x = e.clientX-r.left; mouse.y = e.clientY-r.top; });
    host.addEventListener("mouseleave", () => { mouse.x = -9999; mouse.y = -9999; });
    window.addEventListener("resize", () => { resize(); make(); });
  }

  // ---- Contadores animados ----
  function animate(el, target) {
    const dur = 1100, t0 = performance.now();
    function tick(t) {
      const k = Math.min(1, (t - t0) / dur);
      const e = 1 - Math.pow(1 - k, 3);              // easeOutCubic
      el.textContent = Math.round(target * e).toLocaleString("es");
      if (k < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }
  document.querySelectorAll(".stats b[data-count]").forEach(b => animate(b, +b.dataset.count));
})();
