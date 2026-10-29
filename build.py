"""Erzeugt die komplette statische Website in docs/ (GitHub Pages)."""
import json, shutil, sys
from datetime import date, timedelta
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

sys.path.insert(0, str(Path(__file__).parent))
import holidays as H
from content.articles import ARTICLES

ROOT = Path(__file__).parent
OUT = ROOT / "docs"
SITE = "https://kalenderkompass24.de"
V = "20261029c"
UPDATED = "Oktober 2026"
TODAY = date(2026, 10, 29)
CUR = 2027                      # Hauptjahr der Seite (Planung läuft aufs nächste Jahr)
YEARS = [2026, 2027, 2028]
DATA_YEARS = range(2025, 2031)

M_AT = ["Jänner","Februar","März","April","Mai","Juni","Juli","August","September","Oktober","November","Dezember"]
M_DE = ["Januar"] + M_AT[1:]
MS_AT = ["Jän","Feb","Mär","Apr","Mai","Jun","Jul","Aug","Sep","Okt","Nov","Dez"]
MS_DE = ["Jan"] + MS_AT[1:]
WDL = ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"]
WDS = ["Mo","Di","Mi","Do","Fr","Sa","So"]

NAV = [("/", "Feiertage"), (f"/brueckentage-{CUR}.html", "Brückentage"), ("/urlaubsplaner.html", "Urlaubsplaner"),
       ("/schulferien-2026-2027.html", "Schulferien"), (f"/kalenderwochen-{CUR}.html", "Kalenderwochen"), (f"/kalender-{CUR}-zum-ausdrucken.html", "Kalender drucken")]

env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=True, trim_blocks=True, lstrip_blocks=True)
PAGES = []  # (path, priority) für die Sitemap


def mnames(country): return M_AT if country == "at" else M_DE
def mshort(country): return MS_AT if country == "at" else MS_DE
def fmt(d, country, wd=True, year=True):
    s = f"{d.day}. {mnames(country)[d.month-1]}" + (f" {d.year}" if year else "")
    return (WDL[d.weekday()] + ", " + s) if wd else s


def write(path, template, **ctx):
    base = dict(site=SITE, v=V, updated=UPDATED, nav=NAV, active=ctx.get("active", path), jsonld=[], ads=True,
                lang_at=True, years=YEARS, year=CUR, robots=None, region_attr=None, year_attr=None, og_title=None)
    base.update(ctx)
    base["path"] = "/" if path == "index.html" else "/" + path
    html = env.get_template(template).render(**base)
    (OUT / path).write_text(html, encoding="utf-8")
    if base.get("robots") is None:
        PAGES.append((base["path"], ctx.get("priority", 0.6)))


def rows_for(country, region, year):
    out = []
    for h in H.region_holidays(country, region, year):
        d = h["date"]
        out.append({"day": f"{d.day}. {mnames(country)[d.month-1]}", "wd": WDL[d.weekday()], "name": h["name"],
                    "note": h["note"], "kind": h["kind"], "weekend": d.weekday() >= 5, "date": d})
    return out


def bridge_view(country, region, year):
    res = []
    for b in H.bridge_days(country, region, year):
        take = " + ".join(f"{WDS[d.weekday()]} {d.day}. {mshort(country)[d.month-1]}" for d in b["days"])
        res.append({"take": take, "holiday": b["holiday"], "vacation": b["vacation"], "free": b["free"],
                    "from": fmt(b["start"], country, year=False), "to": fmt(b["end"], country, year=False), "raw": b})
    return res


def band_view(country, region, year):
    hol = {h["date"]: h for h in H.region_holidays(country, region, year)}
    br = {d for b in H.bridge_days(country, region, year) for d in b["days"]}
    months = []
    for m in range(1, 13):
        cells = []
        for dd in range(1, 32):
            try:
                d = date(year, m, dd)
            except ValueError:
                cells.append({"cls": "d x", "title": ""}); continue
            cls, title = "d", f"{WDS[d.weekday()]} {dd}. {mshort(country)[m-1]}"
            if d.weekday() >= 5: cls += " we"
            h = hol.get(d)
            if h and h["kind"] == "legal": cls += " ho"; title += f" – {h['name']}"
            elif h: cls += " pa"; title += f" – {h['name']}"
            if d in br: cls += " br"; title += " – Brückentag"
            cells.append({"cls": cls, "title": title})
        months.append({"label": mshort(country)[m-1], "cells": cells})
    return {"year": year, "months": months}


def region_name(country, region):
    if country == "at": return H.AT_REGIONS[region] if region else "Österreich"
    return H.DE_REGIONS[region][0] if region else "Deutschland"


def crumbs_ld(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i+1, "name": n, "item": SITE + h} for i, (h, n) in enumerate(items)]}


def holiday_ld(country, region, year, rows):
    return {"@context": "https://schema.org", "@type": "ItemList",
            "name": f"Feiertage {year} {region_name(country, region)}",
            "itemListElement": [{"@type": "ListItem", "position": i+1,
                                 "name": f"{r['name']}: {r['day']} {year} ({r['wd']})"}
                                for i, r in enumerate([x for x in rows if x["kind"] == "legal"])]}


