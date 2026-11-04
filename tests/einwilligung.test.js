/* Statistik-Blatt in assets/consent.js – Regeln und Ablauf ohne Browser.
   Start: node --test tests/
   Die Seite wird mit einem kleinen Schein-DOM in einer eigenen VM nachgestellt; Uhr und Timer sind künstlich,
   damit „nach 3 s“ und „nach 12 Monaten“ ohne Warten geprüft werden können. */
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const QUELLE = path.join(__dirname, "..", "assets", "consent.js");
const CODE = fs.readFileSync(QUELLE, "utf8");
const { regel, BLATT_KEY, BLATT_WARTEN } = require(QUELLE);
const MONAT = 30 * 864e5;
const JETZT = Date.UTC(2026, 10, 4, 12, 0, 0);

// ——— Schein-Browser ———
function seite({ tcf = null, gpc = false, gespeichert = null, kekse = [], ohneWerbung = false, start = JETZT } = {}){
  const uhr = { jetzt: start, timer: [] };
  const speicher = new Map(gespeichert ? [[BLATT_KEY, JSON.stringify(gespeichert)]] : []);
  const jar = new Map(kekse.map(k => [k, "1"]));
  const skripte = [];
  const klickHoerer = [];
  const tcfHoerer = [];

  function element(tag){
    const el = {
      tagName: tag.toUpperCase(), dataset: {}, attrs: {}, hidden: false, hoerer: {}, _html: "", parentNode: null, style: {},
      setAttribute(k, v){ this.attrs[k] = String(v); }, hasAttribute(k){ return k in this.attrs; },
      addEventListener(t, f){ (this.hoerer[t] = this.hoerer[t] || []).push(f); },
      set innerHTML(v){ this._html = v; }, get innerHTML(){ return this._html; },
      querySelector(sel){ return sel === "#kk-blatt-titel" && this._html.includes('id="kk-blatt-titel"') ? titel : null; },
      contains(x){ return x === this || (x === titel && this._html.includes("kk-blatt-titel")); },
      after(...els){ els.forEach(e => { e.parentNode = body; body.kinder.push(e); }); },
      focus(){ doc.activeElement = this; },
      getBoundingClientRect(){ return { height: 300 }; },
      classList: { add(){}, remove(){} }
    };
    return el;
  }
  const titel = { focus(){ doc.activeElement = titel; } };
  const body = Object.assign(element("body"), { kinder: [], prepend(...els){ els.forEach(e => { e.parentNode = body; body.kinder.unshift(e); }); } });
  const skip = element("a"); skip.className = "skip"; skip.parentNode = body;
  const knopf = Object.assign(element("button"), { closest: s => s === "[data-privacy-settings]" ? knopf : null });
  const head = { appendChild(s){ skripte.push(s.src); } };
  const doc = {
    currentScript: { hasAttribute: k => k === "data-ohne-werbung" && ohneWerbung },
    documentElement: { lang: "de-AT" }, head, body, activeElement: null,
    createElement: element,
    querySelector: s => s === ".skip" ? skip : null,
    querySelectorAll: () => [],
    addEventListener: (t, f) => { if (t === "click") klickHoerer.push(f); },
    contains: x => x === knopf || body.kinder.includes(x),
    get cookie(){ return [...jar].map(([k, v]) => `${k}=${v}`).join("; "); },
    set cookie(v){
      const [paar, ...rest] = v.split(";").map(s => s.trim());
      const [k, w] = paar.split("=");
      const weg = rest.some(r => r === "max-age=0" || /^expires=Thu, 01 Jan 1970/.test(r));
      if (weg) jar.delete(k); else jar.set(k, w);
    }
  };
  const win = {
    document: doc, navigator: { globalPrivacyControl: gpc }, location: { hostname: "kalenderkompass24.de", hash: "" },
    localStorage: {
      getItem: k => speicher.has(k) ? speicher.get(k) : null,
      setItem: (k, v) => speicher.set(k, String(v)), removeItem: k => speicher.delete(k)
    },
    addEventListener(){},
    setTimeout: (f, ms) => { uhr.timer.push({ f, um: uhr.jetzt + (ms || 0) }); return uhr.timer.length; },
    console
  };
  if (tcf) win.__tcfapi = (cmd, v, cb) => { if (cmd === "addEventListener"){ tcfHoerer.push(cb); if (tcf !== "still") cb(tcf, true); } };
  win.window = win;
  const ctx = vm.createContext(win);
  vm.runInContext(`Date.now = () => __uhr.jetzt; const __D = Date; Date = class extends __D { constructor(...a){ super(...(a.length ? a : [__uhr.jetzt])); } static now(){ return __uhr.jetzt; } };`, Object.assign(ctx, { __uhr: uhr }));
  vm.runInContext(CODE, ctx, { filename: "consent.js" });

  const api = {
    win, doc, uhr, skripte, speicher, jar, knopf,
    laufen(ms){                                 // künstliche Zeit vorspulen und fällige Timer ausführen
      const ziel = uhr.jetzt + ms;
      for (;;){
        uhr.timer.sort((a, b) => a.um - b.um);
        const t = uhr.timer[0];
        if (!t || t.um > ziel) break;
        uhr.timer.shift(); uhr.jetzt = t.um; t.f();
      }
      uhr.jetzt = ziel;
    },
    blatt(){ return body.kinder.find(e => e.className === "kk-blatt") || null; },
    offen(){ const b = api.blatt(); return !!(b && !b.hidden); },
    waehlen(w){ const b = api.blatt(); b.hoerer.click.forEach(f => f({ target: { closest: s => s === "[data-kk-wahl]" ? { dataset: { kkWahl: w } } : null } })); },
    taste(key){ const b = api.blatt(); b.hoerer.keydown.forEach(f => f({ key, preventDefault(){} })); },
    einstellungen(){ klickHoerer.forEach(f => f({ target: knopf })); },
    tcfMelden(tc){ tcfHoerer.forEach(cb => cb(tc, true)); },
    gtm(){ return skripte.filter(s => s && s.includes("googletagmanager.com")).length; },
    werbung(){ return skripte.filter(s => s && s.includes("googlesyndication.com")).length; },
    layer(){ return win.dataLayer.map(a => Array.from(a)); },
    gespeichert(){ const r = speicher.get(BLATT_KEY); return r ? JSON.parse(r) : null; },
    gaAus(){ return win["ga-disable-G-T00HRG2YVF"] === true; }
  };
  return api;
}

