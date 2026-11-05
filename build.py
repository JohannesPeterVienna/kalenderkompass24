"""Erzeugt die komplette statische Website in docs/ (GitHub Pages)."""
import json, re, shutil, sys
from datetime import date, timedelta
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

sys.path.insert(0, str(Path(__file__).parent))
import holidays as H
from content.articles import ARTICLES
from content.laender import LAND, CLAIMS_DE
from content.oesterreich import LAND_AT, CLAIMS_AT
from content.werkzeuge import URLAUBSPLANER
from content.shop import PRODUCTS, SHOP_LIVE

ROOT = Path(__file__).parent
OUT = ROOT / "docs"
SITE = "https://kalenderkompass24.de"
V = "20261105a"
UPDATED = "November 2026"
CHECKED = "2. November 2026"          # sichtbare Prüfzeile auf Ratgeber-, Feiertags- und Ferienseiten
CHECKED_ISO = "2026-11-02"
CHECKED_NEW = "3. November 2026"      # Seiten, die am 3.11.2026 inhaltlich überarbeitet wurden
CHECKED_0411 = "4. November 2026"     # Seiten, die am 4.11.2026 inhaltlich ausgebaut wurden
CHECKED_0511 = "5. November 2026"     # neue Seite Mein Kalender
LASTMOD = "2026-11-04"                # lastmod in der Sitemap
METHODIK = "/quellen-methodik.html"
RIS = "https://www.ris.bka.gv.at/"
TODAY = date(2026, 11, 4)        # Build-Stand: nächste Feiertage auf der Startseite, laufende Ferien
CUR = 2027                      # Hauptjahr der Seite (Planung läuft aufs nächste Jahr)
YEARS = [2026, 2027, 2028]
DATA_YEARS = range(2025, 2031)

M_AT = ["Jänner","Februar","März","April","Mai","Juni","Juli","August","September","Oktober","November","Dezember"]
M_DE = ["Januar"] + M_AT[1:]
MS_AT = ["Jän","Feb","Mär","Apr","Mai","Jun","Jul","Aug","Sep","Okt","Nov","Dez"]
MS_DE = ["Jan"] + MS_AT[1:]
WDL = ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"]
WDS = ["Mo","Di","Mi","Do","Fr","Sa","So"]

NAV = [("/", "Feiertage"), ("/mein-kalender.html", "Mein Kalender"), (f"/brueckentage-{CUR}.html", "Fenstertage"), ("/urlaubsplaner.html", "Urlaubsplaner"),
       ("/schulferien-2026-2027.html", "Schulferien"), ("/familienplaner.html", "Familienplaner"), (f"/kalenderwochen-{CUR}.html", "Kalenderwochen"), (f"/kalender-{CUR}-zum-ausdrucken.html", "Kalender drucken")]

env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=True, trim_blocks=True, lstrip_blocks=True)
PAGES = []  # (path, priority) für die Sitemap


def mnames(country): return M_AT if country == "at" else M_DE
def mshort(country): return MS_AT if country == "at" else MS_DE
def fmt(d, country, wd=True, year=True):
    s = f"{d.day}. {mnames(country)[d.month-1]}" + (f" {d.year}" if year else "")
    return (WDL[d.weekday()] + ", " + s) if wd else s