# ---------------------------------------------------------------- Daten-JSON
def build_data():
    h = {}
    for y in DATA_YEARS:
        for country, regions in (("at", [""] + list(H.AT_REGIONS)), ("de", [""] + list(H.DE_REGIONS))):
            for r in regions:
                h[f"{country}:{r}:{y}"] = [[x["date"].isoformat(), x["name"], x["kind"], x["note"]]
                                          for x in H.region_holidays(country, r, y)]
    data = {"countries": {"at": {"label": "Österreich", "regions": H.AT_REGIONS},
                          "de": {"label": "Deutschland", "regions": {k: v[0] for k, v in H.DE_REGIONS.items()}}},
            "h": h}
    (OUT / "data").mkdir(exist_ok=True)
    (OUT / "data" / "feiertage.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


# ---------------------------------------------------------------- Texte je Region
def region_facts(country, region, year):
    name = region_name(country, region)
    rows = H.region_holidays(country, region, year)
    legal = [r for r in rows if r["kind"] == "legal"]
    wkd = [r for r in legal if r["date"].weekday() < 5]
    facts = []
    if country == "at":
        facts.append(f"In {name} gelten wie in ganz Österreich die 13 gesetzlichen Feiertage nach § 7 Arbeitsruhegesetz. "
                     f"{year} fallen davon {len(wkd)} auf einen Werktag von Montag bis Freitag.")
        pats = [r for r in rows if r["kind"] == "patron"]
        for p in pats:
            facts.append(f"Der {p['name'].split(' (')[0]} am {fmt(p['date'], 'at')} ist in {name} kein gesetzlicher Feiertag. "
                         "Geschäfte haben geöffnet, an den Schulen ist aber in der Regel unterrichtsfrei, und viele Landesdienststellen geben frei.")
        facts.append("Der 24. und der 31. Dezember sind keine Feiertage. Viele Kollektivverträge sehen an diesen Tagen aber ganz oder ab Mittag frei vor.")
        facts.append("Den Karfreitag gibt es in Österreich seit 2019 nicht mehr als Feiertag. Stattdessen kann jede und jeder einen persönlichen Feiertag festlegen, der vom Urlaub abgezogen wird.")
    else:
        code = H.DE_REGIONS[region][1]
        extra = [r["name"] for r in legal if r["name"] not in {
            "Neujahr", "Karfreitag", "Ostermontag", "Tag der Arbeit", "Christi Himmelfahrt", "Pfingstmontag",
            "Tag der Deutschen Einheit", "1. Weihnachtsfeiertag", "2. Weihnachtsfeiertag"}]
        facts.append(f"{name} hat {year} {len(legal)} gesetzliche Feiertage, {len(wkd)} davon an Werktagen von Montag bis Freitag. "
                     + (f"Zusätzlich zu den neun bundesweiten Feiertagen gilt hier: {', '.join(extra)}." if extra
                        else "Es gelten nur die neun bundesweit einheitlichen Feiertage."))
        note = H.de_partial_notes(code)
        if note: facts.append(note)
        if code == "BB":
            facts.append("Ostersonntag und Pfingstsonntag sind in Brandenburg ausdrücklich gesetzliche Feiertage. Für Beschäftigte, die sonntags arbeiten, ist das wegen der Zuschläge relevant.")
        facts.append("Fällt ein Feiertag auf ein Wochenende, gibt es keinen Ersatztag. Der 24. und 31. Dezember sind keine gesetzlichen Feiertage.")
    return facts


# ---------------------------------------------------------------- Seiten
def build_home():
    t = TODAY
    nxt = next(r for y in (t.year, t.year+1) for r in H.region_holidays("at", "", y) if r["date"] >= t)
    n = (nxt["date"] - t).days
    rel = "heute" if n == 0 else "morgen" if n == 1 else f"in {n} Tagen"
    rows = rows_for("at", "", CUR)
    iw = TODAY.isocalendar()
    ld = [{"@context": "https://schema.org", "@type": "WebSite", "name": "Kalenderkompass 24", "url": SITE + "/",
           "inLanguage": "de", "description": "Feiertage, Brückentage und Urlaubsplanung für Österreich und Deutschland."},
          holiday_ld("at", "", CUR, rows)]
    write("index.html", "home.html", title=f"Feiertage & Brückentage {CUR} – Österreich und Deutschland | Kalenderkompass 24",
          description=f"Alle Feiertage und Brückentage {CUR} für jedes Bundesland in Österreich und Deutschland – mit Jahresübersicht, Urlaubsplaner und Kalender-Export.",
          next={"rel": rel, "name": nxt["name"], "date": fmt(nxt["date"], "at")}, band=band_view("at", "", CUR),
          bridge_list=bridge_view("at", "", CUR), rows=rows, year_attr=CUR,
          at_regions=list(H.AT_REGIONS.items()), de_regions=[(k, v[0]) for k, v in H.DE_REGIONS.items()],
          articles=ARTICLES, kw={"week": iw[1], "year": iw[0]}, jsonld=ld, priority=1.0, active="/")


def ferien_teaser(country, slug, name):
    import ferien as F
    ps = [p for p in F.periods(country, slug) if not p["single"]]
    su = F.summer(country, slug)
    lng = max((p for p in ps if p["name"] != "Sommerferien"), key=lambda p: p["days"])
    return {"text": f"Im Schuljahr {F.SCHOOLYEAR} hat {name} {len(ps)} Ferienblöcke mit insgesamt {F.total_days(country, slug)} Ferientagen. "
                    f"Die Sommerferien 2027 dauern von {fmt(su['start'], country)} bis {fmt(su['end'], country)}. "
                    f"Die längsten Ferien nach dem Sommer sind die {lng['name']} mit {lng['days']} Tagen ({fmt(lng['start'], country, wd=False)} bis {fmt(lng['end'], country, wd=False)}). "
                    f"Wer Brückentage und Ferien kombiniert, kann Familienurlaub besonders effizient planen.",
            "href": f"/schulferien-{F.SY_SLUG}-{slug}.html", "sy": F.SCHOOLYEAR}


def build_regions(year):
    for country, regions in (("at", H.AT_REGIONS), ("de", {k: v[0] for k, v in H.DE_REGIONS.items()})):
        cslug = "oesterreich" if country == "at" else "deutschland"
        cname = "Österreich" if country == "at" else "Deutschland"
        for slug, name in regions.items():
            rows = rows_for(country, slug, year)
            legal = [r for r in rows if r["kind"] == "legal"]
            bl = bridge_view(country, slug, year)
            singles = [b for b in bl if b["vacation"] == 1]
            lead = (f"{len(legal)} gesetzliche Feiertage, {len(bl)} Brückentag{'e' if len(bl) != 1 else ''}"
                    + (f" – der beste: {singles[0]['take']}, {singles[0]['free']} Tage frei mit einem Urlaubstag." if singles else ".")
                    + " Mit Jahresübersicht und Kalender-Export.")
            path = f"feiertage-{year}-{slug}.html"
            crumbs = [("/", "Start"), (f"/feiertage-{year}-{cslug}.html", f"Feiertage {year} {cname}"), ("/" + path, name)]
            write(path, "region.html", title=f"Feiertage {year} {name}: alle Termine & Brückentage | Kalenderkompass 24",
                  description=f"Feiertage {year} in {name}: alle {len(legal)} gesetzlichen Feiertage mit Wochentag, Brückentage und Urlaubstipps – mit Kalender-Download.",
                  h1=f"Feiertage {year} in {name}", lead=lead, name=name, slug=slug, country=country,
                  country_slug=cslug, country_name=cname, legal_count=len(legal),
                  weekday_count=len([r for r in legal if r["date"].weekday() < 5]), bridge_count=len(bl),
                  band=band_view(country, slug, year), rows=rows, bridge_list=bl, facts=region_facts(country, slug, year),
                  ferien=ferien_teaser(country, slug, name) if year == 2027 else None,
                  other_years=[y for y in (2027, 2028) if y != year], siblings=[(s, n) for s, n in regions.items() if s != slug],
                  crumbs=crumbs, region_attr=f"{country}:{slug}:{year}", lang_at=(country == "at"),
                  jsonld=[crumbs_ld(crumbs), holiday_ld(country, slug, year, rows)], active="/", priority=0.8 if year == CUR else 0.6)


def build_country(year):
    # Österreich
    rows = rows_for("at", "", year)
    pats = {}
    for slug, lst in H.AT_PATRONS.items():
        for (m, d), n in lst:
            pats.setdefault((m, d, n), []).append(H.AT_REGIONS[slug])
    patrons = [{"day": f"{d}. {M_AT[m-1]} ({WDL[date(year, m, d).weekday()]})", "name": n.split(" (")[0],
                "regions": ", ".join(sorted(r))} for (m, d, n), r in sorted(pats.items())]
    bl = bridge_view("at", "", year)
    crumbs = [("/", "Start"), (f"/feiertage-{year}-oesterreich.html", f"Feiertage {year} Österreich")]
    wk = len([r for r in rows if r["date"].weekday() < 5])
    write(f"feiertage-{year}-oesterreich.html", "country.html",
          title=f"Feiertage {year} Österreich: alle 13 Termine, Fenstertage & Landespatrone | Kalenderkompass 24",
          description=f"Alle 13 gesetzlichen Feiertage {year} in Österreich mit Wochentag, Fenstertagen und den Landespatronen aller Bundesländer.",
          h1=f"Feiertage {year} in Österreich",
          lead=f"Österreich hat 13 gesetzliche Feiertage, bundesweit einheitlich. {year} fallen {wk} davon auf einen Werktag, dazu kommen {len(bl)} Fenstertage.",
          band=band_view("at", "", year), band_title=f"Österreich {year} auf einen Blick", rows=rows,
          table_title=f"Gesetzliche Feiertage {year}", patrons=patrons, matrix=None, bridge_list=bl, bridge_note=None,
          facts=["Grundlage ist § 7 Abs. 2 Arbeitsruhegesetz. Die Feiertage gelten in allen neun Bundesländern gleich; Unterschiede gibt es nur bei den Landespatronen, die keine gesetzlichen Feiertage sind.",
                 "Der Karfreitag ist seit 2019 kein Feiertag mehr. An seine Stelle trat der persönliche Feiertag, den jede und jeder einmal pro Jahr selbst festlegen kann."],
          regions=list(H.AT_REGIONS.items()), region_year=year if year in (2027, 2028) else CUR, country="at",
          other_years=[y for y in YEARS if y != year], slug="oesterreich", country_name="Österreich",
          crumbs=crumbs, jsonld=[crumbs_ld(crumbs), holiday_ld("at", "", year, rows)], priority=0.9 if year == CUR else 0.6)

    # Deutschland
    nat = rows_for("de", "", year)
    allh = {}
    for slug, (name, code) in H.DE_REGIONS.items():
        for r in H.region_holidays("de", slug, year):
            allh.setdefault((r["date"], r["name"]), set()).add(code)
    codes = [v[1] for v in H.DE_REGIONS.values()]
    mrows = [{"name": n, "day": fmt(d, "de", year=False), "cells": [c in s for c in codes]} for (d, n), s in sorted(allh.items())]
    matrix = {"codes": codes, "names": [v[0] for v in H.DE_REGIONS.values()], "rows": mrows,
              "legend": "Kürzel: " + ", ".join(f"{v[1]} = {v[0]}" for v in H.DE_REGIONS.values()) + ". Mariä Himmelfahrt in Bayern gilt in Gemeinden mit überwiegend katholischer Bevölkerung."}
    crumbs = [("/", "Start"), (f"/feiertage-{year}-deutschland.html", f"Feiertage {year} Deutschland")]
    wk = len([r for r in nat if r["date"].weekday() < 5])
    write(f"feiertage-{year}-deutschland.html", "country.html",
          title=f"Feiertage {year} Deutschland: alle Bundesländer im Vergleich | Kalenderkompass 24",
          description=f"Feiertage {year} in Deutschland: die 9 bundesweiten Feiertage und eine Übersicht, welcher Feiertag in welchem Bundesland gilt.",
          h1=f"Feiertage {year} in Deutschland",
          lead=f"Neun Feiertage gelten {year} bundesweit, {wk} davon an Werktagen. Alle weiteren legen die Bundesländer fest – die Tabelle zeigt, wo welcher gilt.",
          band=band_view("de", "", year), band_title=f"Bundesweite Feiertage {year}", rows=nat,
          table_title=f"Bundesweite Feiertage {year}", patrons=None, matrix=matrix, bridge_list=None,
          bridge_note=f"Brückentage hängen in Deutschland vom Bundesland ab. Die Übersicht für alle Länder findest du bei den Brückentagen {year}.",
          facts=["Feiertage sind in Deutschland Ländersache. Nur der Tag der Deutschen Einheit ist durch Bundesrecht festgelegt; die übrigen bundesweiten Feiertage stehen in allen Landesgesetzen."],
          regions=[(k, v[0]) for k, v in H.DE_REGIONS.items()], region_year=year if year in (2027, 2028) else CUR, country="de",
          other_years=[y for y in YEARS if y != year], slug="deutschland", country_name="Deutschland",
          crumbs=crumbs, jsonld=[crumbs_ld(crumbs), holiday_ld("de", "", year, nat)], lang_at=False, priority=0.9 if year == CUR else 0.6)


def build_bridges(year):
    at = bridge_view("at", "", year)
    de_rows = []
    for slug, (name, code) in H.DE_REGIONS.items():
        bl = bridge_view("de", slug, year)
        de_rows.append((slug, name, bl))
    parts = [f"<h2>Österreich: {len(at)} Fenstertage</h2><p>Gilt in allen Bundesländern gleich.</p>"]
    parts.append(env.get_template("macros.html").module.bridges(at, "at", live=False))
    parts.append(f"<h2>Deutschland nach Bundesland</h2><div class='scroll'><table class='tbl'><thead><tr><th>Bundesland</th><th>Brückentage {year}</th><th>Urlaubstage → freie Tage</th></tr></thead><tbody>")
    for slug, name, bl in de_rows:
        days = "<br>".join(b["take"] + f" <span class='muted small'>({b['holiday']})</span>" for b in bl) or "<span class='muted'>keine</span>"
        eff = "<br>".join(f"{b['vacation']} → {b['free']}" for b in bl) or "–"
        parts.append(f"<tr><td><a href='/feiertage-{year}-{slug}.html'>{name}</a></td><td>{days}</td><td>{eff}</td></tr>")
    parts.append("</tbody></table></div>")
    best = max((b["free"] / b["vacation"], name) for slug, name, bl in de_rows for b in bl) if any(bl for _, _, bl in de_rows) else None
    body = ("<h2>So liest du die Übersicht</h2><p>Ein Brückentag ist hier jeder Arbeitstag, der allein oder zu zweit zwischen einem Feiertag und dem Wochenende liegt. "
            "Die erste Zahl sind die nötigen Urlaubstage, die zweite die freien Tage am Stück. Wer dazwischen weitere Tage nimmt, findet im "
            "<a href='/urlaubsplaner.html'>Urlaubsplaner</a> die effizientesten längeren Blöcke.</p>"
            "<p>Ein Anspruch auf Freistellung an Brückentagen besteht weder in Österreich noch in Deutschland. Mehr dazu im Beitrag "
            "<a href='/fenstertag-zwickeltag-brueckentag.html'>Fenstertag, Zwickeltag, Brückentag</a>.</p>")
    crumbs = [("/", "Start"), (f"/brueckentage-{year}.html", f"Brückentage {year}")]
    write(f"brueckentage-{year}.html", "tool.html",
          title=f"Brückentage {year}: Fenstertage Österreich & alle Bundesländer Deutschland | Kalenderkompass 24",
          description=f"Alle Brückentage {year}: die Fenstertage in Österreich und die Brückentage jedes deutschen Bundeslandes – mit freien Tagen pro Urlaubstag.",
          h1=f"Brückentage {year}", lead=f"Mit wenig Urlaub viel frei: alle Brücken- und Fenstertage {year} für Österreich und jedes deutsche Bundesland.",
          tool="".join(str(p) for p in parts), body=body, crumbs=crumbs, show_picker=False, related=[a for a in ARTICLES if a["slug"] in ("ferien-planen", "fenstertag-zwickeltag-brueckentag")],
          jsonld=[crumbs_ld(crumbs)], active=f"/brueckentage-{CUR}.html", priority=0.9 if year == CUR else 0.6)


def build_planner():
    tool = f"""<div class="planner" data-planner>
  <div class="row"><label class="range">Wie viele Urlaubstage willst du einsetzen?<output data-budget-out>10</output><input type="range" min="1" max="30" value="10" data-budget aria-label="Urlaubstage"></label></div>
  <p class="plan-sum" data-plan-sum>Wähle Bundesland und Jahr – der Planer zeigt sofort die effizientesten Termine.</p>
  <div class="band" style="border:0;padding:0;margin:10px 0 16px"><div class="yr" data-plan-band></div>
  <div class="legend"><span><i style="background:var(--red)"></i>Feiertag</span><span><i style="background:var(--sea)"></i>vorgeschlagener Urlaubstag</span><span><i style="background:var(--sun)"></i>weiterer Brückentag</span></div></div>
  <ol class="bridges" data-plan-list></ol>
</div>"""
    body = """<h2>Wie der Planer rechnet</h2>
<p>Für jeden möglichen Urlaubsblock zählt der Planer, wie viele freie Tage am Stück entstehen – Wochenenden und gesetzliche Feiertage deines Bundeslandes inklusive. Dann wählt er die Blöcke mit dem besten Verhältnis von freien Tagen zu Urlaubstagen, bis dein Kontingent aufgebraucht ist. Ein Block umfasst höchstens zehn Urlaubstage.</p>
<p>Ist das gewählte Jahr das laufende, plant er ab heute. Landespatrone in Österreich zählt er nicht als frei, weil sie keine gesetzlichen Feiertage sind.</p>
<h2>Was der Planer nicht weiß</h2>
<p>Schulferien, Betriebsurlaub und Absprachen im Team kennt nur dein Kalender. Nimm die Vorschläge als Ausgangspunkt und stimme den Urlaub wie gewohnt ab – in Österreich muss er vereinbart werden, in Deutschland legt ihn der Arbeitgeber unter Berücksichtigung deiner Wünsche fest.</p>"""
    crumbs = [("/", "Start"), ("/urlaubsplaner.html", "Urlaubsplaner")]
    write("urlaubsplaner.html", "tool.html", title=f"Urlaubsplaner {CUR}: aus wenig Urlaub viele freie Tage machen | Kalenderkompass 24",
          description=f"Urlaubsplaner {CUR} für Österreich und Deutschland: Gib deine Urlaubstage ein und finde die Termine mit den meisten freien Tagen in deinem Bundesland.",
          h1="Urlaubsplaner", lead="Gib ein, wie viele Urlaubstage du einsetzen willst. Der Planer legt sie dorthin, wo sie mit Feiertagen und Wochenenden die meisten freien Tage ergeben.",
          tool=tool, body=body, crumbs=crumbs, show_picker=True, show_year=True, year_attr=CUR,
          related=[a for a in ARTICLES if a["slug"] in ("ferien-planen", "urlaubsanspruch-oesterreich-deutschland", "persoenlicher-feiertag-oesterreich")],
          jsonld=[crumbs_ld(crumbs), {"@context": "https://schema.org", "@type": "WebApplication", "name": "Urlaubsplaner", "applicationCategory": "UtilitiesApplication", "operatingSystem": "Web", "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR"}, "url": SITE + "/urlaubsplaner.html"}],
          active="/urlaubsplaner.html", priority=0.9)


