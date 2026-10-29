/* Kalenderkompass 24 – Familienplaner mit Feiertagen, Schulferien und Geburtstagen (optional mit Foto).
   Alles läuft im Browser: Fotos werden verkleinert und nur lokal gespeichert, das PDF entsteht auf dem Gerät. */
(() => {
  "use strict";
  const root = document.querySelector("[data-familie]"); if (!root) return;
  const $ = (s, r = root) => r.querySelector(s), $$ = (s, r = root) => [...r.querySelectorAll(s)];
  const store = { get(k, d) { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch { return d; } },
                  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); return true; } catch { return false; } } };
  const MON = ["Jänner", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"];
  const MON_DE = ["Januar", ...MON.slice(1)];
  const WD = ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"];
  const COLORS = ["#C4122F", "#0F7C80", "#2457C5", "#B26A00", "#7A3E9D", "#3E7C2B"];
  const PT = 0.3528;
  let H = null, SF = null;
  let st = store.get("kk-familie", null) || {
    region: "at:wien", year: 2027, month: "all", title: "Familie", layout: "spalten", ferien: true,
    people: [{ name: "Mama", bday: "", col: true, photo: "" }, { name: "Papa", bday: "", col: true, photo: "" }, { name: "Kind", bday: "", col: true, photo: "" }]
  };
  const save = () => { if (!store.set("kk-familie", st)) $("[data-fmsg]").textContent = "Hinweis: Der Browser-Speicher ist voll – nimm weniger oder kleinere Fotos."; };

  /* ---------------- Daten */
  const isoD = (y, m, d) => `${y}-${String(m + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
  function holidays(y) { const [c, r] = st.region.split(":"); return new Map((H.h[`${c}:${r}:${y}`] || []).map(x => [x[0], x])); }
  function ferienOn(iso) { if (!st.ferien || !SF) return null; const f = SF.f[st.region]; return f ? (f.find(p => p[1] <= iso && iso <= p[2]) || null) : null; }

  /* ---------------- Zeichnen (mm) */
  function page(landscape) {
    const w = landscape ? 297 : 210, h = landscape ? 210 : 297, ops = [];
    const P = { w, h, ops, m: 11,
      line: (x1, y1, x2, y2, c = "#D8DFE9", lw = 0.2) => ops.push({ t: "line", x1, y1, x2, y2, c, lw }),
      rect: (x, y, rw, rh, s = {}) => ops.push({ t: "rect", x, y, w: rw, h: rh, stroke: s.stroke ?? "#D8DFE9", fill: s.fill ?? null, lw: s.lw ?? 0.2, r: s.r ?? 0 }),
      text: (x, y, txt, s = {}) => ops.push({ t: "text", x, y, txt: String(txt), size: s.size ?? 8, c: s.c ?? "#15233B", align: s.align ?? "left", bold: !!s.bold }),
      img: (src, cx, cy, r) => ops.push({ t: "img", src, cx, cy, r }),
      dot: (cx, cy, r, fill) => ops.push({ t: "circle", cx, cy, r, fill })
    };
    return P;
  }
  const initials = n => (n || "?").trim().split(/\s+/).map(s => s[0]).join("").slice(0, 2).toUpperCase();
  function avatar(P, p, i, cx, cy, r) {
    if (p.photo) P.img(p.photo, cx, cy, r);
    else { P.dot(cx, cy, r, COLORS[i % COLORS.length]); P.text(cx, cy + r * 0.38, initials(p.name), { size: r * 2.1, c: "#fff", bold: true, align: "center" }); }
  }
  function bdaysOn(m, d) { return st.people.map((p, i) => [p, i]).filter(([p]) => { const b = /^(\d{4})?-?(\d{2})-(\d{2})$/.exec(p.bday || ""); return b && +b[2] === m + 1 && +b[3] === d; }); }
  function ageText(p, y) { const yy = +(p.bday || "").slice(0, 4); return yy > 1900 && yy < y ? ` (${y - yy})` : ""; }

  function monthColumns(y, m) {
    const P = page(false), hol = holidays(y), cols = st.people.filter(p => p.col).slice(0, 6);
    const days = new Date(Date.UTC(y, m + 1, 0)).getUTCDate();
    P.text(P.m, P.m + 9, `${st.title || "Familienplaner"}`, { size: 20, bold: true });
    P.text(P.w - P.m, P.m + 9, `${(st.region.startsWith("de") ? MON_DE : MON)[m]} ${y}`, { size: 13, bold: true, c: "#C4122F", align: "right" });
    P.line(P.m, P.m + 12, P.w - P.m, P.m + 12, "#C4122F", 0.6);
    const top = P.m + 16, headH = 17, dateW = 19, notesW = cols.length >= 5 ? 34 : 50;
    const colW = (P.w - 2 * P.m - dateW - notesW) / Math.max(cols.length, 1);
    const rowH = (P.h - P.m - 6 - top - headH) / days;
    cols.forEach((p, i) => { const cx = P.m + dateW + i * colW + colW / 2; avatar(P, p, st.people.indexOf(p), cx, top + 6.5, 5.5); P.text(cx, top + 15.5, (p.name || "").slice(0, 14), { size: 7.5, bold: true, align: "center" }); });
    P.text(P.w - P.m - notesW + 2, top + 15.5, "TERMINE & NOTIZEN", { size: 6.5, bold: true, c: "#C4122F" });
    for (let d = 1; d <= days; d++) {
      const y0 = top + headH + (d - 1) * rowH, iso = isoD(y, m, d), wd = new Date(Date.UTC(y, m, d)).getUTCDay(), h = hol.get(iso), f = ferienOn(iso);
      const we = wd === 0 || wd === 6, legal = h && h[2] === "legal";
      if (f) P.rect(P.m, y0, P.w - 2 * P.m, rowH, { fill: "#E3F2F1", stroke: "#E3F2F1", lw: 0.01 });
      if (we || legal) P.rect(P.m, y0, dateW, rowH, { fill: legal ? "#FBE7EA" : "#EEF1F5", stroke: "#fff", lw: 0.01 });
      P.text(P.m + 2, y0 + rowH * 0.66, `${WD[wd]} ${d}`, { size: Math.min(8.5, rowH * 1.25), bold: true, c: legal || wd === 0 ? "#C4122F" : "#15233B" });
      let note = h ? h[1] : (f && (d === 1 || isoD(y, m, d - 1) < f[1]) ? f[0] : "");
      if (!h && f && iso === f[1]) note = `${f[0]} beginnen`;
      const bd = bdaysOn(m, d);
      bd.forEach(([p, i]) => {
        const k = cols.indexOf(p);
        if (k >= 0) { const cx = P.m + dateW + k * colW + colW / 2; avatar(P, p, i, cx - Math.min(colW / 2 - 4, 9), y0 + rowH / 2, Math.min(rowH * 0.42, 3.4)); P.text(cx + 2, y0 + rowH * 0.66, "Geburtstag!", { size: Math.min(7, rowH), bold: true, c: COLORS[i % COLORS.length], align: "center" }); }
        else note = `Geb. ${p.name}${ageText(p, y)}` + (note ? " · " + note : "");
      });
      if (note) { const fs = Math.min(6.5, rowH * 0.9), max = Math.floor((notesW - 3) / (fs * PT * 0.52)); P.text(P.w - P.m - notesW + 2, y0 + rowH * 0.66, note.length > max ? note.slice(0, max - 1) + "…" : note, { size: fs, c: h ? "#C4122F" : "#0F7C80", bold: !!h }); }
      P.line(P.m, y0 + rowH, P.w - P.m, y0 + rowH);
    }
    for (let i = 0; i <= cols.length; i++) P.line(P.m + dateW + i * colW, top + headH, P.m + dateW + i * colW, top + headH + days * rowH, "#C9D2DE", 0.25);
    P.rect(P.m, top + headH, P.w - 2 * P.m, days * rowH, { stroke: "#9AA6B8", lw: 0.35 });
    legend(P);
    return P;
  }

  function monthGrid(y, m) {
    const P = page(true), hol = holidays(y), names = st.region.startsWith("de") ? MON_DE : MON;
    P.text(P.m, P.m + 9, `${st.title || "Familienplaner"}`, { size: 20, bold: true });
    P.text(P.w - P.m, P.m + 9, `${names[m]} ${y}`, { size: 13, bold: true, c: "#C4122F", align: "right" });
    P.line(P.m, P.m + 12, P.w - P.m, P.m + 12, "#C4122F", 0.6);
    const top = P.m + 16, cw = (P.w - 2 * P.m) / 7, first = new Date(Date.UTC(y, m, 1)), lead = (first.getUTCDay() + 6) % 7;
    const days = new Date(Date.UTC(y, m + 1, 0)).getUTCDate(), rows = Math.ceil((lead + days) / 7), rh = (P.h - P.m - 8 - top - 6) / rows;
    ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"].forEach((n, i) => { P.rect(P.m + i * cw, top, cw, 6, { fill: "#15233B", stroke: "#15233B", lw: 0.1 }); P.text(P.m + i * cw + cw / 2, top + 4.2, n.toUpperCase(), { size: 7.5, c: "#fff", bold: true, align: "center" }); });
    for (let k = 0; k < rows * 7; k++) {
      const d = k - lead + 1, x = P.m + (k % 7) * cw, y0 = top + 6 + Math.floor(k / 7) * rh;
      if (d < 1 || d > days) { P.rect(x, y0, cw, rh, { fill: "#F7F8FA" }); continue; }
      const iso = isoD(y, m, d), h = hol.get(iso), f = ferienOn(iso), legal = h && h[2] === "legal";
      P.rect(x, y0, cw, rh, { fill: legal ? "#FBE7EA" : f ? "#E3F2F1" : (k % 7 >= 5 ? "#F5F6F8" : null) });
      P.text(x + 2, y0 + 5.5, d, { size: 11, bold: true, c: legal || k % 7 === 6 ? "#C4122F" : "#15233B" });
      let ty = y0 + 10;
      if (h) { P.text(x + 2, ty, h[1].slice(0, 24), { size: 6.3, c: "#C4122F", bold: legal }); ty += 3.6; }
      if (f && (iso === f[1] || d === 1)) { P.text(x + 2, ty, f[0].slice(0, 24), { size: 6.3, c: "#0F7C80" }); ty += 3.6; }
      bdaysOn(m, d).forEach(([p, i], j) => { const r = Math.min(4.2, rh * 0.16); avatar(P, p, i, x + cw - r - 1.5 - j * (2 * r + 1), y0 + r + 1.5, r); P.text(x + 2, Math.min(ty + 0.5, y0 + rh - 2), `${p.name}${ageText(p, y)}`.slice(0, 22), { size: 6.5, bold: true, c: COLORS[i % COLORS.length] }); ty += 3.6; });
    }
    legend(P);
    return P;
  }
  function legend(P) {
    const y = P.h - P.m + 3;
    P.rect(P.m, y - 2.6, 4, 3, { fill: "#FBE7EA", stroke: "#FBE7EA" }); P.text(P.m + 5.5, y, "Feiertag", { size: 6.5, c: "#5B6472" });
    if (st.ferien) { P.rect(P.m + 22, y - 2.6, 4, 3, { fill: "#E3F2F1", stroke: "#E3F2F1" }); P.text(P.m + 27.5, y, "Schulferien", { size: 6.5, c: "#5B6472" }); }
    P.text(P.w - P.m, y, "kalenderkompass24.de/familienplaner.html", { size: 6, c: "#A0A6AF", align: "right" });
  }
  function build() {
    const y = +st.year, months = st.month === "all" ? [...Array(12).keys()] : [+st.month];
    return months.map(m => st.layout === "raster" ? monthGrid(y, m) : monthColumns(y, m));
  }

  /* ---------------- SVG & PDF */
  const esc = s => s.replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
  let clipN = 0;
  function svg(P) {
    let s = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${P.w} ${P.h}" width="${P.w}mm" height="${P.h}mm" role="img" aria-label="Vorschau Familienplaner"><rect width="${P.w}" height="${P.h}" fill="#fff"/>`;
    for (const o of P.ops) {
      if (o.t === "line") s += `<line x1="${o.x1.toFixed(2)}" y1="${o.y1.toFixed(2)}" x2="${o.x2.toFixed(2)}" y2="${o.y2.toFixed(2)}" stroke="${o.c}" stroke-width="${o.lw}"/>`;
      else if (o.t === "rect") s += `<rect x="${o.x.toFixed(2)}" y="${o.y.toFixed(2)}" width="${o.w.toFixed(2)}" height="${o.h.toFixed(2)}" fill="${o.fill || "none"}" stroke="${o.stroke || "none"}" stroke-width="${o.lw}"/>`;
      else if (o.t === "circle") s += `<circle cx="${o.cx.toFixed(2)}" cy="${o.cy.toFixed(2)}" r="${o.r.toFixed(2)}" fill="${o.fill}"/>`;
      else if (o.t === "text") s += `<text x="${o.x.toFixed(2)}" y="${o.y.toFixed(2)}" font-size="${(o.size * PT).toFixed(2)}" fill="${o.c}" text-anchor="${o.align === "center" ? "middle" : o.align === "right" ? "end" : "start"}" font-family="Helvetica, Arial, sans-serif"${o.bold ? ' font-weight="700"' : ""}>${esc(o.txt)}</text>`;
      else if (o.t === "img") { const id = `c${++clipN}`; s += `<clipPath id="${id}"><circle cx="${o.cx}" cy="${o.cy}" r="${o.r}"/></clipPath><image href="${o.src}" x="${o.cx - o.r}" y="${o.cy - o.r}" width="${2 * o.r}" height="${2 * o.r}" clip-path="url(#${id})" preserveAspectRatio="xMidYMid slice"/><circle cx="${o.cx}" cy="${o.cy}" r="${o.r}" fill="none" stroke="#fff" stroke-width="0.5"/>`; }
    }
    return s + "</svg>";
  }
  let jsPDFP;
  const loadPDF = () => jsPDFP ||= new Promise((res, rej) => { if (window.jspdf) return res(window.jspdf.jsPDF); const sc = document.createElement("script"); sc.src = "/assets/jspdf.umd.min.js"; sc.onload = () => res(window.jspdf.jsPDF); sc.onerror = rej; document.head.appendChild(sc); });
  const rgb = c => { let h = c.replace("#", ""); if (h.length === 3) h = h.split("").map(x => x + x).join(""); return [0, 2, 4].map(i => parseInt(h.slice(i, i + 2), 16)); };
  async function pdf(pages) {
    const jsPDF = await loadPDF(), P0 = pages[0];
    const doc = new jsPDF({ unit: "mm", format: [P0.w, P0.h], orientation: P0.w > P0.h ? "landscape" : "portrait", compress: true });
    doc.setProperties({ title: `${st.title} ${st.year}`, creator: "Kalenderkompass 24" });
    pages.forEach((P, i) => {
      if (i) doc.addPage([P.w, P.h], P.w > P.h ? "landscape" : "portrait");
      for (const o of P.ops) {
        if (o.t === "line") { doc.setDrawColor(...rgb(o.c)); doc.setLineWidth(o.lw); doc.line(o.x1, o.y1, o.x2, o.y2); }
        else if (o.t === "rect") { if (o.fill) doc.setFillColor(...rgb(o.fill)); if (o.stroke) { doc.setDrawColor(...rgb(o.stroke)); doc.setLineWidth(o.lw); } doc.rect(o.x, o.y, o.w, o.h, o.fill && o.stroke ? "FD" : o.fill ? "F" : "S"); }
        else if (o.t === "circle") { doc.setFillColor(...rgb(o.fill)); doc.circle(o.cx, o.cy, o.r, "F"); }
        else if (o.t === "text") { doc.setFont("helvetica", o.bold ? "bold" : "normal"); doc.setFontSize(o.size); doc.setTextColor(...rgb(o.c)); doc.text(o.txt, o.x, o.y, { align: o.align }); }
        else if (o.t === "img") {
          doc.saveGraphicsState(); doc.circle(o.cx, o.cy, o.r, null); doc.clip(); doc.discardPath();
          doc.addImage(o.src, "JPEG", o.cx - o.r, o.cy - o.r, 2 * o.r, 2 * o.r, undefined, "FAST");
          doc.restoreGraphicsState(); doc.setDrawColor(255, 255, 255); doc.setLineWidth(0.5); doc.circle(o.cx, o.cy, o.r, "S");
        }
      }
    });
    doc.save(`familienplaner-${st.year}${st.month === "all" ? "" : "-" + (+st.month + 1)}.pdf`);
  }

  /* ---------------- Fotos: quadratisch zuschneiden, auf 240 px verkleinern */
  function readPhoto(file) {
    return new Promise((res, rej) => {
      if (!file || !/^image\//.test(file.type)) return rej(new Error("Bitte ein Bild wählen."));
      const img = new Image(), url = URL.createObjectURL(file);
      img.onload = () => { const s = Math.min(img.width, img.height), c = document.createElement("canvas"); c.width = c.height = 240;
        c.getContext("2d").drawImage(img, (img.width - s) / 2, (img.height - s) / 2, s, s, 0, 0, 240, 240); URL.revokeObjectURL(url); res(c.toDataURL("image/jpeg", 0.82)); };
      img.onerror = () => rej(new Error("Das Bild konnte nicht gelesen werden.")); img.src = url;
    });
  }

  /* ---------------- Oberfläche */
  let pages = [], pi = 0;
  function peopleUI() {
    $("[data-people]").innerHTML = st.people.map((p, i) => `<li class="person" data-i="${i}">
      <label class="ph" title="Foto wählen">${p.photo ? `<img src="${p.photo}" alt="">` : `<span style="background:${COLORS[i % COLORS.length]}">${esc(initials(p.name))}</span>`}<input type="file" accept="image/*" data-photo hidden><b>Foto</b></label>
      <label>Name<input type="text" maxlength="20" value="${esc(p.name)}" data-f="name"></label>
      <label>Geburtstag<input type="date" value="${p.bday && p.bday.length === 10 ? p.bday : ""}" data-f="bday"></label>
      <label class="chk2"><input type="checkbox" ${p.col ? "checked" : ""} data-f="col"> eigene Spalte</label>
      <button type="button" class="linkbtn" data-del aria-label="${esc(p.name)} entfernen">Entfernen</button>${p.photo ? `<button type="button" class="linkbtn" data-nophoto>Foto weg</button>` : ""}</li>`).join("");
    $("[data-add]").disabled = st.people.length >= 12;
  }
  function render() {
    if (!H) return;
    pages = build(); pi = Math.min(pi, pages.length - 1);
    const P = pages[pi];
    $("[data-fstage]").innerHTML = `<div class="fsheet" style="aspect-ratio:${P.w}/${P.h}">${svg(P)}</div>`;
    $("[data-finfo]").innerHTML = `${pages.length} Seite${pages.length > 1 ? "n" : ""} · A4 ${P.w > P.h ? "quer" : "hoch"}` + (pages.length > 1 ? ` <span class="pager"><button type="button" data-prev aria-label="Vorige Seite">‹</button> ${pi + 1} / ${pages.length} <button type="button" data-next aria-label="Nächste Seite">›</button></span>` : "");
    $("[data-fnote]").textContent = st.ferien && SF ? `Schulferien enthalten für das Schuljahr ${SF.schuljahr} (bis ${SF.bis.split("-").reverse().join(".")}); spätere Ferien ergänzen wir, sobald sie amtlich veröffentlicht sind.` : "";
    save();
  }
  function bind() {
    const f = $("[data-fform]");
    f.region.value = st.region; f.year.value = st.year; f.month.value = st.month; f.title.value = st.title; f.ferien.checked = st.ferien;
    $$(`input[name=layout]`, f).forEach(r => r.checked = r.value === st.layout);
    f.addEventListener("input", e => {
      if (e.target.closest("[data-people]")) return;
      st.region = f.region.value; st.year = +f.year.value || 2027; st.month = f.month.value; st.title = f.title.value.slice(0, 30); st.ferien = f.ferien.checked;
      st.layout = (f.querySelector("input[name=layout]:checked") || {}).value || "spalten"; render();
    });
    $("[data-people]").addEventListener("input", e => {
      const li = e.target.closest(".person"); if (!li || !e.target.dataset.f) return;
      const p = st.people[+li.dataset.i], k = e.target.dataset.f; p[k] = k === "col" ? e.target.checked : e.target.value;
      if (k === "name") { const sp = li.querySelector(".ph span"); if (sp) sp.textContent = initials(p.name); }
      render();
    });
    $("[data-people]").addEventListener("change", async e => {
      if (!e.target.matches("[data-photo]")) return;
      const li = e.target.closest(".person");
      try { st.people[+li.dataset.i].photo = await readPhoto(e.target.files[0]); $("[data-fmsg]").textContent = ""; } catch (err) { $("[data-fmsg]").textContent = err.message; }
      peopleUI(); render();
    });
    $("[data-people]").addEventListener("click", e => {
      const li = e.target.closest(".person"); if (!li) return;
      if (e.target.matches("[data-del]")) { st.people.splice(+li.dataset.i, 1); peopleUI(); render(); }
      if (e.target.matches("[data-nophoto]")) { st.people[+li.dataset.i].photo = ""; peopleUI(); render(); }
    });
    $("[data-add]").addEventListener("click", () => { st.people.push({ name: `Person ${st.people.length + 1}`, bday: "", col: st.people.filter(p => p.col).length < 6, photo: "" }); peopleUI(); render(); });
    $("[data-finfo]").addEventListener("click", e => { if (e.target.closest("[data-prev]")) { pi = (pi - 1 + pages.length) % pages.length; render(); } if (e.target.closest("[data-next]")) { pi = (pi + 1) % pages.length; render(); } });
    $("[data-fpdf]").addEventListener("click", async e => {
      const b = e.currentTarget, t = b.textContent; b.disabled = true; b.textContent = "PDF wird erstellt …";
      try { await pdf(pages); if (window.gtag) gtag("event", "pdf_download", { template: "familienplaner" }); } catch (err) { console.error(err); $("[data-fmsg]").textContent = "Das PDF konnte nicht erstellt werden. Bitte versuche es noch einmal."; }
      b.disabled = false; b.textContent = t;
    });
    $("[data-freset]").addEventListener("click", () => { try { localStorage.removeItem("kk-familie"); } catch {} location.reload(); });
  }
  async function init() {
    peopleUI(); bind();
    try { const [a, b] = await Promise.all([fetch("/data/feiertage.json").then(r => r.json()), fetch("/data/schulferien.json").then(r => r.json())]); H = a; SF = b; }
    catch { $("[data-fmsg]").textContent = "Die Kalenderdaten konnten nicht geladen werden."; return; }
    const sel = $("[data-fform]").region, cur = st.region;
    sel.innerHTML = ["at", "de"].map(c => `<optgroup label="${H.countries[c].label}">${Object.entries(H.countries[c].regions).map(([k, n]) => `<option value="${c}:${k}">${n}</option>`).join("")}</optgroup>`).join("");
    sel.value = cur; render();
  }
  window.KK_FAMILIE = { build, get state() { return st; }, set state(v) { st = v; } };
  init();
})();
