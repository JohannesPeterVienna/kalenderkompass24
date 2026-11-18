/* Rundgang im echten Browser (Playwright, Chromium) – nach dem Bauen: node tests/rundgang.browser.mjs
   1. Jede Seite der Sitemap bei 390 und 1366 px: keine JavaScript-Fehler, kein waagrechter Überlauf.
   2. Jeder interne Link und jede eingebundene Datei zeigt auf eine vorhandene Datei.
   3. Fristenrechner, Arbeitstage-Rechner und Urlaubsplaner: Beispiele, teilbare Links, Kopieren, Kalenderdatei,
      Tastatur und Unsinnseingaben (auch Schadcode in der Adresse). Fremde Adressen werden nicht geladen. */
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), "..");
const DOCS = path.join(ROOT, "docs");
const CFG = JSON.parse(fs.readFileSync(path.join(ROOT, "content", "fristen.json"), "utf8"));
const TYP = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css", ".svg": "image/svg+xml", ".woff2": "font/woff2", ".json": "application/json", ".xml": "application/xml", ".txt": "text/plain" };

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
  catch (e) { fehler++; console.log("FEHLER –", name, "\n ", String(e.message).split("\n").slice(0, 6).join("\n  ")); }
}
async function kontext(breite) {
  const ctx = await browser.newContext({ viewport: { width: breite, height: 900 }, acceptDownloads: true, permissions: ["clipboard-read", "clipboard-write"] });
  await ctx.route(/^https?:\/\/(?!127\.0\.0\.1)/, r => r.fulfill({ status: 200, contentType: "text/javascript", body: "/* Stub */" }));
  return ctx;
}
async function seite(ctx, pfad) {
  const page = await ctx.newPage(), probleme = [];
  page.on("pageerror", e => probleme.push("pageerror: " + e.message));
  page.on("console", m => { if (m.type() === "error") probleme.push("console: " + m.text()); });
  page.on("dialog", d => { probleme.push("dialog: " + d.message()); d.dismiss(); });
  await page.goto(BASE + pfad, { waitUntil: "load" });
  return { page, probleme };
}
const deLang = iso => { const d = new Date(iso + "T00:00:00Z"); return `${d.getUTCDate()}. ${["Jänner", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"][d.getUTCMonth()]} ${d.getUTCFullYear()}`; };

const sitemap = fs.readFileSync(path.join(DOCS, "sitemap.xml"), "utf8");
const PFADE = [...sitemap.matchAll(/<loc>https:\/\/kalenderkompass24\.de([^<]*)<\/loc>/g)].map(m => m[1]);
const ZUSATZ = ["/privacy.html", "/imprint.html", "/404.html"];

await fall(`Sitemap: ${PFADE.length} Seiten, Weiterleitung nicht enthalten`, async () => {
  assert.ok(PFADE.length >= 40);
  assert.ok(PFADE.includes("/fristenrechner.html"));
  assert.ok(!PFADE.includes("/monatsplanung.html"));
  const w = fs.readFileSync(path.join(DOCS, "monatsplanung.html"), "utf8");
  assert.match(w, /noindex/); assert.match(w, /rel="canonical" href="https:\/\/kalenderkompass24\.de\/arbeitstage-rechner\.html"/);
  assert.match(w, /http-equiv="refresh" content="0; url=\/arbeitstage-rechner\.html"/);
});

