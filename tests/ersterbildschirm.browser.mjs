/* Werbeplätze im ersten Bildschirm (Playwright, Chromium) – nach dem Bauen: node tests/ersterbildschirm.browser.mjs
   Google wird durch einen Stub ersetzt; „gefüllt“ wird simuliert (data-ad-status="filled", responsive Plätze bekommen
   ihre Zielgröße). Geprüft wird jede Seite der Sitemap bei 1366×768 und 390×844:
   1. Der oberste Platz (kopf / auftakt) liegt vollständig im ersten Bildschirm und hat die vorgesehene Größe.
   2. Jeder Platz hält mindestens 150 px Abstand zu jedem Bedienelement im Inhalt und 40 px zu Menü und Seitenfuß.
   3. Die Überschrift ist ohne Scrollen sichtbar; auf Seiten mit Werkzeug oben beginnt das Werkzeug im ersten Bildschirm.
   4. Am Handy liegt im ersten Bildschirm höchstens ein flacher Platz (≤ 100 px); Anzeigen bleiben unter 30 % der Seitenhöhe.
   5. Kein waagrechter Überlauf, keine JavaScript-Fehler.
   6. Haftender Platz (Half Page Ad): nur Desktop, 300 px breit, letzter Platz der Spalte, keine Bedienelemente in der
      Inhaltsspalte, überdeckt nichts und scrollt mit der Spalte hinaus (AdSense-Hilfe 10734935).
   7. Layout-Sprung, wenn Google den obersten Platz füllt, bleibt klein (CLS < 0,05).
   8. Seiten ohne Werbung bleiben ohne Werbeplatz und ohne Google-Skript. */
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const DOCS = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "docs");
const TYP = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css", ".svg": "image/svg+xml", ".woff2": "font/woff2", ".json": "application/json" };
const server = http.createServer((req, res) => {
  const p = decodeURIComponent(req.url.split("?")[0]);
  const f = path.join(DOCS, p.endsWith("/") ? p + "index.html" : p);
  if (!f.startsWith(DOCS) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { "content-type": TYP[path.extname(f)] || "application/octet-stream" });
  res.end(fs.readFileSync(f));
});
await new Promise(r => server.listen(0, "127.0.0.1", r));
const BASE = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch();
let fehler = 0;
async function fall(name, fn) {
  try { await fn(); console.log("ok –", name); }
  catch (e) { fehler++; console.log("FEHLER –", name, "\n ", String(e.message).split("\n").slice(0, 12).join("\n  ")); }
}
async function kontext(w, h) {
  const ctx = await browser.newContext({ viewport: { width: w, height: h } });
  await ctx.route(/^https?:\/\/(?!127\.0\.0\.1)/, r => r.fulfill({ status: 200, contentType: "text/javascript", body: "/* Stub: keine Anzeige */" }));
  return ctx;
}

const sitemap = fs.readFileSync(path.join(DOCS, "sitemap.xml"), "utf8");
const PFADE = [...sitemap.matchAll(/<loc>https:\/\/kalenderkompass24\.de([^<]*)<\/loc>/g)].map(m => m[1]);
const OHNE = ["/imprint.html", "/privacy.html", "/404.html", "/monatsplanung.html"];
const MIT = PFADE.filter(p => !OHNE.includes(p));
const BEDIEN = "main input,main select,main button,main textarea,main summary,main a.btn,main [role=button],main [contenteditable=true],main [tabindex='0']";

