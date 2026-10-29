/* Kalenderkompass 24 — alle Werkzeuge laufen im Browser, Eingaben verlassen das Gerät nicht. */
(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const MONTHS = ["Jänner","Februar","März","April","Mai","Juni","Juli","August","September","Oktober","November","Dezember"];
  const MONTHS_DE = ["Januar",...MONTHS.slice(1)];
  const MSHORT = ["Jän","Feb","Mär","Apr","Mai","Jun","Jul","Aug","Sep","Okt","Nov","Dez"];
  const MSHORT_DE = ["Jan",...MSHORT.slice(1)];
  const WD = ["So","Mo","Di","Mi","Do","Fr","Sa"];
  const WDL = ["Sonntag","Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag"];
  const store = {
    get(k){ try { return localStorage.getItem(k); } catch { return null; } },
    set(k,v){ try { localStorage.setItem(k,v); } catch {} }
  };
  const iso = d => `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`;
  const parse = s => { const [y,m,d] = s.split("-").map(Number); return new Date(y, m-1, d); };
  const add = (d, n) => { const x = new Date(d); x.setDate(x.getDate()+n); return x; };
  const today = () => { const t = new Date(); return new Date(t.getFullYear(), t.getMonth(), t.getDate()); };
  const days = (a, b) => Math.round((b - a) / 864e5);

  let DATA = null;
  const state = { country: "at", region: "wien", year: new Date().getFullYear() };

  function months(country){ return country === "at" ? MONTHS : MONTHS_DE; }
  function fmt(d, country, opts = {}){
    const m = months(country)[d.getMonth()];
    return `${opts.weekday === false ? "" : WDL[d.getDay()] + ", "}${d.getDate()}. ${m}${opts.year === false ? "" : " " + d.getFullYear()}`;
  }

  function holidays(country, region, year){
    return (DATA.h[`${country}:${region || ""}:${year}`] || []).map(([date,name,kind,note]) => ({ date: parse(date), iso: date, name, kind, note }));
  }
  function offSet(country, region, years){
    const s = new Set();
    for (const y of years) for (const h of holidays(country, region, y)) if (h.kind === "legal") s.add(h.iso);
    return s;
  }
  const isWork = (d, off) => d.getDay() !== 0 && d.getDay() !== 6 && !off.has(iso(d));

  function bridges(country, region, year){
    const off = offSet(country, region, [year-1, year, year+1]);
    const names = {};
    for (const y of [year-1, year, year+1]) for (const h of holidays(country, region, y)) if (h.kind === "legal") names[h.iso] = h.name;
    const out = [];
    let d = new Date(year, 0, 1); const end = new Date(year, 11, 31);
    while (d <= end){
      if (isWork(d, off) && !isWork(add(d,-1), off)){
        const run = []; let x = new Date(d);
        while (isWork(x, off)){ run.push(new Date(x)); x = add(x,1); }
        const before = add(d,-1), after = x;
        if (run.length <= 2 && (off.has(iso(before)) || off.has(iso(after)))){
          let s = before; while (!isWork(add(s,-1), off)) s = add(s,-1);
          let t = after; while (!isWork(add(t,1), off)) t = add(t,1);
          out.push({ days: run, start: s, end: t, free: days(s,t)+1, vacation: run.length, holiday: names[iso(before)] || names[iso(after)] });
        }
        d = x;
      } else d = add(d,1);
    }
    return out;
  }

  /* Urlaubsplaner: wählt Blöcke mit dem besten Verhältnis freie Tage / Urlaubstage */
  function plan(country, region, year, budget, from){
    const off = offSet(country, region, [year-1, year, year+1]);
    const start = from && from.getFullYear() === year ? from : new Date(year,0,1);
    const end = new Date(year, 11, 31);
    const N = days(start, end) + 1;
    const work = [], hol = [];
    for (let i=0;i<N;i++){ const d = add(start,i); work.push(isWork(d, off) ? 1 : 0); hol.push(off.has(iso(d)) && d.getDay()!==0 && d.getDay()!==6 ? 1 : 0); }
    const holPrefix = [0]; for (let i=0;i<N;i++) holPrefix.push(holPrefix[i] + hol[i]);
    const cand = [];
    for (let i=0;i<N;i++){
      if (!work[i]) continue;
      const startsFree = i===0 || !work[i-1];
      let used = 0;
      for (let j=i;j<N && used<=Math.min(budget,10);j++){
        if (work[j]) used++;
        if (used>Math.min(budget,10)) break;
        // Block muss an mindestens einer Seite an freie Tage grenzen
        if (!startsFree && j+1<N && work[j+1]) continue;
        let s=i; while (s>0 && !work[s-1]) s--;
        let t=j; while (t+1<N && !work[t+1]) t++;
        const free = t - s + 1;
        // Nur Blöcke mit einem Feiertag an einem Werktag – ein einzelner Freitag ist kein Plan
        const hasHoliday = holPrefix[t+1] - holPrefix[s] > 0;
        if (used>0 && hasHoliday) cand.push({ s, t, i, j, used, free, ratio: free/used });
      }
    }
    // Optimale Auswahl: überschneidungsfreie Blöcke, Summe Urlaubstage ≤ Budget, maximal viele freie Tage
    cand.sort((a,b) => a.t - b.t);
    const K = cand.length, B = budget;
    const prev = cand.map(c => { let lo = 0, hi = K - 1, r = -1; while (lo <= hi){ const m = (lo+hi)>>1; if (cand[m].t < c.s){ r = m; lo = m+1; } else hi = m-1; } return r; });
    const score = c => c.free * 100 - c.used; // bei Gleichstand weniger Urlaub
    const dp = Array.from({length: K+1}, () => new Float64Array(B+1));
    for (let k=1;k<=K;k++){
      const c = cand[k-1], pk = prev[k-1] + 1;
      for (let bb=0;bb<=B;bb++){
        let v = dp[k-1][bb];
        if (c.used <= bb){ const w = dp[pk][bb - c.used] + score(c); if (w > v) v = w; }
        dp[k][bb] = v;
      }
    }
    const chosen = []; let k = K, bb = B;
    while (k > 0){
      const c = cand[k-1];
      if (dp[k][bb] === dp[k-1][bb]) { k--; continue; }
      chosen.push(c); bb -= c.used; k = prev[k-1] + 1;
    }
    chosen.sort((a,b)=>a.s-b.s);
    return chosen.map(c => ({ start: add(start,c.s), end: add(start,c.t), takeFrom: add(start,c.i), takeTo: add(start,c.j), used: c.used, free: c.free }));
  }

  /* ---------- Darstellung ---------- */
  function band(el, country, region, year, extra = {}){
    const off = offSet(country, region, [year-1,year,year+1]);
    const hol = Object.fromEntries(holidays(country, region, year).map(h => [h.iso, h]));
    const br = new Set(); bridges(country, region, year).forEach(b => b.days.forEach(d => br.add(iso(d))));
    const va = extra.vacation || new Set();
    const t = iso(today());
    const ms = country === "at" ? MSHORT : MSHORT_DE;
    let html = "";
    for (let m=0;m<12;m++){
      html += `<span class="m">${ms[m]}</span>`;
      const len = new Date(year, m+1, 0).getDate();
      for (let d=1; d<=31; d++){
        if (d>len){ html += `<span class="d x"></span>`; continue; }
        const date = new Date(year, m, d), k = iso(date), h = hol[k];
        let c = "d"; let title = `${WD[date.getDay()]} ${d}. ${ms[m]}`;
        if (date.getDay()===0 || date.getDay()===6) c += " we";
        if (h && h.kind === "legal"){ c += " ho"; title += ` – ${h.name}`; }
        else if (h){ c += " pa"; title += ` – ${h.name}`; }
        if (va.has(k)){ c += " va"; title += " – Urlaubstag"; }
        else if (br.has(k)){ c += " br"; title += " – Brückentag"; }
        if (k === t) c += " to";
        html += `<span class="${c}" title="${title}"></span>`;
      }
    }
    el.innerHTML = html;
    el.setAttribute("aria-label", `Jahresübersicht ${year}: Feiertage rot, Brückentage gelb`);
  }

  function regionLabel(country, region){
    const c = DATA.countries[country];
    return region ? c.regions[region] : c.label;
  }

  function renderNext(){
    const el = $("[data-next]"); if (!el) return;
    const t = today();
    const list = [...holidays(state.country, state.region, t.getFullYear()), ...holidays(state.country, state.region, t.getFullYear()+1)]
      .filter(h => h.kind === "legal" && h.date >= t);
    const h = list[0]; if (!h) return;
    const n = days(t, h.date);
    const rel = n === 0 ? "heute" : n === 1 ? "morgen" : `in ${n} Tagen`;
    el.innerHTML = `<div class="when">${rel}</div><div class="what">${h.name}</div><div class="rel">${fmt(h.date, state.country)} · ${regionLabel(state.country, state.region)}</div>`;
  }

  function renderBridges(){
    $$("[data-bridges]").forEach(el => {
      const list = bridges(state.country, state.region, state.year);
      if (!list.length){ el.innerHTML = `<li class="empty">Für ${regionLabel(state.country,state.region)} gibt es ${state.year} keine Brückentage mit ein oder zwei Urlaubstagen.</li>`; return; }
      el.innerHTML = list.map(b => {
        const take = b.days.map(d => `${WD[d.getDay()]} ${d.getDate()}. ${(state.country==="at"?MSHORT:MSHORT_DE)[d.getMonth()]}`).join(" + ");
        return `<li class="bridge"><span class="chip">${b.vacation}</span><div><div class="take">${take}</div><div class="muted small">rund um ${b.holiday} · frei von ${fmt(b.start,state.country,{year:false})} bis ${fmt(b.end,state.country,{year:false})}</div></div><div class="ratio"><b>${b.free}</b><span class="small muted">Tage frei</span></div></li>`;
      }).join("");
    });
  }

  function renderTable(){
    $$("[data-table]").forEach(el => {
      const rows = holidays(state.country, state.region, state.year);
      el.innerHTML = rows.map(h => {
        const we = h.date.getDay()===0 || h.date.getDay()===6;
        return `<tr class="${we?"we":""} ${h.kind==="patron"?"patron":""}"><td class="date">${h.date.getDate()}. ${months(state.country)[h.date.getMonth()]}</td><td>${WDL[h.date.getDay()]}</td><td>${h.name}${h.note?`<div class="small muted">${h.note}</div>`:""}</td></tr>`;
      }).join("");
    });
    $$("[data-year-label]").forEach(e => e.textContent = state.year);
    $$("[data-region-label]").forEach(e => e.textContent = regionLabel(state.country, state.region));
  }

  function renderBands(){
    $$("[data-band]").forEach(el => band(el, state.country, state.region, state.year));
  }

  function renderPlanner(){
    const root = $("[data-planner]"); if (!root) return;
    const budget = +$("[data-budget]", root).value;
    $("[data-budget-out]", root).textContent = budget;
    const t = today();
    const from = state.year === t.getFullYear() ? t : null;
    const res = plan(state.country, state.region, state.year, budget, from);
    const used = res.reduce((a,b)=>a+b.used,0), free = res.reduce((a,b)=>a+b.free,0);
    const va = new Set(); const off = offSet(state.country,state.region,[state.year]);
    res.forEach(r => { for (let d=new Date(r.takeFrom); d<=r.takeTo; d=add(d,1)) if (isWork(d, off)) va.add(iso(d)); });
    $("[data-plan-sum]", root).innerHTML = res.length
      ? `Mit <b>${used}</b> Urlaubstagen kommst du auf <b>${free}</b> freie Tage in ${res.length} ${res.length===1?"Block":"Blöcken"}${from?" (ab heute gerechnet)":""}.`
      : "Für diesen Zeitraum findet der Planer keinen Block rund um Feiertage mehr.";
    if (res.length && used < budget) $("[data-plan-sum]", root).innerHTML += ` <span class="muted">Die übrigen ${budget-used} Tage bringen rund um Feiertage keinen Vorteil mehr – leg sie in einen längeren Urlaub, etwa im Sommer.</span>`;
    $("[data-plan-list]", root).innerHTML = res.map(r => `<li class="bridge"><span class="chip">${r.used}</span><div><div class="take">${fmt(r.start,state.country,{year:false})} – ${fmt(r.end,state.country,{year:false})}</div><div class="muted small">Urlaub nehmen: ${fmt(r.takeFrom,state.country,{weekday:false,year:false})}${r.used>1?` bis ${fmt(r.takeTo,state.country,{weekday:false,year:false})}`:""}</div></div><div class="ratio"><b>${r.free}</b><span class="small muted">Tage frei</span></div></li>`).join("");
    const b = $("[data-plan-band]", root); if (b) band(b, state.country, state.region, state.year, { vacation: va });
  }

  function ics(){
    const rows = holidays(state.country, state.region, state.year);
    const stamp = new Date().toISOString().replace(/[-:]/g,"").replace(/\.\d+/,"");
    const lines = ["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//Kalenderkompass 24//DE","CALSCALE:GREGORIAN",`X-WR-CALNAME:Feiertage ${state.year} ${regionLabel(state.country,state.region)}`];
    rows.forEach((h,i) => {
      const d = h.iso.replace(/-/g,""), e = iso(add(h.date,1)).replace(/-/g,"");
      lines.push("BEGIN:VEVENT",`UID:${d}-${i}-${state.country}-${state.region}@kalenderkompass24.de`,`DTSTAMP:${stamp}`,`DTSTART;VALUE=DATE:${d}`,`DTEND;VALUE=DATE:${e}`,`SUMMARY:${h.name}`,"TRANSP:TRANSPARENT","END:VEVENT");
    });
    lines.push("END:VCALENDAR");
    const blob = new Blob([lines.join("\r\n")], { type: "text/calendar" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `feiertage-${state.year}-${state.region || state.country}.ics`;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }

  /* ISO-Kalenderwoche */
  function isoWeek(d){
    const x = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
    const day = x.getUTCDay() || 7; x.setUTCDate(x.getUTCDate() + 4 - day);
    const y0 = new Date(Date.UTC(x.getUTCFullYear(),0,1));
    return { week: Math.ceil(((x - y0) / 864e5 + 1) / 7), year: x.getUTCFullYear() };
  }
  function renderKW(){
    $$("[data-kw-now]").forEach(el => {
      const t = today(), w = isoWeek(t);
      const mon = add(t, -((t.getDay()+6)%7)), sun = add(mon, 6);
      el.innerHTML = `<b>KW ${w.week}</b><span>${fmt(mon,"at",{year:false})} bis ${fmt(sun,"at")}</span>`;
    });
    $$("[data-kw-row]").forEach(tr => { if (tr.dataset.kwRow === `${isoWeek(today()).year}-${isoWeek(today()).week}`) tr.style.background = "var(--sea-soft)"; });
  }

  /* Arbeitstage-Rechner */
  function renderWorkdays(){
    const root = $("[data-workdays]"); if (!root) return;
    const a = $("[name=from]", root).value, b = $("[name=to]", root).value, out = $("[data-workdays-out]", root);
    if (!a || !b){ out.textContent = "Wähle Start- und Enddatum."; return; }
    let s = parse(a), e = parse(b);
    if (e < s) [s,e] = [e,s];
    const off = offSet(state.country, state.region, [...new Set([s.getFullYear(), e.getFullYear()])]);
    let total = 0, work = 0, hol = 0, we = 0;
    for (let d = new Date(s); d <= e; d = add(d,1)){
      total++;
      if (d.getDay()===0 || d.getDay()===6) we++;
      else if (off.has(iso(d))) hol++;
      else work++;
    }
    out.innerHTML = `<p class="plan-sum"><b>${work}</b> Arbeitstage zwischen ${fmt(s,state.country)} und ${fmt(e,state.country)} (beide Tage mitgezählt).</p><table class="tbl"><tbody><tr><td>Kalendertage gesamt</td><td>${total}</td></tr><tr><td>Samstage und Sonntage</td><td>${we}</td></tr><tr><td>Feiertage an Werktagen (${regionLabel(state.country,state.region)})</td><td>${hol}</td></tr><tr><td>Differenz ohne Starttag</td><td>${total-1} Tage</td></tr></tbody></table>`;
  }

  /* ---------- Steuerung ---------- */
  function fillRegions(){
    $$("[data-region]").forEach(sel => {
      const c = DATA.countries[state.country];
      sel.innerHTML = (state.country === "de" ? `<option value="">bundesweit</option>` : `<option value="">ganz Österreich</option>`) +
        Object.entries(c.regions).map(([k,v]) => `<option value="${k}">${v}</option>`).join("");
      sel.value = state.region;
    });
    $$("[data-country]").forEach(sel => sel.value = state.country);
    $$("[data-year]").forEach(sel => sel.value = state.year);
  }
  function renderAll(){ renderNext(); renderBands(); renderBridges(); renderTable(); renderPlanner(); renderWorkdays(); }

  function bind(){
    document.addEventListener("change", e => {
      const t = e.target;
      if (t.matches("[data-country]")){ state.country = t.value; state.region = ""; fillRegions(); }
      else if (t.matches("[data-region]")) state.region = t.value;
      else if (t.matches("[data-year]")) state.year = +t.value;
      else if (!t.closest("[data-workdays]")) return;
      store.set("kk24-region", `${state.country}:${state.region}`);
      renderAll();
    });
    document.addEventListener("input", e => { if (e.target.matches("[data-budget]")) renderPlanner(); });
    document.addEventListener("click", e => { if (e.target.closest("[data-ics]")) ics(); if (e.target.closest("[data-print]")) window.print(); });
  }

  async function init(){
    renderKW();
    const root = document.body;
    if (!$("[data-next],[data-bridges],[data-table],[data-planner],[data-band],[data-workdays]")) return;
    // Seiten mit fester Region (z. B. Feiertage 2027 Wien) geben sie vor
    const fixed = root.dataset.fixed;
    if (fixed){ const [c,r,y] = fixed.split(":"); state.country = c; state.region = r; if (y) state.year = +y; }
    else {
      const saved = store.get("kk24-region");
      if (saved){ const [c,r] = saved.split(":"); state.country = c; state.region = r; }
      else if ((navigator.language||"").toLowerCase() === "de-de"){ state.country = "de"; state.region = ""; }
      if (root.dataset.year) state.year = +root.dataset.year;
    }
    try {
      const res = await fetch("/data/feiertage.json");
      DATA = await res.json();
    } catch { return; } // ohne Daten bleibt der vorgerenderte Inhalt stehen
    fillRegions(); bind(); renderAll();
  }
  init();
})();