def build_workdays():
    a, b = date(CUR, 1, 1), date(CUR, 12, 31)
    tool = f"""<div class="planner" data-workdays>
  <div class="row"><label class="range" style="flex:0 1 200px">Von<input type="date" name="from" value="{a.isoformat()}"></label>
  <label class="range" style="flex:0 1 200px">Bis<input type="date" name="to" value="{b.isoformat()}"></label></div>
  <div data-workdays-out style="margin-top:12px"><p class="plan-sum">Wähle zwei Daten.</p></div>
</div>"""
    at = sum(1 for i in range((b - a).days + 1) if (d := a + timedelta(i)).weekday() < 5 and d not in H.off_days("at", "wien", CUR))
    def wd_month(country, region, y, m):
        off = H.off_days(country, region, y); d = date(y, m, 1); n = 0
        while d.month == m:
            n += d.weekday() < 5 and d not in off; d += timedelta(1)
        return n
    de_tot = {name: sum(wd_month("de", slug, CUR, m) for m in range(1, 13)) for slug, (name, code) in H.DE_REGIONS.items()}
    lo, hi = min(de_tot.values()), max(de_tot.values())
    lo_n = ", ".join(k for k, v in de_tot.items() if v == lo); hi_n = ", ".join(k for k, v in de_tot.items() if v == hi)
    rows = "".join(f"<tr><td>{M_AT[m-1]}</td><td>{wd_month('at', 'wien', CUR, m)}</td><td>{wd_month('de', 'bayern', CUR, m)}</td><td>{wd_month('de', 'berlin', CUR, m)}</td></tr>" for m in range(1, 13))
    body = f"""<h2>Arbeitstage {CUR} im Überblick</h2>
<p>In Wien hat {CUR} {at} Arbeitstage von Montag bis Freitag. In Deutschland hängt die Zahl vom Bundesland ab: Am wenigsten Arbeitstage hat {CUR} {lo_n} mit {lo}, am meisten {hi_n} mit {hi}. Der Grund sind unterschiedlich viele Feiertage – zwischen 10 und 13 – und die Frage, ob sie auf ein Wochenende fallen.</p>
<h2>Arbeitstage {CUR} pro Monat</h2>
<div class="scroll"><table class="tbl"><thead><tr><th scope="col">Monat</th><th scope="col">Wien</th><th scope="col">Bayern</th><th scope="col">Berlin</th></tr></thead><tbody>{rows}
<tr><td><strong>Jahr</strong></td><td><strong>{at}</strong></td><td><strong>{de_tot['Bayern']}</strong></td><td><strong>{de_tot['Berlin']}</strong></td></tr></tbody></table></div>
<p class="small muted">Montag bis Freitag ohne gesetzliche Feiertage. Für Bayern mit Mariä Himmelfahrt (gilt nur in Gemeinden mit überwiegend katholischer Bevölkerung{'; fällt ' + str(CUR) + ' auf ' + WDL[date(CUR, 8, 15).weekday()] if date(CUR, 8, 15).weekday() >= 5 else ''}), ohne das Augsburger Friedensfest.</p>
<h2>Arbeitstage, Werktage, Kalendertage</h2>
<ul><li><strong>Kalendertage</strong> sind alle Tage, auch Wochenenden und Feiertage.</li>
<li><strong>Werktage</strong> sind im rechtlichen Sinn meist Montag bis Samstag ohne Feiertage. Der Urlaubsanspruch in Österreich wird teils in Werktagen angegeben (30 Werktage = 5 Wochen).</li>
<li><strong>Arbeitstage</strong> sind die Tage, an denen tatsächlich gearbeitet wird – bei einer Fünftagewoche Montag bis Freitag ohne Feiertage. Diese zählt der Rechner.</li></ul>
<h2>Wofür man Arbeitstage braucht</h2>
<p><strong>Projektplanung:</strong> Wie viele Arbeitstage bleiben bis zur Deadline? <strong>Tagessätze:</strong> Wer ein Monatsgehalt durch die Arbeitstage teilt, erhält den Wert eines Arbeitstags – praktisch etwa bei unbezahltem Urlaub oder anteiliger Bezahlung. <strong>Fristen:</strong> Manche Fristen laufen in Arbeitstagen, die meisten gesetzlichen Fristen aber in Kalendertagen – hier lohnt sich ein genauer Blick.</p>
<p>Der Rechner zählt Anfangs- und Enddatum mit. Er berücksichtigt Samstage und Sonntage sowie die gesetzlichen Feiertage des gewählten Bundeslandes – nicht aber Urlaub, Krankenstand, betriebliche Schließtage oder Feiertage einzelner Gemeinden.</p>
<p>Mehr zu Kalender-, Werk- und Arbeitstagen und zur Berechnung von Fristen im Beitrag <a href="/tage-richtig-zaehlen.html">Tage richtig zählen</a>.</p>"""
    crumbs = [("/", "Start"), ("/arbeitstage-rechner.html", "Arbeitstage-Rechner")]
    write("arbeitstage-rechner.html", "tool.html", title="Arbeitstage-Rechner: Arbeitstage zwischen zwei Daten zählen | Kalenderkompass 24",
          description="Arbeitstage zwischen zwei Daten berechnen – mit den Feiertagen deines Bundeslandes in Österreich oder Deutschland.",
          h1="Arbeitstage-Rechner", lead="Wie viele Arbeitstage liegen zwischen zwei Daten? Der Rechner zieht Wochenenden und die Feiertage deines Bundeslandes ab.",
          tool=tool, body=body, crumbs=crumbs, show_picker=True, show_year=False,
          related=[a for a in ARTICLES if a["slug"] in ("tage-richtig-zaehlen", "urlaubsanspruch-oesterreich-deutschland")],
          jsonld=[crumbs_ld(crumbs)], active="/", priority=0.8)