// im Browser: alle Plätze als gefüllt darstellen und vermessen
function vermessen(BEDIEN) {
  const mobil = innerWidth < 768;
  document.querySelectorAll(".ad.on ins.adsbygoogle").forEach(i => {
    const b = i.parentElement;
    if (i.getBoundingClientRect().height === 0) {       // responsive Plätze ohne feste Höhe: Zielgröße
      const g = { billboard: [Math.min(970, b.clientWidth), mobil ? 280 : 250], rect: [mobil ? 300 : 336, mobil ? 250 : 280], half: [300, 600] }[b.dataset.ad];
      if (g) { i.style.display = "inline-block"; i.style.width = g[0] + "px"; i.style.height = g[1] + "px"; }
    }
    i.setAttribute("data-ad-status", "filled");
  });
  const sicht = e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== "hidden"; };
  const dist = (a, b) => Math.round(Math.hypot(Math.max(0, a.left - b.right, b.left - a.right), Math.max(0, a.top - b.bottom, b.top - a.bottom)));
  const naechstes = (r, l) => l.reduce((m, e) => { const d = dist(r, e.getBoundingClientRect()); return d < m.d ? { d, was: e.tagName + " " + (e.textContent || "").trim().slice(0, 24) } : m; }, { d: 99999, was: "" });
  const bed = [...document.querySelectorAll(BEDIEN)].filter(sicht);
  const menue = [...document.querySelectorAll("header a,footer a,footer button")].filter(sicht);
  const ads = [...document.querySelectorAll(".ad.on")].filter(sicht).map(b => {
    const r = b.querySelector("ins").getBoundingClientRect();
    return { art: b.dataset.ad, w: Math.round(r.width), h: Math.round(r.height), top: Math.round(r.top), bottom: Math.round(r.bottom), left: r.left, right: r.right,
             bed: naechstes(r, bed), menue: naechstes(r, menue), label: getComputedStyle(b, "::before").content };
  });
  const h1 = document.querySelector("h1").getBoundingClientRect();
  // Beginn des Inhalts: auf Seiten mit Werkzeug oben das Werkzeug bzw. die Auswahl, sonst die Einleitung unter der Überschrift
  const werkzeug = document.querySelector(".ad--kopf") ? document.querySelector(".hero .picker, .layout > div:first-child > :first-child") : document.querySelector("h1 ~ .lead, h1 ~ p");
  const de = document.documentElement;
  return { ads, h1: [Math.round(h1.top), Math.round(h1.bottom)], bed1: bed.length ? Math.round(Math.min(...bed.map(e => e.getBoundingClientRect().top))) : null,
           inhalt1: werkzeug ? Math.round(werkzeug.getBoundingClientRect().top) : null, kopfUnten: Math.round(document.querySelector("header.top").getBoundingClientRect().bottom),
           sw: de.scrollWidth, iw: innerWidth, vh: innerHeight, hoehe: document.querySelector("main").getBoundingClientRect().height,
           werkzeugOben: !!document.querySelector(".ad--kopf") };
}

const ZEILEN = [];
for (const [w, h] of [[1366, 768], [390, 844]]) {
  const ctx = await kontext(w, h);
  await fall(`${w}×${h}: ${MIT.length} Seiten – oberster Platz im ersten Bildschirm, Abstände, Überschrift, kein Überlauf, keine JS-Fehler`, async () => {
    const mängel = [];
    for (const pfad of MIT) {
      const page = await ctx.newPage(), js = [];
      page.on("pageerror", e => js.push(e.message));
      page.on("console", m => { if (m.type() === "error") js.push(m.text()); });
      await page.goto(BASE + pfad, { waitUntil: "load" });
      await page.waitForFunction(() => document.querySelectorAll(".ad.on ins.adsbygoogle").length > 0);
      await page.waitForTimeout(120);
      const m = await page.evaluate(vermessen, BEDIEN);
      const mangel = t => mängel.push(`${pfad}: ${t}`);
      const oben = m.ads.find(a => a.art === "kopf" || a.art === "auftakt");
      if (!oben) mangel("kein Platz kopf/auftakt");
      else {
        if (m.ads[0] !== oben) mangel("oberster Platz ist nicht kopf/auftakt");
        if (oben.top < m.kopfUnten || oben.bottom > m.vh) mangel(`oberster Platz ${oben.top}–${oben.bottom} nicht vollständig im ersten Bildschirm (${m.vh})`);
        const soll = w < 768 ? [320, 100] : oben.art === "kopf" ? [728, 90] : null;
        if (soll && (oben.w !== soll[0] || oben.h !== soll[1])) mangel(`${oben.art} ${oben.w}×${oben.h} statt ${soll.join("×")}`);
        if (!soll && (oben.h !== 250 || oben.w < 600 || oben.w > 970)) mangel(`auftakt ${oben.w}×${oben.h} statt 600…970×250`);
        ZEILEN.push(`${w}×${h} ${pfad} ${oben.art} ${oben.w}×${oben.h} oben ${oben.top} unten ${oben.bottom}`);
      }
      for (const a of m.ads) {
        if (a.bed.d < 150) mangel(`${a.art}: nur ${a.bed.d} px zu „${a.bed.was}“`);
        if (a.menue.d < 40) mangel(`${a.art}: nur ${a.menue.d} px zu Menü/Fuß „${a.menue.was}“`);
        if (a.label !== '"Werbung"') mangel(`${a.art}: Beschriftung ${a.label}`);
        if (a.left < 0 || a.right > m.iw + 0.5) mangel(`${a.art}: ragt seitlich hinaus`);
      }
      if (m.h1[0] < 0 || m.h1[1] > m.vh) mangel(`Überschrift ${m.h1.join("–")} nicht im ersten Bildschirm`);
      if (m.inhalt1 === null || m.inhalt1 >= m.vh - 40) mangel(`Inhalt/Werkzeug beginnt erst bei ${m.inhalt1}`);
      if (m.werkzeugOben && m.bed1 !== null && w >= 1024 && m.bed1 >= m.vh - 40) mangel(`erstes Bedienelement des Werkzeugs erst bei ${m.bed1}`);
      const imSchirm = m.ads.filter(a => a.top < m.vh);
      const flaeche = imSchirm.reduce((s, a) => s + a.w * (Math.min(a.bottom, m.vh) - a.top), 0) / (m.iw * m.vh);
      if (flaeche > 0.3) mangel(`Anzeigen belegen ${(flaeche * 100).toFixed(0)} % des ersten Bildschirms`);
      if (w < 768) {
        if (imSchirm.length !== 1 || imSchirm[0].h > 100) mangel(`mobil im ersten Bildschirm: ${imSchirm.map(a => a.art + " " + a.h).join(", ")}`);
        const anteil = m.ads.reduce((s, a) => s + a.h, 0) / m.hoehe;
        if (anteil > 0.3) mangel(`Anzeigenhöhe ${(anteil * 100).toFixed(0)} % der Seitenhöhe`);
      }
      if (m.sw > m.iw + 1) mangel(`waagrechter Überlauf ${m.sw} > ${m.iw}`);
      if (js.length) mangel("JS: " + js.join(" | "));
      await page.close();
    }
    assert.deepEqual(mängel, []);
  });
  await ctx.close();
}

