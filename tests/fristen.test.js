/* Fristenrechner – Rechenlogik. Nach dem Bauen: node --test tests/fristen.test.js
   Braucht docs/data/feiertage.json (python3 build.py). */
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const F = require("../assets/fristen.js");

const CFG = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "content", "fristen.json"), "utf8"));
const datei = path.join(__dirname, "..", "docs", "data", "feiertage.json");
assert.ok(fs.existsSync(datei), "docs/data/feiertage.json fehlt – zuerst python3 build.py ausführen");
const DATA = JSON.parse(fs.readFileSync(datei, "utf8"));
const REGEL = Object.fromEntries(CFG.regeln.map(r => [r.id, r]));
const JAHRE = [2026, 2027, 2028, 2029, 2030];
function feiertage(land, region) {
  const out = {};
  for (const y of JAHRE) for (const [d, name, kind, note] of DATA.h[`${land}:${region}:${y}`] || []) if (kind === "legal") out[d] = { name, note };
  return out;
}
const rechne = (e) => F.berechne(e, REGEL[e.regel], feiertage(e.land, e.region || ""));

/* Osterfesttabelle der PTB (abgerufen 18.11.2026), wörtlich. */
const PTB = `1980 06.04. 1981 19.04. 1982 11.04. 1983 03.04. 1984 22.04. 1985 07.04. 1986 30.03. 1987 19.04. 1988 03.04.
1989 26.03. 1990 15.04. 1991 31.03. 1992 19.04. 1993 11.04. 1994 03.04. 1995 16.04. 1996 07.04. 1997 30.03.
1998 12.04. 1999 04.04. 2000 23.04. 2001 15.04. 2002 31.03. 2003 20.04. 2004 11.04. 2005 27.03. 2006 16.04.
2007 08.04. 2008 23.03. 2009 12.04. 2010 04.04. 2011 24.04. 2012 08.04. 2013 31.03. 2014 20.04. 2015 05.04.
2016 27.03. 2017 16.04. 2018 01.04. 2019 21.04. 2020 12.04. 2021 04.04. 2022 17.04. 2023 09.04. 2024 31.03.
2025 20.04. 2026 05.04. 2027 28.03. 2028 16.04. 2029 01.04. 2030 21.04. 2031 13.04.`.split(/\s+/);

test("Ostern im Browser-Code stimmt mit der PTB-Tabelle 1980–2031 überein", () => {
  assert.equal(PTB.length, 104);
  for (let i = 0; i < PTB.length; i += 2) {
    const [t, m] = PTB[i + 1].split(".");
    assert.equal(F.iso(F.ostern(+PTB[i])), `${PTB[i]}-${m}-${t}`);
  }
});

test("Karfreitag aus dem Browser-Code = Karfreitag in den deutschen Feiertagsdaten", () => {
  for (const y of JAHRE) {
    const kf = DATA.h[`de:berlin:${y}`].find(h => h[1] === "Karfreitag")[0];
    assert.equal(F.iso(F.karfreitag(y)), kf);
  }
});

test("Rechnerisches Ende: Tage, Wochen, Monate, Jahre", () => {
  const roh = (s, n, u, m = "ereignis") => F.iso(F.rohEnde(F.parse(s), n, u, m).datum);
  assert.equal(roh("2027-03-01", 14, "tage"), "2027-03-15");          // Ereignistag zählt nicht mit
  assert.equal(roh("2027-12-22", 2, "wochen"), "2028-01-05");         // gleicher Wochentag
  assert.equal(roh("2027-05-13", 1, "monate"), "2027-06-13");         // gleiche Zahl
  assert.equal(roh("2027-01-31", 1, "monate"), "2027-02-28");         // Tag fehlt → Monatsletzter
  assert.equal(roh("2028-01-31", 1, "monate"), "2028-02-29");         // Schaltjahr
  assert.equal(roh("2027-01-29", 1, "monate"), "2027-02-28");
  assert.equal(roh("2027-08-31", 6, "monate"), "2028-02-29");
  assert.equal(roh("2027-11-30", 3, "monate"), "2028-02-29");
  assert.equal(roh("2028-02-29", 1, "jahre"), "2029-02-28");          // 29. Februar + 1 Jahr
  assert.equal(roh("2026-12-15", 2, "jahre"), "2028-12-15");
  assert.equal(F.rohEnde(F.parse("2027-01-31"), 1, "monate", "ereignis").fehlt, true);
  assert.equal(F.rohEnde(F.parse("2027-01-28"), 1, "monate", "ereignis").fehlt, false);
  // § 187 Abs. 2, § 188 Abs. 2 zweite Alternative BGB: erster Tag zählt mit
  assert.equal(roh("2027-03-01", 14, "tage", "tagesbeginn"), "2027-03-14");
  assert.equal(roh("2027-03-01", 1, "wochen", "tagesbeginn"), "2027-03-07");
  assert.equal(roh("2027-03-01", 1, "monate", "tagesbeginn"), "2027-03-31");
  assert.equal(roh("2027-01-01", 1, "jahre", "tagesbeginn"), "2027-12-31");
  assert.equal(roh("2027-01-31", 1, "monate", "tagesbeginn"), "2027-02-28");   // § 188 Abs. 3
  assert.equal(roh("2027-03-15", 1, "monate", "tagesbeginn"), "2027-04-14");
});

