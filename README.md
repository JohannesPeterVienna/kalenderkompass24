# Kalenderkompass 24

Statische Website für https://kalenderkompass24.de – Feiertage, Brückentage, Urlaubsplaner und Kalenderwochen für Österreich und Deutschland.

- `holidays.py` – Feiertags- und Brückentage-Engine (einzige Datenquelle, mit Selbsttests: `python3 holidays.py`)
- `content/articles.py` – Ratgeber-Artikel
- `templates/`, `assets/` – Vorlagen, CSS, JavaScript, Schriften (lokal gehostet)
- `build.py` – erzeugt die komplette Seite in `docs/` (GitHub Pages veröffentlicht aus `docs/` auf `main`)

Bauen: `pip install jinja2 && python3 build.py`

Werbung: `assets/consent.js` – AdSense-Block-IDs nach der Freigabe in `SLOTS` eintragen. Google Analytics lädt nur nach Einwilligung im Google-CMP (TCF). Übergang: Meldet die CMP nach 3 s keine Entscheidung, fragt das eigene „Statistik-Blatt“ in `consent.js` nur nach Analytics (localStorage `kk24-statistik`, 12 Monate); eine echte CMP-Entscheidung hat Vorrang.

- `assets/fristen.js`, `content/fristen.json` – Fristenrechner: Rechenlogik (läuft auch unter Node) und die Vorschriften-Tabelle samt Beispielen; `build.py` erzeugt daraus `fristenrechner.html` und `docs/data/fristen.json`

Tests Rechenlogik: `python3 -m unittest tests/test_feiertage_amtlich.py` (Ostern gegen die PTB-Osterfesttabelle 1980–2031, Österreich gegen § 7 ARG, Bayern und Berlin gegen Landesgesetz bzw. Senatsverwaltung); nach dem Bauen `node --test tests/fristen.test.js` (Fristenrechner) und `node tests/rundgang.browser.mjs` (Playwright: alle Seiten der Sitemap bei 390 und 1366 px, Links, Werkzeuge mit Unsinnseingaben).

Tests: `node --test tests/einwilligung.test.js` (Regeln und Ablauf des Statistik-Blatts), nach dem Bauen `node tests/werbeflaechen.browser.mjs` (Playwright: leere Werbeflächen bleiben unsichtbar, gefüllte erscheinen mit Abstand) und `node tests/ersterbildschirm.browser.mjs` (jede Seite der Sitemap bei 1366×768 und 390×844: oberster Werbeplatz im ersten Bildschirm, 150 px Abstand zu Bedienelementen, Überschrift sichtbar, haftender Platz, Layout-Sprung).

Werbeplätze im ersten Bildschirm (19.11.2026): `kopf` (728×90 / 320×100 unter der Kopfzeile, Seiten mit Werkzeug oben) und `auftakt` (bis 970×250 / 320×100 nach Überschrift und Einleitung). Ihr `<ins>` steht im HTML, die Größen je Bildschirmbreite als `<style>` im `<head>` von `templates/base.html`; Block-ID in `build.py` (`AD_OBEN_SLOT`) und `assets/consent.js` (`SLOTS`).

Shop: `content/shop.py` – `SHOP_FREIGEGEBEN = False`, solange kein echter Kauf funktioniert; dann wird `shop.html` nicht gebaut.
