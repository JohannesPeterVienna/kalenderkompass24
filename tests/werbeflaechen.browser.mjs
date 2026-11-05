/* Leere Werbeflächen im echten Browser (Playwright, Chromium) – nach dem Bauen: node tests/werbeflaechen.browser.mjs
   Google wird durch einen Stub ersetzt, der nie eine Anzeige liefert. Erwartung:
   - ohne data-ad-status="filled" ist keine Werbefläche sichtbar (Höhe 0, kein „Werbung“, kein Abstand);
   - mit data-ad-status="filled" erscheint der Platz samt Beschriftung und dem Abstand zu Bedienelementen. */
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

for (const breite of [390, 1366]) {
  for (const pfad of ["/", "/urlaubsanspruch-oesterreich-deutschland.html"]) {
    await fall(`${breite} px ${pfad}: Stub ohne Anzeige → keine Werbefläche sichtbar`, async () => {
      const { ctx, page, fehlerJs } = await seite(breite, pfad);
      assert.deepEqual(await sichtbar(page), []);
      assert.deepEqual(fehlerJs, []);
      await ctx.close();
    });
  }
}

await fall("1366 px: data-ad-status=filled → Platz, „Werbung“ und 150-px-Abstand sind da", async () => {
  const { ctx, page } = await seite(1366, "/");
  await page.$$eval(".ad.on ins.adsbygoogle", inse => inse.forEach(i => i.setAttribute("data-ad-status", "filled")));
  const boxen = await sichtbar(page);
  const art = Object.fromEntries(boxen.map(b => [b.art, b]));
  assert.ok(art.superbanner && art.superbanner.h >= 90 && art.superbanner.label, "Superbanner sichtbar mit Beschriftung");
  assert.equal(art.superbanner.mb, 120);
  assert.ok(art.rect2 && art.rect2.h >= 250, "Medium Rectangle sichtbar");
  assert.equal(art.rect2.mt, 150, "Abstand 150 px zu Bedienelementen bleibt");
  assert.equal(await page.$$eval(".ad.on", b => b.every(x => x.classList.contains("ad--gefuellt"))), true, "Fallback-Klasse gesetzt");
  await ctx.close();
});

await fall("390 px: unfilled bleibt zu, nur gefüllte Fläche erscheint", async () => {
  const { ctx, page } = await seite(390, "/");
  await page.$eval('.ad.on[data-ad="rect2"] ins.adsbygoogle', i => i.setAttribute("data-ad-status", "unfilled"));
  assert.deepEqual(await sichtbar(page), []);
  await page.$eval('.ad.on[data-ad="rect2"] ins.adsbygoogle', i => i.setAttribute("data-ad-status", "filled"));
  const boxen = await sichtbar(page);
  assert.deepEqual(boxen.map(b => b.art), ["rect2"]);
  await ctx.close();
});

await browser.close();
server.close();
console.log(fehler ? `${fehler} Fall/Fälle fehlgeschlagen` : "Werbeflächen: alle Fälle bestanden");
process.exit(fehler ? 1 : 0);