def write(path, template, **ctx):
    base = dict(site=SITE, v=V, updated=UPDATED, nav=NAV, active=ctx.get("active", path), jsonld=[], ads=True,
                lang_at=True, years=YEARS, year=CUR, robots=None, region_attr=None, year_attr=None, og_title=None,
                checked=None, sources=None, skip_ads=(), extra_html=None, mk=False, shop_live=SHOP_LIVE)
    m = re.fullmatch(r"[a-z-]+?-(20\d\d)(-[a-z-]+)?\.html", path)
    if "year" not in ctx and m and int(m.group(1)) in YEARS:
        base["year"] = int(m.group(1))       # Jahresseiten zeigen immer ihr eigenes Jahr
    base.update(ctx)
    base["path"] = "/" if path == "index.html" else "/" + path
    # Anzeigenplätze nur auf indexierbaren Seiten; Einwilligung/Statistik (consent.js) bleibt überall gleich
    base["slots"] = bool(base["ads"]) and "noindex" not in (base["robots"] or "")
    if template == "tool.html":
        # Erste Anzeige erst nach dem ersten Erklärabschnitt unter dem Werkzeug
        body = base.get("body") or ""
        cut = body.find("<h2", body.find("<h2") + 1) if body.count("<h2") > 1 else -1
        base["body_first"], base["body_rest"] = (body[:cut], body[cut:]) if cut > 0 else (body, "")
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
        d0 = b["days"][0]
        res.append({"dt": f"{d0.day:02d}.{d0.month:02d}.", "take": take, "holiday": b["holiday"], "vacation": b["vacation"], "free": b["free"],
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
            if d in br: cls += " br"; title += " – Fenstertag" if country == "at" else " – Brückentag"
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
            "art": H.REGION_ARTICLE, "h": h}
    (OUT / "data").mkdir(exist_ok=True)
    (OUT / "data" / "feiertage.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    import ferien as F
    sf = {f"{c}:{slug}": [[p["name"], p["start"].isoformat(), p["end"].isoformat()] for p in F.periods(c, slug)]
          for c in ("at", "de") for slug in F.regions(c)}
    (OUT / "data" / "schulferien.json").write_text(json.dumps({"schuljahr": F.SCHOOLYEAR, "bis": F.SY_END.isoformat(), "f": sf}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


# ---------------------------------------------------------------- Texte je Region
def region_facts(country, region, year):
    name = region_name(country, region)
    in_name = H.region_in(region, name)
    rows = H.region_holidays(country, region, year)
    legal = [r for r in rows if r["kind"] == "legal"]
    wkd = [r for r in legal if r["date"].weekday() < 5]
    facts = []
    if country == "at":
        facts.append(f"{H.cap(in_name)} gelten wie in ganz Österreich die 13 gesetzlichen Feiertage nach § 7 Arbeitsruhegesetz. "
                     f"{year} fallen davon {len(wkd)} auf einen Werktag von Montag bis Freitag.")
        pats = [r for r in rows if r["kind"] == "patron"]
        for p in pats:
            facts.append(f"Der {p['name'].split(' (')[0]} am {fmt(p['date'], 'at')} ist {in_name} kein gesetzlicher Feiertag. "
                         "Geschäfte haben geöffnet, an den Schulen ist aber in der Regel unterrichtsfrei. Ob Betriebe oder Dienststellen freigeben, regeln Kollektivvertrag, Betriebsvereinbarung oder Dienstrecht.")
        facts.append("Der 24. und der 31. Dezember sind keine Feiertage. Viele Kollektivverträge sehen an diesen Tagen aber ganz oder ab Mittag frei vor.")
        facts.append("Den Karfreitag gibt es in Österreich seit 2019 nicht mehr als Feiertag. Stattdessen kann jede und jeder einen persönlichen Feiertag festlegen, der vom Urlaub abgezogen wird.")
    else:
        code = H.DE_REGIONS[region][1]
        extra = [r["name"] for r in legal if r["name"] not in {
            "Neujahr", "Karfreitag", "Ostermontag", "Tag der Arbeit", "Christi Himmelfahrt", "Pfingstmontag",
            "Tag der Deutschen Einheit", "1. Weihnachtsfeiertag", "2. Weihnachtsfeiertag"}]
        facts.append(f"{H.cap(H.region_nom(region, name))} hat {year} {len(legal)} gesetzliche Feiertage, {len(wkd)} davon an Werktagen von Montag bis Freitag. "
                     + (f"Zusätzlich zu den neun bundesweiten Feiertagen gilt hier: {', '.join(extra)}." if extra
                        else "Es gelten nur die neun bundesweit einheitlichen Feiertage."))
        note = H.de_partial_notes(code)
        if note: facts.append(note)
        if code == "BB":
            facts.append("Ostersonntag und Pfingstsonntag sind in Brandenburg ausdrücklich gesetzliche Feiertage. Für Beschäftigte, die sonntags arbeiten, ist das wegen der Zuschläge relevant.")
        facts.append("Fällt ein Feiertag auf ein Wochenende, gibt es keinen Ersatztag. Der 24. und 31. Dezember sind keine gesetzlichen Feiertage.")
    return facts


# ---------------------------------------------------------------- Urlaubsblöcke je Land (DE-Länderseiten)
def best_block(country, region, year, k, around, prefer=None):
    """Längster freier Block mit genau k Urlaubstagen (Mo–Fr ohne gesetzlichen Feiertag), der einen der
    Feiertage in `around` enthält. Alle Urlaubstage liegen im Jahr `year`; vor und nach dem Block liegt ein
    Arbeitstag. Bei Gleichstand gewinnt der Block mit dem höheren Wert `prefer(take)` (z. B. mehr schulfreie
    Urlaubstage), danach der frühere."""
    off = set()
    for y in (year - 1, year, year + 1):
        off |= H.off_days(country, region, y)
    wk = lambda d: H.is_workday(d, off)
    best = None
    lo, hi = min(around) - timedelta(30), max(around) + timedelta(30)
    starts = [lo + timedelta(i) for i in range((hi - lo).days + 1)]
    for a in starts:
        if not wk(a - timedelta(1)) or a > min(around): continue
        for i in range(0, 40):
            b = a + timedelta(i)
            if not any(a <= h <= b for h in around): continue
            if not wk(b + timedelta(1)): continue
            take = [a + timedelta(j) for j in range(i + 1) if wk(a + timedelta(j))]
            if len(take) > k: break
            if len(take) != k or take[0].year != year or take[-1].year != year: continue
            free = i + 1
            score = (free, prefer(take) if prefer else 0)
            if best is None or score > best["score"]:
                best = {"from": a, "to": b, "take": take, "free": free, "vacation": k, "score": score}
    return best


def check_block(country, region, blk):
    """Unabhängige Gegenrechnung über die Feiertagsliste (nicht über off_days)."""
    names = {h["date"] for y in (blk["from"].year - 1, blk["from"].year, blk["to"].year + 1)
             for h in H.region_holidays(country, region, y) if h["kind"] == "legal"}
    work = lambda d: d.weekday() <= 4 and d not in names
    n = (blk["to"] - blk["from"]).days + 1
    assert n == blk["free"], blk
    assert sum(work(blk["from"] + timedelta(i)) for i in range(n)) == blk["vacation"] == len(blk["take"]), blk
    assert work(blk["from"] - timedelta(1)) and work(blk["to"] + timedelta(1)), blk


def school_free(country, slug, days):
    """Zahl der Tage aus `days`, die in amtlichen Schulferien oder an schulfreien Tagen liegen; None außerhalb des Schuljahres."""
    import ferien as F
    if any(d < F.SY_START or d > F.SY_END for d in days): return None
    ps = F.periods(country, slug)
    return sum(any(p["start"] <= d <= p["end"] for p in ps) for d in days)


def de_plan_html(slug, year):
    """Berechneter Abschnitt „Urlaub planen“ für eine deutsche Länderseite: je Feiertag (Mo–Fr) der beste Block
    mit einem und mit vier Urlaubstagen, dazu wie viele der Urlaubstage schulfrei sind."""
    name, code = H.DE_REGIONS[slug]
    in_name = H.region_in(slug, name)
    legal = [h for h in H.region_holidays("de", slug, year) if h["kind"] == "legal"]
    wkd = [h for h in legal if h["date"].weekday() < 5]
    wke = [h for h in legal if h["date"].weekday() >= 5]
    groups = []
    for h in wkd:
        if groups and (h["date"] - groups[-1][-1]["date"]).days <= 4: groups[-1].append(h)
        else: groups.append([h])
    sd = lambda d: f"{WDS[d.weekday()]} {d.day}. {MS_DE[d.month-1]}"
    rng = lambda b: (f"{b['from'].day}.–{fmt(b['to'], 'de', wd=False, year=b['to'].year != year)}" if b["from"].month == b["to"].month
                     else f"{fmt(b['from'], 'de', wd=False, year=False)} – {fmt(b['to'], 'de', wd=False, year=b['to'].year != year)}")
    rows, longest, fam_rows = [], None, []
    for g in groups:
        around = [h["date"] for h in g]
        pref = lambda take: school_free("de", slug, take) or 0
        one, four = best_block("de", slug, year, 1, around, pref), best_block("de", slug, year, 4, around, pref)
        for b in (one, four):
            if b: check_block("de", slug, b)
        sf = school_free("de", slug, four["take"]) if four else None
        fam_rows.append((g, sf))
        if four and (longest is None or four["free"] > longest[1]["free"]): longest = (g, four)
        label = " und ".join(h["name"] for h in g)
        c1 = f"{sd(one['take'][0])} → {one['free']} Tage ({rng(one)})" if one else "–"
        c4 = f"{' + '.join(sd(d) for d in four['take'])} → {four['free']} Tage ({rng(four)})" if four else "–"
        cs = ("Schuljahr 2027/28 noch nicht in unseren Daten" if sf is None else
              "keiner schulfrei" if sf == 0 else "alle schulfrei" if sf == 4 else f"{sf} von 4 schulfrei")
        rows.append(f"<tr><td><strong>{label}</strong><div class='small muted'>{', '.join(sd(h['date']) for h in g)}</div></td><td>{c1}</td><td>{c4}</td><td>{cs}</td></tr>")
    we_txt = (", ".join(f"{h['name']} ({WDL[h['date'].weekday()]})" for h in wke[:-1]) + (" und " if len(wke) > 1 else "") + f"{wke[-1]['name']} ({WDL[wke[-1]['date'].weekday()]})") if wke else ""
    g, lb = longest
    fams = [(sf, gg) for gg, sf in fam_rows if sf]
    if fams:
        top = max(f[0] for f in fams)
        names_top = [" und ".join(h["name"] for h in gg) for sf, gg in fams if sf == top]
        fam = (f"Für Eltern passt {year} am besten der Block rund um {' sowie '.join(names_top)}: Dort {'sind alle vier Urlaubstage' if top == 4 else 'ist einer der vier Urlaubstage' if top == 1 else f'sind {top} der vier Urlaubstage'} auch schulfrei.")
    else:
        fam = "Keiner der Vier-Tage-Blöcke fällt in die Schulferien – Eltern müssen für diese Tage eine Betreuung einplanen oder den Urlaub an die Ferien anpassen."
    return f"""
<h2>Urlaub {year} {in_name}: die ergiebigsten Termine</h2>
<p>Von den {len(legal)} gesetzlichen Feiertagen liegen {year} {in_name} {len(wkd)} auf einem Werktag. {('Aufs Wochenende ' + ('fällt ' if len(wke) == 1 else 'fallen ') + we_txt + '.') if wke else ''} Was ein und was vier Urlaubstage rund um jeden dieser Feiertage bringen:</p>
<div class="scroll"><table class="tbl"><thead><tr><th scope="col">Feiertag</th><th scope="col">1 Urlaubstag</th><th scope="col">4 Urlaubstage</th><th scope="col">davon schulfrei</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<p>Den längsten Block mit vier Urlaubstagen gibt es rund um {' und '.join(h['name'] for h in g)}: {lb['free']} Tage vom {fmt(lb['from'], 'de', year=False)} bis {fmt(lb['to'], 'de', year=lb['to'].year != year)}. {fam}</p>
<p class="small muted">Fünftagewoche; 24. und 31. Dezember als Arbeitstage; Feiertage einzelner Gemeinden nicht berücksichtigt. „davon schulfrei“: Urlaubstage, an denen nach dem amtlichen Ferienkalender auch die Schulen {in_name} geschlossen sind. Andere Urlaubsmengen rechnet der <a href="/urlaubsplaner.html">Urlaubsplaner</a> durch.</p>
"""


# ---------------------------------------------------------------- Seiten
def build_home():
    t = TODAY
    # Statisch nur Datumsangaben (ohne „in X Tagen“), damit die Seite ohne JavaScript nie veraltet wirkt;
    # app.js ersetzt den Kasten im Browser durch den tagesaktuellen Countdown für das gewählte Bundesland.
    nxt = [r for y in (t.year, t.year+1) for r in H.region_holidays("at", "", y) if r["date"] >= t][:3]
    rows = rows_for("at", "", CUR)
    iw = TODAY.isocalendar()
    ld = [{"@context": "https://schema.org", "@type": "WebSite", "name": "Kalenderkompass 24", "url": SITE + "/",
           "inLanguage": "de", "description": "Feiertage, Brückentage und Urlaubsplanung für Österreich und Deutschland."},
          holiday_ld("at", "", CUR, rows)]
    write("index.html", "home.html", title=f"Feiertage & Fenstertage {CUR}: Österreich und Deutschland | Kalenderkompass 24",
          description=f"Alle Feiertage {CUR} mit Fenstertagen (Österreich) und Brückentagen (Deutschland) für jedes Bundesland – mit eigenem Kalender, Urlaubsplaner und Export.",
          next_list=[{"name": r["name"], "date": fmt(r["date"], "at")} for r in nxt], next_sheet={"month": M_AT[nxt[0]["date"].month-1], "day": nxt[0]["date"].day, "wd": WDS[nxt[0]["date"].weekday()] + " · KW " + str(nxt[0]["date"].isocalendar()[1])}, next_asof=fmt(t, "at", wd=False), band=band_view("at", "", CUR),
          bridge_list=bridge_view("at", "", CUR), rows=rows, year_attr=CUR,
          at_regions=list(H.AT_REGIONS.items()), de_regions=[(k, v[0]) for k, v in H.DE_REGIONS.items()],
          articles=ARTICLES, kw={"week": iw[1], "year": iw[0]}, jsonld=ld, priority=1.0, active="/", mk=True,
          skip_ads=("half", "sky"))   # Seitenleisten-Anzeigen lägen direkt neben Brückentagen und Urlaubsplaner


def ferien_teaser(country, slug, name):
    import ferien as F
    ps = [p for p in F.periods(country, slug) if not p["single"]]
    su = F.summer(country, slug)
    lng = max((p for p in ps if p["name"] != "Sommerferien"), key=lambda p: p["days"])
    return {"text": f"Im Schuljahr {F.SCHOOLYEAR} hat {H.region_nom(slug, name)} {len(ps)} Ferienblöcke mit insgesamt {F.total_days(country, slug)} Ferientagen. "
                    f"Die Sommerferien 2027 dauern von {fmt(su['start'], country)} bis {fmt(su['end'], country)}. "
                    f"Die längsten Ferien nach dem Sommer sind die {lng['name']} mit {lng['days']} Tagen ({fmt(lng['start'], country, wd=False)} bis {fmt(lng['end'], country, wd=False)}). "
                    f"Wer Brückentage und Ferien kombiniert, kann Familienurlaub besonders effizient planen.",
            "href": f"/schulferien-{F.SY_SLUG}-{slug}.html", "sy": F.SCHOOLYEAR}


def at_bridge_text(year, in_name):
    """Kurzfassung der (bundesweit gleichen) Fenstertage für AT-Länderseiten mit eigenem Text; die volle Liste steht im Ratgeber."""
    bl = H.bridge_days("at", "", year)
    one = [b for b in bl if b["vacation"] == 1]
    two = [b for b in bl if b["vacation"] == 2]
    lst = ", ".join(fmt(b["days"][0], "at", year=False) for b in one[:-1]) + " und " + fmt(one[-1]["days"][0], "at", year=False)
    hs = sorted({b["holiday"] for b in two})
    return (f"Die gesetzlichen Feiertage sind in ganz Österreich gleich, deshalb gelten {in_name} dieselben Fenstertage wie im übrigen Land: "
            f"{lst} – mit je einem Urlaubstag {one[0]['free']} freie Tage am Stück. Dazu kommen {len(two)} Zwickel aus je zwei Arbeitstagen rund um "
            f"{' und '.join(hs)}. Der Landespatron zählt dabei nicht mit, weil er für Beschäftigte ein normaler Arbeitstag ist.")


def build_regions(year):
    for country, regions in (("at", H.AT_REGIONS), ("de", {k: v[0] for k, v in H.DE_REGIONS.items()})):
        cslug = "oesterreich" if country == "at" else "deutschland"
        cname = "Österreich" if country == "at" else "Deutschland"
        for slug, name in regions.items():
            rows = rows_for(country, slug, year)
            legal = [r for r in rows if r["kind"] == "legal"]
            bl = bridge_view(country, slug, year)
            singles = [b for b in bl if b["vacation"] == 1]
            bt = "Fenstertag" if country == "at" else "Brückentag"
            lead = (f"{len(legal)} gesetzliche Feiertage, {len(bl)} {bt}{'e' if len(bl) != 1 else ''}"
                    + (f" – der beste: {singles[0]['take']}, {singles[0]['free']} Tage frei mit einem Urlaubstag." if singles else ".")
                    + " Mit Jahresübersicht und Kalender-Export.")
            path = f"feiertage-{year}-{slug}.html"
            in_name = H.region_in(slug, name)
            own = (LAND_AT if country == "at" else LAND).get(slug) if year == CUR else None
            srcs = [("Arbeitsruhegesetz § 7 und Schulzeitgesetz 1985 im RIS", RIS)] if country == "at" else []
            if country == "at" and own:
                import ferien as F
                srcs.append(F.SRC_AT)
                pat = [r for r in rows if r["kind"] == "patron" and r["date"].weekday() < 5]
                sem = next(p for p in F.periods("at", slug) if p["name"] == "Semesterferien")
                lead = (f"{len(legal)} gesetzliche Feiertage wie in ganz Österreich, dazu "
                        + " und ".join(f"der {p['name'].split(' (')[0]} am {fmt(p['date'], 'at', year=False)}" for p in pat)
                        + f" – an Schulen in der Regel unterrichtsfrei. Semesterferien {sem['start'].day}.–{fmt(sem['end'], 'at', wd=False, year=False)}, "
                        f"Sommerferien ab {fmt(F.summer('at', slug)['start'], 'at', wd=False, year=False)}.")
            crumbs = [("/", "Start"), (f"/feiertage-{year}-{cslug}.html", f"Feiertage {year} {cname}"), ("/" + path, name)]
            write(path, "region.html", title=f"Feiertage {year} {name}: Termine & {bt}e | Kalenderkompass 24",
                  description=f"Feiertage {year} {in_name}: alle {len(legal)} gesetzlichen Feiertage mit Wochentag, {bt}e und Urlaubstipps – mit Kalender-Download.",
                  h1=f"Feiertage {year} {in_name}", lead=lead, name=name, in_name=in_name, slug=slug, country=country,
                  country_slug=cslug, country_name=cname, legal_count=len(legal),
                  weekday_count=len([r for r in legal if r["date"].weekday() < 5]), bridge_count=len(bl),
                  band=band_view(country, slug, year), rows=rows, bridge_list=bl,
                  # Mit eigenem AT-Länderteil nur der erste, landesbezogene Satz – der Rest stünde wortgleich auf allen neun Seiten
                  facts=region_facts(country, slug, year)[:1] if (country == "at" and own) else region_facts(country, slug, year),
                  bridge_text=at_bridge_text(year, in_name) if (country == "at" and own) else None,
                  land_html=(own + de_plan_html(slug, year)) if (country == "de" and own) else own,
                  land_title=(f"Landespatron, Ferien und Besonderheiten {in_name}" if country == "at" else f"Rechtsgrundlage und Besonderheiten {in_name}"),
                  ferien=ferien_teaser(country, slug, name) if (year == 2027 and not (country == "at" and own)) else None,
                  other_years=[y for y in (2027, 2028) if y != year], siblings=[(s, n) for s, n in regions.items() if s != slug],
                  crumbs=crumbs, region_attr=f"{country}:{slug}:{year}", lang_at=(country == "at"),
                  # Nur Seiten des Hauptjahres mit eigenem Länderteil (content/laender.py, content/oesterreich.py)
                  # werden indexiert; Folgejahr-Seiten (Vorschau) und Länder ohne eigenen Text bleiben
                  # für Besucher erreichbar, werden aber nicht als eigene Suchseite angeboten.
                  robots=None if own else "noindex,follow",
                  checked=CHECKED_NEW if (own and country == "at") else CHECKED_0411 if own else CHECKED, sources=srcs,
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
          extra_html=at_country_html(year),
          crumbs=crumbs, checked=CHECKED_0411, sources=[("Arbeitsruhegesetz § 7 im RIS", RIS)],
          jsonld=[crumbs_ld(crumbs), holiday_ld("at", "", year, rows)], priority=0.9 if year == CUR else 0.6)

    # Deutschland
    nat = rows_for("de", "", year)
    allh = {}
    for slug, (name, code) in H.DE_REGIONS.items():
        for r in H.region_holidays("de", slug, year):
            if r["kind"] != "legal": continue          # schulfreie Tage (z. B. Buß- und Bettag in Bayern) sind keine Feiertage
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
          extra_html=de_country_html(year),
          crumbs=crumbs, checked=CHECKED_0411, jsonld=[crumbs_ld(crumbs), holiday_ld("de", "", year, nat)], lang_at=False, priority=0.9 if year == CUR else 0.6)


def at_country_html(year):
    """Ausbau der Österreich-Übersicht: Jahresbilanz (berechnet), Herkunft der Feiertage, Rechtliches."""
    rows = H.region_holidays("at", "", year)
    we = [h for h in rows if h["date"].weekday() >= 5]
    mofr = [h for h in rows if h["date"].weekday() in (0, 4)]
    mid = [h for h in rows if h["date"].weekday() in (1, 2, 3)]
    lst = lambda xs: (", ".join(xs[:-1]) + " und " + xs[-1]) if len(xs) > 1 else (xs[0] if xs else "keiner")
    nf = date(year, 10, 26)
    return f"""
<h2>Das Feiertagsjahr {year} in Zahlen</h2>
<p>{len(rows) - len(we)} der 13 Feiertage liegen {year} auf einem Werktag von Montag bis Freitag. Aufs Wochenende {'fällt' if len(we) == 1 else 'fallen'} {lst([h['name'] + ' (' + WDL[h['date'].weekday()] + ')' for h in we])}; einen Ersatztag gibt es dafür nicht. Ein langes Wochenende ohne Urlaub bringen die Feiertage an einem Montag oder Freitag – {year} sind das {lst([h['name'] for h in mofr])}. Feiertage am Dienstag, Mittwoch oder Donnerstag ({lst([h['name'] for h in mid])}) sind die Kandidaten für Fenstertage. Der Nationalfeiertag ist {year} ein {WDL[nf.weekday()]}.</p>

<h2>Woher die österreichischen Feiertage kommen</h2>
<p>Zehn der 13 Feiertage sind kirchlichen Ursprungs: Heilige Drei Könige, Ostermontag, Christi Himmelfahrt, Pfingstmontag, Fronleichnam, Mariä Himmelfahrt, Allerheiligen, Mariä Empfängnis, Christtag und Stefanitag. Die beweglichen davon hängen am Ostersonntag – {year} ist das der {fmt(H.easter(year), 'at', wd=False)}. Weltlich sind Neujahr, der <strong>Staatsfeiertag</strong> am 1. Mai und der <strong>Nationalfeiertag</strong> am 26. Oktober. Er erinnert an den 26. Oktober 1955, an dem der Nationalrat das Bundesverfassungsgesetz über die immerwährende Neutralität beschloss.</p>
<p>Der <strong>Karfreitag</strong> war bis 2018 nur für Angehörige der evangelischen Kirchen, der Altkatholischen und der Methodistischen Kirche ein Feiertag. Nachdem der Europäische Gerichtshof diese Regel im Jänner 2019 als Diskriminierung beurteilt hatte, wurde sie gestrichen. Seitdem gibt es den <a href="/persoenlicher-feiertag-oesterreich.html">persönlichen Feiertag</a>: einen Urlaubstag pro Jahr, den alle Beschäftigten mit drei Monaten Vorlauf selbst festlegen können.</p>

<h2>Was an Feiertagen gilt</h2>
<p>Grundlage ist das Arbeitsruhegesetz (ARG). An den 13 Feiertagen haben Arbeitnehmerinnen und Arbeitnehmer Anspruch auf ununterbrochene Ruhe von mindestens 24 Stunden und behalten ihr Entgelt. Wer an einem Feiertag arbeiten muss, bekommt zusätzlich zum fortgezahlten Entgelt die geleistete Arbeit bezahlt (§ 9 ARG). Eine Besonderheit ist der 8. Dezember: Geschäfte dürfen an Mariä Empfängnis öffnen, sofern der Tag nicht auf einen Sonntag fällt; Beschäftigte im Handel können die Arbeit an diesem Tag aber ablehnen. Die Landespatrone sind keine Feiertage im Sinn des ARG – ob Betriebe freigeben, regeln Kollektivvertrag, Betriebsvereinbarung oder Dienstrecht. Der 24. und der 31. Dezember sind ebenfalls keine Feiertage, viele Kollektivverträge sehen aber ganz oder ab Mittag frei vor.</p>
"""


def de_country_html(year):
    """Ausbau der Deutschland-Übersicht: Feiertage je Land (berechnet), Herkunft der Zusatzfeiertage, Rechtsgrundlage."""
    nat = {h["name"] for h in H.region_holidays("de", "", year)}
    per, where = [], {}
    for slug, (name, code) in H.DE_REGIONS.items():
        legal = [h for h in H.region_holidays("de", slug, year) if h["kind"] == "legal"]
        extra = [h for h in legal if h["name"] not in nat]
        for h in extra: where.setdefault(h["name"], []).append(name)
        per.append((slug, name, len(legal), sum(h["date"].weekday() < 5 for h in legal), extra))
    rows = "".join(f"<tr><td><a href='/feiertage-{year if year in (2027, 2028) else CUR}-{slug}.html'>{name}</a></td><td>{n}</td><td>{w}</td>"
                   f"<td>{', '.join(h['name'] for h in ex) or '–'}</td></tr>" for slug, name, n, w, ex in per)
    mx, mn = max(p[3] for p in per), min(p[3] for p in per)
    most = [p[1] for p in per if p[3] == mx]; least = [p[1] for p in per if p[3] == mn]
    nat_rows = H.region_holidays("de", "", year)
    nat_we = [h for h in nat_rows if h["date"].weekday() >= 5]
    lst = lambda xs: (", ".join(xs[:-1]) + " und " + xs[-1]) if len(xs) > 1 else xs[0]
    w = lambda n: lst(sorted(where.get(n, [])))
    e = H.easter(year)
    fl = e + timedelta(60)
    bb = H.buss_und_bettag(year)
    assert where.get("Buß- und Bettag") == ["Sachsen"] and where.get("Weltkindertag") == ["Thüringen"]
    assert sorted(where.get("Internationaler Frauentag")) == ["Berlin", "Mecklenburg-Vorpommern"]
    return f"""
<h2>Feiertage {year} je Bundesland</h2>
<p>Die Zahl der gesetzlichen Feiertage schwankt in Deutschland zwischen {min(p[2] for p in per)} und {max(p[2] for p in per)}. Entscheidend für die freien Tage ist aber, wie viele davon auf einen Werktag fallen: {year} sind das am meisten in {lst(most)} ({mx}), am wenigsten in {lst(least)} ({mn}). Bundesweit {'liegt einer' if len(nat_we) == 1 else 'liegen ' + str(len(nat_we))} der neun gemeinsamen Feiertage auf einem Wochenende{(': ' + lst([h['name'] for h in nat_we])) if nat_we else ''}. Einen Ersatztag gibt es dafür in keinem Land.</p>
<div class="scroll"><table class="tbl"><thead><tr><th scope="col">Bundesland</th><th scope="col">Feiertage {year}</th><th scope="col">davon Mo–Fr</th><th scope="col">zusätzlich zu den neun bundesweiten</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="small muted">Gezählt sind landesweite gesetzliche Feiertage; Bayern mit Mariä Himmelfahrt, das dort in Gemeinden mit überwiegend katholischer Bevölkerung gilt. Brandenburg zählt Ostersonntag und Pfingstsonntag ausdrücklich als Feiertage mit, die immer auf einen Sonntag fallen.</p>

<h2>Rechtsgrundlage: die Feiertagsgesetze der Länder</h2>
<p>Für Feiertage sind in Deutschland die Länder zuständig. Jedes der 16 Länder hat ein eigenes Sonn- und Feiertagsgesetz, das die gesetzlichen Feiertage aufzählt und regelt, was an ihnen erlaubt ist. Nur der Tag der Deutschen Einheit ist bundesrechtlich festgelegt: Artikel 2 Absatz 2 des Einigungsvertrags bestimmt den 3. Oktober als gesetzlichen Feiertag. Das Grundgesetz schützt die Sonntage und die staatlich anerkannten Feiertage „als Tage der Arbeitsruhe und der seelischen Erhebung“ (Art. 140 GG in Verbindung mit Art. 139 der Weimarer Reichsverfassung), legt aber selbst keine Feiertage fest.</p>
<p>Daraus folgt eine praktische Regel: Für Beschäftigte zählen die Feiertage am Arbeitsort, nicht am Wohnort. Wer in Mainz wohnt und in Frankfurt arbeitet, hat an Allerheiligen keinen freien Tag; wer in Leipzig wohnt und in Halle arbeitet, hat am Buß- und Bettag keinen. Fällt ein Feiertag auf ein Wochenende, entfällt er ersatzlos. Der 24. und der 31. Dezember sind in keinem Land gesetzliche Feiertage; viele Tarifverträge stellen sie aber ganz oder ab Mittag frei.</p>

<h2>Die Zusatzfeiertage und woher sie kommen</h2>
<ul>
<li><strong>Heilige Drei Könige (6. Januar)</strong> – in {w('Heilige Drei Könige')}. Das Fest der Erscheinung des Herrn (Epiphanias) erinnert an die Sterndeuter aus dem Osten, die nach dem Matthäusevangelium dem neugeborenen Jesus Gaben brachten.</li>
<li><strong>Internationaler Frauentag (8. März)</strong> – in {w('Internationaler Frauentag')}. Berlin hat ihn 2019 eingeführt, Mecklenburg-Vorpommern 2023. Der erste Frauentag fand 1911 statt, seit 1921 wird er am 8. März begangen.</li>
<li><strong>Fronleichnam</strong> – in {w('Fronleichnam')}, {year} am {fmt(fl, 'de', year=False)}. Das katholische Fest des Leibes und Blutes Christi liegt 60 Tage nach Ostern, immer an einem Donnerstag. In einzelnen katholischen Gemeinden Sachsens (Oberlausitz) und Thüringens (Eichsfeld) ist es zusätzlich Feiertag.</li>
<li><strong>Mariä Himmelfahrt (15. August)</strong> – im Saarland landesweit, in Bayern in Gemeinden mit überwiegend katholischer Bevölkerung. Gefeiert wird die Aufnahme Marias in den Himmel.</li>
<li><strong>Weltkindertag (20. September)</strong> – nur in Thüringen, seit 2019. Die Vereinten Nationen hatten 1954 empfohlen, einen Tag für Kinder einzuführen.</li>
<li><strong>Reformationstag (31. Oktober)</strong> – in {w('Reformationstag')}. Er erinnert an Martin Luthers 95 Thesen von 1517. 2017 war er zum 500. Jubiläum einmalig bundesweit frei; Bremen, Hamburg, Niedersachsen und Schleswig-Holstein haben ihn 2018 dauerhaft eingeführt.</li>
<li><strong>Allerheiligen (1. November)</strong> – in {w('Allerheiligen')}. Die katholische Kirche gedenkt an diesem Tag aller Heiligen; viele Familien besuchen die Gräber ihrer Angehörigen.</li>
<li><strong>Buß- und Bettag</strong> – nur in Sachsen, {year} am {fmt(bb, 'de', year=False)}. Er liegt immer am Mittwoch vor dem 23. November. In den übrigen Ländern wurde er ab 1995 abgeschafft, um die Arbeitgeber bei der Finanzierung der Pflegeversicherung zu entlasten; Beschäftigte in Sachsen tragen dafür einen höheren Anteil am Pflegeversicherungsbeitrag. In Bayern ist an diesem Tag schulfrei.</li>
<li><strong>Augsburger Hohes Friedensfest (8. August)</strong> – nur im Stadtgebiet von Augsburg. Die Stadt feiert seit 1650 das Ende der Benachteiligung der Protestanten nach dem Dreißigjährigen Krieg. Weil es nicht im ganzen Land gilt, rechnen wir es nicht mit.</li>
</ul>
<p>Ostersonntag und Pfingstsonntag sind überall Sonntage und damit ohnehin arbeitsfrei; Brandenburg nennt sie zusätzlich ausdrücklich als Feiertage, was für Zuschläge bei Sonntagsarbeit eine Rolle spielen kann. Wie wir rechnen und welche Quellen wir nutzen, steht unter <a href="/quellen-methodik.html">Quellen &amp; Methodik</a>; Brücken- und Urlaubstage für jedes Land findest du bei den <a href="/brueckentage-{year if year in (2027, 2028) else CUR}.html">Brückentagen {year if year in (2027, 2028) else CUR}</a>.</p>
"""


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
    crumbs = [("/", "Start"), (f"/brueckentage-{year}.html", f"Fenster- und Brückentage {year}")]
    write(f"brueckentage-{year}.html", "tool.html",
          title=f"Fenster- & Brückentage {year}: Österreich & Deutschland | Kalenderkompass 24",
          description=f"Alle Brückentage {year}: die Fenstertage in Österreich und die Brückentage jedes deutschen Bundeslandes – mit freien Tagen pro Urlaubstag.",
          h1=f"Fenster- und Brückentage {year}", lead=f"Mit wenig Urlaub viel frei: alle Fenstertage {year} in Österreich und die Brückentage in jedem deutschen Bundesland.",
          tool="".join(str(p) for p in parts), body=body, crumbs=crumbs, show_picker=False, related=[a for a in ARTICLES if a["slug"] in ("ferien-planen", "fenstertag-zwickeltag-brueckentag")],
          jsonld=[crumbs_ld(crumbs)], active=f"/brueckentage-{CUR}.html", priority=0.9 if year == CUR else 0.6)


def build_planner():
    tool = f"""<div class="planner" data-planner>
  <div class="row"><label class="range">Wie viele Urlaubstage willst du einsetzen?<output data-budget-out>10</output><input type="range" min="1" max="30" value="10" data-budget aria-label="Urlaubstage"></label></div>
  <p class="plan-sum" data-plan-sum>Wähle Bundesland und Jahr – der Planer zeigt sofort die effizientesten Termine.</p>
  <div class="band" style="border:0;padding:0;margin:10px 0 16px"><div class="yr" data-plan-band></div>
  <div class="legend"><span><i style="background:var(--red)"></i>Feiertag</span><span><i style="background:var(--sea)"></i>vorgeschlagener Urlaubstag</span><span><i style="background:var(--card);box-shadow:inset 0 0 0 2px var(--ink)"></i>weiterer Fenster-/Brückentag</span></div></div>
  <ol class="bridges" data-plan-list></ol>
</div>"""
    body = URLAUBSPLANER
    crumbs = [("/", "Start"), ("/urlaubsplaner.html", "Urlaubsplaner")]
    write("urlaubsplaner.html", "tool.html", title=f"Urlaubsplaner {CUR}: aus wenig Urlaub viele freie Tage machen | Kalenderkompass 24",
          description=f"Urlaubsplaner {CUR} für Österreich und Deutschland: Gib deine Urlaubstage ein und finde die Termine mit den meisten freien Tagen in deinem Bundesland.",
          h1="Urlaubsplaner", lead="Gib ein, wie viele Urlaubstage du einsetzen willst. Der Planer legt sie dorthin, wo sie mit Feiertagen und Wochenenden die meisten freien Tage ergeben.",
          tool=tool, body=body, crumbs=crumbs, show_picker=True, show_year=True, year_attr=CUR,
          related=[a for a in ARTICLES if a["slug"] in ("ferien-planen", "urlaubsanspruch-oesterreich-deutschland", "persoenlicher-feiertag-oesterreich")],
          jsonld=[crumbs_ld(crumbs), {"@context": "https://schema.org", "@type": "WebApplication", "name": "Urlaubsplaner", "applicationCategory": "UtilitiesApplication", "operatingSystem": "Web", "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR"}, "url": SITE + "/urlaubsplaner.html"}],
          active="/urlaubsplaner.html", priority=0.9,
          skip_ads=("half", "sky"))   # Seitenleisten-Anzeigen lägen direkt neben Planer und Ergebnisliste


def build_mein_kalender():
    tool = '<div class="mk" data-mk></div>'
    body = f"""<h2>So funktioniert Mein Kalender</h2>
<p>Tipp auf einen Tag, wähle eine Kategorie und schreib einen kurzen Text dazu – fertig. Für Urlaube oder Schulwochen gibst du zusätzlich ein Enddatum an. Die gesetzlichen Feiertage deines Bundeslandes stehen schon drin und bleiben immer <strong>rot</strong>; Fenstertage (in Deutschland: Brückentage) sind schwarz umrandet. Deine eigenen Einträge erscheinen in den Farben deiner Kategorien – auch im Jahresband auf der Startseite.</p>
<h2>Deine Farben – passend zu deinem bisherigen Kalender</h2>
<p>Wenn du schon einen Kalender am Handy oder am Computer verwendest, musst du dich nicht umgewöhnen. Unter „Farben und Kategorien“ benennst du die Kategorien so wie dort und übernimmst die Farben: aus den Paletten von Google Kalender und Apple Kalender oder mit dem Farbwähler als beliebige eigene Farbe. Bis zu acht Kategorien sind möglich.</p>
<h2>Aufs Handy, als PDF oder auf Papier</h2>
<ul>
<li><strong>Aufs Handy:</strong> „Als Kalenderdatei (.ics)“ lädt alle Einträge – auf Wunsch mit den Feiertagen – als Datei herunter. Auf dem iPhone öffnest du sie und tippst auf „Alle hinzufügen“; bei Google Kalender importierst du sie am Computer unter Einstellungen → Importieren. Die Kategorie wird als Kategorie mitgegeben, die Farbe legt die Kalender-App selbst fest.</li>
<li><strong>Als PDF oder auf Papier:</strong> „Monat drucken“ öffnet den Druckdialog deines Browsers; dort wählst du einen Drucker oder „Als PDF sichern“. Die Farben werden mitgedruckt.</li>
<li><strong>Sicherung:</strong> „Sicherung speichern“ legt eine kleine Datei mit allen Einträgen und Farben ab. Mit „Sicherung laden“ holst du sie auf einem anderen Gerät oder nach dem Löschen der Browserdaten zurück.</li>
</ul>
<h2>Datenschutz: Deine Einträge bleiben bei dir</h2>
<p>Mein Kalender braucht kein Konto. Alle Einträge werden nur im Speicher deines Browsers auf diesem Gerät abgelegt (localStorage) und nie an unseren oder einen anderen Server übertragen. Löschst du die Browserdaten, sind auch die Einträge weg – deshalb gibt es die Sicherung. Ein anderes Gerät sieht deine Einträge erst, wenn du dort die Sicherung lädst.</p>"""
    crumbs = [("/", "Start"), ("/mein-kalender.html", "Mein Kalender")]
    write("mein-kalender.html", "tool.html", title=f"Mein Kalender {CUR}: eigene Termine in deinen Farben | Kalenderkompass 24",
          description="Eigener Kalender mit Feiertagen deines Bundeslandes: Termine, Urlaub und Schule in selbst gewählten Farben eintragen, als .ics aufs Handy, drucken oder als PDF – ohne Anmeldung.",
          h1="Mein Kalender", lead="Feiertage deines Bundeslandes plus deine eigenen Termine – in deinen Farben, ohne Anmeldung. Die Einträge bleiben in deinem Browser.",
          tool=tool, body=body, crumbs=crumbs, show_picker=True, show_year=False, mk=True,
          jsonld=[crumbs_ld(crumbs), {"@context": "https://schema.org", "@type": "WebApplication", "name": "Mein Kalender", "applicationCategory": "UtilitiesApplication", "operatingSystem": "Web", "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR"}, "url": SITE + "/mein-kalender.html"}],
          active="/mein-kalender.html", priority=0.9, checked=CHECKED_0511,
          skip_ads=("half", "sky"))   # Seitenleisten-Anzeigen lägen direkt neben dem Kalender


def build_shop():
    cards = []
    for pr in PRODUCTS:
        buy = (f'<a class="btn" href="{pr["checkout"]}" rel="noopener" data-shop-buy="{pr["slug"]}">Kaufen · {pr["price"]}</a>' if pr["checkout"] and pr["price"]
               else '<span class="small muted">In Vorbereitung</span>')
        cards.append(f'<li class="shop-item"><h3>{pr["title"]}</h3><p>{pr["text"]}</p><p class="small muted">{pr["format"]}</p>{buy}</li>')
    tool = '<ul class="shop">' + "".join(cards) + "</ul>"
    body = """<h2>Kostenlos oder gekauft?</h2>
<p>Alle Werkzeuge auf Kalenderkompass 24 bleiben kostenlos: Feiertage, Fenstertage, Urlaubsplaner und <a href="/mein-kalender.html">Mein Kalender</a> mit Druck, PDF und Kalenderdatei. Die Druckvorlagen im Shop sind zusätzlich gestaltete Wandkalender und Planer in Druckqualität für alle, die etwas Fertiges an die Wand hängen wollen.</p>
<h2>Bezahlung und Rechnung</h2>
<p>Die Bezahlung läuft über die gesicherte Bezahlseite unseres Zahlungsanbieters. Er stellt die Rechnung mit Umsatzsteuer aus und liefert den Download-Link per E-Mail. Auf dieser Website selbst werden keine Zahlungsdaten eingegeben oder gespeichert.</p>"""
    crumbs = [("/", "Start"), ("/shop.html", "Shop")]
    write("shop.html", "tool.html", title="Shop: Wandkalender und Planer zum Ausdrucken | Kalenderkompass 24",
          description="Druckvorlagen von Kalenderkompass 24: Wandkalender, Familienplaner und Urlaubsplan fürs Team als PDF.",
          h1="Shop", lead="Wandkalender und Planer im Kalenderblatt-Stil als druckfertige PDF-Vorlagen.",
          tool=tool, body=body, crumbs=crumbs, show_picker=False, active="/shop.html",
          robots=None if SHOP_LIVE else "noindex,nofollow", ads=SHOP_LIVE)


def build_familie():
    tool = """<div class="familie" data-familie>
<form class="fform" data-fform onsubmit="return false">
  <div class="fgrid">
    <label>Bundesland<select name="region"><option>wird geladen …</option></select></label>
    <label>Jahr<select name="year"><option value="2026">2026</option><option value="2027">2027</option><option value="2028">2028</option></select></label>
    <label>Monate<select name="month"><option value="all">alle 12 Monate</option>""" + "".join(f'<option value="{i}">{n}</option>' for i, n in enumerate(M_AT)) + """</select></label>
    <label>Überschrift<input type="text" name="title" maxlength="30" placeholder="z. B. Familie Huber"></label>
  </div>
  <fieldset class="flay"><legend>Darstellung</legend>
    <label><input type="radio" name="layout" value="spalten"> Spalte pro Person (A4 hoch)</label>
    <label><input type="radio" name="layout" value="raster"> Monatsraster (A4 quer)</label>
    <label><input type="checkbox" name="ferien"> Schulferien einzeichnen</label>
  </fieldset>
  <h3>Familie &amp; Geburtstage</h3>
  <p class="small muted">Bis zu sechs Personen bekommen eine eigene Spalte. Weitere Personen – etwa Großeltern – erscheinen mit ihrem Geburtstag bei den Terminen. Fotos bleiben auf deinem Gerät.</p>
  <ul class="people" data-people></ul>
  <p><button type="button" class="btn ghost" data-add>+ Person hinzufügen</button></p>
</form>
<div class="fpreview"><div data-fstage class="fstage"></div><p class="small muted" data-finfo></p>
  <p class="factions"><button type="button" class="btn" data-fpdf>PDF herunterladen</button> <button type="button" class="linkbtn" data-freset>Alles zurücksetzen</button></p>
  <p class="small muted" data-fnote></p><p class="small" data-fmsg role="status"></p></div>
</div>
<script src="/assets/familie.js?v=""" + V + """" defer></script>"""
    import ferien as F
    body = """<h2>So entsteht dein Familienplaner</h2>
<ol><li><strong>Bundesland wählen:</strong> Die gesetzlichen Feiertage und die amtlichen Schulferien deines Bundeslandes werden automatisch eingetragen.</li>
<li><strong>Familie eintragen:</strong> Name, Geburtstag und – wenn du willst – ein Foto. Jede Person bekommt eine eigene Spalte mit Foto im Kopf.</li>
<li><strong>Prüfen und drucken:</strong> Die Vorschau zeigt jede Seite genau so, wie sie gedruckt wird. Ein Klick erzeugt ein PDF mit allen zwölf Monaten.</li></ol>
<h2>Warum ein Familienplaner auf Papier?</h2>
<p>Ein gedruckter Planer an der Kühlschranktür ist für alle sichtbar – auch für Kinder ohne Handy und für Großeltern, die zu Besuch sind. Wer wann Training hat, wer abgeholt werden muss und wann der nächste Geburtstag ansteht, sieht man auf einen Blick. Die Spalte pro Person verhindert, dass Termine untergehen.</p>
<h2>Geburtstage mit Foto</h2>
<p>Am Geburtstag erscheint das Foto der Person direkt im Kalender – bei eigener Spalte in dieser Spalte, sonst bei den Terminen. Gibst du das Geburtsjahr ein, steht bei Personen ohne eigene Spalte auch das Alter dabei („Oma Geburtstag (75)“). Ideal für Großeltern, Paten und Freunde der Kinder.</p>
<h2>Deine Fotos bleiben bei dir</h2>
<p>Fotos werden direkt in deinem Browser quadratisch zugeschnitten und verkleinert. Sie werden nicht hochgeladen und nicht an uns übertragen; gespeichert werden sie nur im lokalen Speicher deines Browsers, damit du später weitermachen kannst. „Alles zurücksetzen“ löscht sie wieder.</p>
<h2>Tipps zum Drucken</h2>
<p>Drucke im Format A4 mit 100 % Skalierung („Tatsächliche Größe“). Auf etwas stärkerem Papier (100–120 g/m²) halten Kugelschreiber und Fineliner gut und nichts schlägt durch. Gelocht passt der Planer in jeden Ordner; mit einer Klemmleiste wird er zum Wandkalender.</p>
<h2>Was im Planer steht – und woher es kommt</h2>
<ul>
<li><strong>Gesetzliche Feiertage</strong> deines Bundeslandes, rot markiert. Sie kommen aus derselben Datenquelle wie unsere Feiertagstabellen und werden aus den Feiertagsgesetzen berechnet; bewegliche Feiertage leiten sich vom Osterdatum ab.</li>
<li><strong>Landespatrone und schulfreie Tage</strong> erscheinen als Hinweis; das Datum selbst wird aber nicht wie bei gesetzlichen Feiertagen rot hervorgehoben – in Österreich etwa der Leopolditag in Wien und Niederösterreich, in Bayern der Buß- und Bettag. Für Beschäftigte sind das Arbeitstage, für Schulkinder in der Regel nicht.</li>
<li><strong>Schulferien</strong> werden auf Wunsch farbig hinterlegt. Wir verwenden nur amtlich veröffentlichte Termine: für Österreich den Ferienkalender auf oesterreich.gv.at, für Deutschland den Ferienkalender der Kultusministerkonferenz. Enthalten ist derzeit das Schuljahr {F_SY}, also bis zum Ende der Sommerferien {CUR}. Spätere Ferien ergänzen wir, sobald sie veröffentlicht sind; geschätzte Termine gibt es bei uns nicht.</li>
<li><strong>Geburtstage</strong> aus deinen Eingaben, mit Foto oder mit den Initialen in einem farbigen Kreis.</li>
</ul>
<p>Schulautonome Tage legt jede Schule selbst fest. Sie stehen in keinem amtlichen Kalender und fehlen deshalb auch im Planer – am besten gleich nach Schulbeginn in die Notizspalte eintragen.</p>
<h2>Zwei Darstellungen</h2>
<p><strong>Spalte pro Person (A4 hoch):</strong> Jeder Monat bekommt eine Seite mit einer Zeile pro Tag. Bis zu sechs Personen haben eine eigene Spalte mit Foto und Namen im Kopf, rechts bleibt Platz für Termine und Notizen. Diese Ansicht eignet sich für Familien mit Kindern, die eigene Termine haben – Training, Musikschule, Elternabend.</p>
<p><strong>Monatsraster (A4 quer):</strong> Klassisches Kalenderblatt mit sieben Spalten von Montag bis Sonntag. Feiertage, Ferienbeginn und Geburtstage stehen direkt im Tagesfeld. Das Raster ist übersichtlicher, wenn vor allem die ganze Familie gemeinsame Termine einträgt.</p>
<h2>Beispiel: eine Familie in Wien</h2>
<p>Zwei Erwachsene, zwei Schulkinder, dazu die Großeltern mit Geburtstag. Die vier Familienmitglieder bekommen je eine Spalte, die Großeltern erscheinen nur an ihrem Geburtstag bei den Terminen – mit Alter, wenn das Geburtsjahr eingetragen ist. Mit eingeschalteten Schulferien sieht man im Februar sofort die Semesterferien, im November den Leopolditag als schulfreien Tag, an dem die Eltern arbeiten. Wer in einem anderen Bundesland arbeitet als die Kinder zur Schule gehen, wählt das Bundesland der Schule: Die Ferien sind für die Planung meist wichtiger als die wenigen Feiertage, die sich unterscheiden.</p>
<h2>Häufige Fragen</h2>
<p><strong>Kann ich später weitermachen?</strong> Ja. Deine Eingaben bleiben im lokalen Speicher dieses Browsers, bis du „Alles zurücksetzen“ wählst oder die Browserdaten löschst. Auf einem anderen Gerät beginnst du neu.</p>
<p><strong>Muss ich immer das ganze Jahr drucken?</strong> Nein. Unter „Monate“ wählst du einen einzelnen Monat, etwa wenn du den Planer monatlich neu ausdrucken willst. Zur Auswahl stehen die Jahre 2026 bis 2028.</p>
<p><strong>Kann ich Personen ohne eigene Spalte anlegen?</strong> Ja. Ab der siebten Person – oder wenn du die Spalte abwählst – erscheint die Person nur mit ihrem Geburtstag bei den Terminen.</p>
<h2>Grenzen</h2>
<ul>
<li>Pro Planer gibt es ein Bundesland. Für Familien mit Schulkindern in zwei Ländern lässt sich ein zweiter Planer erstellen.</li>
<li>Namen werden im Druck gekürzt, wenn sie sehr lang sind; die Überschrift hat höchstens 30 Zeichen.</li>
<li>Feiertage einzelner Gemeinden, betriebliche Schließtage und Regelungen aus Kollektiv- oder Tarifverträgen sind nicht enthalten.</li>
<li>Das PDF entsteht in deinem Browser. Auf älteren Geräten kann das bei zwölf Monaten mit vielen Fotos etwas dauern.</li>
</ul>
<p class="small muted">Feiertage nach den Feiertagsgesetzen, Schulferien nach oesterreich.gv.at und der Kultusministerkonferenz. Wie wir rechnen, steht unter <a href="/quellen-methodik.html">Quellen &amp; Methodik</a>. Alle Angaben ohne Gewähr.</p>""".replace("{F_SY}", F.SCHOOLYEAR).replace("{CUR}", str(CUR))
    crumbs = [("/", "Start"), ("/familienplaner.html", "Familienplaner")]
    write("familienplaner.html", "tool.html", title="Familienplaner 2027 zum Ausdrucken – mit Feiertagen, Schulferien & Geburtstagsfotos | Kalenderkompass 24",
          description="Familienplaner 2027 kostenlos gestalten: Spalte pro Person, Feiertage und Schulferien deines Bundeslandes, Geburtstage mit Foto – als PDF zum Ausdrucken.",
          h1="Familienplaner 2027", lead="Gestalte euren Familienkalender mit Feiertagen und Schulferien deines Bundeslandes – und den Geburtstagen der Familie, auf Wunsch mit Foto.",
          tool=tool, body=body, crumbs=crumbs, show_picker=False, related=[a for a in ARTICLES if a["slug"] in ("ferien-planen",)],
          jsonld=[crumbs_ld(crumbs), {"@context": "https://schema.org", "@type": "WebApplication", "name": "Familienplaner", "applicationCategory": "UtilitiesApplication", "operatingSystem": "Web", "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR"}, "url": SITE + "/familienplaner.html"}],
          active="/familienplaner.html", priority=0.9,
          skip_ads=("half", "sky"))   # Seitenleisten-Anzeigen lägen direkt neben dem Formular


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
    def wd_range(country, region, a0, b0):
        off = H.off_days(country, region, a0.year) | H.off_days(country, region, b0.year)
        return sum(H.is_workday(a0 + timedelta(i), off) for i in range((b0 - a0).days + 1))
    ex_q1 = wd_range("at", "wien", date(CUR, 1, 1), date(CUR, 3, 31))
    ex_by, ex_be = wd_range("de", "bayern", date(CUR, 5, 1), date(CUR, 6, 30)), wd_range("de", "berlin", date(CUR, 5, 1), date(CUR, 6, 30))
    ex_mar_at, ex_mar_be = wd_month("at", "wien", CUR, 3), wd_month("de", "berlin", CUR, 3)
    ex_xmas = wd_range("at", "wien", date(CUR, 12, 20), date(CUR + 1, 1, 7))
    assert date(CUR, 12, 25).weekday() >= 5 and date(CUR, 12, 26).weekday() >= 5
    # Kernaussagen der Beispiele (Text ist für 2027 formuliert)
    assert H.easter(CUR) + timedelta(1) <= date(CUR, 3, 31) and ex_by == ex_be - 1 and ex_mar_at > ex_mar_be, (ex_by, ex_be, ex_mar_at, ex_mar_be)
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
<h2>So rechnet der Rechner</h2>
<p>Der Rechner geht jeden Tag zwischen Anfangs- und Enddatum einzeln durch – beide Tage eingeschlossen. Ein Tag zählt als Arbeitstag, wenn er ein Montag bis Freitag ist und kein gesetzlicher Feiertag des gewählten Bundeslandes. Die Feiertage stammen aus derselben Datei wie unsere Feiertagstabellen: feste Termine aus den Feiertagsgesetzen, bewegliche aus dem Osterdatum. Landespatrone in Österreich und schulfreie Tage wie der Buß- und Bettag in Bayern sind keine gesetzlichen Feiertage und zählen deshalb als Arbeitstage. Fällt ein Feiertag auf ein Wochenende, ändert er nichts, weil Samstag und Sonntag ohnehin nicht gezählt werden.</p>
<p>Gerechnet wird vollständig in deinem Browser; das gewählte Bundesland merkt sich die Seite lokal, sonst wird nichts gespeichert oder übertragen.</p>
<h2>Drei Beispiele für {CUR}</h2>
<p><strong>Ein Quartal in Wien:</strong> Vom 1. Jänner bis 31. März {CUR} zählt der Rechner {ex_q1} Arbeitstage. Abgezogen sind Neujahr ({WDL[date(CUR, 1, 1).weekday()]}) und Heilige Drei Könige ({WDL[date(CUR, 1, 6).weekday()]}); der Ostermontag fällt mit dem {fmt(H.easter(CUR) + timedelta(1), 'at', wd=False, year=False)} gerade noch ins erste Quartal.</p>
<p><strong>Gleicher Zeitraum, anderes Land:</strong> Vom 1. Mai bis 30. Juni {CUR} hat Bayern {ex_by} Arbeitstage, Berlin {ex_be}. Der Unterschied ist Fronleichnam am {fmt(H.easter(CUR) + timedelta(60), 'de', year=False)}, der in Bayern gilt, in Berlin nicht. Wer Projekte über Landesgrenzen plant, sollte deshalb immer das Land des Arbeitsorts wählen.</p>
<p><strong>Tageswert berechnen:</strong> Teilt man ein Monatsentgelt durch die Arbeitstage des Monats, erhält man einen rechnerischen Wert pro Arbeitstag. Der März {CUR} hat in Wien {ex_mar_at}, in Berlin {ex_mar_be} Arbeitstage, weil in Berlin zusätzlich der Frauentag und der Karfreitag frei sind – bei gleichem Gehalt ergibt sich in Berlin also ein höherer rechnerischer Tageswert. Viele Verträge, Kollektiv- und Tarifverträge verwenden für Abzüge oder anteilige Zahlungen allerdings feste Teiler statt der tatsächlichen Arbeitstage; maßgeblich ist immer die Regel im eigenen Vertrag.</p>
<p><strong>Über den Jahreswechsel:</strong> Vom 20. Dezember {CUR} bis 7. Jänner {CUR + 1} hat Wien {ex_xmas} Arbeitstage. Der Rechner nimmt dafür die Feiertage beider Jahre: Mariä Empfängnis liegt davor, Christtag und Stefanitag {CUR} fallen aufs Wochenende, Neujahr {CUR + 1} ist ein {WDL[date(CUR + 1, 1, 1).weekday()]} und Heilige Drei Könige {CUR + 1} ein {WDL[date(CUR + 1, 1, 6).weekday()]}.</p>
<p><strong>Anfang und Ende zählen mit:</strong> Von Montag bis Freitag derselben Woche sind es fünf Arbeitstage, nicht vier. Wer „bis“ ausschließlich meint, etwa bei einer Abgabe am Morgen des Enddatums, wählt den Vortag als Ende.</p>
<h2>Grenzen des Rechners</h2>
<ul>
<li><strong>Fünftagewoche:</strong> Gezählt wird Montag bis Freitag. Wer an Samstagen arbeitet, in Schichten oder in Teilzeit an bestimmten Tagen, muss das Ergebnis anpassen – bei Teilzeit etwa nur die eigenen Arbeitstage zählen.</li>
<li><strong>Keine Halbtage:</strong> Der 24. und der 31. Dezember sind keine gesetzlichen Feiertage und zählen voll, auch wenn viele Betriebe dort früher schließen.</li>
<li><strong>Keine Gemeindefeiertage:</strong> Feiertage, die nur in einzelnen Orten gelten – das Augsburger Friedensfest oder Fronleichnam in Teilen Sachsens und Thüringens –, sind nicht enthalten. Mariä Himmelfahrt in Bayern ist enthalten, obwohl er nur in Gemeinden mit überwiegend katholischer Bevölkerung gilt.</li>
<li><strong>Keine persönlichen Abwesenheiten:</strong> Urlaub, Krankenstand, Zeitausgleich und betriebliche Schließtage kennt der Rechner nicht.</li>
<li><strong>Fristen:</strong> Gesetzliche Fristen laufen meist in Kalendertagen, Wochen oder Monaten und haben eigene Regeln für Wochenenden und Feiertage. Für eine Frist ist der Arbeitstage-Rechner deshalb nur ein Hilfsmittel, keine verbindliche Berechnung.</li>
</ul>
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