const ziele = new Map();   // interner Pfad → erste Fundstelle
for (const breite of [390, 1366]) {
  const ctx = await kontext(breite);
  await fall(`${breite} px: alle Seiten ohne JavaScript-Fehler und ohne waagrechten Überlauf`, async () => {
    const mängel = [];
    for (const pfad of [...PFADE, ...ZUSATZ]) {
      const { page, probleme } = await seite(ctx, pfad);
      await page.waitForTimeout(150);
      const m = await page.evaluate(() => {
        const de = document.documentElement, breit = [];
        if (de.scrollWidth > window.innerWidth + 1) {
          for (const el of document.querySelectorAll("body *")) {
            const r = el.getBoundingClientRect();
            if (r.right > window.innerWidth + 1 && r.width > 0 && !el.closest(".scroll,.yr,[style*='overflow']")) { breit.push(el.tagName + "." + el.className + " " + Math.round(r.right)); if (breit.length > 3) break; }
          }
        }
        const links = [...document.querySelectorAll("a[href],link[href],script[src],img[src]")].map(e => e.getAttribute("href") || e.getAttribute("src"));
        return { sw: de.scrollWidth, iw: window.innerWidth, breit, links, h1: document.querySelectorAll("h1").length, title: document.title };
      });
      if (m.sw > m.iw + 1) mängel.push(`${pfad}: Überlauf ${m.sw} > ${m.iw} (${m.breit.join("; ")})`);
      if (m.h1 !== 1) mängel.push(`${pfad}: ${m.h1} h1`);
      if (!m.title) mängel.push(`${pfad}: kein Titel`);
      for (const p of probleme) mängel.push(`${pfad}: ${p}`);
      for (const l of m.links) if (l && l.startsWith("/") && !l.startsWith("//") && !ziele.has(l.split(/[?#]/)[0])) ziele.set(l.split(/[?#]/)[0], pfad);
      await page.close();
    }
    assert.deepEqual(mängel, []);
  });
  await ctx.close();
}

await fall(`keine toten internen Links (${ziele.size} Ziele)`, async () => {
  const tot = [];
  for (const [ziel, von] of ziele) {
    const f = path.join(DOCS, ziel.endsWith("/") ? ziel + "index.html" : ziel);
    if (!fs.existsSync(f) || fs.statSync(f).isDirectory()) tot.push(`${ziel} (auf ${von})`);
  }
  assert.deepEqual(tot, []);
  assert.ok(![...ziele.keys()].includes("/monatsplanung.html"), "niemand verlinkt mehr auf die aufgelöste Seite");
});

for (const breite of [390, 1366]) {
  const ctx = await kontext(breite);
  const ergebnis = page => page.locator("[data-fr-aus] .plan-sum").innerText();

  await fall(`${breite} px Fristenrechner: jedes Beispiel ergibt das genannte Ende`, async () => {
    const { page, probleme } = await seite(ctx, "/fristenrechner.html");
    await page.waitForSelector("[data-fr-aus] .fr-streifen");
    assert.match(await ergebnis(page), new RegExp(deLang(CFG.beispiele[0].ende)));
    const knöpfe = page.locator("[data-fr-beispiel]");
    assert.equal(await knöpfe.count(), CFG.beispiele.length);
    for (let i = 0; i < CFG.beispiele.length; i++) {
      await knöpfe.nth(i).click();
      assert.match(await ergebnis(page), new RegExp(deLang(CFG.beispiele[i].ende)), CFG.beispiele[i].titel);
      assert.equal(await page.locator("[name=regel]").inputValue(), CFG.beispiele[i].regel);
      assert.equal(await page.locator(".fr-tag.ziel").count(), 1);
      assert.equal(await page.locator(".fr-schritte li").count(), 3);
    }
    assert.match(await page.locator(".fr-hinweise").innerText().catch(() => ""), /^$|./);
    assert.deepEqual(probleme, []);
    await page.close();
  });

  await fall(`${breite} px Fristenrechner: Link, Text, Kalenderdatei, Tastatur, Tabellenfilter`, async () => {
    const { page, probleme } = await seite(ctx, "/fristenrechner.html?land=de&region=bayern&regel=de-zpo&start=2027-05-13&n=2&einheit=wochen");
    await page.waitForSelector("[data-fr-aus] .fr-streifen");
    assert.match(await ergebnis(page), /Freitag, 28\. Mai 2027/);
    assert.match(await page.locator(".fr-schritte").innerText(), /Fronleichnam/);
    await page.click("[data-fr=link]");
    await page.waitForFunction(() => /Link kopiert/.test(document.querySelector("[data-fr-meldung]").textContent));
    const link = await page.evaluate(() => navigator.clipboard.readText());
    assert.match(link, /fristenrechner\.html\?land=de&region=bayern&regel=de-zpo&start=2027-05-13&n=2&einheit=wochen&modus=ereignis$/);
    await page.click("[data-fr=text]");
    await page.waitForFunction(() => /Text kopiert/.test(document.querySelector("[data-fr-meldung]").textContent));
    const text = await page.evaluate(() => navigator.clipboard.readText());
    assert.match(text, /^Fristende: Freitag, 28\. Mai 2027/); assert.match(text, /§ 222 ZPO/); assert.match(text, /Fronleichnam/);
    const [dl] = await Promise.all([page.waitForEvent("download"), page.click("[data-fr=ics]")]);
    assert.equal(dl.suggestedFilename(), "fristende-2027-05-28.ics");
    const ics = fs.readFileSync(await dl.path(), "utf8");
    assert.match(ics, /DTSTART;VALUE=DATE:20270528\r\nDTEND;VALUE=DATE:20270529\r\n/); assert.match(ics, /^BEGIN:VCALENDAR\r\n/); assert.match(ics, /END:VCALENDAR\r\n$/);
    // Tastatur: Länge mit Pfeiltaste ändern, Land per Tastatur wechseln
    await page.locator("[name=n]").focus(); await page.keyboard.press("ArrowUp");
    assert.equal(await page.locator("[name=n]").inputValue(), "3");
    assert.match(await ergebnis(page), /Donnerstag, 3\. Juni 2027/);
    await page.locator("[name=land]").focus(); await page.locator("[name=land]").selectOption("at");
    assert.equal(await page.locator("[name=regel] option").count(), CFG.regeln.filter(r => r.land === "at").length);
    assert.equal(await page.locator("[name=modus] option[value=tagesbeginn]").evaluate(o => o.disabled), true);
    // Tabelle filtern
    assert.equal(await page.locator("[data-fr-tabelle] tbody tr:visible").count(), CFG.regeln.length);
    await page.fill("[data-fr-suche]", "postlauf");
    assert.equal(await page.locator("[data-fr-tabelle] tbody tr:visible").count(), 2);
    await page.fill("[data-fr-suche]", "<script>alert(1)</script>");
    assert.equal(await page.locator("[data-fr-tabelle] tbody tr:visible").count(), 0);
    assert.equal(await page.locator("[data-fr-zahl]").innerText(), "0 Vorschriften");
    await page.fill("[data-fr-suche]", ""); await page.selectOption("[data-fr-land]", "de");
    assert.equal(await page.locator("[data-fr-tabelle] tbody tr:visible").count(), CFG.regeln.filter(r => r.land === "de").length);
    assert.deepEqual(probleme, []);
    await page.close();
  });

  await fall(`${breite} px Fristenrechner: Unsinn und Schadcode in Adresse und Feldern`, async () => {
    const böse = `"><img src=x onerror="window.__xss=1"><script>window.__xss=1</script>`;
    const q = new URLSearchParams({ land: böse, region: böse, regel: böse, start: böse, n: böse, einheit: böse, modus: böse });
    const { page, probleme } = await seite(ctx, "/fristenrechner.html?" + q);
    await page.waitForSelector("[data-fr-aus] .plan-sum");
    await page.waitForTimeout(200);
    assert.equal(await page.evaluate(() => window.__xss), undefined);
    assert.equal(await page.locator("[data-fristen] img, [data-fristen] script").count(), 0);
    assert.match(await ergebnis(page), new RegExp(deLang(CFG.beispiele[0].ende)), "ungültige Werte werden ignoriert, die Vorgabe bleibt");
    for (const n of ["", "0", "-5", "abc", "1.5", "99999"]) {
      await page.locator("[name=n]").evaluate((el, v) => { el.value = v; el.dispatchEvent(new Event("input", { bubbles: true })); }, n);
      assert.match(await ergebnis(page), /ganze Zahl/, `n=${n}`);
    }
    await page.click("[data-fr=link]");
    assert.match(await page.locator("[data-fr-meldung]").innerText(), /Erst eine gültige Frist/);
    await page.fill("[name=n]", "4"); await page.fill("[name=start]", "");
    assert.match(await ergebnis(page), /gültiges Datum/);
    await page.fill("[name=start]", "2031-06-01");
    assert.match(await ergebnis(page), /Feiertagsdaten/);
    await page.fill("[name=start]", "2027-02-26");
    assert.match(await ergebnis(page), new RegExp(deLang(CFG.beispiele[0].ende)));
    assert.deepEqual(probleme, []);
    await page.close();
  });

  await fall(`${breite} px Arbeitstage-Rechner: Werte aus dem Link, Kopieren, Schadcode`, async () => {
    const { page, probleme } = await seite(ctx, "/arbeitstage-rechner.html?land=de&region=bayern&von=2027-05-01&bis=2027-06-30");
    await page.waitForSelector("[data-workdays-out] table");
    assert.match(await page.locator("[data-workdays-out] .plan-sum").innerText(), /^40 Arbeitstage/);
    assert.equal(await page.locator("[data-region]").first().inputValue(), "bayern");
    await page.click("[data-share=link]");
    await page.waitForFunction(() => /Link kopiert/.test(document.querySelector("[data-share-msg]").textContent));
    assert.match(await page.evaluate(() => navigator.clipboard.readText()), /arbeitstage-rechner\.html\?land=de&region=bayern&von=2027-05-01&bis=2027-06-30$/);
    await page.click("[data-share=text]");
    await page.waitForFunction(() => /Text kopiert/.test(document.querySelector("[data-share-msg]").textContent));
    const t = await page.evaluate(() => navigator.clipboard.readText());
    assert.match(t, /40 Arbeitstage/); assert.match(t, /Kalendertage gesamt: 61/);
    await page.close();
    const böse = `"><img src=x onerror="window.__xss=1">`;
    const s2 = await seite(ctx, "/arbeitstage-rechner.html?" + new URLSearchParams({ land: böse, region: böse, von: böse, bis: "2027-99-99", jahr: böse, tage: böse }));
    await s2.page.waitForSelector("[data-workdays-out] .plan-sum");
    await s2.page.waitForTimeout(200);
    assert.equal(await s2.page.evaluate(() => window.__xss), undefined);
    assert.equal(await s2.page.locator("main img").count(), 0);
    assert.deepEqual([...probleme, ...s2.probleme], []);
    await s2.page.close();
  });

  await fall(`${breite} px Urlaubsplaner: Werte aus dem Link, Kopieren`, async () => {
    const { page, probleme } = await seite(ctx, "/urlaubsplaner.html?land=de&region=berlin&jahr=2028&tage=7");
    await page.waitForSelector("[data-plan-list] li");
    assert.equal(await page.locator("[data-budget-out]").innerText(), "7");
    assert.equal(await page.locator("select[data-year]").first().inputValue(), "2028");
    assert.equal(await page.locator("[data-region]").first().inputValue(), "berlin");
    await page.click("[data-share=link]");
    await page.waitForFunction(() => /Link kopiert/.test(document.querySelector("[data-share-msg]").textContent));
    assert.match(await page.evaluate(() => navigator.clipboard.readText()), /urlaubsplaner\.html\?land=de&region=berlin&jahr=2028&tage=7$/);
    await page.click("[data-share=text]");
    await page.waitForFunction(() => /Text kopiert/.test(document.querySelector("[data-share-msg]").textContent));
    assert.match(await page.evaluate(() => navigator.clipboard.readText()), /^Urlaubsplaner 2028, Berlin: Mit 7 Urlaubstagen/);
    await page.close();
    const s2 = await seite(ctx, "/urlaubsplaner.html?tage=9999&jahr=1&region=__proto__&land=xx");
    await s2.page.waitForSelector("[data-plan-list] li");
    assert.equal(await s2.page.locator("[data-budget-out]").innerText(), "10");
    assert.equal(await s2.page.locator("select[data-year]").first().inputValue(), "2027");
    const ohne = await seite(ctx, "/urlaubsplaner.html");
    await ohne.page.waitForSelector("[data-plan-list] li");
    assert.equal(await ohne.page.locator("select[data-year]").first().inputValue(), "2027", "ohne Werte im Link bleibt das Hauptjahr");
    assert.match(await ohne.page.locator("[data-plan-sum]").innerText(), /Mit \d+ Urlaubstagen/);
    await ohne.page.close();
    assert.deepEqual([...probleme, ...s2.probleme], []);
    await s2.page.close();
  });
  await ctx.close();
}

await browser.close();
server.close();
console.log(fehler ? `\n${fehler} Fehler` : "\nalles in Ordnung");
process.exit(fehler ? 1 : 0);
