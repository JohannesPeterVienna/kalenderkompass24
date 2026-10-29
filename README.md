# Kalenderkompass 24

Statische Website für https://kalenderkompass24.de – Feiertage, Brückentage, Urlaubsplaner und Kalenderwochen für Österreich und Deutschland.

- `holidays.py` – Feiertags- und Brückentage-Engine (einzige Datenquelle, mit Selbsttests: `python3 holidays.py`)
- `content/articles.py` – Ratgeber-Artikel
- `templates/`, `assets/` – Vorlagen, CSS, JavaScript, Schriften (lokal gehostet)
- `build.py` – erzeugt die komplette Seite in `docs/` (GitHub Pages veröffentlicht aus `docs/` auf `main`)

Bauen: `pip install jinja2 && python3 build.py`

Werbung: `assets/consent.js` – AdSense-Block-IDs nach der Freigabe in `SLOTS` eintragen. Google Analytics lädt nur nach Einwilligung im Google-CMP (TCF).