# ---------------------------------------------------------------- Fenstertage Österreich (Ratgeber, Hauptjahr)
def leave_block(a, b, country="at", region=""):
    """Freier Block von a bis b: benötigte Urlaubstage = Arbeitstage (Mo–Fr ohne gesetzliche Feiertage) darin."""
    off = set()
    for y in range(a.year - 1, b.year + 2):
        off |= H.off_days(country, region, y)
    days = [a + timedelta(i) for i in range((b - a).days + 1)]
    take = [d for d in days if H.is_workday(d, off)]
    # Block muss an beiden Enden an freie Tage stoßen, sonst wäre er nicht maximal gewählt
    assert not H.is_workday(a, off) and not H.is_workday(b, off), (a, b)
    return {"from": a, "to": b, "free": len(days), "take": take, "vacation": len(take)}


def fenstertage_body(year=CUR):
    import ferien as F
    c = "at"
    f = lambda d, wd=True, y=False: fmt(d, c, wd=wd, year=y)
    hol = H.region_holidays(c, "", year)
    wk = [h for h in hol if h["date"].weekday() < 5]
    we = [h for h in hol if h["date"].weekday() >= 5]
    br = H.bridge_days(c, "", year)
    singles = [b for b in br if b["vacation"] == 1]
    e = H.easter(year)
    assert e == date(2027, 3, 28) and year == 2027, "Texte unten sind für 2027 geschrieben"
    # Kernaussagen, auf die sich der Text stützt
    assert [b["days"][0] for b in singles] == [date(2027, 5, 7), date(2027, 5, 28), date(2027, 10, 25)], singles
    assert date(2027, 8, 15).weekday() == 6 and date(2027, 11, 1).weekday() == 0 and date(2027, 12, 8).weekday() == 2

    rows = "".join(f"<tr class='{'we' if h['date'].weekday() >= 5 else ''}'><td class='date'>{f(h['date'], wd=False)}</td><td>{WDL[h['date'].weekday()]}</td><td>{h['name']}</td>"
                   f"<td>{'Wochenende – kein Ersatztag' if h['date'].weekday() >= 5 else ('langes Wochenende' if h['date'].weekday() in (0, 4) else 'Fenstertag möglich')}</td></tr>" for h in hol)
    brows = "".join(f"<tr><td class='date'>{' + '.join(f(d) for d in b['days'])}</td><td>{b['holiday']}</td><td>{b['vacation']}</td>"
                    f"<td>{b['free']} ({f(b['start'], wd=False)} – {f(b['end'], wd=False)})</td></tr>" for b in br)
    plans = [
        ("Jahresstart", date(2027, 1, 1), date(2027, 1, 10), "Neujahr (Freitag) und Heilige Drei Könige (Mittwoch) rahmen die erste Woche ein."),
        ("Karwoche", date(2027, 3, 20), date(2027, 3, 29), "Die ganze Karwoche frei bis Ostermontag; der Karfreitag ist ein Arbeitstag."),
        ("Osterwoche", date(2027, 3, 27), date(2027, 4, 4), "Variante nach Ostern: Dienstag bis Freitag nach Ostermontag."),
        ("Christi Himmelfahrt", date(2027, 5, 1), date(2027, 5, 9), "Staatsfeiertag fällt auf Samstag, der Donnerstag ist frei."),
        ("Pfingsten + Fronleichnam", date(2027, 5, 15), date(2027, 5, 30), "Zwei Feiertage in zwei Wochen: Pfingstmontag und Fronleichnam."),
        ("Nationalfeiertag + Allerheiligen", date(2027, 10, 23), date(2027, 11, 1), "Dienstag 26. Oktober und Montag 1. November."),
        ("Mariä Empfängnis", date(2027, 12, 4), date(2027, 12, 12), "Feiertag am Mittwoch, zwei Tage davor und danach."),
        ("Weihnachten bis Dreikönig", date(2027, 12, 25), date(2028, 1, 9), "Christtag und Stefanitag fallen aufs Wochenende; Neujahr 2028 ist ein Samstag, Heilige Drei Könige 2028 ein Donnerstag."),
    ]
    pl = [(n, leave_block(a, b), t) for n, a, b, t in plans]
    prow = "".join(f"<tr><td><strong>{n}</strong><div class='small muted'>{t}</div></td><td class='date'>{f(x['from'], wd=False)} – {fmt(x['to'], c, wd=False, year=x['to'].year != year)}</td>"
                   f"<td>{x['vacation']}</td><td>{x['free']}</td><td>{f"{x['free'] / x['vacation']:.1f}".replace('.', ',')}</td></tr>" for n, x, t in pl)
    by = {n: x for n, x, t in pl}
    combo = [by[k] for k in ("Jahresstart", "Karwoche", "Christi Himmelfahrt", "Pfingsten + Fronleichnam", "Nationalfeiertag + Allerheiligen")]
    cv, cf = sum(x["vacation"] for x in combo), sum(x["free"] for x in combo)

    # Bundesländer-Tabelle: Landespatron, Wochentag, Semester- und Sommerferien
    srows = []
    for slug, name in H.AT_REGIONS.items():
        pats = [h for h in H.region_holidays(c, slug, year) if h["kind"] == "patron"]
        pt = "<br>".join(f"{p['name'].split(' (')[0]}: {f(p['date'])}" for p in pats)
        sem = next(p for p in F.periods(c, slug) if p["name"] == "Semesterferien")
        su = F.summer(c, slug)
        srows.append(f"<tr><td><a href='/feiertage-{year}-{slug}.html'>{name}</a></td><td>{pt}</td>"
                     f"<td>{sem['start'].day}.–{f(sem['end'], wd=False)}</td><td>{'Ost' if su['start'] == date(2027, 7, 3) else 'West'} (ab {f(su['start'], wd=False)})</td></tr>")
    return f"""
<p>Ein <strong>Fenstertag</strong> ist ein Arbeitstag, der zwischen einem Feiertag und dem Wochenende liegt. Wer ihn freinimmt, verbindet beides zu einem langen Block. In Österreich gelten {year} bundesweit dieselben 13 gesetzlichen Feiertage; {len(wk)} davon fallen auf einen Werktag, {len(we)} aufs Wochenende. Daraus ergeben sich {len(singles)} klassische Fenstertage, an denen ein einziger Urlaubstag vier freie Tage bringt, und {len(br) - len(singles)} Zwickel aus je zwei Arbeitstagen. Alles auf dieser Seite ist aus denselben Daten berechnet wie unsere Feiertagstabellen – Ostersonntag {year} ist der {f(e, wd=False)}.</p>

<h2>Die Fenstertage {year} auf einen Blick</h2>
<div class="scroll"><table class="tbl"><thead><tr><th scope="col">Urlaub nehmen</th><th scope="col">rund um</th><th scope="col">Urlaubstage</th><th scope="col">freie Tage am Stück</th></tr></thead><tbody>{brows}</tbody></table></div>
<p>Die drei Einzel-Fenstertage sind <strong>Freitag, 7. Mai</strong> (nach Christi Himmelfahrt am 6. Mai), <strong>Freitag, 28. Mai</strong> (nach Fronleichnam am 27. Mai) und <strong>Montag, 25. Oktober</strong> (vor dem Nationalfeiertag am Dienstag, 26. Oktober). Heilige Drei Könige und Mariä Empfängnis fallen auf einen Mittwoch – da sind es jeweils zwei Tage davor oder danach.</p>

<h2>Fenstertag, Zwickeltag, Brückentag: drei Wörter, eine Sache</h2>
<p><strong>Fenstertag</strong> sagt man in Österreich: Der Tag ist wie ein Fenster zwischen zwei freien Blöcken. <strong>Zwickeltag</strong> ist vor allem in Ostösterreich und Bayern üblich – der Tag ist zwischen Feiertag und Wochenende „eingezwickt“. <strong>Brückentag</strong> ist der Begriff in Deutschland und in der Schweiz. Gemeint ist immer dasselbe.</p>

<h2>Alle Feiertage {year} und was sie bringen</h2>
<div class="scroll"><table class="tbl"><thead><tr><th scope="col">Datum</th><th scope="col">Wochentag</th><th scope="col">Feiertag</th><th scope="col">Wirkung</th></tr></thead><tbody>{rows}</tbody></table></div>
<p>{year} ist kein starkes Feiertagsjahr: Der Staatsfeiertag ({f(date(2027, 5, 1))}), Mariä Himmelfahrt ({f(date(2027, 8, 15))}) sowie Christtag und Stefanitag fallen aufs Wochenende. Einen Ersatztag gibt es in Österreich dafür nicht. Dafür liegen Ostermontag, Pfingstmontag und Allerheiligen auf einem Montag und bringen ohne Urlaub ein langes Wochenende.</p>

<h2>Urlaub effizient planen: freie Tage pro Urlaubstag</h2>
<p>Ein einzelner Urlaubstag am Montag bringt drei freie Tage – das ist der Normalfall. Gut ist alles, was deutlich darüber liegt. Die folgenden Blöcke sind die ergiebigsten des Jahres; gezählt sind Urlaubstage bei einer Fünftagewoche (Montag bis Freitag), der 24. und 31. Dezember als normale Arbeitstage.</p>
<div class="scroll"><table class="tbl"><thead><tr><th scope="col">Block</th><th scope="col">Zeitraum</th><th scope="col">Urlaubstage</th><th scope="col">frei</th><th scope="col">Tage je Urlaubstag</th></tr></thead><tbody>{prow}</tbody></table></div>
<p><strong>Beispielplan mit {cv} Urlaubstagen:</strong> Jahresstart, Karwoche, Christi Himmelfahrt, Pfingsten mit Fronleichnam und die Woche um den Nationalfeiertag ergeben zusammen {cf} freie Tage. Das ist der gesetzliche Mindesturlaub von fünf Wochen – in der Praxis wird man einen Teil davon für den Sommer behalten. Der <a href="/urlaubsplaner.html">Urlaubsplaner</a> rechnet das für jede andere Zahl von Urlaubstagen durch.</p>
<p><strong>Mit Schulkindern</strong> lohnen sich andere Blöcke: Die Osterferien dauern in ganz Österreich vom 20. bis 29. März 2027, die Pfingstferien vom 15. bis 17. Mai. Der Pfingstblock mit Fronleichnam überlappt also mit schulfreien Tagen – die Kinder sind in der Woche danach allerdings wieder in der Schule.</p>

<h2>Landespatrone und Ferien nach Bundesland</h2>
<p>Die gesetzlichen Feiertage sind in allen neun Bundesländern gleich. Unterschiede gibt es bei den Landespatronen: Ihre Festtage sind keine gesetzlichen Feiertage, an den Schulen ist aber in der Regel unterrichtsfrei. Für Eltern können sie deshalb wie ein zusätzlicher Fenstertag wirken – oder wie ein Betreuungsproblem.</p>
<div class="scroll"><table class="tbl"><thead><tr><th scope="col">Bundesland</th><th scope="col">Landespatron {year}</th><th scope="col">Semesterferien</th><th scope="col">Sommerferien</th></tr></thead><tbody>{''.join(srows)}</tbody></table></div>
<ul>
<li><strong>Josefitag, Freitag 19. März</strong> (Kärnten, Steiermark, Tirol, Vorarlberg): direkt vor den Osterferien. Schulkinder haben dort elf Tage am Stück frei.</li>
<li><strong>Florianitag, Dienstag 4. Mai</strong> (Oberösterreich): in der Woche von Christi Himmelfahrt.</li>
<li><strong>Rupertitag, Freitag 24. September</strong> (Salzburg): langes Schulwochenende kurz nach Schulbeginn.</li>
<li><strong>Martinitag, Donnerstag 11. November</strong> (Burgenland) und <strong>Leopolditag, Montag 15. November</strong> (Wien, Niederösterreich).</li>
<li><strong>Tag der Volksabstimmung</strong> in Kärnten (10. Oktober): {year} ein Sonntag, er entfällt also.</li>
</ul>
<p>Salzburg, Tirol und Vorarlberg haben ihre Semesterferien 2027 um eine Woche in die dritte Februarwoche verlegt. Quelle der Ferientermine: <a href="{F.SRC_AT[1]}" rel="noopener">{F.SRC_AT[0]}</a>.</p>

<h2>Der persönliche Feiertag als Fenstertag</h2>
<p>Seit 2019 darf jede Arbeitnehmerin und jeder Arbeitnehmer einmal pro Urlaubsjahr einen Urlaubstag einseitig festlegen (§ 7a Arbeitsruhegesetz) – mit mindestens drei Monaten Vorlauf, schriftlich. Für den begehrten 7. Mai heißt das: Meldung bis Anfang Februar. Für den 25. Oktober reicht Juli. Details im Beitrag <a href="/persoenlicher-feiertag-oesterreich.html">Persönlicher Feiertag in Österreich</a>.</p>

<h2>Muss der Arbeitgeber am Fenstertag freigeben?</h2>
<p>Nein. Ein Fenstertag ist ein ganz normaler Arbeitstag. Wer frei haben möchte, nimmt Urlaub oder baut Zeitguthaben ab.</p>
<ul>
<li><strong>Österreich:</strong> Der Zeitpunkt des Urlaubs wird zwischen Arbeitgeber und Arbeitnehmer vereinbart (§ 4 Urlaubsgesetz). Keine Seite kann ihn allein festlegen – mit Ausnahme des persönlichen Feiertags.</li>
<li><strong>Deutschland:</strong> Der Arbeitgeber legt den Urlaub fest, muss aber die Wünsche der Beschäftigten berücksichtigen, sofern keine dringenden betrieblichen Gründe entgegenstehen (§ 7 Abs. 1 Bundesurlaubsgesetz).</li>
</ul>
<p>Viele Betriebe schließen an beliebten Fenstertagen trotzdem. Dann wird der Tag meist als Betriebsurlaub verbucht, der in Österreich vereinbart werden muss. Manche Kollektivverträge regeln den 24. und 31. Dezember gesondert; das ist hier nicht eingerechnet.</p>
<div class="note">Tipp: Beliebte Fenstertage sind im Team schnell vergeben. Wer früh im Jahr plant, hat die besten Chancen. Die Brückentage aller deutschen Länder stehen bei den <a href="/brueckentage-{year}.html">Brückentagen {year}</a>, wie wir rechnen unter <a href="/quellen-methodik.html">Quellen &amp; Methodik</a>.</div>
"""


