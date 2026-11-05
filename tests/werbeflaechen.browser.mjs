/* Werbeflächen im echten Browser (Playwright, Chromium) – nach dem Bauen: node tests/werbeflaechen.browser.mjs
   Google wird durch einen Stub ersetzt, der nie eine Anzeige liefert. Erwartung (AdSense-Hilfe 10762946):
   - ohne data-ad-status bleibt das <ins class="adsbygoogle"> sichtbar und ungeschnitten (Breite > 0, kein height:0,
     kein overflow:hidden), nur „Werbung“, Mindesthöhe und Abstände fehlen;
   - data-ad-status="unfilled" → ins display:none, kein Beiwerk;
   - "filled" / "unfill-optimized" → Platz samt Beschriftung und dem Abstand zu Bedienelementen. */
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
  if (!f.startsWith(DOCS) || !fs.existsSync(f)) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { "content-type": TYP[path.extname(f)] || "application/octet-stream" });
  res.end(fs.readFileSync(f));
});
await new Promise(r => server.listen(0, "127.0.0.1", r));
const BASE = `http://127.0.0.1:${server.address().port}`;

const browser = await chromium.launch();
let fehler = 0;
async function fall(name, fn){
  try { await fn(); console.log("ok –", name); }
  catch (e) { fehler++; console.log("FEHLER –", name, "\n ", e.message); }
}

async function seite(breite, pfad){
  const ctx = await browser.newContext({ viewport: { width: breite, height: 900 } });
  // Google-Stub: adsbygoogle.js lädt, füllt aber nichts; alle anderen fremden Adressen bleiben leer
  await ctx.route(/^https?:\/\/(?!127\.0\.0\.1)/, r => r.fulfill({ status: 200, contentType: "text/javascript", body: "/* Stub: keine Anzeige */" }));
  const page = await ctx.newPage();
  const fehlerJs = [];
  page.on("pageerror", e => fehlerJs.push(e.message));
  await page.goto(BASE + pfad);
  await page.waitForFunction(() => document.querySelectorAll(".ad.on ins.adsbygoogle").length > 0);
  return { ctx, page, fehlerJs };
}

const sichtbar = page => page.$$eval(".ad", boxen => boxen.map(b => {
  const r = b.getBoundingClientRect(), cs = getComputedStyle(b);
  if (cs.display === "none") return { h: 0, mt: 0, mb: 0, label: false };      // auf dieser Bildschirmbreite gar nicht vorgesehen
  return { art: b.dataset.ad, h: r.height, mt: parseFloat(cs.marginTop), mb: parseFloat(cs.marginBottom),
           label: getComputedStyle(b, "::before").display !== "none" && r.height > 0 };
}).filter(x => x.h > 0 || x.label || x.mt > 0 || x.mb > 0));

// Zustand jedes aktiven <ins> und seines Platzes
const inse = page => page.$$eval(".ad.on ins.adsbygoogle", l => l.map(i => {
  const b = i.parentElement, ci = getComputedStyle(i), cb = getComputedStyle(b), ri = i.getBoundingClientRect(), rb = b.getBoundingClientRect();
  return { art: b.dataset.ad, insDisplay: ci.display, insVis: ci.visibility, insW: ri.width, insH: ri.height,
           boxOverflow: cb.overflowX + "/" + cb.overflowY, boxH: rb.height, boxVis: cb.visibility, boxDisplay: cb.display,
           label: getComputedStyle(b, "::before").display !== "none", mt: parseFloat(cb.marginTop), mb: parseFloat(cb.marginBottom),
           minH: cb.minHeight };
}));