def build_kw(year):
    first = date.fromisocalendar(year, 1, 1)
    weeks = date(year, 12, 28).isocalendar()[1]
    rows = []
    for w in range(1, weeks + 1):
        mon = date.fromisocalendar(year, w, 1); sun = mon + timedelta(6)
        rows.append(f"<tr data-kw-row='{year}-{w}'><td class='date'>KW {w}</td><td>{fmt(mon,'at',wd=False)}</td><td>{fmt(sun,'at',wd=False)}</td></tr>")
    tool = (f"<div class='planner'><div class='kw-now' data-kw-now><b>KW</b></div><p class='small muted' style='margin:6px 0 0'>Aktuelle Kalenderwoche nach ISO 8601</p></div>"
            f"<h2>Alle {weeks} Kalenderwochen {year}</h2><div class='scroll'><table class='tbl'><thead><tr><th>Woche</th><th>Montag</th><th>Sonntag</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>")
    body = f"""<h2>Wie Kalenderwochen gezählt werden</h2>
<p>In Österreich, Deutschland und der Schweiz gilt die Norm ISO 8601: Eine Woche beginnt am Montag, und die erste Kalenderwoche ist die Woche mit dem ersten Donnerstag des Jahres. Anders gesagt: KW 1 ist die Woche, in der der 4. Jänner liegt.</p>
<p>{year} beginnt die KW 1 am {fmt(first,'at')}. Das Jahr hat {weeks} Kalenderwochen. Jahre mit 53 Wochen gibt es, wenn das Jahr an einem Donnerstag beginnt oder ein Schaltjahr an einem Mittwoch beginnt – etwa 2026 und 2032.</p>
<p>In den USA beginnt die Woche dagegen am Sonntag, und die erste Woche ist die mit dem 1. Jänner. Bei internationalen Terminen in Kalenderwochen lohnt es sich deshalb, das Datum dazuzuschreiben.</p>"""
    crumbs = [("/", "Start"), (f"/kalenderwochen-{year}.html", f"Kalenderwochen {year}")]
    write(f"kalenderwochen-{year}.html", "tool.html", title=f"Kalenderwochen {year}: alle KW mit Datum | Kalenderkompass 24",
          description=f"Alle {weeks} Kalenderwochen {year} mit Start- und Enddatum nach ISO 8601 – und welche KW gerade ist.",
          h1=f"Kalenderwochen {year}", lead=f"Welche Kalenderwoche ist heute? Hier stehen alle {weeks} Wochen {year} mit Datum von Montag bis Sonntag.",
          tool=tool, body=body, crumbs=crumbs, show_picker=False, related=[], jsonld=[crumbs_ld(crumbs)],
          active=f"/kalenderwochen-{CUR}.html", priority=0.8 if year in (2026, 2027) else 0.5)


