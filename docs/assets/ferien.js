/* Kalenderkompass 24 – Schulferien: Countdown und Kalender-Export */
(() => {
  const D = s => { const [y,m,d] = s.split("-").map(Number); return new Date(y, m-1, d); };
  const btn = document.querySelector("[data-ferien-ics]");
  if (!btn) return;
  const rows = JSON.parse(btn.dataset.rows);
  const box = document.querySelector("[data-ferien-next]");
  if (box){
    const t = new Date(); t.setHours(0,0,0,0);
    const cur = rows.find(r => D(r[1]) <= t && t <= D(r[2]));
    const nxt = rows.find(r => D(r[1]) > t);
    const dd = (a,b) => Math.round((b - a) / 864e5);
    const f = s => D(s).toLocaleDateString("de-AT", { day:"numeric", month:"long", year:"numeric" });
    const set = (sel, v) => { const el = box.querySelector(sel); if (el) el.textContent = v; };
    if (cur){ const left = dd(t, D(cur[2])); set("[data-fn-when]", left === 0 ? "Letzter Tag" : `noch ${left} Tag${left===1?"":"e"}`); set("[data-fn-what]", `${cur[0]} laufen gerade`); set("[data-fn-rel]", `bis ${f(cur[2])}`); box.querySelector(".small").textContent = "Jetzt";}
    else if (nxt){ const n = dd(t, D(nxt[1])); set("[data-fn-when]", n === 1 ? "morgen" : `in ${n} Tagen`); set("[data-fn-what]", nxt[0]); set("[data-fn-rel]", `ab ${f(nxt[1])}`); }
  }
  btn.addEventListener("click", () => {
    const stamp = new Date().toISOString().replace(/[-:]/g,"").replace(/\.\d+/,"");
    const iso = d => `${d.getFullYear()}${String(d.getMonth()+1).padStart(2,"0")}${String(d.getDate()).padStart(2,"0")}`;
    const L = ["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//Kalenderkompass 24//DE","CALSCALE:GREGORIAN",`X-WR-CALNAME:${btn.dataset.name}`];
    rows.forEach((r,i) => { const e = D(r[2]); e.setDate(e.getDate()+1);
      L.push("BEGIN:VEVENT",`UID:${r[1]}-${i}-${btn.dataset.file}@kalenderkompass24.de`,`DTSTAMP:${stamp}`,`DTSTART;VALUE=DATE:${r[1].replace(/-/g,"")}`,`DTEND;VALUE=DATE:${iso(e)}`,`SUMMARY:${r[0]}`,"TRANSP:TRANSPARENT","END:VEVENT"); });
    L.push("END:VCALENDAR");
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([L.join("\r\n")], { type:"text/calendar" }));
    a.download = btn.dataset.file; document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  });
})();