const versteckt = { gdprApplies: true, eventStatus: "tcloaded", tcString: "", displayStatus: "hidden", purpose: { consents: {} }, vendor: { consents: {} } };
const googleNein = { gdprApplies: true, eventStatus: "useractioncomplete", tcString: "CQ-nein", displayStatus: "hidden", purpose: { consents: {} }, vendor: { consents: {} } };
const eigeneJa = (zeit = JETZT - 864e5) => ({ v: 1, wahl: "ja", zeit });

function keineWerbeFreigabe(p){
  for (const a of p.layer()) if (a[0] === "consent"){
    const w = a[2] || {};
    for (const k of ["ad_storage", "ad_user_data", "ad_personalization"]) assert.notEqual(w[k], "granted", `${k} darf nie granted werden`);
  }
}

// ——— Regeln ———
test("Regel: echte Google-Entscheidung nur bei useractioncomplete oder tcloaded mit tcString", () => {
  assert.equal(regel.echteEntscheidung({ eventStatus: "useractioncomplete" }), true);
  assert.equal(regel.echteEntscheidung({ eventStatus: "tcloaded", tcString: "CQabc" }), true);
  assert.equal(regel.echteEntscheidung({ eventStatus: "tcloaded", tcString: "" }), false);
  assert.equal(regel.echteEntscheidung({ eventStatus: "cmpuishown", tcString: "CQabc" }), false);
  assert.equal(regel.echteEntscheidung(null), false);
});

test("Regel: Lage je nach CMP, GPC und eigener Wahl", () => {
  const L = o => regel.lage(Object.assign({ tc: null, gpc: false, eintrag: null, jetzt: JETZT }, o));
  assert.equal(L({}), "fragen");                                               // kein __tcfapi
  assert.equal(L({ tc: versteckt }), "fragen");                                // hidden ohne Entscheidung
  assert.equal(L({ tc: Object.assign({}, versteckt, { displayStatus: "disabled" }) }), "fragen");
  assert.equal(L({ tc: Object.assign({}, versteckt, { eventStatus: "cmpuishown", displayStatus: "visible" }) }), "warten");
  assert.equal(L({ tc: googleNein, eintrag: eigeneJa() }), "google");          // CMP schlägt eigene Wahl
  assert.equal(L({ tc: { gdprApplies: false, eventStatus: "tcloaded", tcString: "" } }), "google");
  assert.equal(L({ gpc: true, eintrag: eigeneJa() }), "gpc");
  assert.equal(L({ eintrag: eigeneJa() }), "ja");
  assert.equal(L({ tc: versteckt, eintrag: { v: 1, wahl: "nein", zeit: JETZT } }), "nein");
  assert.equal(L({ eintrag: { v: 2, wahl: "ja", zeit: JETZT } }), "fragen");   // fremde Version
  assert.equal(L({ eintrag: { v: 1, wahl: "vielleicht", zeit: JETZT } }), "fragen");
  assert.equal(L({ eintrag: { v: 1, google: JETZT - 864e5 } }), "warten");     // früher bei Google gewählt, CMP noch stumm
  assert.equal(L({ tc: versteckt, eintrag: { v: 1, google: JETZT - 864e5 } }), "fragen");
});