def build_print(year):
    def month_grid(country, region):
        hol = {h["date"]: h for h in H.region_holidays(country, region, year)}
        out = []
        for m in range(1, 13):
            d = date(year, m, 1); cells = ["<td></td>"] * d.weekday()
            while d.month == m:
                h = hol.get(d); style = ""
                if h and h["kind"] == "legal": style = " style='color:var(--red);font-weight:700'"
                elif d.weekday() >= 5: style = " class='muted'"
                cells.append(f"<td{style}{' title=\"'+h['name']+'\"' if h else ''}>{d.day}</td>")
                d += timedelta(1)
            weeks = [cells[i:i+7] for i in range(0, len(cells), 7)]
            body = "".join("<tr>" + "".join(w) + "</tr>" for w in weeks)
            out.append(f"<div><h3 style='margin:0 0 6px;font-size:1rem'>{M_AT[m-1]}</h3><table class='mini'><thead><tr>{''.join('<th>'+x+'</th>' for x in WDS)}</tr></thead><tbody>{body}</tbody></table></div>")
        return "".join(out)
    hlist = "".join(f"<li>{r['day']}: {r['name']}</li>" for r in rows_for("at", "", year))
    tool = (f"<style>.months{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:18px}}"
            ".mini{border-collapse:collapse;width:100%;font-size:.82rem;text-align:center}.mini th{color:var(--muted);font-weight:600}.mini td,.mini th{padding:3px}"
            "@media print{.months{grid-template-columns:repeat(4,1fr);gap:8px}.mini{font-size:9pt}h1{font-size:18pt}}</style>"
            f"<p class='no-print'><button class='btn' type='button' data-print>Drucken oder als PDF speichern</button></p>"
            f"<div class='months'>{month_grid('at','')}</div>"
            f"<h2 style='font-size:1.1rem'>Feiertage {year} in Österreich</h2><ul style='columns:2;font-size:.9rem'>{hlist}</ul>")
    body = f"""<h2>Für jedes Bundesland</h2>
<p>Dieser Kalender zeigt die bundesweiten Feiertage Österreichs. Für dein Bundesland – auch in Deutschland – öffnest du die passende Seite unter <a href="/feiertage-{year}-oesterreich.html">Feiertage {year} Österreich</a> oder <a href="/feiertage-{year}-deutschland.html">Feiertage {year} Deutschland</a> und druckst dort die Jahresübersicht.</p>
<p>Tipp: Im Druckdialog „Querformat“ wählen. Werbung und Navigation werden beim Druck automatisch ausgeblendet.</p>"""
    crumbs = [("/", "Start"), (f"/kalender-{year}-zum-ausdrucken.html", f"Kalender {year} zum Ausdrucken")]
    write(f"kalender-{year}-zum-ausdrucken.html", "tool.html", title=f"Kalender {year} zum Ausdrucken – mit Feiertagen (A4, PDF) | Kalenderkompass 24",
          description=f"Kostenloser Jahreskalender {year} zum Ausdrucken auf A4 – mit allen Feiertagen, als PDF speicherbar.",
          h1=f"Kalender {year} zum Ausdrucken", lead=f"Das ganze Jahr {year} auf einer A4-Seite, Feiertage in Rot. Kostenlos drucken oder als PDF speichern.",
          tool=tool, body=body, crumbs=crumbs, show_picker=False, related=[a for a in ARTICLES if a["slug"] == "monatsplanung"],
          jsonld=[crumbs_ld(crumbs)], active=f"/kalender-{CUR}-zum-ausdrucken.html", priority=0.8)