def ferien_planen_table(year=CUR):
    """Tabelle für den Ratgeber „Urlaub planen“: 1 und 4 Urlaubstage rund um die Frühjahrsfeiertage, AT und NRW."""
    e = H.easter(year)
    sets = [("Ostern", {"at": [e + timedelta(1)], "de": [e - timedelta(2), e + timedelta(1)]}),
            ("Christi Himmelfahrt", {"at": [e + timedelta(39)], "de": [e + timedelta(39)]}),
            ("Pfingstmontag", {"at": [e + timedelta(50)], "de": [e + timedelta(50)]}),
            ("Fronleichnam", {"at": [e + timedelta(60)], "de": [e + timedelta(60)]})]
    reg = {"at": "", "de": "nordrhein-westfalen"}
    def cell(c, around, k):
        b = best_block(c, reg[c], year, k, around)
        check_block(c, reg[c], b)
        return f"{b['free']} Tage ({fmt(b['from'], c, wd=False, year=False)} – {fmt(b['to'], c, wd=False, year=False)})"
    for c in ("at", "de"):   # alle Tage müssen dort gesetzliche Feiertage sein
        off = H.off_days(c, reg[c], year)
        assert all(d in off for _, a in sets for d in a[c]), c
    rows = "".join(f"<tr><td><strong>{n}</strong></td><td>{cell('at', a['at'], 1)}</td><td>{cell('at', a['at'], 4)}</td>"
                   f"<td>{cell('de', a['de'], 1)}</td><td>{cell('de', a['de'], 4)}</td></tr>" for n, a in sets)
    return (f"<div class='scroll'><table class='tbl'><thead><tr><th scope='col'>{year}</th><th scope='col'>Österreich: 1 Urlaubstag</th><th scope='col'>Österreich: 4 Urlaubstage</th>"
            f"<th scope='col'>NRW: 1 Urlaubstag</th><th scope='col'>NRW: 4 Urlaubstage</th></tr></thead><tbody>{rows}</tbody></table></div>")