await fall("Haftender Platz: nur Desktop, 300 px, letzter der Spalte, keine Bedienelemente daneben, überdeckt nichts, scrollt hinaus", async () => {
  const mängel = []; let anzahl = 0;
  const ctx = await kontext(1366, 768);
  for (const pfad of MIT) {
    const page = await ctx.newPage();
    await page.goto(BASE + pfad, { waitUntil: "load" });
    await page.waitForFunction(() => document.querySelectorAll(".ad.on ins.adsbygoogle").length > 0);
    await page.evaluate(vermessen, BEDIEN);
    const haftend = await page.$$eval(".ad.on", l => l.filter(b => ["sticky", "fixed"].includes(getComputedStyle(b).position)).map(b => b.dataset.ad));
    const klasse = await page.$(".side--haftend .ad--half.on");
    if (!klasse) { if (haftend.length) mängel.push(`${pfad}: haftet ohne .side--haftend: ${haftend}`); await page.close(); continue; }
    anzahl++;
    if (haftend.join() !== "half") mängel.push(`${pfad}: haftende Plätze ${haftend.join() || "keiner"}`);
    const lage = await page.evaluate(async BEDIEN => {
      const side = document.querySelector(".side--haftend"), box = side.querySelector(".ad--half"), haupt = side.parentElement.firstElementChild;
      const out = { letzter: side.lastElementChild === box, bedien: [...haupt.querySelectorAll(BEDIEN.replace(/main /g, ""))].length, breite: box.getBoundingClientRect().width, zeilen: [] };
      const schnitt = (a, b) => a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom;
      for (const y of [0, 600, 1500, Math.round(document.documentElement.scrollHeight / 2), document.documentElement.scrollHeight]) {
        scrollTo(0, y); await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
        const r = box.getBoundingClientRect(), s = side.getBoundingClientRect(), h = haupt.getBoundingClientRect();
        const andere = [...side.children].filter(e => e !== box).some(e => schnitt(r, e.getBoundingClientRect()));
        out.zeilen.push({ y: Math.round(scrollY), top: Math.round(r.top), bottom: Math.round(r.bottom), inSpalte: r.top >= s.top - 1 && r.bottom <= s.bottom + 1, ueberdeckt: andere || schnitt(r, h),
                          abstandInhalt: Math.round(r.left - h.right), fuss: Math.round(document.querySelector("footer").getBoundingClientRect().top) });
      }
      scrollTo(0, 0);
      return out;
    }, BEDIEN);
    if (!lage.letzter) mängel.push(`${pfad}: haftender Platz ist nicht der letzte der Spalte`);
    if (lage.bedien) mängel.push(`${pfad}: ${lage.bedien} Bedienelemente in der Inhaltsspalte neben dem haftenden Platz`);
    if (lage.breite > 300) mängel.push(`${pfad}: haftender Platz ${lage.breite} px breit`);
    for (const z of lage.zeilen) {
      if (!z.inSpalte || z.ueberdeckt) mängel.push(`${pfad} @${z.y}: Platz ${z.top}–${z.bottom} verlässt die Spalte oder überdeckt Inhalt`);
      if (z.abstandInhalt < 32) mängel.push(`${pfad} @${z.y}: nur ${z.abstandInhalt} px zum Inhalt`);
      if (z.bottom > z.fuss) mängel.push(`${pfad} @${z.y}: Platz ragt in den Seitenfuß`);
      if (z.top < 0 && z.bottom > 0 && z.bottom < z.fuss - 1 && z.top !== 24 && z.y > 0 && z.top > -600 && z.bottom === 768) mängel.push(`${pfad} @${z.y}: abgeschnitten`);
    }
    if (!lage.zeilen.some(z => z.top === 24)) mängel.push(`${pfad}: Platz haftet nie bei 24 px (${lage.zeilen.map(z => z.top).join(", ")})`);
    await page.close();
  }
  await ctx.close();
  assert.ok(anzahl >= 9, `Seiten mit haftendem Platz: ${anzahl}`);
  // Handy, Tablet und niedrige Fenster: nichts haftet
  for (const [w, h] of [[390, 844], [820, 1180], [1000, 768], [1366, 640]]) {
    const c = await kontext(w, h), page = await c.newPage();
    await page.goto(BASE + "/urlaubsanspruch-oesterreich-deutschland.html", { waitUntil: "load" });
    const pos = await page.$$eval(".ad", l => l.map(b => getComputedStyle(b).position).filter(p => p === "sticky" || p === "fixed"));
    if (pos.length) mängel.push(`${w}×${h}: haftet (${pos})`);
    await c.close();
  }
  assert.deepEqual(mängel, []);
});

