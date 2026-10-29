"""Schulferien-Seiten für Kalenderkompass 24 (wird von build.py aufgerufen)."""
import json
from datetime import date, timedelta

import ferien as F
import holidays as H

TYPE = {"Sommerferien": "su", "Weihnachtsferien": "xm", "Herbstferien": "au", "Osterferien": "ea",
        "Semesterferien": "wi", "Winterferien": "wi", "Frühjahrsferien": "ea", "Pfingstferien": "pf",
        "Himmelfahrt-/Pfingstferien": "pf"}

def tclass(name):
    for k, v in TYPE.items():
        if name.startswith(k): return v
    return "day"


def legal_dates(country, slug):
    s = set()
    for y in (2026, 2027):
        for h in H.region_holidays(country, slug, y):
            if h["kind"] == "legal": s.add(h["date"])
    return s


def workdays(a, b, legal):
    n, d = 0, a
    while d <= b:
        if d.weekday() < 5 and d not in legal: n += 1
        d += timedelta(days=1)
    return n


def axis():
    total = (F.SY_END - F.SY_START).days
    out, d = [], date(F.SY_START.year, F.SY_START.month, 1)
    while d < F.SY_END:
        nxt = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
        out.append({"left": round((d - F.SY_START).days / total * 100, 3), "label": d.month})
        d = nxt
    return out


def bars(periods, start=F.SY_START, end=F.SY_END):
    total = (end - start).days
    out = []
    for p in periods:
        a, b = max(p["start"], start), min(p["end"], end)
        if b < a: continue
        out.append({"left": round((a - start).days / total * 100, 3), "width": max(round(((b - a).days + 1) / total * 100, 3), .35),
                    "cls": tclass(p["name"]), "title": p["name"], "start": p["start"], "end": p["end"]})
    return out