def build_methodik():
    import ferien as F
    body = f"""
<p>Kalenderkompass 24 schreibt Feiertage nicht von anderen Seiten ab. Wir berechnen sie aus den Rechtsgrundlagen, übernehmen Schulferien nur aus amtlichen Veröffentlichungen und prüfen das Ergebnis bei jedem Build automatisch. Hier steht, welche Quellen wir verwenden, wie die Berechnung funktioniert und wo die Grenzen liegen.</p>

<h2>Rechtsgrundlagen Österreich</h2>
<ul>
<li><strong>Arbeitsruhegesetz (ARG), § 7 Abs. 2:</strong> zählt die 13 Feiertage auf, an denen Arbeitnehmerinnen und Arbeitnehmer Anspruch auf Feiertagsruhe haben – Neujahr, Heilige Drei Könige, Ostermontag, Staatsfeiertag, Christi Himmelfahrt, Pfingstmontag, Fronleichnam, Mariä Himmelfahrt, Nationalfeiertag, Allerheiligen, Mariä Empfängnis, Christtag und Stefanitag. Sie gelten in allen Bundesländern gleich.</li>
<li><strong>Feiertagsruhegesetz 1957:</strong> legt dieselben Tage als Feiertage im Sinn des öffentlichen Rechts fest.</li>
<li><strong>§ 7a ARG – persönlicher Feiertag:</strong> seit 2019 an Stelle des früheren Karfreitags-Feiertags für Angehörige bestimmter Kirchen. Er ist ein Urlaubstag, kein zusätzlicher Feiertag.</li>
<li><strong>Schulzeitgesetz 1985:</strong> regelt Unterrichtsjahr, Ferien und schulfreie Tage an Bundesschulen; für Pflichtschulen gelten die Schulzeit-Ausführungsgesetze der Länder. Danach ist unter anderem der Festtag des Landespatrons schulfrei. Wir schreiben deshalb „an Schulen in der Regel unterrichtsfrei“ – einen Feiertag für Beschäftigte begründet er nicht.</li>
</ul>
<p>Alle Bundesgesetze sind im Rechtsinformationssystem des Bundes kostenlos abrufbar: <a href="{RIS}" rel="noopener">RIS – ris.bka.gv.at</a>.</p>

<h2>Rechtsgrundlagen Deutschland</h2>
<p>In Deutschland sind Feiertage Ländersache. Jedes der 16 Länder hat ein eigenes Sonn- und Feiertagsgesetz; nur der Tag der Deutschen Einheit am 3. Oktober ist bundesrechtlich festgelegt (Einigungsvertrag). Neun Feiertage gelten in allen Ländern, dazu kommen je nach Land Heilige Drei Könige, Frauentag, Fronleichnam, Mariä Himmelfahrt, Weltkindertag, Reformationstag, Allerheiligen oder Buß- und Bettag. Auf den Seiten der Länder mit eigenem Länderteil verlinken wir das jeweilige Landesgesetz direkt. Feiertage, die nur in einzelnen Gemeinden gelten – etwa Fronleichnam in Teilen Sachsens und Thüringens oder das Hohe Friedensfest in Augsburg –, nennen wir als Hinweis, rechnen sie aber nicht mit.</p>

<h2>Schulferien</h2>
<ul>
<li><strong>Österreich:</strong> Ferienkalender auf oesterreich.gv.at, der die Termine des Bildungsministeriums und die Verordnungen der Länder zusammenfasst (<a href="{F.SRC_AT[1]}" rel="noopener">{F.SRC_AT[0]}</a>).</li>
<li><strong>Deutschland:</strong> Ferienkalender der Kultusministerkonferenz (KMK), eingelesen aus den dort veröffentlichten Kalenderdateien (<a href="{F.SRC_DE[1]}" rel="noopener">{F.SRC_DE[0]}</a>).</li>
</ul>
<p>Wir zeigen nur Schuljahre, die amtlich veröffentlicht sind – derzeit {F.SCHOOLYEAR}. Schätzungen für spätere Jahre gibt es bei uns nicht. Schulautonome Tage legt jede Schule selbst fest; sie stehen in keinem amtlichen Kalender und sind nicht enthalten.</p>

<h2>Wie wir die Termine berechnen</h2>
<p>Feste Feiertage wie der 26. Oktober stehen direkt im Gesetz. Die beweglichen Feiertage hängen am Ostersonntag. Diesen berechnen wir mit der Gaußschen Osterformel in der heute üblichen Fassung für den gregorianischen Kalender (dem sogenannten anonymen Algorithmus, wie ihn etwa Jean Meeus beschreibt). Für {CUR} ergibt sie Sonntag, {fmt(H.easter(CUR), 'at', wd=False)}. Davon abgeleitet:</p>
<ul>
<li>Karfreitag: 2 Tage vor Ostern (in Deutschland Feiertag, in Österreich nicht)</li>
<li>Ostermontag: 1 Tag nach Ostern</li>
<li>Christi Himmelfahrt: 39 Tage nach Ostern, immer ein Donnerstag</li>
<li>Pfingstmontag: 50 Tage nach Ostern</li>
<li>Fronleichnam: 60 Tage nach Ostern, immer ein Donnerstag</li>
<li>Buß- und Bettag (Sachsen): der Mittwoch vor dem 23. November</li>
</ul>
<p><strong>Fenster- und Brückentage</strong> sind bei uns Folgen von einem oder zwei Arbeitstagen (Montag bis Freitag, kein gesetzlicher Feiertag), die zwischen einem gesetzlichen Feiertag und einem Wochenende oder einem weiteren Feiertag liegen. Landespatrone und andere schulfreie Tage zählen dabei nicht als frei, weil sie für Beschäftigte normale Arbeitstage sind. „Freie Tage je Urlaubstag“ ist die Länge des freien Blocks geteilt durch die dafür nötigen Urlaubstage bei einer Fünftagewoche.</p>

<h2>So prüfen wir</h2>
<p>Bei jedem Build laufen Selbsttests: Ostertermine von 2000 bis 2038 gegen bekannte Daten, der Buß- und Bettag gegen eine zweite, unabhängige Rechnung, die Zahl der bundesweiten Feiertage, die Fenstertage {CUR} in Österreich und alle Datumsangaben in den Bundesländer-Texten gegen die Datentabellen. Schlägt ein Test fehl, wird die Seite nicht erzeugt. Zusätzlich gleichen wir die Ergebnisse stichprobenartig mit amtlichen Veröffentlichungen ab.</p>

<h2>Stand und Grenzen</h2>
<p>Letzte inhaltliche Prüfung: {CHECKED_NEW}. Nicht enthalten sind Regelungen aus Kollektiv- und Tarifverträgen (etwa zum 24. und 31. Dezember), betriebliche Schließtage und Feiertage einzelner Gemeinden. Alle Angaben erfolgen ohne Gewähr und ersetzen keine Rechtsberatung. Einen Fehler gefunden? Schreib an <a href="mailto:office@adstern.com">office@adstern.com</a> – wir prüfen jeden Hinweis.</p>
"""
    crumbs = [("/", "Start"), (METHODIK, "Quellen & Methodik")]
    write("quellen-methodik.html", "page.html", title="Quellen & Methodik: so berechnen wir Feiertage und Ferien | Kalenderkompass 24",
          description="Rechtsgrundlagen, amtliche Ferienquellen und Rechenweg von Kalenderkompass 24: Arbeitsruhegesetz, Schulzeitgesetz, Feiertagsgesetze der Länder, KMK und Osterformel.",
          h1="Quellen & Methodik", lead="Woher unsere Feiertags- und Feriendaten stammen, wie wir rechnen und wie wir prüfen.",
          body=body, related=[], crumbs=crumbs, jsonld=[crumbs_ld(crumbs)], active="", priority=0.5, checked=CHECKED_NEW)