test("Regel: eigene Wahl gilt 12 Monate, danach wird neu gefragt", () => {
  const zeit = Date.UTC(2025, 10, 4, 12);
  assert.equal(regel.eigeneWahl({ v: 1, wahl: "ja", zeit }, Date.UTC(2026, 10, 4, 11, 59)), "ja");
  assert.equal(regel.eigeneWahl({ v: 1, wahl: "ja", zeit }, Date.UTC(2026, 10, 4, 12, 1)), null);
  assert.equal(regel.eigeneWahl({ v: 1, wahl: "ja", zeit: JETZT + 5 * 864e5 }, JETZT), null);   // Zeitstempel aus der Zukunft
});

test("Regel: nur _ga und _ga_* werden gelöscht, für alle Domain-Varianten", () => {
  assert.deepEqual(regel.gaCookies("_ga=GA1.1; kk=1; _ga_T00HRG2YVF=GS1; _gab=1; FCCDCF=x"), ["_ga", "_ga_T00HRG2YVF"]);
  assert.deepEqual(regel.domains("www.kalenderkompass24.de"), ["", "www.kalenderkompass24.de", ".www.kalenderkompass24.de", "kalenderkompass24.de", ".kalenderkompass24.de"]);
});

// ——— Ablauf auf einer Inhaltsseite ———
test("Ohne __tcfapi: Blatt erst nach 3 s, vor Zustimmung kein googletagmanager, nach Zustimmung genau einmal", () => {
  const p = seite();
  assert.equal(p.werbung(), 1, "AdSense-Code wie bisher");
  p.laufen(BLATT_WARTEN - 10);
  assert.equal(p.offen(), false, "vor 3 s kein Blatt");
  p.laufen(20);
  assert.equal(p.offen(), true, "nach 3 s Blatt sichtbar");
  const html = p.blatt().innerHTML;
  const knoepfe = [...html.matchAll(/<button type="button" class="([^"]+)" data-kk-wahl="(ja|nein)">/g)];
  assert.equal(knoepfe.length, 2, "Zustimmen und Ablehnen vorhanden");
  assert.equal(knoepfe[0][1], knoepfe[1][1], "beide Knöpfe gleich gestaltet");
  assert.match(html, /Google Analytics \(Google Ireland Ltd\.\)/);
  assert.match(html, /Keine Zustimmung zu Werbung/);
  assert.match(html, /href="\/privacy\.html#statistik-fenster"/);
  assert.equal(p.blatt().attrs.role, "dialog");
  assert.equal(p.blatt().attrs["aria-labelledby"], "kk-blatt-titel");
  p.laufen(10000);
  assert.equal(p.gtm(), 0, "ohne Wahl kein GA");
  assert.equal(p.gaAus(), true);

  p.waehlen("ja");
  assert.equal(p.gtm(), 1);
  assert.equal(p.offen(), false);
  assert.equal(p.gaAus(), false);
  const L = p.layer();
  assert.ok(L.some(a => a[0] === "consent" && a[1] === "update" && a[2].analytics_storage === "granted"));
  const cfg = L.find(a => a[0] === "config");
  assert.deepEqual([cfg[1], cfg[2].allow_google_signals, cfg[2].allow_ad_personalization_signals], ["G-T00HRG2YVF", false, false]);
  keineWerbeFreigabe(p);
  const e = p.gespeichert();
  assert.deepEqual([e.v, e.wahl, e.zeit], [1, "ja", p.uhr.jetzt]);

  p.einstellungen(); p.waehlen("ja");
  assert.equal(p.gtm(), 1, "erneutes Zustimmen lädt nicht doppelt");
});

test("Google-Dialog hidden ohne Entscheidung: Blatt erscheint; Ablehnen lädt nichts", () => {
  const p = seite({ tcf: versteckt });
  p.laufen(BLATT_WARTEN + 50);
  assert.equal(p.offen(), true);
  p.waehlen("nein");
  p.laufen(10000);
  assert.equal(p.gtm(), 0);
  assert.equal(p.gaAus(), true);
  assert.equal(p.gespeichert().wahl, "nein");
  keineWerbeFreigabe(p);
});