def run(write, fmt, mshort, crumbs_ld, TODAY, SITE):
    def span(p, c):
        if p["single"]: return fmt(p["start"], c)
        same_y = p["start"].year == p["end"].year
        return f"{fmt(p['start'], c, year=not same_y)} – {fmt(p['end'], c)}"

    WS = ["Mo","Di","Mi","Do","Fr","Sa","So"]
    def short(a, b):
        f = lambda d: f"{WS[d.weekday()]} {d.day}.{d.month}."
        return f(a) if a == b else f"{f(a)}–{f(b)}"

    def axis_ctx(c):
        ms = mshort(c)
        return [{"left": a["left"], "label": ms[a["label"] - 1]} for a in axis()]

    # ---------------- Daten je Region
    data = {}
    for c in ("at", "de"):
        for slug, name in F.regions(c).items():
            ps = F.periods(c, slug)
            legal = legal_dates(c, slug)
            rows = []
            for p in ps:
                rows.append(dict(p, span=span(p, c), short=short(p["start"], p["end"]), wd=workdays(p["start"], p["end"], legal), cls=tclass(p["name"])))
            data[(c, slug)] = {"name": name, "rows": rows, "bars": bars(ps), "total": sum(p["days"] for p in ps),
                               "wd": sum(r["wd"] for r in rows), "summer": F.summer(c, slug)}

    def rank_summer(c):
        lst = sorted(F.regions(c), key=lambda s: (data[(c, s)]["summer"]["start"], s))
        return lst

    country_label = {"at": "Österreich", "de": "Deutschland"}
    leave = {"at": 25, "de": 30}   # AT: 5 Wochen gesetzlich; DE: verbreitet 30 Tage (gesetzlich 20 bei 5-Tage-Woche)

    # ---------------- Seiten je Bundesland
    for c in ("at", "de"):
        regs = F.regions(c)
        order = rank_summer(c)
        for slug, name in regs.items():
            d = data[(c, slug)]
            su = d["summer"]
            pos = order.index(slug) + 1
            same = [regs[s] for s in regs if s != slug and data[(c, s)]["summer"]["start"] == su["start"]]
            upcoming = [r for r in d["rows"] if r["end"] >= TODAY]
            nxt = upcoming[0] if upcoming else d["rows"][-1]
            longest_non_summer = max((r for r in d["rows"] if r["cls"] != "su"), key=lambda r: r["days"])
            gap = d["wd"] - leave[c]
            facts = []
            facts.append(f"Im Schuljahr {F.SCHOOLYEAR} haben Schülerinnen und Schüler in {name} insgesamt {d['total']} Ferientage "
                         f"(Kalendertage inklusive Wochenenden). Die Sommerferien dauern {su['days']} Tage, von {fmt(su['start'], c)} bis {fmt(su['end'], c)}.")
            if c == "de":
                facts.append(f"Mit dem Sommerferienbeginn liegt {name} auf Platz {pos} von 16 Ländern"
                             + (f" – gemeinsam mit {', '.join(same)}" if same else "") + ". "
                             "Die Länder staffeln die Sommerferien, damit nicht ganz Deutschland gleichzeitig verreist; die Reihenfolge wechselt von Jahr zu Jahr.")
            else:
                grp = "Burgenland, Niederösterreich und Wien" if su["start"] == date(2027, 7, 3) else "Kärnten, Oberösterreich, Salzburg, Steiermark, Tirol und Vorarlberg"
                facts.append(f"In Österreich beginnen die Sommerferien in zwei Gruppen: zuerst in Burgenland, Niederösterreich und Wien, eine Woche später "
                             f"in den übrigen Bundesländern. {name} gehört zur Gruppe {grp}. Herbst-, Weihnachts-, Oster- und Pfingstferien sind österreichweit gleich, "
                             f"die Semesterferien sind auf drei Wochen im Februar verteilt.")
            facts.append(f"Die längsten Ferien nach dem Sommer sind die {longest_non_summer['name']} mit {longest_non_summer['days']} Tagen.")
            two = 2 * leave[c]
            if d["wd"] > two:
                tail = (f"Selbst zwei Elternteile mit je {leave[c]} Urlaubstagen decken davon nur {two} ab – "
                        f"{d['wd'] - two} Arbeitstage bleiben für Großeltern, Ferienbetreuung oder Feriencamps. Und dann bliebe kein einziger Urlaubstag für gemeinsame Familienzeit.")
            elif d["wd"] > leave[c]:
                tail = f"Mit {leave[c]} Urlaubstagen allein geht sich das nicht aus; teilen sich zwei Elternteile die Ferien, reicht es rechnerisch."
            else:
                tail = f"Mit {leave[c]} Urlaubstagen ließe sich das rechnerisch allein abdecken."
            facts.append(f"Für berufstätige Eltern: Alle Ferien zusammen enthalten {d['wd']} Arbeitstage (Montag bis Freitag ohne gesetzliche Feiertage). " + tail)
            path = f"schulferien-{F.SY_SLUG}-{slug}.html"
            cslug = "oesterreich" if c == "at" else "deutschland"
            crumbs = [("/", "Start"), (f"/schulferien-{F.SY_SLUG}.html", f"Schulferien {F.SCHOOLYEAR}"), ("/" + path, name)]
            ics = [[r["name"], r["start"].isoformat(), r["end"].isoformat()] for r in d["rows"]]
            ld_events = [{"@type": "Event", "name": f"{r['name']} {name}", "startDate": r["start"].isoformat(), "endDate": r["end"].isoformat(),
                          "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode", "eventStatus": "https://schema.org/EventScheduled",
                          "location": {"@type": "AdministrativeArea", "name": f"{name}, {country_label[c]}"}} for r in d["rows"] if not r["single"]]
            write(path, "ferien_region.html",
                  title=f"Schulferien {F.SCHOOLYEAR} {name}: alle Termine | Kalenderkompass 24",
                  description=f"Schulferien {F.SCHOOLYEAR} in {name}: alle Ferientermine mit Dauer, Sommerferien {fmt(su['start'], c, wd=False)} – {fmt(su['end'], c, wd=False)}, Zeitstrahl, Kalender-Download und Urlaubstage-Bedarf für Eltern.",
                  h1=f"Schulferien {F.SCHOOLYEAR} in {name}",
                  lead=f"{len([r for r in d['rows'] if not r['single']])} Ferienblöcke, {d['total']} Ferientage, Sommerferien ab {fmt(su['start'], c)}. Amtliche Termine, mit Zeitstrahl und Kalender-Export.",
                  name=name, slug=slug, country=c, d=d, nxt=nxt, axis=axis_ctx(c), facts=facts, ics_json=json.dumps(ics, ensure_ascii=False),
                  siblings=[(s, n) for s, n in regs.items() if s != slug], cslug=cslug, country_name=country_label[c],
                  src=F.SRC_AT if c == "at" else F.SRC_DE, sy=F.SCHOOLYEAR, sy_slug=F.SY_SLUG, crumbs=crumbs, lang_at=(c == "at"),
                  jsonld=[crumbs_ld(crumbs)], active=f"/schulferien-{F.SY_SLUG}.html", priority=0.8)

    # ---------------- Übersicht
    def gantt(c):
        return [{"href": f"/schulferien-{F.SY_SLUG}-{s}.html", "name": n, "bars": data[(c, s)]["bars"]} for s, n in F.regions(c).items()]

    summer_rows = []
    for c in ("at", "de"):
        for s, n in F.regions(c).items():
            su = data[(c, s)]["summer"]
            summer_rows.append({"name": n, "country": country_label[c], "href": f"/schulferien-{F.SY_SLUG}-{s}.html",
                                "start": su["start"], "end": su["end"], "days": su["days"],
                                "span": f"{fmt(su['start'], c, year=False)} – {fmt(su['end'], c, year=False)}", "short": short(su["start"], su["end"]), "c": c})
    summer_rows.sort(key=lambda r: (r["start"], r["name"]))
    crumbs = [("/", "Start"), (f"/schulferien-{F.SY_SLUG}.html", f"Schulferien {F.SCHOOLYEAR}")]
    write(f"schulferien-{F.SY_SLUG}.html", "ferien_overview.html",
          title=f"Schulferien {F.SCHOOLYEAR}: Österreich & Deutschland im Überblick | Kalenderkompass 24",
          description=f"Schulferien {F.SCHOOLYEAR} für alle 9 österreichischen Bundesländer und 16 deutschen Länder: Zeitstrahl, Sommerferien-Vergleich und Kalender-Download.",
          h1=f"Schulferien {F.SCHOOLYEAR}",
          lead="Alle amtlichen Ferientermine für Österreich und Deutschland auf einem Zeitstrahl – so siehst du sofort, wann wo Ferien sind und wo sie sich überschneiden.",
          axis_at=axis_ctx("at"), axis_de=axis_ctx("de"), gantt_at=gantt("at"), gantt_de=gantt("de"), summer_rows=summer_rows,
          src_at=F.SRC_AT, src_de=F.SRC_DE, sy=F.SCHOOLYEAR, sy_slug=F.SY_SLUG, crumbs=crumbs,
          jsonld=[crumbs_ld(crumbs)], active=f"/schulferien-{F.SY_SLUG}.html", priority=0.9)

    # ---------------- Sommerferien 2027
    s0, s1 = date(2027, 6, 20), date(2027, 9, 20)
    tot = (s1 - s0).days
    weeks = []
    d = s0 + timedelta(days=(7 - s0.weekday()) % 7)
    while d < s1:
        weeks.append({"left": round((d - s0).days / tot * 100, 3), "label": f"{d.day}.{d.month}."})
        d += timedelta(days=14)
    srows = []
    for r in summer_rows:
        p = {"name": "Sommerferien", "start": r["start"], "end": r["end"]}
        srows.append(dict(r, bars=bars([p], s0, s1)))
    earliest, latest = summer_rows[0], summer_rows[-1]
    longest = max(summer_rows, key=lambda r: r["days"]); shortest = min(summer_rows, key=lambda r: r["days"])
    # Tage, an denen in mindestens einem Land Sommerferien sind
    first, last = min(r["start"] for r in summer_rows), max(r["end"] for r in summer_rows)
    peak_day, peak_n = None, 0
    d = first
    while d <= last:
        n = sum(1 for r in summer_rows if r["start"] <= d <= r["end"])
        if n > peak_n: peak_day, peak_n = d, n
        d += timedelta(days=1)
    crumbs = [("/", "Start"), (f"/schulferien-{F.SY_SLUG}.html", f"Schulferien {F.SCHOOLYEAR}"), ("/sommerferien-2027.html", "Sommerferien 2027")]
    write("sommerferien-2027.html", "ferien_summer.html",
          title="Sommerferien 2027: alle Termine in Österreich & Deutschland | Kalenderkompass 24",
          description="Sommerferien 2027 in allen 25 Bundesländern Österreichs und Deutschlands – sortiert nach Beginn, mit Dauer und Zeitstrahl. Wer startet zuerst, wo sind sie am längsten?",
          h1="Sommerferien 2027",
          lead=f"Den Anfang macht {earliest['name']} am {fmt(earliest['start'], earliest['c'])}, als Letzte starten {latest['name']} am {fmt(latest['start'], latest['c'])}. "
               f"Am {fmt(peak_day, 'de')} sind in {peak_n} von 25 Ländern gleichzeitig Ferien.",
          rows=srows, weeks=weeks, longest=longest, shortest=shortest, peak_day=fmt(peak_day, "de"), peak_n=peak_n,
          span_all=f"{fmt(first, 'de', wd=False)} bis {fmt(last, 'de', wd=False)}",
          src_at=F.SRC_AT, src_de=F.SRC_DE, sy_slug=F.SY_SLUG, crumbs=crumbs, lang_at=False,
          jsonld=[crumbs_ld(crumbs)], active=f"/schulferien-{F.SY_SLUG}.html", priority=0.9)
