/* Mein Kalender — eigene Einträge in selbst gewählten Farben. Gespeichert nur im Browser (localStorage „kk24-mein“),
   nichts verlässt das Gerät. Feiertage bleiben immer rot, Fenster-/Brückentage schwarz umrandet. Braucht app.js (window.KK). */
(() => {
  const KEY = "kk24-mein";
  const HEX = /^#[0-9a-fA-F]{6}$/, ISO = /^\d{4}-\d{2}-\d{2}$/;
  const DEFAULT_CATS = [
    { id: "urlaub", name: "Urlaub", color: "#2E7D4F" },
    { id: "familie", name: "Familie", color: "#2F5D8A" },
    { id: "arbeit", name: "Arbeit", color: "#6B4FA0" },
    { id: "schule", name: "Schule", color: "#B7791F" }
  ];
  // Farbpaletten bekannter Kalender-Apps, damit die eigenen Farben zum bisherigen Kalender passen
  const PALETTES = {
    "Ruhig (Standard)": ["#2E7D4F", "#2F5D8A", "#6B4FA0", "#B7791F", "#5E5E5A", "#8A3B5C"],
    "Google Kalender": ["#D50000", "#E67C73", "#F4511E", "#F6BF26", "#33B679", "#0B8043", "#039BE5", "#3F51B5", "#7986CB", "#8E24AA", "#616161"],
    "Apple Kalender": ["#FF3B30", "#FF9500", "#FFCC00", "#34C759", "#007AFF", "#AF52DE", "#A2845E"]
  };
  const MAX_CATS = 8, MAX_ENTRIES = 1500;
  const WDS = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"];
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const uid = () => Math.random().toString(36).slice(2, 10);

  function load(){
    try {
      const m = JSON.parse(localStorage.getItem(KEY) || "null");
      if (m && Array.isArray(m.cats) && Array.isArray(m.entries)) return clean(m);
    } catch {}
    return { v: 1, cats: DEFAULT_CATS.map(c => ({ ...c })), entries: [] };
  }
  function clean(m){
    const cats = m.cats.filter(c => c && typeof c.id === "string" && HEX.test(c.color || "")).slice(0, MAX_CATS)
      .map(c => ({ id: c.id.slice(0, 20), name: String(c.name || "Kategorie").slice(0, 24), color: c.color }));
    const ids = new Set(cats.map(c => c.id));
    const entries = m.entries.filter(e => e && ISO.test(e.from || "")).slice(0, MAX_ENTRIES).map(e => ({
      id: String(e.id || uid()).slice(0, 12), from: e.from, to: ISO.test(e.to || "") && e.to >= e.from ? e.to : e.from,
      text: String(e.text || "").slice(0, 40), cat: ids.has(e.cat) ? e.cat : (cats[0] && cats[0].id)
    }));
    return { v: 1, cats: cats.length ? cats : DEFAULT_CATS.map(c => ({ ...c })), entries };
  }
  let M = load();
  let saveOk = true;
  function save(){
    try { localStorage.setItem(KEY, JSON.stringify(M)); saveOk = true; } catch { saveOk = false; }
    if (window.KK) window.KK.refreshBands();
  }

  const view = { y: 0, m: 0, sel: "", editCat: "" };

  function kk(){ return window.KK; }
  function dayInfo(year){
    const K = kk(); const out = { hol: {}, br: new Set() };
    if (!K || !K.data) return out;
    const { country, region } = K.state;
    for (const h of K.holidays(country, region, year)) out.hol[h.iso] = h;
    K.bridges(country, region, year).forEach(b => b.days.forEach(d => out.br.add(K.iso(d))));
    return out;
  }
  const isoOf = (y, m, d) => `${y}-${String(m + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
  const catOf = id => M.cats.find(c => c.id === id) || M.cats[0];
  function entriesOn(k){ return M.entries.filter(e => e.from <= k && e.to >= k); }
  function monthName(m){ const K = kk(); return K ? K.months(K.state.country)[m] : ["Jänner","Februar","März","April","Mai","Juni","Juli","August","September","Oktober","November","Dezember"][m]; }

  function gridHTML(){
    const { y, m } = view, info = dayInfo(y);
    const first = new Date(y, m, 1), len = new Date(y, m + 1, 0).getDate(), lead = (first.getDay() + 6) % 7;
    const t = new Date(), tk = isoOf(t.getFullYear(), t.getMonth(), t.getDate());
    const bt = kk() ? kk().BT(kk().state.country, false) : "Fenstertag";
    let h = WDS.map(w => `<div class="mk-wd">${w}</div>`).join("") + "<div></div>".repeat(lead);
    for (let d = 1; d <= len; d++){
      const k = isoOf(y, m, d), hol = info.hol[k], we = ((lead + d - 1) % 7) >= 5;
      let cls = "mk-d"; if (we) cls += " we"; if (hol && hol.kind === "legal") cls += " ho"; else if (hol) cls += " pa";
      if (info.br.has(k)) cls += " br"; if (k === tk) cls += " to"; if (k === view.sel) cls += " sel";
      let tags = hol ? `<span class="mk-hol">${esc(hol.name)}</span>` : (info.br.has(k) ? `<span class="mk-br">${bt}</span>` : "");
      for (const e of entriesOn(k)){ const c = catOf(e.cat); tags += `<span class="mk-tag" style="--c:${c.color}" title="${esc(c.name)}">${esc(e.text || c.name)}</span>`; }
      h += `<button type="button" class="${cls}" data-mk-day="${k}" aria-label="${d}. ${monthName(m)}${hol ? ", " + esc(hol.name) : ""}"><span class="n">${d}</span>${tags}</button>`;
    }
    return h;
  }

  function catOptions(sel){ return M.cats.map(c => `<option value="${esc(c.id)}"${c.id === sel ? " selected" : ""}>${esc(c.name)}</option>`).join(""); }
  function legendHTML(){
    return `<span><i class="mk-sw" style="background:var(--red)"></i>Feiertag</span>` +
      M.cats.map(c => `<span><i class="mk-sw" style="background:${c.color}"></i>${esc(c.name)}</span>`).join("");
  }

  function catEditorHTML(){
    return `<h3>Farben und Kategorien</h3>
<p class="small muted">Übernimm die Farben aus deinem bisherigen Kalender: Kategorie wählen, dann eine Farbe aus der Palette antippen oder eine eigene Farbe einstellen.</p>
<ul class="mk-cats">${M.cats.map(c => `<li${c.id === view.editCat ? ' class="on"' : ""}>
  <button type="button" class="mk-pick" data-mk-editcat="${esc(c.id)}" aria-label="Kategorie ${esc(c.name)} bearbeiten"><i class="mk-sw lg" style="background:${c.color}"></i></button>
  <input type="text" value="${esc(c.name)}" maxlength="24" data-mk-catname="${esc(c.id)}" aria-label="Name der Kategorie">
  <input type="color" value="${c.color}" data-mk-catcolor="${esc(c.id)}" aria-label="Eigene Farbe für ${esc(c.name)}">
  ${M.cats.length > 1 ? `<button type="button" class="linkbtn small" data-mk-delcat="${esc(c.id)}">entfernen</button>` : ""}
</li>`).join("")}</ul>
${M.cats.length < MAX_CATS ? `<p><button type="button" class="btn ghost" data-mk-addcat>Kategorie hinzufügen</button></p>` : ""}
<div class="mk-pal">${Object.entries(PALETTES).map(([n, cols]) => `<div><div class="small muted">${esc(n)}</div><div class="mk-pal-row">${cols.map(col => `<button type="button" class="mk-sw-btn" style="background:${col}" data-mk-color="${col}" aria-label="Farbe ${col} für die gewählte Kategorie"></button>`).join("")}</div></div>`).join("")}</div>
<p class="small muted" data-mk-editinfo>${view.editCat ? `Palette färbt: <b>${esc(catOf(view.editCat).name)}</b>` : "Tipp: zuerst links auf das Farbfeld einer Kategorie tippen."}</p>`;
  }

  function listHTML(){
    const pre = `${view.y}-${String(view.m + 1).padStart(2, "0")}`;
    const rows = M.entries.filter(e => e.from.slice(0, 7) <= pre && e.to.slice(0, 7) >= pre).sort((a, b) => a.from < b.from ? -1 : 1);
    if (!rows.length) return `<p class="small muted">Noch keine eigenen Einträge im ${monthName(view.m)}.</p>`;
    const f = s => { const [, mm, dd] = s.split("-"); return `${+dd}.${+mm}.`; };
    return `<ul class="mk-list">${rows.map(e => { const c = catOf(e.cat); return `<li><i class="mk-sw" style="background:${c.color}"></i><span class="mono">${f(e.from)}${e.to !== e.from ? "–" + f(e.to) : ""}</span> ${esc(e.text || c.name)} <span class="muted small">· ${esc(c.name)}</span> <button type="button" class="linkbtn small" data-mk-del="${esc(e.id)}">löschen</button></li>`; }).join("")}</ul>`;
  }

  function render(root){
    const full = !root.hasAttribute("data-mk-compact");
    const now = new Date();
    const sel = view.sel || (now.getFullYear() === view.y && now.getMonth() === view.m ? isoOf(view.y, view.m, now.getDate()) : isoOf(view.y, view.m, 1));
    root.innerHTML = `
<div class="mk-head"><button type="button" class="mk-nav" data-mk-prev aria-label="Vormonat">‹</button><h3 class="mk-title">${monthName(view.m)} ${view.y}</h3><button type="button" class="mk-nav" data-mk-next aria-label="Nächster Monat">›</button></div>
<div class="mk-grid">${gridHTML()}</div>
<div class="legend mk-legend">${legendHTML()}</div>
<form class="mk-form no-print" data-mk-form novalidate>
  <label>Von<input type="date" name="from" value="${sel}" required></label>
  ${full ? `<label>Bis (optional)<input type="date" name="to"></label>` : ""}
  <label>Kategorie<select name="cat">${catOptions(M.cats[0].id)}</select></label>
  <label class="grow">Text<input type="text" name="text" maxlength="40" placeholder="Zahnarzt 9 Uhr"></label>
  <button class="btn" type="submit">Eintragen</button>
  <p class="mk-err" data-mk-err role="alert"></p>
</form>
${full ? `<div class="mk-month no-print">${listHTML()}</div>
<div class="mk-tools no-print">
  <label class="mk-chk"><input type="checkbox" data-mk-icshol checked> Feiertage mitnehmen</label>
  <button class="btn" type="button" data-mk-ics>Als Kalenderdatei (.ics) aufs Handy</button>
  <button class="btn ghost" type="button" data-mk-print>Monat drucken / als PDF sichern</button>
  <button class="btn ghost" type="button" data-mk-backup>Sicherung speichern</button>
  <label class="btn ghost mk-file">Sicherung laden<input type="file" accept="application/json,.json" data-mk-restore hidden></label>
</div>
<div class="mk-editor no-print">${catEditorHTML()}</div>` : ""}
${saveOk ? "" : `<p class="mk-err">Dein Browser erlaubt hier kein Speichern (z. B. privates Fenster). Einträge gehen beim Schließen verloren – nutze „Sicherung speichern“.</p>`}`;
  }

  function renderAll(){ document.querySelectorAll("[data-mk]").forEach(render); }

  function icsEscape(s){ return String(s).replace(/\\/g, "\\\\").replace(/;/g, "\\;").replace(/,/g, "\\,").replace(/\r?\n/g, "\\n"); }
  function exportICS(withHol){
    const K = kk(), stamp = new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d+/, "");
    const next = s => { const d = new Date(s + "T12:00:00"); d.setDate(d.getDate() + 1); return d.toISOString().slice(0, 10).replace(/-/g, ""); };
    const L = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Kalenderkompass 24//Mein Kalender//DE", "CALSCALE:GREGORIAN", "X-WR-CALNAME:Mein Kalender (Kalenderkompass 24)"];
    for (const e of M.entries){
      const c = catOf(e.cat);
      L.push("BEGIN:VEVENT", `UID:${e.id}-${e.from.replace(/-/g, "")}@kalenderkompass24.de`, `DTSTAMP:${stamp}`, `DTSTART;VALUE=DATE:${e.from.replace(/-/g, "")}`, `DTEND;VALUE=DATE:${next(e.to)}`, `SUMMARY:${icsEscape(e.text || c.name)}`, `CATEGORIES:${icsEscape(c.name)}`, "TRANSP:TRANSPARENT", "END:VEVENT");
    }
    if (withHol && K && K.data){
      const { country, region } = K.state;
      for (const y of [view.y, view.y + 1]) for (const h of K.holidays(country, region, y))
        L.push("BEGIN:VEVENT", `UID:fei-${h.iso.replace(/-/g, "")}-${country}-${region || "all"}@kalenderkompass24.de`, `DTSTAMP:${stamp}`, `DTSTART;VALUE=DATE:${h.iso.replace(/-/g, "")}`, `DTEND;VALUE=DATE:${next(h.iso)}`, `SUMMARY:${icsEscape(h.name)}`, "CATEGORIES:Feiertag", "TRANSP:TRANSPARENT", "END:VEVENT");
    }
    L.push("END:VCALENDAR");
    download(new Blob([L.join("\r\n")], { type: "text/calendar" }), "mein-kalender.ics");
  }
  function download(blob, name){
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = name;
    document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }

  function err(root, msg){ const e = root.querySelector("[data-mk-err]"); if (e) e.textContent = msg; }

  function bind(){
    document.addEventListener("click", ev => {
      const t = ev.target, root = t.closest("[data-mk]"); if (!root) return;
      if (t.closest("[data-mk-prev]")){ view.m--; if (view.m < 0){ view.m = 11; view.y--; } renderAll(); }
      else if (t.closest("[data-mk-next]")){ view.m++; if (view.m > 11){ view.m = 0; view.y++; } renderAll(); }
      else if (t.closest("[data-mk-day]")){ view.sel = t.closest("[data-mk-day]").dataset.mkDay; renderAll(); const f = root.querySelector('[data-mk-form] [name="text"]'); if (f) f.focus(); }
      else if (t.closest("[data-mk-del]")){ const id = t.closest("[data-mk-del]").dataset.mkDel; M.entries = M.entries.filter(e => e.id !== id); save(); renderAll(); }
      else if (t.closest("[data-mk-editcat]")){ view.editCat = t.closest("[data-mk-editcat]").dataset.mkEditcat; renderAll(); }
      else if (t.closest("[data-mk-color]")){
        if (!view.editCat){ const i = root.querySelector("[data-mk-editinfo]"); if (i) i.textContent = "Wähle zuerst links eine Kategorie aus."; return; }
        catOf(view.editCat).color = t.closest("[data-mk-color]").dataset.mkColor; save(); renderAll();
      }
      else if (t.closest("[data-mk-addcat]")){ if (M.cats.length < MAX_CATS){ const c = { id: "k" + uid(), name: "Neue Kategorie", color: "#5E5E5A" }; M.cats.push(c); view.editCat = c.id; save(); renderAll(); } }
      else if (t.closest("[data-mk-delcat]")){
        const id = t.closest("[data-mk-delcat]").dataset.mkDelcat; if (M.cats.length < 2) return;
        M.cats = M.cats.filter(c => c.id !== id); M.entries.forEach(e => { if (e.cat === id) e.cat = M.cats[0].id; }); if (view.editCat === id) view.editCat = ""; save(); renderAll();
      }
      else if (t.closest("[data-mk-ics]")) exportICS(!!(root.querySelector("[data-mk-icshol]") || {}).checked);
      else if (t.closest("[data-mk-print]")){ document.body.classList.add("mk-printing"); window.print(); setTimeout(() => document.body.classList.remove("mk-printing"), 500); }
      else if (t.closest("[data-mk-backup]")) download(new Blob([JSON.stringify(M, null, 1)], { type: "application/json" }), "mein-kalender-sicherung.json");
    });
    document.addEventListener("submit", ev => {
      const f = ev.target.closest("[data-mk-form]"); if (!f) return; ev.preventDefault();
      const root = f.closest("[data-mk]"), from = f.from.value, to = f.to ? f.to.value : "", text = f.text.value.trim();
      if (!ISO.test(from)) return err(root, "Wähle ein Datum.");
      if (to && to < from) return err(root, "„Bis“ liegt vor „Von“.");
      if (to && (new Date(to) - new Date(from)) / 864e5 > 366) return err(root, "Ein Eintrag darf höchstens ein Jahr lang sein.");
      if (!text && !f.cat.value) return err(root, "Gib einen Text ein oder wähle eine Kategorie.");
      if (M.entries.length >= MAX_ENTRIES) return err(root, "Die Höchstzahl an Einträgen ist erreicht. Lösche alte Einträge.");
      M.entries.push({ id: uid(), from, to: to || from, text: text.slice(0, 40), cat: f.cat.value });
      const d = new Date(from + "T12:00:00"); view.y = d.getFullYear(); view.m = d.getMonth(); view.sel = from;
      save(); renderAll();
    });
    document.addEventListener("input", ev => {
      const t = ev.target;
      if (t.matches("[data-mk-form] input")){ const r = t.closest("[data-mk]"); err(r, ""); }
      if (t.matches("[data-mk-catname]")){ catOf(t.dataset.mkCatname).name = t.value.slice(0, 24) || "Kategorie"; save(); }
    });
    document.addEventListener("change", ev => {
      const t = ev.target;
      if (t.matches("[data-mk-catcolor]") && HEX.test(t.value)){ catOf(t.dataset.mkCatcolor).color = t.value; view.editCat = t.dataset.mkCatcolor; save(); renderAll(); }
      else if (t.matches("[data-mk-catname]")) renderAll();
      else if (t.matches("[data-mk-restore]") && t.files && t.files[0]){
        const root = t.closest("[data-mk]"), file = t.files[0];
        if (file.size > 500000) return err(root, "Die Datei ist zu groß für eine Sicherung.");
        file.text().then(txt => { try { const m = JSON.parse(txt); if (!Array.isArray(m.cats) || !Array.isArray(m.entries)) throw 0; M = clean(m); save(); renderAll(); } catch { err(root, "Das ist keine gültige Sicherung von „Mein Kalender“."); } });
      }
    });
    document.addEventListener("kk:change", renderAll);
  }

  function init(){
    if (!document.querySelector("[data-mk]")) return;
    const t = new Date(); view.y = t.getFullYear(); view.m = t.getMonth();
    bind(); renderAll();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init); else init();
})();