test("Alle Beispiele der Seite ergeben das dort genannte Ende", () => {
  assert.ok(CFG.beispiele.length >= 5);
  for (const b of CFG.beispiele) {
    const r = rechne(b);
    assert.equal(r.fehler, undefined, b.titel);
    assert.equal(r.roh, b.roh, b.titel + " (rechnerisch)");
    assert.equal(r.ende, b.ende, b.titel + " (Ende)");
  }
});

test("Welche Tage verschieben, hängt von der Vorschrift ab", () => {
  const basis = { land: "at", region: "wien", n: 1, einheit: "tage", modus: "ereignis" };
  const ende = (regel, start, extra = {}) => rechne({ ...basis, ...extra, regel, start }).ende;
  // Karfreitag 26.3.2027: nur Verfahrensvorschriften verschieben (bis Di 30.3., weil Ostermontag Feiertag ist)
  for (const id of ["at-avg", "at-bao", "at-zpo", "at-stpo"]) assert.equal(ende(id, "2027-03-25"), "2027-03-30", id);
  assert.equal(ende("at-abgb", "2027-03-25"), "2027-03-26");
  // 24.12.2026 (Donnerstag): nur AVG und BAO; danach Christtag (Fr), Stefanitag (Sa), Sonntag → Montag 28.12.
  for (const id of ["at-avg", "at-bao"]) assert.equal(ende(id, "2026-12-23"), "2026-12-28", id);
  for (const id of ["at-abgb", "at-zpo", "at-stpo"]) assert.equal(ende(id, "2026-12-23"), "2026-12-24", id);
  // Samstag 6.3.2027 und Sonntag verschieben überall auf Montag 8.3. – in Berlin ist der 8.3. Feiertag (Frauentag) → Dienstag
  for (const r of CFG.regeln) {
    const e = rechne({ land: r.land, region: r.land === "at" ? "wien" : "bayern", regel: r.id, start: "2027-03-05", n: 1, einheit: "tage", modus: "ereignis" });
    assert.equal(e.ende, "2027-03-08", r.id);
    assert.deepEqual(e.schritte.map(s => s.grund), ["Samstag", "Sonntag"], r.id);
  }
  assert.equal(rechne({ land: "de", region: "berlin", regel: "de-bgb", start: "2027-03-05", n: 1, einheit: "tage" }).ende, "2027-03-09");
  // Landespatron (Leopolditag, Mo 15.11.2027 in Wien) verschiebt nichts
  assert.equal(ende("at-avg", "2027-11-14"), "2027-11-15");
  // Allerheiligen Mo 1.11.2027: Bayern ja, Berlin nein
  assert.equal(rechne({ land: "de", region: "bayern", regel: "de-zpo", start: "2027-10-18", n: 2, einheit: "wochen" }).ende, "2027-11-02");
  assert.equal(rechne({ land: "de", region: "berlin", regel: "de-zpo", start: "2027-10-18", n: 2, einheit: "wochen" }).ende, "2027-11-01");
});

test("Tagesbeginn nur, wo die Vorschrift ihn kennt", () => {
  const e = { land: "at", region: "", regel: "at-avg", start: "2027-03-01", n: 1, einheit: "monate", modus: "tagesbeginn" };
  assert.equal(rechne(e).modus, "ereignis");
  assert.equal(rechne(e).roh, "2027-04-01");
  assert.equal(rechne({ ...e, land: "de", regel: "de-bgb" }).modus, "tagesbeginn");
});

test("Das Ende ist nie ein Tag, der laut Vorschrift verschiebt – alle Starttage 2027, alle Vorschriften", () => {
  for (const r of CFG.regeln) {
    const region = r.land === "at" ? "tirol" : "sachsen", ft = feiertage(r.land, region);
    for (let d = F.parse("2027-01-01"); F.iso(d) <= "2027-12-31"; d = F.plus(d, 1)) {
      for (const [n, u] of [[3, "tage"], [2, "wochen"], [1, "monate"], [1, "jahre"]]) {
        const x = F.berechne({ start: F.iso(d), n, einheit: u, modus: "ereignis" }, r, ft);
        assert.equal(x.fehler, undefined);
        assert.equal(F.grund(F.parse(x.ende), r, ft), "", `${r.id} ${F.iso(d)} ${n} ${u}`);
        assert.ok(x.ende >= x.roh && x.roh > x.start);
        assert.ok(x.schritte.length <= 6, "höchstens Karfreitag bis Ostermontag bzw. 24.–27. Dezember");
        assert.equal(x.kalendertage, Math.round((F.parse(x.ende) - F.parse(x.start)) / 864e5));
      }
    }
  }
});