test("Neu laden: gespeichertes Ja startet GA ohne Blatt, gespeichertes Nein bleibt aus", () => {
  const ja = seite({ gespeichert: eigeneJa() });
  ja.laufen(BLATT_WARTEN - 10);
  assert.equal(ja.gtm(), 0, "auch mit Ja erst nach der Google-Wartezeit");
  ja.laufen(20);
  assert.equal(ja.gtm(), 1); assert.equal(ja.offen(), false);
  const nein = seite({ gespeichert: { v: 1, wahl: "nein", zeit: JETZT - 864e5 }, kekse: ["_ga"] });
  nein.laufen(10000);
  assert.equal(nein.gtm(), 0); assert.equal(nein.offen(), false);
  assert.equal(nein.jar.has("_ga"), false, "alte Analytics-Cookies werden entfernt");
});

test("Google-Entscheidung schlägt eigene Wahl und schließt ein offenes Blatt", () => {
  const p = seite({ gespeichert: eigeneJa(), tcf: googleNein });
  p.laufen(10000);
  assert.equal(p.gtm(), 0, "Google sagt Nein → kein GA trotz eigenem Ja");
  assert.equal(p.offen(), false);
  assert.equal(typeof p.gespeichert().google, "number", "Google-Entscheidung wird vermerkt");
  assert.equal(p.gespeichert().wahl, undefined, "eigene Wahl wird bei Google-Entscheidung gelöscht");

  const q = seite({ tcf: "still" });            // CMP vorhanden, meldet zunächst nichts
  q.laufen(BLATT_WARTEN + 10);
  assert.equal(q.offen(), true);
  q.waehlen("ja");
  assert.equal(q.gtm(), 1);
  q.tcfMelden(googleNein);                      // später echte Google-Entscheidung: Nein
  assert.equal(q.gaAus(), true, "Google-Nein schaltet die über das Blatt gestartete Statistik ab");
  q.einstellungen();
  assert.equal(q.offen(), false, "Einstellungen öffnen jetzt den Google-Dialog, nicht das Blatt");
});

test("Eigenes Ja → Google-Nein → Neuladen ohne tcString: keine Messung, Blatt fragt neu; _ga gelöscht", () => {
  const a = seite({ tcf: "still", kekse: ["_ga", "_ga_T00HRG2YVF", "kk-test"] });
  a.laufen(BLATT_WARTEN + 10);
  a.waehlen("ja");
  assert.equal(a.gtm(), 1);
  a.tcfMelden(googleNein);
  a.laufen(1000);
  assert.equal(a.gaAus(), true);
  assert.equal(a.jar.has("_ga"), false, "_ga nach Google-Nein gelöscht");
  assert.equal(a.jar.has("_ga_T00HRG2YVF"), false);
  assert.equal(a.jar.has("kk-test"), true);
  const rest = a.gespeichert();
  assert.equal(rest.wahl, undefined, "eigenes Ja ist weg");
  // Neuladen: FC-Cookie verloren, CMP meldet wieder nur hidden ohne tcString, localStorage ist noch da
  const b = seite({ tcf: versteckt, gespeichert: rest });
  b.laufen(10000);
  assert.equal(b.gtm(), 0, "keine Messung mit alter eigener Zustimmung");
  assert.equal(b.offen(), true, "Blatt fragt neu");
});

test("Schließen-Knopf ×: kleiner, neutral, speichert nichts; Platz unten frei solange offen", () => {
  const p = seite();
  p.laufen(BLATT_WARTEN + 10);
  const html = p.blatt().innerHTML;
  assert.match(html, /<button type="button" class="kk-blatt__zu" data-kk-wahl="zu" aria-label="Schließen, ohne zu entscheiden">×<\/button>/);
  assert.ok(html.indexOf('data-kk-wahl="nein"') < html.indexOf('data-kk-wahl="zu"'), "× nach den Entscheidungsknöpfen im Tab-Ablauf");
  assert.equal(p.doc.body.style.paddingBottom, "324px", "Platzhalter unter dem Seitenfuß");
  p.waehlen("zu");
  assert.equal(p.offen(), false);
  assert.equal(p.gespeichert(), null);
  assert.equal(p.gtm(), 0);
  assert.equal(p.doc.body.style.paddingBottom, "", "Platzhalter wieder entfernt");
});

test("Google-Dialog sichtbar: kein eigenes Blatt", () => {
  const p = seite({ tcf: { gdprApplies: true, eventStatus: "cmpuishown", displayStatus: "visible", tcString: "" } });
  p.laufen(10000);
  assert.equal(p.offen(), false); assert.equal(p.gtm(), 0);
});

