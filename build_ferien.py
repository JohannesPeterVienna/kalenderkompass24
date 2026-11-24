"""Schulferien-Seiten für Kalenderkompass 24 (wird von build.py aufgerufen).

Seit 24.11.2026 eine Seite je Land mit Abschnitten je Bundesland (Sprungmarke = Kürzel des Bundeslandes);
der Sommerferien-Vergleich steht auf der Deutschland-Seite (#sommerferien)."""
import html
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


def run(write, fmt, mshort, crumbs_ld, TODAY, SITE, SF_URL, FT_URL, macros):
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

    def cell_span(r):
        return f"<td class='date'><span class='lg'>{r['span']}</span><span class='sm'>{r['short']}</span></td>"

    # ---------------- Daten je Region
    data = {}
    for c in ("at", "de"):
        for slug, name in F.regions(c).items():
            ps = F.periods(c, slug)
            legal = legal_dates(c, slug)
            rows = []
            for p in ps:
                rows.append(dict(p, span=span(p, c), short=short(p["start"], p["end"]), wd=workdays(p["start"], p["end"], legal), cls=tclass(p["name"])))
            upcoming = [r for r in rows if r["end"] >= TODAY]
            data[(c, slug)] = {"name": name, "rows": rows, "bars": bars(ps), "total": sum(p["days"] for p in ps),
                               "wd": sum(r["wd"] for r in rows), "summer": F.summer(c, slug),
                               "nxt": upcoming[0] if upcoming else rows[-1],
                               "ics": json.dumps([[r["name"], r["start"].isoformat(), r["end"].isoformat()] for r in rows], ensure_ascii=False)}

    country_label = {"at": "Österreich", "de": "Deutschland"}

    def ics_button(c, slug, label):
        d = data[(c, slug)]
        return (f"<button class='btn ghost' type='button' data-ferien-ics data-region='{slug}' data-name='Schulferien {F.SCHOOLYEAR} {d['name']}' "
                f"data-file='schulferien-{F.SY_SLUG}-{slug}.ics' data-rows=\"{html.escape(d['ics'])}\">{label}</button>")

    def gantt(c):
        return [{"href": f"#{s}", "name": n, "bars": data[(c, s)]["bars"]} for s, n in F.regions(c).items()]

    def page(c, path, crumbs, title, description, h1, lead, jumps, body_first, body_rest, side, srcs, lastmod):
        regs = F.regions(c)
        first = next(iter(regs))
        write(path, "ferien_land.html", title=title, description=description, h1=h1, lead=lead, jumps=jumps,
              country=c, regions=list(regs.items()), nxt_region=first, nxt=data[(c, first)]["nxt"],
              sy=F.SCHOOLYEAR, in_country=f"in {country_label[c]}", gantt=gantt(c), axis=axis_ctx(c),
              body_first=body_first, body_rest=body_rest, side=side, srcs=srcs, crumbs=crumbs, lang_at=(c == "at"),
              checked="2. November 2026", lastmod=lastmod, jsonld=[crumbs_ld(crumbs)], active=SF_URL["at"], priority=0.9)

    zaehl = """<h2 id="zaehlweise">Welche Tage für die Betreuung zählen</h2>
<p>Die Spalte „Tage“ zählt den ersten und den letzten Ferientag mit. Von Samstag bis zum Sonntag der folgenden Woche sind das neun Kalendertage. Darin liegen fünf Tage von Montag bis Freitag. Fällt einer davon auf einen am Ort berücksichtigten gesetzlichen Feiertag, weist die Tabelle vier Arbeitstage aus.</p>
<p>Wer beispielsweise nur Montag, Dienstag und Donnerstag arbeitet, markiert im Kalenderexport diese drei Wochentage. Bei geteilten Ferien zählen für ein Treffen nur die Tage zwischen dem späteren Beginn und dem früheren Ende. Ein gemeinsamer erster Ferientag garantiert noch kein gemeinsames Ferienende.</p>"""
    th = ("<th scope='col'>Ferien</th><th scope='col'>Zeitraum</th><th scope='col'>Tage</th>"
          "<th scope='col' title='Montag bis Freitag ohne gesetzliche Feiertage'><span class='lg'>Arbeitstage</span><span class='sm'>Arb.-T.</span></th>")

    # ---------------- Österreich
    c = "at"
    regs = F.regions(c)
    keyset = lambda r: (r["name"], r["start"], r["end"])
    common = [r for r in data[(c, next(iter(regs)))]["rows"] if all(any(keyset(x) == keyset(r) for x in data[(c, s)]["rows"]) for s in regs)]
    assert [r["name"] for r in common] == ["Herbstferien", "Allerseelen (schulfrei)", "Weihnachtsferien", "Osterferien", "Pfingstferien"], common
    assert len({tuple(r["wd"] for r in data[(c, s)]["rows"] if r in common) for s in regs}) == 1   # gleiche Feiertage → gleiche Arbeitstage
    crow = "".join(f"<tr><td><span class='dot f-{r['cls']}'></span>{r['name']}</td>{cell_span(r)}<td>{r['days']}</td><td>{r['wd']}</td></tr>" for r in common)
    rrow = []
    for s, n in regs.items():
        d = data[(c, s)]
        sem = next(r for r in d["rows"] if r["name"] == "Semesterferien")
        su = next(r for r in d["rows"] if r["name"] == "Sommerferien")
        # Festtag des Landespatrons im Unterrichtsjahr (schulfrei nach § 2 Abs. 4 Z 2 SchZG)
        pat = []
        for (m, dd), pn in H.AT_PATRONS[s]:
            if "Landespatron" not in pn: continue
            pd = date(F.SY_START.year if m >= 9 else F.SY_END.year, m, dd)
            pat.append(f"{pn.split(' (')[0]}<div class='small muted'>{WS[pd.weekday()]} {pd.day}.{pd.month}.{pd.year}</div>")
        rrow.append(f"<tr id='{s}'><td><strong>{n}</strong><div class='small'><a href='{FT_URL['at']}#{s}'>Landespatron und Feiertage</a></div></td>"
                    f"<td class='date'>{short(sem['start'], sem['end'])}</td><td class='date'>{short(su['start'], su['end'])}</td><td>{'<br>'.join(pat)}</td>"
                    f"<td>{d['total']}</td><td>{d['wd']}</td><td class='no-print'>{ics_button(c, s, '.ics')}</td></tr>")
    east = [n for s, n in regs.items() if data[(c, s)]["summer"]["start"] == date(2027, 7, 3)]
    first_html = f"""
<h2>In allen Bundesländern gleich</h2>
<div class="scroll"><table class="tbl"><thead><tr>{th}</tr></thead><tbody>{crow}</tbody></table></div>
<p class="small muted">Arbeitstage: Montag bis Freitag ohne gesetzliche Feiertage – wie viele Urlaubstage berufstätige Eltern für die ganze Ferienzeit bräuchten.</p>
<h2 id="bundeslaender">Semester- und Sommerferien nach Bundesland</h2>
<p>Die Semesterferien liegen in drei Gruppen in den ersten drei Februarwochen. Im Sommer beginnen {jlist(east)} eine Woche früher als die übrigen Bundesländer. Je Zeile: alle Ferien des Bundeslandes zusammen und der Kalender-Export mit allen Terminen.</p>
<div class="scroll"><table class="tbl"><thead><tr><th scope="col">Bundesland</th><th scope="col">Semesterferien</th><th scope="col">Sommerferien</th><th scope="col">Landespatron (schulfrei)</th><th scope="col">Ferientage gesamt</th><th scope="col">Arbeitstage gesamt</th><th scope="col" class="no-print">Kalender</th></tr></thead><tbody>{''.join(rrow)}</tbody></table></div>
"""
    assert date(2026, 10, 26).weekday() == 0   # Nationalfeiertag 2026 an einem Montag → höchstens drei schulautonome Tage
    sz = "https://www.ris.bka.gv.at/NormDokument.wxe?Abfrage=Bundesnormen&amp;Gesetzesnummer=10009575&amp;Paragraf=2"
    rest_html = f"""
<h2 id="schulzeitgesetz">Was das Schulzeitgesetz festlegt</h2>
<p>Die Ferien stehen in § 2 des Schulzeitgesetzes 1985. Der Ferienkalender von oesterreich.gv.at gilt nach eigener Angabe für öffentliche und private mittlere und höhere Schulen mit Öffentlichkeitsrecht; für Volksschulen, Neue Mittelschulen, Sonder-, Berufs- und Polytechnische Schulen gelten diese Ferien üblicherweise ebenfalls, Schulen im Tourismusbereich können abweichen. Die Festtage der Landespatrone nennt er nicht.</p>
<ul>
<li><strong>Semesterferien:</strong> eine Woche. Sie beginnen in Niederösterreich und Wien am ersten Montag im Februar, im Burgenland, in Kärnten, Salzburg, Tirol und Vorarlberg am zweiten und in Oberösterreich und der Steiermark am dritten Montag (§ 2 Abs. 2 Z 1 lit. b). Stellen Bildungsdirektion und Land aus fremdenverkehrspolitischen Gründen gleichlautende Anträge, kann der Bundesminister den Beginn durch Verordnung um eine Woche verlegen (Abs. 2a). Im Ferienkalender 2026/2027 liegen Salzburg, Tirol und Vorarlberg mit Oberösterreich und der Steiermark in der dritten Februarwoche.</li>
<li><strong>Sommerferien:</strong> Sie beginnen im Burgenland, in Niederösterreich und Wien an dem Samstag zwischen 28. Juni und 4. Juli, in den übrigen sechs Bundesländern an dem Samstag zwischen 5. und 11. Juli (§ 2 Abs. 2 Z 2).</li>
<li><strong>Weitere schulfreie Tage</strong> (§ 2 Abs. 4): der Allerseelentag, in jedem Bundesland der Festtag des Landespatrons sowie der Landesfeiertag, wenn er dort arbeitsfrei begangen wird, die Herbstferien vom 27. bis 31. Oktober, die Weihnachtsferien vom 24. Dezember bis 6. Jänner (dazu der 23. Dezember, wenn er auf einen Montag fällt), die Osterferien vom Samstag vor dem Palmsonntag bis zum Ostermontag und die Pfingstferien vom Samstag vor dem Pfingstsonntag bis zum Pfingstmontag.</li>
<li><strong>Schulautonome Tage</strong> (§ 2 Abs. 5): Schulforum oder Schulgemeinschaftsausschuss können je Unterrichtsjahr höchstens zwei Tage schulfrei erklären, wenn der 26. Oktober auf einen Sonntag fällt, höchstens drei, wenn er auf einen Montag oder Samstag fällt, sonst höchstens vier. 2026 ist der 26. Oktober ein Montag – im Unterrichtsjahr 2026/2027 sind es also höchstens drei Tage. Die Schulbehörde kann in besonderen Fällen einen weiteren Tag durch Verordnung schulfrei erklären. Welche Tage das sind, legt jede Schule fest; deshalb stehen sie in keinem amtlichen Kalender und fehlen auch hier.</li>
</ul>
<p class="small muted">Quellen: <a href="{sz}" rel="noopener">Schulzeitgesetz 1985, BGBl. Nr. 77/1985, zuletzt geändert durch BGBl. I Nr. 96/2022, § 2 im RIS</a>; <a href="{F.SRC_AT[1]}" rel="noopener">{F.SRC_AT[0]}</a> (Stand 25.08.2026). Beide abgerufen am 24. November 2026.</p>
<p class="small muted">Wie Kalender- und Arbeitstage gezählt werden und was das für die Betreuung heißt, steht bei den <a href="{SF_URL['de']}#zaehlweise">Schulferien in Deutschland</a>.</p>
<p class="small muted">Alle Angaben ohne Gewähr.</p>
"""
    crumbs = [("/", "Start"), (SF_URL["at"], "Schulferien Österreich")]
    page(c, SF_URL["at"].lstrip("/"), crumbs,
         title=f"Schulferien {F.SCHOOLYEAR} Österreich: alle 9 Bundesländer | Kalenderkompass 24",
         description=f"Schulferien {F.SCHOOLYEAR} in Österreich: gemeinsame Ferien, Semester- und Sommerferien je Bundesland, Zeitstrahl, Arbeitstage für Eltern und Kalender-Download.",
         h1=f"Schulferien {F.SCHOOLYEAR} in Österreich",
         lead="Herbst-, Weihnachts-, Oster- und Pfingstferien sind in ganz Österreich gleich. Unterschiede gibt es nur bei den Semesterferien (drei Gruppen im Februar) und beim Sommer: Burgenland, Niederösterreich und Wien starten eine Woche früher.",
         jumps=[("#bundeslaender", "Nach Bundesland"), ("#schulzeitgesetz", "Was das Gesetz festlegt"), (SF_URL["de"], "Schulferien Deutschland")],
         body_first=first_html, body_rest=rest_html, srcs=[F.SRC_AT], lastmod="2026-11-24",
         side=[(FT_URL["at"], "Feiertage Österreich"), (SF_URL["de"], "Schulferien Deutschland"), (f"{SF_URL['de']}#sommerferien", "Sommerferien 2027 im Vergleich"), ("/urlaubsplaner.html", "Urlaubsplaner"), ("/familienplaner.html", "Familienplaner")])

    # ---------------- Deutschland
    c = "de"
    regs = F.regions(c)
    summer_rows = []
    for cc in ("at", "de"):
        for s, n in F.regions(cc).items():
            su = data[(cc, s)]["summer"]
            summer_rows.append({"name": n, "slug": s, "country": country_label[cc], "href": (f"#{s}" if cc == "de" else f"{SF_URL['at']}#{s}"),
                                "start": su["start"], "end": su["end"], "days": su["days"],
                                "span": f"{fmt(su['start'], cc, year=False)} – {fmt(su['end'], cc, year=False)}", "short": short(su["start"], su["end"]), "c": cc})
    summer_rows.sort(key=lambda r: (r["start"], r["name"]))
    s0, s1 = date(2027, 6, 20), date(2027, 9, 20)
    tot = (s1 - s0).days
    weeks = []
    d = s0 + timedelta(days=(7 - s0.weekday()) % 7)
    while d < s1:
        weeks.append({"left": round((d - s0).days / tot * 100, 3), "label": f"{d.day}.{d.month}."})
        d += timedelta(days=14)
    sg = [dict(r, name=f"{r['name']} ({'AT' if r['c'] == 'at' else 'DE'})", bars=bars([{"name": "Sommerferien", "start": r["start"], "end": r["end"]}], s0, s1)) for r in summer_rows]
    def names(rows, form):
        """Namensliste mit Gleichständen: „Hessen, Rheinland-Pfalz und im Saarland“ / „… und das Saarland“."""
        if len(rows) == 9 and all(r["c"] == "at" for r in rows):
            return {"in": "in allen neun österreichischen Bundesländern", "nom": "alle neun österreichischen Bundesländer"}[form]
        if form == "in":
            parts = [H.region_in(r["slug"], r["name"]) for r in rows]
            parts = [parts[0]] + [p[3:] if p.startswith("in ") else p for p in parts[1:]]   # „in A, B und im C“
        else:
            parts = [H.region_nom(r["slug"], r["name"]) for r in rows]
        return parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " und " + parts[-1]
    first_start, last_start = summer_rows[0]["start"], summer_rows[-1]["start"]
    earliest = [r for r in summer_rows if r["start"] == first_start]
    latest = [r for r in summer_rows if r["start"] == last_start]
    max_days, min_days = max(r["days"] for r in summer_rows), min(r["days"] for r in summer_rows)
    longest = [r for r in summer_rows if r["days"] == max_days]
    shortest = [r for r in summer_rows if r["days"] == min_days]
    c0, c1 = earliest[0]["c"], latest[0]["c"]
    first, last = min(r["start"] for r in summer_rows), max(r["end"] for r in summer_rows)
    peak_day, peak_n = None, 0
    d = first
    while d <= last:
        n = sum(1 for r in summer_rows if r["start"] <= d <= r["end"])
        if n > peak_n: peak_day, peak_n = d, n
        d += timedelta(days=1)
    srow = "".join(f"<tr><td><a href='{r['href']}'>{r['name']}</a> <span class='small muted'>{'AT' if r['c'] == 'at' else 'DE'}</span></td>"
                   f"<td class='date'><span class='lg'>{r['span']}</span><span class='sm'>{r['short']}</span></td><td>{r['days']}</td></tr>" for r in summer_rows)
    je = lambda g: "je " if len(g) > 1 else ""
    summer_html = f"""
<h2 id="sommerferien">Sommerferien 2027 – wer startet zuerst?</h2>
<p>Den Anfang {'machen' if len(earliest) > 1 else 'macht'} {H.cap(names(earliest, 'nom'))} am {fmt(first_start, c0)}, als {'Letzte starten' if len(latest) > 1 else 'Letztes startet'} {names(latest, 'nom')} am {fmt(last_start, c1)}. Zum Vergleich stehen die neun österreichischen Bundesländer mit in der Übersicht.</p>
<section class="band" aria-label="Sommerferien 2027 im Zeitstrahl">{macros.gantt(sg, weeks, "Sommerferien 2027 in Österreich und Deutschland")}<div class="legend"><span><i class="f-su"></i>Sommerferien</span><span>AT = Österreich, DE = Deutschland</span></div></section>
<div class="scroll"><table class="tbl"><thead><tr><th scope="col">Land</th><th scope="col">Sommerferien</th><th scope="col">Tage</th></tr></thead><tbody>{srow}</tbody></table></div>
<p>Zwischen {fmt(first, 'de', wd=False, year=False)} und {fmt(last, 'de', wd=False, year=False)} sind irgendwo in Österreich oder Deutschland Sommerferien. Am längsten dauern sie {names(longest, 'in')} ({je(longest)}{max_days} Tage), am kürzesten {names(shortest, 'in')} ({je(shortest)}{min_days} Tage).</p>
<p>Den größten Andrang gibt es rund um den {fmt(peak_day, 'de')}: Dann haben {peak_n} der 25 Länder gleichzeitig frei. Wer flexibel ist, reist besser am Anfang oder am Ende des Sommers – dann sind Unterkünfte und Flüge oft günstiger.</p>
<p>Österreich hat mit rund neun Wochen deutlich längere Sommerferien als Deutschland, wo sie meist sechs Wochen dauern. Dafür haben deutsche Länder oft längere Herbst- oder Pfingstferien.</p>
"""
    sections = []
    for s, n in regs.items():
        d = data[(c, s)]
        su = d["summer"]
        same = [regs[x] for x in regs if x != s and data[(c, x)]["summer"]["start"] == su["start"]]
        rows = "".join(f"<tr><td><span class='dot f-{r['cls']}'></span>{r['name']}</td>{cell_span(r)}<td>{r['days']}</td><td>{r['wd']}</td></tr>" for r in d["rows"])
        same_txt = (f"<p>Den gleichen Sommerferienbeginn haben auch {jlist(same)}.</p>" if same else "")
        sections.append(f"<section id='{s}' class='land'><h3>{n}</h3><div class='scroll'><table class='tbl'><thead><tr>{th}</tr></thead>"
                        f"<tbody>{rows}<tr class='sum'><td>Gesamt</td><td></td><td>{d['total']}</td><td>{d['wd']}</td></tr></tbody></table></div>{same_txt}"
                        f"<p class='no-print'>{ics_button(c, s, 'Ferien in den Kalender (.ics)')} <a class='btn ghost' href='{FT_URL['de']}#{s}'>Feiertage {n}</a></p></section>")
    tiles = "".join(f'<li><a href="#{s}">{n}</a></li>' for s, n in regs.items())
    first_html = summer_html
    rest_html = f"""
<h2 id="laender">Die 16 Länder</h2>
<ul class="tiles no-print">{tiles}</ul>
{''.join(sections)}
{zaehl}
<p class="small muted">Quelle: <a href="{F.SRC_DE[1]}" rel="noopener">{F.SRC_DE[0]}</a>. Alle Angaben ohne Gewähr. Schulautonome Tage legt jede Schule selbst fest; sie sind hier nicht enthalten.</p>
"""
    crumbs = [("/", "Start"), (SF_URL["de"], "Schulferien Deutschland")]
    page(c, SF_URL["de"].lstrip("/"), crumbs,
         title=f"Schulferien {F.SCHOOLYEAR} Deutschland: alle 16 Länder & Sommerferien 2027 | Kalenderkompass 24",
         description=f"Schulferien {F.SCHOOLYEAR} für alle 16 deutschen Länder: Zeitstrahl, alle Termine je Land, Sommerferien 2027 im Vergleich mit Österreich und Kalender-Download.",
         h1=f"Schulferien {F.SCHOOLYEAR} in Deutschland",
         lead="In Deutschland legt jedes Land seine Ferien selbst fest; die Kultusministerkonferenz stimmt vor allem die Sommerferien ab, damit sie gestaffelt beginnen.",
         jumps=[("#sommerferien", "Sommerferien 2027"), ("#laender", "Die 16 Länder"), (SF_URL["at"], "Schulferien Österreich")],
         body_first=first_html, body_rest=rest_html, srcs=[F.SRC_DE, F.SRC_AT], lastmod="2026-11-24",
         side=[(FT_URL["de"], "Feiertage Deutschland"), (SF_URL["at"], "Schulferien Österreich"), ("/brueckentage.html#jahr-2027", "Brückentage 2027"), ("/urlaubsplaner.html", "Urlaubsplaner"), ("/familienplaner.html", "Familienplaner")])


def jlist(xs):
    return (", ".join(xs[:-1]) + " und " + xs[-1]) if len(xs) > 1 else (xs[0] if xs else "")