def check_claims():
    """Selbsttest: Datumsangaben in den österreichischen Bundesländer-Texten stimmen mit holidays.py/ferien.py überein."""
    import ferien as F
    for slug, cl in CLAIMS_AT.items():
        text = LAND_AT[slug]
        m, d = cl["patron"]
        pats = [h for h in H.region_holidays("at", slug, CUR) if h["kind"] == "patron"]
        p = next(h for h in pats if (h["date"].month, h["date"].day) == (m, d))
        wd = WDL[p["date"].weekday()]
        assert wd in text and f"{d}. {M_AT[m-1]}" in text, (slug, wd)
        sem = next(x for x in F.periods("at", slug) if x["name"] == "Semesterferien")
        assert f"{sem['start'].day}." == cl["sem"][0] and f"{sem['end'].day}. Februar" == cl["sem"][1], slug
        assert f"{cl['sem'][0]} bis Samstag, {cl['sem'][1]} 2027" in text, slug
        su = F.summer("at", slug)
        assert f"{su['start'].day}. Juli" == cl["summer"] and cl["summer"] in text, slug
        assert f"{su['end'].day}. September" in text, slug
    print("Länder-Selbsttest AT: Landespatron, Semester- und Sommerferien stimmen mit den Daten überein")


WD_RE = "|".join(WDL)
MO_RE = "|".join(M_DE)


