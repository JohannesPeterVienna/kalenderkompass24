"""Feiertags- und Brückentage-Engine für Österreich und Deutschland.

Einzige Datenquelle der Website: build.py erzeugt daraus die statischen Seiten
und die JSON-Datei, die das JavaScript im Browser verwendet.

Rechtsgrundlagen:
- Österreich: § 7 Abs. 2 Arbeitsruhegesetz (13 gesetzliche Feiertage, bundesweit gleich).
  Landespatrone sind keine gesetzlichen Feiertage, meist aber schulfrei.
- Deutschland: Feiertagsgesetze der Länder; 9 bundesweit einheitliche Feiertage.
"""
from datetime import date, timedelta


def easter(year: int) -> date:
    """Ostersonntag nach dem gregorianischen Kalender (anonymer Algorithmus)."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return date(year, month, day + 1)


def buss_und_bettag(year: int) -> date:
    """Mittwoch vor dem 23. November."""
    d = date(year, 11, 22)
    while d.weekday() != 2:
        d -= timedelta(days=1)
    return d


AT_REGIONS = {
    "burgenland": "Burgenland",
    "kaernten": "Kärnten",
    "niederoesterreich": "Niederösterreich",
    "oberoesterreich": "Oberösterreich",
    "salzburg": "Salzburg",
    "steiermark": "Steiermark",
    "tirol": "Tirol",
    "vorarlberg": "Vorarlberg",
    "wien": "Wien",
}

DE_REGIONS = {
    "baden-wuerttemberg": ("Baden-Württemberg", "BW"),
    "bayern": ("Bayern", "BY"),
    "berlin": ("Berlin", "BE"),
    "brandenburg": ("Brandenburg", "BB"),
    "bremen": ("Bremen", "HB"),
    "hamburg": ("Hamburg", "HH"),
    "hessen": ("Hessen", "HE"),
    "mecklenburg-vorpommern": ("Mecklenburg-Vorpommern", "MV"),
    "niedersachsen": ("Niedersachsen", "NI"),
    "nordrhein-westfalen": ("Nordrhein-Westfalen", "NW"),
    "rheinland-pfalz": ("Rheinland-Pfalz", "RP"),
    "saarland": ("Saarland", "SL"),
    "sachsen": ("Sachsen", "SN"),
    "sachsen-anhalt": ("Sachsen-Anhalt", "ST"),
    "schleswig-holstein": ("Schleswig-Holstein", "SH"),
    "thueringen": ("Thüringen", "TH"),
}

# Landespatrone in Österreich: kein gesetzlicher Feiertag, an Schulen meist frei.
AT_PATRONS = {
    "kaernten": [((3, 19), "Josefitag (Landespatron)"), ((10, 10), "Tag der Volksabstimmung")],
    "steiermark": [((3, 19), "Josefitag (Landespatron)")],
    "tirol": [((3, 19), "Josefitag (Landespatron)")],
    "vorarlberg": [((3, 19), "Josefitag (Landespatron)")],
    "oberoesterreich": [((5, 4), "Florianitag (Landespatron)")],
    "salzburg": [((9, 24), "Rupertitag (Landespatron)")],
    "burgenland": [((11, 11), "Martinitag (Landespatron)")],
    "wien": [((11, 15), "Leopolditag (Landespatron)")],
    "niederoesterreich": [((11, 15), "Leopolditag (Landespatron)")],
}


def at_holidays(year: int):
    e = easter(year)
    return [
        (date(year, 1, 1), "Neujahr"),
        (date(year, 1, 6), "Heilige Drei Könige"),
        (e + timedelta(days=1), "Ostermontag"),
        (date(year, 5, 1), "Staatsfeiertag"),
        (e + timedelta(days=39), "Christi Himmelfahrt"),
        (e + timedelta(days=50), "Pfingstmontag"),
        (e + timedelta(days=60), "Fronleichnam"),
        (date(year, 8, 15), "Mariä Himmelfahrt"),
        (date(year, 10, 26), "Nationalfeiertag"),
        (date(year, 11, 1), "Allerheiligen"),
        (date(year, 12, 8), "Mariä Empfängnis"),
        (date(year, 12, 25), "Christtag"),
        (date(year, 12, 26), "Stefanitag"),
    ]


def de_holidays(year: int, code: str):
    """Gesetzliche Feiertage im Bundesland. Rückgabe: (datum, name, hinweis)."""
    e = easter(year)
    h = [
        (date(year, 1, 1), "Neujahr", ""),
        (e - timedelta(days=2), "Karfreitag", ""),
        (e + timedelta(days=1), "Ostermontag", ""),
        (date(year, 5, 1), "Tag der Arbeit", ""),
        (e + timedelta(days=39), "Christi Himmelfahrt", ""),
        (e + timedelta(days=50), "Pfingstmontag", ""),
        (date(year, 10, 3), "Tag der Deutschen Einheit", ""),
        (date(year, 12, 25), "1. Weihnachtsfeiertag", ""),
        (date(year, 12, 26), "2. Weihnachtsfeiertag", ""),
    ]
    if code in ("BW", "BY", "ST"):
        h.append((date(year, 1, 6), "Heilige Drei Könige", ""))
    if code in ("BE", "MV"):
        h.append((date(year, 3, 8), "Internationaler Frauentag", ""))
    if code == "BB":
        h.append((e, "Ostersonntag", ""))
        h.append((e + timedelta(days=49), "Pfingstsonntag", ""))
    if code in ("BW", "BY", "HE", "NW", "RP", "SL"):
        h.append((e + timedelta(days=60), "Fronleichnam", ""))
    if code == "SL":
        h.append((date(year, 8, 15), "Mariä Himmelfahrt", ""))
    if code == "BY":
        h.append((date(year, 8, 15), "Mariä Himmelfahrt",
                  "gilt in Gemeinden mit überwiegend katholischer Bevölkerung, etwa München"))
    if code == "TH":
        h.append((date(year, 9, 20), "Weltkindertag", ""))
    if code in ("BB", "HB", "HH", "MV", "NI", "SN", "ST", "SH", "TH"):
        h.append((date(year, 10, 31), "Reformationstag", ""))
    if code in ("BW", "BY", "NW", "RP", "SL"):
        h.append((date(year, 11, 1), "Allerheiligen", ""))
    if code == "SN":
        h.append((buss_und_bettag(year), "Buß- und Bettag", ""))
    return sorted(h)


def de_partial_notes(code: str):
    """Feiertage, die nur in Teilen eines Landes gelten und nicht mitgerechnet werden."""
    notes = {
        "SN": "Fronleichnam ist in einigen überwiegend katholischen Gemeinden der Oberlausitz zusätzlich Feiertag.",
        "TH": "Fronleichnam ist in Teilen des Eichsfelds zusätzlich Feiertag.",
        "BY": "In Augsburg ist der 8. August (Hohes Friedensfest) zusätzlich Feiertag.",
    }
    return notes.get(code, "")


def region_holidays(country: str, region: str, year: int):
    """Einheitliche Liste: dicts mit date, name, note, kind ('legal' | 'patron')."""
    out = []
    if country == "at":
        for d, n in at_holidays(year):
            out.append({"date": d, "name": n, "note": "", "kind": "legal"})
        if region:
            for (m, dd), n in AT_PATRONS.get(region, []):
                out.append({"date": date(year, m, dd), "name": n,
                            "note": "kein gesetzlicher Feiertag, an Schulen in der Regel frei",
                            "kind": "patron"})
    else:
        code = DE_REGIONS[region][1] if region else None
        if code:
            for d, n, note in de_holidays(year, code):
                out.append({"date": d, "name": n, "note": note, "kind": "legal"})
        else:
            # bundesweit einheitliche Feiertage
            for d, n, note in de_holidays(year, "XX"):
                out.append({"date": d, "name": n, "note": note, "kind": "legal"})
    return sorted(out, key=lambda x: x["date"])


def off_days(country, region, year):
    """Gesetzliche Feiertage (nur 'legal') als Set, für Brückentage."""
    return {h["date"] for h in region_holidays(country, region, year) if h["kind"] == "legal"}


def is_workday(d: date, holidays: set) -> bool:
    return d.weekday() < 5 and d not in holidays


def bridge_days(country, region, year, max_gap=2):
    """Lücken aus 1–2 Arbeitstagen zwischen freien Tagen, an mindestens einer Seite ein Feiertag.

    Rückgabe: Liste von dicts: days (Arbeitstage, die man frei nimmt), start, end (gesamter
    freier Block), free (Tage am Stück), vacation (benötigte Urlaubstage), holiday (Name).
    """
    hol = set()
    for y in (year - 1, year, year + 1):
        hol |= off_days(country, region, y)
    names = {}
    for y in (year - 1, year, year + 1):
        for h in region_holidays(country, region, y):
            if h["kind"] == "legal":
                names[h["date"]] = h["name"]
    result = []
    d = date(year, 1, 1)
    end_year = date(year, 12, 31)
    while d <= end_year:
        if is_workday(d, hol) and not is_workday(d - timedelta(days=1), hol):
            # Beginn einer Arbeitstag-Folge
            run = []
            x = d
            while is_workday(x, hol):
                run.append(x)
                x += timedelta(days=1)
            before = d - timedelta(days=1)
            after = x
            if len(run) <= max_gap and (before in hol or after in hol):
                # gesamten freien Block bestimmen
                s = before
                while not is_workday(s - timedelta(days=1), hol):
                    s -= timedelta(days=1)
                t = after
                while not is_workday(t + timedelta(days=1), hol):
                    t += timedelta(days=1)
                hname = names.get(before) or names.get(after)
                result.append({
                    "days": run, "start": s, "end": t,
                    "free": (t - s).days + 1, "vacation": len(run), "holiday": hname,
                })
            d = x
        else:
            d += timedelta(days=1)
    return result


if __name__ == "__main__":
    # Plausibilitätsprüfungen gegen bekannte Daten
    assert easter(2026) == date(2026, 4, 5)
    assert easter(2027) == date(2027, 3, 28)
    assert easter(2028) == date(2028, 4, 16)
    assert buss_und_bettag(2027) == date(2027, 11, 17)
    assert len(at_holidays(2027)) == 13
    assert len(de_holidays(2027, "XX")) == 9
    # Brückentag Österreich 2027: Fr 7. Mai (Christi Himmelfahrt Do 6. Mai)
    b = bridge_days("at", "wien", 2027)
    singles = [x["days"][0] for x in b if x["vacation"] == 1]
    assert date(2027, 5, 7) in singles, singles
    assert date(2027, 5, 28) in singles, singles
    for x in b:
        print(x["days"][0], x["vacation"], x["free"], x["holiday"], x["start"], x["end"])
    print("---DE NW")
    for x in bridge_days("de", "nordrhein-westfalen", 2027):
        print(x["days"][0], x["vacation"], x["free"], x["holiday"])
    print("OK")