def build_articles():
    for a in ARTICLES:
        crumbs = [("/", "Start"), ("/" + a["slug"] + ".html", a["title"])]
        related = [x for x in ARTICLES if x["slug"] != a["slug"]][:3]
        ld = [crumbs_ld(crumbs), {"@context": "https://schema.org", "@type": "Article", "headline": a["title"],
              "description": a["description"], "inLanguage": "de", "datePublished": "2026-10-29", "dateModified": "2026-10-29",
              "author": {"@type": "Organization", "name": "Redaktion Kalenderkompass 24", "url": SITE + "/about.html"},
              "publisher": {"@type": "Organization", "name": "AdStern"}, "mainEntityOfPage": SITE + "/" + a["slug"] + ".html"}]
        write(a["slug"] + ".html", "page.html", title=f"{a['title']} | Kalenderkompass 24", description=a["description"],
              h1=a["title"], lead=a["teaser"], body=a["body"], related=related, crumbs=crumbs, jsonld=ld, active="", priority=0.7)


LEGAL_ADDR = "AdStern :: Agentur für digitales Marketing<br>Seilerstätte 8, 1010 Wien, Österreich<br>E-Mail: <a href='mailto:office@adstern.com'>office@adstern.com</a><br>Web: <a href='https://www.adstern.com'>www.adstern.com</a>"