test("Unsinnseingaben liefern eine Meldung, keinen Absturz", () => {
  const ok = { land: "at", region: "wien", regel: "at-avg", start: "2027-02-26", n: 4, einheit: "wochen", modus: "ereignis" };
  assert.equal(rechne(ok).fehler, undefined);
  for (const start of ["", "heute", "2027-02-30", "2027-13-01", "27-02-26", "<script>alert(1)</script>", "2027-02-26T00:00", null, undefined, 5]) {
    assert.match(rechne({ ...ok, start }).fehler, /gültiges Datum/, String(start));
  }
  for (const n of ["", "abc", "0", "-3", "1.5", "1e9", "1000", "<img src=x onerror=alert(1)>", " ", null, NaN, Infinity]) {
    assert.match(rechne({ ...ok, n }).fehler, /ganze Zahl/, String(n));
  }
  assert.match(rechne({ ...ok, einheit: "stunden" }).fehler, /Einheit/);
  assert.match(F.berechne(ok, undefined, {}).fehler, /Vorschrift/);
  assert.match(rechne({ ...ok, start: "2025-12-31" }).fehler, /Feiertagsdaten/);
  assert.match(rechne({ ...ok, start: "2030-12-20", n: 1, einheit: "tage" }).fehler, /Feiertagsdaten/);
  assert.equal(rechne({ ...ok, start: "2030-12-19", n: 1, einheit: "tage" }).ende, "2030-12-20");
  assert.match(rechne({ ...ok, n: 999, einheit: "jahre" }).fehler, /Feiertagsdaten/);
});

test("Hinweise: Karfreitag im Vertragsrecht, Gemeindefeiertage, fehlender Monatstag", () => {
  const h = (e) => { const r = rechne(e), ft = feiertage(e.land, e.region || ""); return F.hinweise(r, REGEL[e.regel], e, ft, F.regionaleTage(e.land, e.region, JAHRE)).join(" | "); };
  assert.match(h(CFG.beispiele[1]), /Karfreitag/);
  assert.doesNotMatch(h(CFG.beispiele[0]), /Karfreitag/);
  assert.match(h(CFG.beispiele[2]), /Monatsletzten/);
  // Mariä Himmelfahrt 2028 (Dienstag) in Bayern: verschiebt, mit Hinweis auf die Gemeinden
  const by = { land: "de", region: "bayern", regel: "de-bgb", start: "2028-08-01", n: 2, einheit: "wochen", modus: "ereignis" };
  assert.equal(rechne(by).ende, "2028-08-16");
  assert.match(h(by), /überwiegend katholischer Bevölkerung/);
  // Fronleichnam 2027 in Sachsen: kein landesweiter Feiertag → kein Verschieben, aber Hinweis
  const sn = { land: "de", region: "sachsen", regel: "de-zpo", start: "2027-05-13", n: 2, einheit: "wochen", modus: "ereignis" };
  assert.equal(rechne(sn).ende, "2027-05-27");
  assert.match(h(sn), /Oberlausitz/);
  assert.match(h({ ...sn, region: "" }), /bundesweiten Feiertagen/);
  // Augsburg: Fristende Freitag, 8.8.2030
  assert.match(h({ land: "de", region: "bayern", regel: "de-bgb", start: "2030-08-01", n: 1, einheit: "wochen", modus: "ereignis" }), /Augsburg/);
});

test("Die Vorschriften-Tabelle ist in sich stimmig", () => {
  const ids = new Set();
  for (const r of CFG.regeln) {
    assert.ok(!ids.has(r.id)); ids.add(r.id);
    assert.ok(["at", "de"].includes(r.land));
    for (const k of ["sa", "so", "ft", "kf", "d24", "tagesbeginn"]) assert.equal(typeof r[k], "boolean", r.id + "." + k);
    assert.ok(r.quellen.length >= 1);
    for (const [name, url] of r.quellen) { assert.ok(name.length > 3); assert.match(url, /^https:\/\/(www\.ris\.bka\.gv\.at|ris\.bka\.gv\.at|www\.gesetze-im-internet\.de)\//); }
    if (r.land === "de") { assert.equal(r.kf, false); assert.equal(r.d24, false); }   // Karfreitag ist dort ohnehin Feiertag
  }
  assert.deepEqual(CFG.regeln.filter(r => r.d24).map(r => r.id).sort(), ["at-avg", "at-bao"]);
  assert.deepEqual(CFG.regeln.filter(r => r.tagesbeginn).map(r => r.id), ["de-bgb"]);
  assert.match(CFG.abruf, /^\d{4}-\d{2}-\d{2}$/);
});