// Layout-Sprung: Platz ist von Anfang an reserviert; beim Füllen kommen nur Beschriftung und Abstand dazu
const CLS = [];
for (const [w, h] of [[1366, 768], [390, 844]]) {
  for (const pfad of ["/", "/fristenrechner.html", "/urlaubsanspruch-oesterreich-deutschland.html", "/feiertage-2027-oesterreich.html", "/feiertage-2027-wien.html"]) {
    for (const status of ["filled", "unfilled"]) {
      const ctx = await kontext(w, h), page = await ctx.newPage();
      await page.addInitScript(() => { window.__cls = 0; new PerformanceObserver(l => { for (const e of l.getEntries()) if (!e.hadRecentInput) window.__cls += e.value; }).observe({ type: "layout-shift", buffered: true }); });
      await page.goto(BASE + pfad, { waitUntil: "load" });
      await page.waitForFunction(() => document.querySelectorAll(".ad.on ins.adsbygoogle").length > 0);
      await page.waitForTimeout(700);
      const vor = await page.evaluate(() => window.__cls);
      await page.$eval('.ad--kopf.on ins, .ad--auftakt.on ins', (i, st) => i.setAttribute("data-ad-status", st), status);
      await page.waitForTimeout(700);
      const nach = await page.evaluate(() => window.__cls);
      CLS.push({ w, pfad, status, laden: +vor.toFixed(3), sprung: +(nach - vor).toFixed(3) });
      await ctx.close();
    }
  }
}
await fall("Layout-Sprung: beim Laden < 0,05 und beim Füllen des obersten Platzes < 0,05", async () => {
  const zuGross = CLS.filter(c => c.laden >= 0.05 || (c.status === "filled" && c.sprung >= 0.05));
  assert.deepEqual(zuGross, []);
});
console.log("  CLS (laden / Sprung): " + CLS.map(c => `${c.w} ${c.pfad} ${c.status} ${c.laden}/${c.sprung}`).join(" · "));

await fall("Seiten ohne Werbung: kein Werbeplatz, kein Google-Skript, keine Größenklassen", async () => {
  for (const pfad of OHNE) {
    const html = fs.readFileSync(path.join(DOCS, pfad), "utf8");
    assert.ok(!/data-ad=|adsbygoogle\.js|kk_kopf/.test(html), pfad);
  }
  // nicht indexierte Seiten: Google-Skript (Auto Ads) wie bisher, aber keine festen Plätze
  const noindex = fs.readdirSync(DOCS).filter(f => f.endsWith(".html") && /name="robots" content="noindex/.test(fs.readFileSync(path.join(DOCS, f), "utf8")));
  for (const f of noindex) assert.ok(!/data-ad=/.test(fs.readFileSync(path.join(DOCS, f), "utf8")), f);
});

if (process.argv.includes("--tabelle")) console.log(ZEILEN.join("\n"));
await browser.close();
server.close();
console.log(fehler ? `${fehler} Fall/Fälle fehlgeschlagen` : "Erster Bildschirm: alle Fälle bestanden");
process.exit(fehler ? 1 : 0);