def build_legal():
    write("imprint.html", "page.html", title="Impressum | Kalenderkompass 24", description="Impressum und Offenlegung von Kalenderkompass 24.",
          h1="Impressum", body=f"""<h2>Medieninhaber und Herausgeber</h2><p>{LEGAL_ADDR}</p>
<h2>Unternehmensangaben</h2><p>Unternehmensgegenstand: Werbeagentur<br>UID-Nummer: ATU54682507<br>Gewerbebehörde: Magistratisches Bezirksamt für den 1. Bezirk, Wien</p>
<p>Angaben nach § 5 E-Commerce-Gesetz und § 25 Mediengesetz.</p>
<h2>Grundlegende Richtung</h2><p>Kalenderkompass 24 ist eine unabhängige Informationsseite zu Feiertagen, Brückentagen, Kalenderwochen und Urlaubsplanung in Österreich und Deutschland. Die Seite finanziert sich über Werbung.</p>
<h2>Haftung</h2><p>Alle Angaben wurden sorgfältig nach den geltenden Feiertagsgesetzen berechnet und geprüft, erfolgen aber ohne Gewähr. Rechtliche Hinweise in den Ratgebern ersetzen keine Rechtsberatung.</p>""",
          ads=False, robots="noindex,follow", active="")
    write("about.html", "page.html", title="Über Kalenderkompass 24", description="Wer hinter Kalenderkompass 24 steht und wie die Feiertage berechnet werden.",
          h1="Über Kalenderkompass 24", lead="Feiertage, Brückentage und Urlaubsplanung – genau, schnell und ohne Anmeldung.",
          body=f"""<p>Kalenderkompass 24 wird von AdStern in Wien betrieben. Die Seite beantwortet Fragen, die sich jedes Jahr wieder stellen: Wann ist der nächste Feiertag? Welche Brückentage gibt es? Wann sind Schulferien? Und wie hole ich aus meinem Urlaub die meisten freien Tage heraus?</p>
<h2>Was du hier findest</h2>
<ul><li>Gesetzliche Feiertage für alle 9 österreichischen Bundesländer und alle 16 deutschen Länder, mit Landespatronen und regionalen Besonderheiten</li>
<li>Brückentage und einen Urlaubsplaner, der Urlaubstage rund um Feiertage optimal verteilt</li>
<li>Amtliche Schulferien-Termine mit Zeitstrahl und Kalender-Export</li>
<li>Kalenderwochen, Arbeitstage-Rechner und Kalender zum Ausdrucken</li>
<li>Ratgeber zu Urlaubsanspruch, Fristen und Feiertagsregeln</li></ul>
<h2>Woher die Daten kommen</h2>
<p><strong>Feiertage</strong> werden nicht abgeschrieben, sondern aus den Rechtsgrundlagen berechnet: für Österreich aus § 7 Arbeitsruhegesetz, für Deutschland aus den Feiertagsgesetzen der 16 Länder. Bewegliche Feiertage wie Ostermontag, Christi Himmelfahrt oder Pfingstmontag leiten wir vom Osterdatum ab, das nach dem gregorianischen Kalender berechnet wird. Der Buß- und Bettag in Sachsen ist der Mittwoch vor dem 23. November.</p>
<p><strong>Schulferien</strong> übernehmen wir ausschließlich aus amtlichen Quellen: für Österreich aus dem Ferienkalender auf oesterreich.gv.at, für Deutschland aus den Kalenderdateien der Kultusministerkonferenz. Wir zeigen nur Schuljahre, die dort bereits veröffentlicht sind – keine Schätzungen.</p>
<h2>So prüfen wir</h2>
<p>Bei jeder Aktualisierung prüft ein Testprogramm die Berechnung gegen bekannte Stichproben – etwa die Ostertermine von 2000 bis 2038, den Buß- und Bettag und die Zahl der bundesweiten Feiertage. Schlägt ein Test fehl, wird die Seite nicht veröffentlicht. Zusätzlich gleichen wir die Ergebnisse mit amtlichen Veröffentlichungen ab. Brückentage und Urlaubsvorschläge werden aus denselben Daten abgeleitet, damit Tabellen, Kalender und Planer immer übereinstimmen.</p>
<h2>Grenzen</h2>
<p>Nicht enthalten sind Feiertage einzelner Gemeinden (etwa das Hohe Friedensfest in Augsburg – wir weisen auf solche Fälle hin), schulautonome Tage, betriebliche Schließtage und Regelungen aus Kollektiv- oder Tarifverträgen. Landespatrone sind in Österreich keine gesetzlichen Feiertage; wir zeigen sie getrennt an.</p>
<h2>Deine Daten</h2><p>Alle Werkzeuge rechnen in deinem Browser. Was du eingibst, verlässt dein Gerät nicht. Werbung und Statistik laufen nur mit deiner Einwilligung, Details in der <a href="/privacy.html">Datenschutzerklärung</a>.</p>
<h2>Fehler gefunden?</h2><p>Schreib uns an <a href="mailto:office@adstern.com">office@adstern.com</a>. Wir prüfen jeden Hinweis und korrigieren Fehler so schnell wie möglich. Stand der Daten: {UPDATED}.</p>""",
          active="", priority=0.3)
    write("privacy.html", "page.html", title="Datenschutz | Kalenderkompass 24", description="Datenschutzerklärung von Kalenderkompass 24.",
          h1="Datenschutzerklärung", lead="Stand: 29. Oktober 2026", ads=False, robots="noindex,follow", active="", body=f"""
<h2>Verantwortlicher</h2><p>{LEGAL_ADDR}</p>
<h2>Hosting</h2><p>Die Website wird über GitHub Pages (GitHub, Inc., 88 Colin P. Kelly Jr. Street, San Francisco, USA) ausgeliefert. Beim Aufruf verarbeitet GitHub technisch notwendige Verbindungsdaten wie IP-Adresse, aufgerufene Adresse, Browserinformationen und Zeitpunkt, um die Seite auszuliefern und vor Angriffen zu schützen. Rechtsgrundlage ist unser berechtigtes Interesse an einem sicheren Betrieb (Art. 6 Abs. 1 lit. f DSGVO). GitHub ist nach dem EU-US Data Privacy Framework zertifiziert. Die Schriften liegen auf unserem eigenen Server; es wird keine Verbindung zu Google Fonts aufgebaut.</p>
<h2>Werkzeuge</h2><p>Kalender, Planer und Rechner arbeiten ausschließlich in deinem Browser. Deine Eingaben werden nicht an uns übertragen. Damit die Seite sich dein Bundesland merkt, speichern wir es im lokalen Speicher deines Browsers (localStorage). Diese Speicherung ist für die von dir gewünschte Funktion erforderlich (§ 165 Abs. 3 TKG 2021). Du kannst sie jederzeit über die Browser-Einstellungen löschen.</p>
<h2>Einwilligungsverwaltung</h2><p>Für Werbung und Statistik nutzen wir die Einwilligungsverwaltung „Datenschutz &amp; Mitteilungen“ von Google (Google Ireland Limited, Gordon House, Barrow Street, Dublin 4, Irland), eine nach dem IAB Transparency &amp; Consent Framework zertifizierte Lösung. Beim ersten Besuch kannst du dort zustimmen, ablehnen oder einzelne Zwecke und Anbieter auswählen. Deine Auswahl kannst du jederzeit über „Datenschutz-Einstellungen“ im Seitenfuß ändern oder widerrufen.</p>
<h2>Google AdSense</h2><p>Wir finanzieren die Seite über Anzeigen von Google AdSense (Google Ireland Limited). Google und die im Einwilligungsdialog genannten Werbepartner können dabei IP-Adresse, Geräte- und Browserinformationen, besuchte Seiten sowie Interaktionen mit Anzeigen verarbeiten und Cookies oder ähnliche Technologien einsetzen, um Anzeigen auszuliefern, zu messen und Betrug zu verhindern. Personalisierte Anzeigen erscheinen nur mit deiner Einwilligung (Art. 6 Abs. 1 lit. a DSGVO, § 165 Abs. 3 TKG 2021). Ohne Einwilligung kann Google nicht personalisierte Anzeigen ausliefern; auch dabei werden für Auslieferung und Betrugsschutz technisch notwendige Daten verarbeitet. Ist in deinem Browser „Global Privacy Control“ aktiv, laden wir keine Werbung. Mehr dazu: <a href="https://policies.google.com/technologies/partner-sites?hl=de" rel="noopener">Datennutzung durch Google auf Partner-Websites</a>, <a href="https://policies.google.com/privacy?hl=de" rel="noopener">Datenschutzerklärung von Google</a>, <a href="https://adssettings.google.com" rel="noopener">Google-Anzeigeneinstellungen</a>.</p>
<h2>Google Analytics</h2><p>Mit deiner Einwilligung im Google-Dialog (Zweck „Informationen auf einem Gerät speichern und/oder abrufen“ und Anbieter Google) verwenden wir Google Analytics 4 von Google Ireland Limited, um zu verstehen, welche Seiten genutzt werden. Ohne diese Einwilligung wird Google Analytics nicht geladen. Google-Signale und Werbepersonalisierung sind in unserer Analytics-Einbindung deaktiviert. Google speichert in Google Analytics 4 keine vollständigen IP-Adressen. Eingaben in unsere Werkzeuge werden nicht übermittelt. Rechtsgrundlage ist deine Einwilligung (Art. 6 Abs. 1 lit. a DSGVO, § 165 Abs. 3 TKG 2021); widerrufen kannst du sie jederzeit über „Datenschutz-Einstellungen“.</p>
<h2>Übermittlung in Drittländer</h2><p>Google und GitHub können Daten auch in den USA verarbeiten. Beide Unternehmen sind nach dem EU-US Data Privacy Framework zertifiziert; die Übermittlung stützt sich auf den Angemessenheitsbeschluss der EU-Kommission.</p>
<h2>Kontakt per E-Mail</h2><p>Schreibst du uns, verwenden wir deine Adresse und Nachricht nur zur Bearbeitung deiner Anfrage (Art. 6 Abs. 1 lit. b oder f DSGVO) und löschen sie, wenn sie nicht mehr gebraucht werden und keine Aufbewahrungspflicht besteht.</p>
<h2>Deine Rechte</h2><p>Du hast das Recht auf Auskunft, Berichtigung, Löschung, Einschränkung der Verarbeitung, Datenübertragbarkeit und Widerspruch sowie das Recht, eine Einwilligung jederzeit zu widerrufen. Anfragen an <a href="mailto:office@adstern.com">office@adstern.com</a>. Beschwerden kannst du bei der Österreichischen Datenschutzbehörde einreichen (<a href="https://www.dsb.gv.at" rel="noopener">dsb.gv.at</a>).</p>""")
    write("404.html", "page.html", title="Seite nicht gefunden | Kalenderkompass 24", description="Diese Seite gibt es nicht.",
          h1="Diese Seite gibt es nicht", lead="Vielleicht hilft dir einer dieser Links weiter.", ads=False, robots="noindex",
          body=f"<ul><li><a href='/'>Feiertage und Brückentage</a></li><li><a href='/feiertage-{CUR}-oesterreich.html'>Feiertage {CUR} Österreich</a></li><li><a href='/feiertage-{CUR}-deutschland.html'>Feiertage {CUR} Deutschland</a></li><li><a href='/urlaubsplaner.html'>Urlaubsplaner</a></li></ul>", active="")