for (const breite of [390, 1366]) {
  for (const pfad of ["/", "/urlaubsanspruch-oesterreich-deutschland.html"]) {
    await fall(`${breite} px ${pfad}: ohne Status → ins sichtbar und ungeschnitten, Beiwerk aus`, async () => {
      const { ctx, page, fehlerJs } = await seite(breite, pfad);
      const l = await inse(page);
      assert.ok(l.length > 0, "aktive Werbeflächen vorhanden");
      for (const x of l) {
        assert.notEqual(x.insDisplay, "none", `${x.art}: ins nicht display:none`);
        assert.equal(x.insVis, "visible", `${x.art}: ins sichtbar`);
        assert.ok(x.insW > 0, `${x.art}: ins hat Breite`);
        assert.equal(x.boxOverflow, "visible/visible", `${x.art}: Platz schneidet nicht ab`);
        assert.equal(x.boxVis, "visible", `${x.art}: Platz nicht versteckt`);
        assert.notEqual(x.boxDisplay, "none", `${x.art}: Platz nicht display:none`);
        assert.ok(x.boxH >= x.insH, `${x.art}: Platz mindestens so hoch wie das ins`);
        assert.equal(x.label, false, `${x.art}: „Werbung“ ausgeblendet`);
        assert.equal(x.mt + x.mb, 0, `${x.art}: kein Abstand`);
        assert.equal(x.minH, "0px", `${x.art}: keine Mindesthöhe`);
      }
      assert.deepEqual(fehlerJs, []);
      await ctx.close();
    });
  }
}

for (const status of ["filled", "unfill-optimized"]) {
  await fall(`1366 px: data-ad-status=${status} → Platz, „Werbung“ und 150-px-Abstand sind da`, async () => {
    const { ctx, page } = await seite(1366, "/");
    await page.$$eval(".ad.on ins.adsbygoogle", (l, st) => l.forEach(i => i.setAttribute("data-ad-status", st)), status);
    const boxen = await sichtbar(page);
    const art = Object.fromEntries(boxen.map(b => [b.art, b]));
    assert.ok(art.superbanner && art.superbanner.h >= 90 && art.superbanner.label, "Superbanner sichtbar mit Beschriftung");
    assert.equal(art.superbanner.mb, 120);
    assert.ok(art.rect2 && art.rect2.h >= 250 && art.rect2.label, "Medium Rectangle sichtbar mit Beschriftung");
    assert.equal(art.rect2.mt, 150, "Abstand 150 px zu Bedienelementen bleibt");
    assert.equal(await page.$$eval(".ad.on", b => b.every(x => x.classList.contains("ad--gefuellt"))), true, "Fallback-Klasse gesetzt");
    await ctx.close();
  });
}

await fall("390 px: unfilled → ins display:none, kein Beiwerk; filled → Platz erscheint", async () => {
  const { ctx, page } = await seite(390, "/");
  await page.$$eval(".ad.on ins.adsbygoogle", l => l.forEach(i => i.setAttribute("data-ad-status", "unfilled")));
  assert.ok((await inse(page)).every(x => x.insDisplay === "none" && !x.label && x.boxH === 0), "unfilled: ins display:none, Platz ohne Höhe und Beschriftung");
  assert.deepEqual(await sichtbar(page), []);
  await page.$eval('.ad.on[data-ad="rect2"] ins.adsbygoogle', i => i.setAttribute("data-ad-status", "filled"));
  const boxen = await sichtbar(page);
  assert.deepEqual(boxen.map(b => b.art), ["rect2"]);
  assert.ok(boxen[0].label && boxen[0].mt === 150);
  await ctx.close();
});

await fall("ohne :has() (Rückfall-Klassen): leer ohne Beiwerk, ins sichtbar; filled mit Beiwerk", async () => {
  const { ctx, page } = await seite(1366, "/");
  // :has()-Regeln entfernen und den Rückfall erzwingen, wie in einem Browser ohne :has()
  await page.evaluate(() => {
    for (const sh of document.styleSheets) { try { for (let k = sh.cssRules.length - 1; k >= 0; k--) if (sh.cssRules[k].cssText.includes(":has(")) sh.deleteRule(k); } catch (e) {} }
    document.documentElement.classList.add("ad--ohne-has");
  });
  let l = await inse(page);
  assert.ok(l.every(x => x.insDisplay !== "none" && x.insW > 0 && x.boxOverflow === "visible/visible" && !x.label && x.mt + x.mb === 0), "leer: ins sichtbar, kein Beiwerk");
  await page.$$eval(".ad.on ins.adsbygoogle", l => l.forEach(i => i.setAttribute("data-ad-status", "unfill-optimized")));
  l = await inse(page);
  assert.ok(l.every(x => x.label), "unfill-optimized: Beschriftung da");
  assert.equal(l.find(x => x.art === "rect2").mt, 150);
  await ctx.close();
});

await browser.close();
server.close();
console.log(fehler ? `${fehler} Fall/Fälle fehlgeschlagen` : "Werbeflächen: alle Fälle bestanden");
process.exit(fehler ? 1 : 0);