def check_weekdays(text, year, where):
    """Jede Angabe „Wochentag, Tag. Monat [Jahr]“ und „Tag. Monat … auf einen Wochentag“ muss zum Kalender passen."""
    plain = re.sub(r"<[^>]+>", " ", text)
    n = 0
    for wd, d, m, y in re.findall(rf"\b({WD_RE}),? (?:der |den |dem )?(\d{{1,2}})\. ({MO_RE})(?:,? (20\d\d))?", plain):
        real = WDL[date(int(y or year), M_DE.index(m) + 1, int(d)).weekday()]
        assert real == wd, f"{where}: {wd}, {d}. {m} {y or year} ist ein {real}"; n += 1
    for d, m, y, wd in re.findall(rf"\b(\d{{1,2}})\. ({MO_RE})(?: (20\d\d))?[^.<]{{0,60}}?auf (?:einen|ein) ({WD_RE})\b", plain):
        real = WDL[date(int(y or year), M_DE.index(m) + 1, int(d)).weekday()]
        assert real == wd, f"{where}: {d}. {m} {y or year} ist ein {real}, nicht {wd}"; n += 1
    return n


def check_claims_de():
    """Selbsttest: Datums- und Zahlangaben in den deutschen Länder-Texten stimmen mit holidays.py/ferien.py überein."""
    import ferien as F
    assert set(CLAIMS_DE) == set(LAND), "jeder deutsche Ländertext braucht Pflichtangaben in CLAIMS_DE"
    total = 0
    for slug, cl in CLAIMS_DE.items():
        text = LAND[slug]
        total += check_weekdays(text, CUR, slug)
        word, n = cl["count"]
        legal = [h for h in H.region_holidays("de", slug, CUR) if h["kind"] == "legal"]
        assert f"{word} gesetzliche Feiertage" in text or f"{word} Feiertage" in text, (slug, word)
        assert len(legal) == n, (slug, len(legal), n)
        ps = F.periods("de", slug)
        for name, a, b in cl["ferien"]:
            a, b = date.fromisoformat(a), date.fromisoformat(b)
            assert any(p["name"] == name and p["start"] == a and p["end"] == b for p in ps), (slug, name, a, b)
            assert f"{b.day}. {M_DE[b.month-1]}" in text, (slug, name, "Enddatum fehlt im Text")
            total += 1
        for d in cl["frei"]:
            d = date.fromisoformat(d)
            assert any(p["start"] <= d <= p["end"] for p in ps), (slug, d, "nicht schulfrei")
            total += 1
    print(f"Länder-Selbsttest DE: {total} Datums- und Ferienangaben stimmen mit den Daten überein")


def build_articles():
    for a in ARTICLES:
        crumbs = [("/", "Start"), ("/" + a["slug"] + ".html", a["title"])]
        related = [x for x in ARTICLES if x["slug"] != a["slug"]][:3]
        ld = [crumbs_ld(crumbs), {"@context": "https://schema.org", "@type": "Article", "headline": a["title"],
              "description": a["description"], "inLanguage": "de", "datePublished": "2026-10-29", "dateModified": CHECKED_ISO,
              "author": {"@type": "Organization", "name": "AdStern", "url": SITE + "/about.html"},
              "publisher": {"@type": "Organization", "name": "AdStern"}, "mainEntityOfPage": SITE + "/" + a["slug"] + ".html"}]
        fenster = a["slug"] == "fenstertag-zwickeltag-brueckentag"
        if fenster: ld[1]["dateModified"] = "2026-11-03"
        neu = a["slug"] in ("urlaubsanspruch-oesterreich-deutschland", "ferien-planen")   # am 4.11.2026 ausgebaut
        if neu: ld[1]["dateModified"] = LASTMOD
        write(a["slug"] + ".html", "page.html", title=f"{a['title']} | Kalenderkompass 24", description=a["description"],
              h1=a["title"], lead=a["teaser"], body=fenstertage_body() if fenster else a["body"].replace("<!--PLAN-->", ferien_planen_table()), related=related, crumbs=crumbs, jsonld=ld,
              active="", priority=0.8 if fenster else 0.7, checked=CHECKED_NEW if fenster else CHECKED_0411 if neu else CHECKED,
              sources=[("Arbeitsruhegesetz im RIS", RIS)] if fenster else None)


LEGAL_ADDR = "AdStern :: Agentur für digitales Marketing<br>Seilerstätte 8, 1010 Wien, Österreich<br>E-Mail: <a href='mailto:office@adstern.com'>office@adstern.com</a><br>Web: <a href='https://www.adstern.com'>www.adstern.com</a>"