def build_static():
    (OUT / "assets").mkdir(parents=True, exist_ok=True)
    for f in (ROOT / "assets").iterdir():
        shutil.copy(f, OUT / "assets" / f.name)
    (OUT / "assets" / "icon.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect x="2" y="5" width="28" height="25" rx="5" fill="#15233B"/><rect x="2" y="5" width="28" height="8" rx="4" fill="#C4122F"/><rect x="7" y="17" width="5" height="5" rx="1" fill="#F2B100"/><rect x="14" y="23.5" width="5" height="4" rx="1" fill="#0F7C80"/></svg>')
    (OUT / "CNAME").write_text("kalenderkompass24.de\n")
    (OUT / ".nojekyll").write_text("")
    (OUT / "google9bf1079fd4bf073e.html").write_text("google-site-verification: google9bf1079fd4bf073e.html")
    (OUT / "ads.txt").write_text("google.com, pub-7811071715414905, DIRECT, f08c47fec0942fa0\n")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
    urls = "".join(f"<url><loc>{SITE}{p}</loc><lastmod>2026-10-29</lastmod><priority>{pr}</priority></url>" for p, pr in PAGES)
    (OUT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')


def main():
    H.selftest()
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir()
    build_data()
    build_home()
    for y in (2027, 2028): build_regions(y)
    for y in YEARS: build_country(y)
    for y in (2027, 2028): build_bridges(y)
    build_planner(); build_workdays()
    for y in YEARS: build_kw(y)
    for y in (2027, 2028): build_print(y)
    import build_ferien; build_ferien.run(write, fmt, mshort, crumbs_ld, TODAY, SITE)
    build_articles(); build_legal(); build_static()
    print(f"{len(PAGES)} indexierbare Seiten in {OUT}")


if __name__ == "__main__":
    main()