test("gdprApplies false: bestehende Logik, kein Blatt", () => {
  const p = seite({ tcf: { gdprApplies: false, eventStatus: "tcloaded", tcString: "" } });
  p.laufen(10000);
  assert.equal(p.offen(), false);
});

test("GPC: kein Blatt, keine Statistik – auch mit gespeichertem Ja; Einstellungen erklären GPC", () => {
  const p = seite({ gpc: true, gespeichert: eigeneJa() });
  p.laufen(10000);
  assert.equal(p.offen(), false); assert.equal(p.gtm(), 0);
  p.einstellungen();
  assert.equal(p.blatt().dataset.art, "gpc");
  assert.doesNotMatch(p.blatt().innerHTML, /data-kk-wahl="ja"/);
});

test("Nach 12 Monaten wird wieder gefragt", () => {
  const alt = seite({ gespeichert: eigeneJa(JETZT - 13 * MONAT) });
  alt.laufen(BLATT_WARTEN + 10);
  assert.equal(alt.offen(), true); assert.equal(alt.gtm(), 0);
  const jung = seite({ gespeichert: eigeneJa(JETZT - 11 * MONAT) });
  jung.laufen(BLATT_WARTEN + 10);
  assert.equal(jung.offen(), false); assert.equal(jung.gtm(), 1);
});

test("Widerruf über Datenschutz-Einstellungen: GA aus, _ga-Cookies weg, andere Cookies bleiben", () => {
  const p = seite({ gespeichert: eigeneJa(), kekse: ["_ga", "_ga_T00HRG2YVF", "kk-test"] });
  p.laufen(BLATT_WARTEN + 10);
  assert.equal(p.gtm(), 1);
  p.einstellungen();
  assert.equal(p.offen(), true);
  assert.match(p.blatt().innerHTML, /Stand: zugestimmt am 3\. November 2026/);
  assert.equal(p.doc.activeElement !== null, true, "Fokus springt ins Blatt");
  p.waehlen("nein");
  assert.equal(p.gaAus(), true);
  assert.equal(p.jar.has("_ga"), false); assert.equal(p.jar.has("_ga_T00HRG2YVF"), false);
  assert.equal(p.jar.has("kk-test"), true);
  const letzte = p.layer().filter(a => a[0] === "consent" && a[1] === "update").pop();
  assert.deepEqual(Object.keys(letzte[2]), ["analytics_storage"], "Widerruf fasst nur analytics_storage an");
  assert.equal(letzte[2].analytics_storage, "denied");
  assert.equal(p.doc.activeElement, p.knopf, "Fokus zurück auf den Knopf");
  keineWerbeFreigabe(p);
});

test("Escape schließt ohne Zustimmung und ohne Speichern", () => {
  const p = seite();
  p.laufen(BLATT_WARTEN + 10);
  p.taste("Escape");
  assert.equal(p.offen(), false);
  assert.equal(p.gespeichert(), null);
  assert.equal(p.gtm(), 0);
});

// ——— Seiten ohne Werbung (Impressum, Datenschutz, 404) ———
test("Seite ohne Werbung: kein Google-Skript, kein Blatt von selbst, Widerruf möglich", () => {
  const p = seite({ ohneWerbung: true, gespeichert: eigeneJa(), kekse: ["_ga"] });
  p.laufen(10000);
  assert.equal(p.werbung(), 0); assert.equal(p.gtm(), 0); assert.equal(p.offen(), false);
  p.einstellungen();
  assert.equal(p.offen(), true);
  p.waehlen("nein");
  assert.equal(p.gespeichert().wahl, "nein");
  assert.equal(p.jar.has("_ga"), false);
  p.einstellungen(); p.waehlen("ja");
  assert.equal(p.gtm(), 0, "auch nach Zustimmung wird hier nichts geladen");

  const g = seite({ ohneWerbung: true, gespeichert: { v: 1, google: JETZT - 864e5 } });
  g.einstellungen();
  assert.equal(g.blatt().dataset.art, "google", "bei Google-Entscheidung Verweis auf eine Inhaltsseite");
  assert.match(g.blatt().innerHTML, /href="\/#datenschutz-einstellungen"/);
});

test("localStorage gesperrt: Wahl gilt wenigstens für den Seitenaufruf", () => {
  const p = seite();
  p.win.localStorage.getItem = () => { throw new Error("blockiert"); };
  p.win.localStorage.setItem = () => { throw new Error("blockiert"); };
  p.laufen(BLATT_WARTEN + 10);
  assert.equal(p.offen(), true);
  p.waehlen("ja");
  assert.equal(p.gtm(), 1);
});