def build_legal():
    write("imprint.html", "page.html", title="Impressum | Kalenderkompass 24", description="Impressum und Offenlegung von Kalenderkompass 24.",
          h1="Impressum", body=f"""<h2>Medieninhaber und Herausgeber</h2><p>{LEGAL_ADDR}</p>
<h2>Unternehmensangaben</h2><p>Unternehmensgegenstand: Werbeagentur<br>UID-Nummer: ATU54682507<br>Gewerbebehörde: Magistratisches Bezirksamt für den 1. und 8. Bezirk, Wien<br>Kammerzugehörigkeit: Wirtschaftskammer Wien, Fachgruppe Werbung und Marktkommunikation<br>Berufsbezeichnung: Werbeagentur (Gewerbe, verliehen in Österreich)<br>Anwendbare Rechtsvorschriften: Gewerbeordnung, abrufbar unter <a href="https://www.ris.bka.gv.at" rel="noopener">www.ris.bka.gv.at</a></p>
<p>Angaben nach § 5 E-Commerce-Gesetz und § 25 Mediengesetz.</p>
<h2>Grundlegende Richtung</h2><p>Kalenderkompass 24 ist eine unabhängige Informationsseite zu Feiertagen, Brückentagen, Kalenderwochen und Urlaubsplanung in Österreich und Deutschland. Die Seite finanziert sich über Werbung.</p>
<h2>Haftung</h2><p>Alle Angaben wurden sorgfältig nach den geltenden Feiertagsgesetzen berechnet und geprüft, erfolgen aber ohne Gewähr. Rechtliche Hinweise in den Ratgebern ersetzen keine Rechtsberatung.</p>""",
          ads=False, robots="noindex,follow", active="")
    write("about.html", "page.html", title="Über Kalenderkompass 24: Herausgeber, Methode und Datenquellen", description="Wer Kalenderkompass 24 herausgibt, woher die Feiertags- und Feriendaten stammen, wie sie berechnet und bei jedem Build automatisch geprüft werden.",
          h1="Über Kalenderkompass 24", lead="Feiertage, Brückentage und Urlaubsplanung – genau, schnell und ohne Anmeldung.", checked=CHECKED_0411,
          body=f"""<p>Kalenderkompass 24 beantwortet Fragen, die sich jedes Jahr wieder stellen: Wann ist der nächste Feiertag? Welche Brückentage gibt es? Wann sind Schulferien? Und wie hole ich aus meinem Urlaub die meisten freien Tage heraus? Die Seite deckt Österreich und Deutschland ab, jedes Bundesland einzeln, und funktioniert ohne Anmeldung.</p>
<h2>Herausgeber</h2>
<p>Kalenderkompass 24 ist ein Angebot von <strong>AdStern :: Agentur für digitales Marketing</strong>, Seilerstätte 8, 1010 Wien. AdStern ist Medieninhaber und Herausgeber und verantwortet alle Inhalte; die vollständigen Angaben stehen im <a href="/imprint.html">Impressum</a>. Die Seite ist unabhängig von Behörden, Kirchen und Interessenverbänden und finanziert sich über Werbung. Anzeigen sind als „Werbung“ gekennzeichnet und vom redaktionellen Inhalt getrennt.</p>
<h2>Was du hier findest</h2>
<ul><li>Gesetzliche Feiertage für alle 9 österreichischen Bundesländer und alle 16 deutschen Länder, mit Landespatronen und regionalen Besonderheiten</li>
<li>Brückentage und einen Urlaubsplaner, der Urlaubstage rund um Feiertage optimal verteilt</li>
<li>Amtliche Schulferien-Termine mit Zeitstrahl und Kalender-Export</li>
<li>Kalenderwochen, Arbeitstage-Rechner, Familienplaner und Kalender zum Ausdrucken</li>
<li>Ratgeber zu Urlaubsanspruch, Fristen und Feiertagsregeln</li></ul>
<h2>Woher die Daten kommen</h2>
<p><strong>Feiertage</strong> werden nicht abgeschrieben, sondern aus den Rechtsgrundlagen berechnet: für Österreich aus § 7 Abs. 2 Arbeitsruhegesetz, für Deutschland aus den Feiertagsgesetzen der 16 Länder und – für den 3. Oktober – aus dem Einigungsvertrag. Bewegliche Feiertage wie Ostermontag, Christi Himmelfahrt, Pfingstmontag oder Fronleichnam leiten wir vom Osterdatum ab, das mit der Gaußschen Osterformel für den gregorianischen Kalender berechnet wird. Der Buß- und Bettag in Sachsen ist der Mittwoch vor dem 23. November.</p>
<p><strong>Schulferien</strong> übernehmen wir ausschließlich aus amtlichen Quellen: für Österreich aus dem Ferienkalender auf oesterreich.gv.at, für Deutschland aus den Kalenderdateien der Kultusministerkonferenz. Wir zeigen nur Schuljahre, die dort bereits veröffentlicht sind – keine Schätzungen.</p>
<p><strong>Rechtliche Hinweise</strong> in den Ländertexten und Ratgebern stützen sich auf die Gesetzestexte selbst, wie sie im Rechtsinformationssystem des Bundes (RIS), auf gesetze-im-internet.de und in den Landesrechtsportalen veröffentlicht sind. Wo wir Gesetzblätter oder Landtagsdrucksachen zitieren, verlinken wir sie direkt. Einen Überblick über alle Quellen gibt die Seite <a href="/quellen-methodik.html">Quellen &amp; Methodik</a>.</p>
<h2>Wann wir aktualisieren</h2>
<p>Feiertage berechnen wir für die Jahre {YEARS[0]} bis {YEARS[-1]} im Voraus; Schulferien ergänzen wir, sobald ein neues Schuljahr amtlich veröffentlicht ist. Ändert ein Land sein Feiertagsgesetz – wie Berlin 2019 und Mecklenburg-Vorpommern 2023 mit dem Frauentag oder Thüringen 2019 mit dem Weltkindertag –, passen wir Daten und Texte an. Jede inhaltlich geprüfte Seite trägt ein sichtbares Prüfdatum.</p>
<h2>Wie wir rechnen</h2>
<p>Alle Tabellen, Kalender, Brückentage und Urlaubsvorschläge entstehen aus einer einzigen Datenquelle. Brückentage sind bei uns ein oder zwei Arbeitstage zwischen einem gesetzlichen Feiertag und einem Wochenende; Landespatrone und andere schulfreie Tage zählen dabei nicht als frei, weil sie für Beschäftigte Arbeitstage sind. Urlaubsblöcke rechnen wir mit einer Fünftagewoche, den 24. und 31. Dezember als normale Arbeitstage. Werkzeuge wie der Urlaubsplaner oder der Arbeitstage-Rechner verwenden im Browser dieselben Daten wie die gedruckten Tabellen.</p>
<h2>So prüfen wir: Selbsttests bei jedem Build</h2>
<p>Die Seite wird von einem Programm aus den Daten erzeugt. Bevor sie veröffentlicht wird, laufen automatische Selbsttests; schlägt einer fehl, entsteht keine neue Fassung der Seite. Geprüft werden unter anderem:</p>
<ul>
<li>die Osterformel gegen bekannte Ostertermine aus den Jahren 2000 bis 2038,</li>
<li>der Buß- und Bettag gegen eine zweite, unabhängige Rechnung über den ersten Advent,</li>
<li>die Zahl der Feiertage: 13 in Österreich, 9 bundesweit in Deutschland,</li>
<li>die Fenstertage {CUR} in Österreich, auf die sich unser Fenstertage-Ratgeber stützt,</li>
<li>jede Datumsangabe in den Bundesländer-Texten: Wochentage, Landespatrone, Ferienbeginn und -ende werden gegen die Datentabellen gerechnet,</li>
<li>jeder berechnete Urlaubsblock mit einer zweiten Zählung der Arbeitstage,</li>
<li>dass Jahresseiten in Titel und Überschriften nur ihr eigenes Jahr nennen.</li>
</ul>
<p>Zusätzlich gleichen wir die Ergebnisse stichprobenartig mit amtlichen Veröffentlichungen ab und prüfen die Seiten vor der Veröffentlichung in einem Browser auf Smartphone- und Desktop-Breite.</p>
<h2>Grenzen</h2>
<p>Nicht enthalten sind Feiertage einzelner Gemeinden (etwa das Hohe Friedensfest in Augsburg – wir weisen auf solche Fälle hin), schulautonome Tage, betriebliche Schließtage und Regelungen aus Kollektiv- oder Tarifverträgen. Landespatrone sind in Österreich keine gesetzlichen Feiertage; wir zeigen sie getrennt an. Unsere Ratgeber erklären die Rechtslage allgemein und ersetzen keine Rechtsberatung.</p>
<h2>KI-Werkzeuge und Prüfung</h2><p>Die Texte entstehen mit Unterstützung von KI-Werkzeugen; jede Berechnung ist durch die automatisierten Selbsttests abgesichert, und jeder Text wird vor der Veröffentlichung in einem eigenen Prüfdurchgang gegen die verlinkten Quellen geprüft. Ein Redaktionsteam gibt es nicht; verantwortlich ist AdStern.</p>
<h2>Deine Daten</h2><p>Alle Werkzeuge rechnen in deinem Browser. Was du eingibst, verlässt dein Gerät nicht. Werbung und Statistik laufen nur im Rahmen deiner Auswahl im Einwilligungsdialog, Details in der <a href="/privacy.html">Datenschutzerklärung</a>.</p>
<h2>Fehler gefunden?</h2><p>Schreib uns an <a href="mailto:office@adstern.com">office@adstern.com</a>. Wir prüfen jeden Hinweis und korrigieren Fehler so schnell wie möglich. Stand der Daten: {UPDATED}.</p>""",
          active="", priority=0.3)
    write("privacy.html", "page.html", title="Datenschutz | Kalenderkompass 24", description="Datenschutzerklärung von Kalenderkompass 24.",
          h1="Datenschutzerklärung", lead="Stand: 4. November 2026", ads=False, robots="noindex,follow", active="", body=f"""
<h2>Verantwortlicher</h2><p>{LEGAL_ADDR}</p>
<h2>Hosting</h2><p>Die Website wird über GitHub Pages (GitHub, Inc., 88 Colin P. Kelly Jr. Street, San Francisco, USA) ausgeliefert. Beim Aufruf verarbeitet GitHub technisch notwendige Verbindungsdaten wie IP-Adresse, aufgerufene Adresse, Browserinformationen und Zeitpunkt, um die Seite auszuliefern und vor Angriffen zu schützen. Rechtsgrundlage ist unser berechtigtes Interesse an einem sicheren Betrieb (Art. 6 Abs. 1 lit. f DSGVO). GitHub ist nach dem EU-US Data Privacy Framework zertifiziert. Die Schriften liegen auf unserem eigenen Server; es wird keine Verbindung zu Google Fonts aufgebaut.</p>
<h2>Werkzeuge</h2><p>Kalender, Planer und Rechner arbeiten ausschließlich in deinem Browser. Deine Eingaben werden nicht an uns übertragen. Damit die Seite sich dein Bundesland merkt, speichern wir es im lokalen Speicher deines Browsers (localStorage). Im Familienplaner gilt dasselbe für Namen, Geburtstage und Fotos: Fotos werden im Browser verkleinert, nicht hochgeladen und nur lokal gespeichert; das PDF entsteht auf deinem Gerät. Diese Speicherung ist für die von dir gewünschte Funktion erforderlich (§ 165 Abs. 3 TKG 2021). Du kannst sie jederzeit über die Browser-Einstellungen löschen.</p>
<h2>Einwilligungsverwaltung</h2><p>Für Werbung und Statistik nutzen wir die Einwilligungsverwaltung „Datenschutz &amp; Mitteilungen“ von Google (Google Ireland Limited, Gordon House, Barrow Street, Dublin 4, Irland), eine nach dem IAB Transparency &amp; Consent Framework zertifizierte Lösung. Beim ersten Besuch kannst du dort zustimmen, ablehnen oder einzelne Zwecke und Anbieter auswählen. Deine Auswahl kannst du jederzeit über „Datenschutz-Einstellungen“ im Seitenfuß ändern oder widerrufen.</p>
<h2>Google AdSense</h2><p>Wir finanzieren die Seite über Anzeigen von Google AdSense (Google Ireland Limited). Google und die im Einwilligungsdialog genannten Werbepartner können dabei IP-Adresse, Geräte- und Browserinformationen, besuchte Seiten sowie Interaktionen mit Anzeigen verarbeiten und Cookies oder ähnliche Technologien einsetzen, um Anzeigen auszuliefern, zu messen und Betrug zu verhindern. Personalisierte Anzeigen erscheinen nur mit deiner Einwilligung (Art. 6 Abs. 1 lit. a DSGVO, § 165 Abs. 3 TKG 2021). Wichtig: Auch nicht personalisierte Anzeigen, die nur zum Seiteninhalt passen, verwenden Cookies oder vergleichbare Kennungen (Häufigkeitsbegrenzung, Berichte, Betrugsabwehr) und erscheinen daher nur mit deiner Einwilligung zum Speichern und Abrufen von Informationen auf deinem Gerät. Ohne diese Einwilligung sind nur eingeschränkte Anzeigen möglich – ohne Werbe-Cookies, ohne lokale Speicherung zu Werbezwecken und ohne Personalisierung; technisch notwendige Daten wie die IP-Adresse verarbeitet Google dabei weiterhin für Auslieferung und Betrugsschutz. Der Werbe-Code von Google wird auf allen indexierten Inhaltsseiten geladen; dort kann Google neben unseren festen Werbeplätzen auch automatisch Anzeigen platzieren. Auf Impressum, Datenschutzerklärung, Fehlerseite und anderen nicht indexierten Seiten wird er nicht geladen. Ist in deinem Browser „Global Privacy Control“ aktiv, fordern wir keine Anzeigen an: Der Werbe-Code von Google wird auf unseren Inhaltsseiten zwar geladen, Anzeigenanfragen bleiben aber angehalten, und alle Google-Speicher- und Messfunktionen bleiben auf „abgelehnt“. Mehr dazu: <a href="https://policies.google.com/technologies/partner-sites?hl=de" rel="noopener">Datennutzung durch Google auf Partner-Websites</a>, <a href="https://policies.google.com/privacy?hl=de" rel="noopener">Datenschutzerklärung von Google</a>, <a href="https://adssettings.google.com" rel="noopener">Google-Anzeigeneinstellungen</a>.</p>
<p>Drittanbieter wie Google nutzen Werbe-Cookies, um dir Anzeigen auf Basis deiner bisherigen Besuche auf Kalenderkompass 24 und anderen Websites zu zeigen. Personalisierte Google-Werbung lässt sich in den <a href="https://adssettings.google.com" rel="noopener">Google-Anzeigeneinstellungen</a> abschalten; andere teilnehmende Anbieter kannst du über <a href="https://www.youronlinechoices.com/at/" rel="noopener">youronlinechoices.com</a> oder <a href="https://www.aboutads.info/choices/" rel="noopener">aboutads.info</a> ablehnen.</p>
<h2>Google Analytics</h2><p>Mit deiner Einwilligung im Google-Dialog (Zweck „Informationen auf einem Gerät speichern und/oder abrufen“ und Anbieter Google) verwenden wir Google Analytics 4 von Google Ireland Limited, um zu verstehen, welche Seiten genutzt werden. Zusätzlich muss der Google-Dialog deine Zustimmung zur Statistik (Analyse-Speicherung im Google Consent Mode) melden; bis dahin stehen alle Google-Speicher- und Messfunktionen auf „abgelehnt“. Fehlt eine dieser Zustimmungen oder ist sie unklar, wird Google Analytics nicht geladen. Bei Aufrufen außerhalb des Geltungsbereichs der DSGVO (laut Google-Dialog) wird Google Analytics nur geladen, wenn der Dialog die Statistik ausdrücklich erlaubt oder als nicht einwilligungspflichtig meldet und keinen US-Widerspruch (Opt-out nach US-Bundesstaatenrecht) anzeigt. Widerrufst oder änderst du deine Einwilligung, endet die Messung sofort: Google Analytics wird abgeschaltet und sendet keine weiteren Daten; erst nach einer erneuten Zustimmung misst es wieder. Google-Signale und Werbepersonalisierung sind in unserer Analytics-Einbindung deaktiviert. Google speichert in Google Analytics 4 keine vollständigen IP-Adressen. Die Ereignisdaten werden nach der im Google-Analytics-Konto eingestellten Speicherdauer gelöscht, höchstens nach 14 Monaten. Eingaben in unsere Werkzeuge werden nicht übermittelt. Rechtsgrundlage ist deine Einwilligung (Art. 6 Abs. 1 lit. a DSGVO, § 165 Abs. 3 TKG 2021); widerrufen kannst du sie jederzeit über „Datenschutz-Einstellungen“.</p>
<h2>Übermittlung in Drittländer</h2><p>Google und GitHub können Daten auch in den USA verarbeiten. Beide Unternehmen sind nach dem EU-US Data Privacy Framework zertifiziert; die Übermittlung stützt sich auf den Angemessenheitsbeschluss der EU-Kommission.</p>
<h2>Kontakt per E-Mail</h2><p>Schreibst du uns, verwenden wir deine Adresse und Nachricht nur zur Bearbeitung deiner Anfrage (Art. 6 Abs. 1 lit. b oder f DSGVO) und löschen sie, wenn sie nicht mehr gebraucht werden und keine Aufbewahrungspflicht besteht.</p>
<h2>Deine Rechte</h2><p>Du hast das Recht auf Auskunft, Berichtigung, Löschung, Einschränkung der Verarbeitung, Datenübertragbarkeit und Widerspruch sowie das Recht, eine Einwilligung jederzeit zu widerrufen. Deine Einwilligung zu Werbung und Statistik kannst du jederzeit selbst über „Datenschutz-Einstellungen“ unten auf jeder Seite ändern oder widerrufen.</p><h2>Beschwerde bei der Datenschutzbehörde</h2><p>Wenn du meinst, dass die Verarbeitung deiner Daten gegen das Datenschutzrecht verstößt, kannst du dich direkt an die zuständige Aufsichtsbehörde wenden:<br>Österreichische Datenschutzbehörde, Barichgasse 40–42, 1030 Wien<br>E-Mail: <a href="mailto:dsb@dsb.gv.at">dsb@dsb.gv.at</a> · Web: <a href="https://www.dsb.gv.at" rel="noopener">www.dsb.gv.at</a></p>""")
    write("404.html", "page.html", title="Seite nicht gefunden | Kalenderkompass 24", description="Diese Seite gibt es nicht.",
          h1="Diese Seite gibt es nicht", lead="Vielleicht hilft dir einer dieser Links weiter.", ads=False, robots="noindex",
          body=f"<ul><li><a href='/'>Feiertage und Brückentage</a></li><li><a href='/feiertage-{CUR}-oesterreich.html'>Feiertage {CUR} Österreich</a></li><li><a href='/feiertage-{CUR}-deutschland.html'>Feiertage {CUR} Deutschland</a></li><li><a href='/urlaubsplaner.html'>Urlaubsplaner</a></li></ul>", active="")


def build_static():
    (OUT / "assets").mkdir(parents=True, exist_ok=True)
    for f in (ROOT / "assets").iterdir():
        shutil.copy(f, OUT / "assets" / f.name)
    (OUT / "assets" / "icon.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect x="3" y="6" width="26" height="23" rx="3" fill="#fff" stroke="#141414" stroke-width="2.4"/><rect x="3" y="6" width="26" height="7" rx="3" fill="#C4122F"/><text x="16" y="25.5" text-anchor="middle" font-family="Georgia,serif" font-size="11" font-weight="700" fill="#141414">24</text></svg>')
    (OUT / "CNAME").write_text("kalenderkompass24.de\n")
    (OUT / ".nojekyll").write_text("")
    (OUT / "google9bf1079fd4bf073e.html").write_text("google-site-verification: google9bf1079fd4bf073e.html")
    (OUT / "ads.txt").write_text("google.com, pub-7811071715414905, DIRECT, f08c47fec0942fa0\n")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
    urls = "".join(f"<url><loc>{SITE}{p}</loc><lastmod>{LASTMOD}</lastmod><priority>{pr}</priority></url>" for p, pr in PAGES)
    (OUT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')


def check_years():
    """Selbsttest: Auf jeder Jahresseite dürfen Titel und Überschriften nur das eigene Jahr nennen."""
    bad = []
    for f in OUT.glob("*.html"):
        m = re.fullmatch(r"[a-z-]+?-(20\d\d)(-[a-z-]+)?\.html", f.name)
        if not m: continue
        y = m.group(1)
        html = f.read_text(encoding="utf-8")
        for tag in re.findall(r"<(?:title|h1|h2)[^>]*>(.*?)</(?:title|h1|h2)>", html, re.S):
            text = re.sub(r"<[^>]+>", "", tag)
            others = {x for x in re.findall(r"\b20\d\d\b", text) if x != y and "/" not in text}
            if others: bad.append(f"{f.name}: „{text.strip()[:80]}“")
    if bad:
        sys.exit("Jahres-Selbsttest fehlgeschlagen:\n" + "\n".join(bad[:30]))
    print("Jahres-Selbsttest: alle Jahresseiten nennen nur ihr eigenes Jahr")


def main():
    H.selftest()
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir()
    build_data()
    build_home()
    for y in (2027, 2028): build_regions(y)
    for y in YEARS: build_country(y)
    for y in (2027, 2028): build_bridges(y)
    build_planner(); build_workdays(); build_familie(); build_mein_kalender(); build_shop()
    for y in YEARS: build_kw(y)
    for y in (2027, 2028): build_print(y)
    import build_ferien; build_ferien.run(write, fmt, mshort, crumbs_ld, TODAY, SITE)
    check_claims(); check_claims_de()
    build_articles(); build_methodik(); build_legal(); build_static()
    check_years()
    print(f"{len(PAGES)} indexierbare Seiten in {OUT}")


if __name__ == "__main__":
    main()
