"""Schulferien Österreich und Deutschland – nur amtlich veröffentlichte Termine.

Österreich: oesterreich.gv.at, Ferienkalender 2026/2027 (Stand 25.08.2026).
Deutschland: Kultusministerkonferenz, Ferien im Schuljahr 2026/2027 (Stand 09.10.2025),
eingelesen aus den offiziellen iCal-Dateien (content/ferien_de_2026_27.json).
"""
import json
from datetime import date, timedelta
from pathlib import Path

import holidays as H

SCHOOLYEAR = "2026/2027"
SY_SLUG = "2026-2027"
SY_START, SY_END = date(2026, 9, 1), date(2027, 9, 15)   # Zeitachse
SRC_AT = ("oesterreich.gv.at – Ferienkalender 2026/2027", "https://www.oesterreich.gv.at/de/themen/bildung_und_ausbildung/schulen/Seite.1100114")
SRC_DE = ("Kultusministerkonferenz – Ferien im Schuljahr 2026/2027", "https://www.kmk.org/service/ferienregelung/ferienkalender.html")

D = date.fromisoformat
_E, _W = {"burgenland", "niederoesterreich", "wien"}, None

def _at(slug):
    out = [("Herbstferien", D("2026-10-27"), D("2026-10-31")),
           ("Allerseelen (schulfrei)", D("2026-11-02"), D("2026-11-02")),
           ("Weihnachtsferien", D("2026-12-24"), D("2027-01-06"))]
    if slug in ("wien", "niederoesterreich"): sem = ("2027-02-01", "2027-02-06")
    elif slug in ("burgenland", "kaernten"): sem = ("2027-02-08", "2027-02-13")
    else: sem = ("2027-02-15", "2027-02-20")
    out.append(("Semesterferien", D(sem[0]), D(sem[1])))
    out += [("Osterferien", D("2027-03-20"), D("2027-03-29")),
            ("Pfingstferien", D("2027-05-15"), D("2027-05-17"))]
    out.append(("Sommerferien",) + ((D("2027-07-03"), D("2027-09-05")) if slug in _E else (D("2027-07-10"), D("2027-09-12"))))
    return out

EASTER = H.easter(2027)
PENTECOST = EASTER + timedelta(days=49)

def _de_name(kind, a, b):
    if kind == "Herbst": return "Herbstferien"
    if kind.startswith("Buß"): return "Buß- und Bettag (schulfrei)"
    if kind == "Weihnachten": return "Weihnachtsferien"
    if kind == "Winter": return "Winterferien"
    if kind == "Sommer": return "Sommerferien"
    if kind == "Ostern/Frühjahr":
        return "Osterferien" if (a <= EASTER + timedelta(days=8) and b >= EASTER - timedelta(days=8)) else "Frühjahrsferien"
    # Himmelfahrt/Pfingsten
    if b >= PENTECOST - timedelta(days=1): return "Pfingstferien"
    return "Brückentag nach Christi Himmelfahrt" if a == b else "Himmelfahrt-/Pfingstferien"

_raw = json.loads((Path(__file__).parent / "content" / "ferien_de_2026_27.json").read_text(encoding="utf-8"))

def periods(country, slug):
    """Liste von Dicts: name, start, end, days (Kalendertage), single (bool)."""
    if country == "at":
        raw = _at(slug)
    else:
        raw = [(_de_name(k, D(a), D(b)), D(a), D(b)) for k, a, b in _raw["de"][slug]]
    out = []
    for n, a, b in raw:
        if a == b and not n.startswith(("Allerseelen", "Brückentag", "Buß")): n = f"{n} (einzelner Tag)"
        out.append({"name": n, "start": a, "end": b, "days": (b - a).days + 1, "single": a == b})
    return out

def regions(country):
    return H.AT_REGIONS if country == "at" else {k: v[0] for k, v in H.DE_REGIONS.items()}

def summer(country, slug):
    return next(p for p in periods(country, slug) if p["name"] == "Sommerferien")

def total_days(country, slug):
    return sum(p["days"] for p in periods(country, slug))


if __name__ == "__main__":
    for c in ("at", "de"):
        for s in regions(c):
            print(c, s, total_days(c, s), [(p["name"], p["start"].isoformat(), p["days"]) for p in periods(c, s)][:3])
