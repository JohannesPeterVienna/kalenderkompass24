"""Erzeugt die Shop-Produkte (PDF-Druckvorlagen) für alle 25 Bundesländer aus derselben Datenquelle wie die Website.

Aufruf:  python produkte/erzeugen.py <Zielordner>
Ergebnis: <Ziel>/<produkt>/<land>/*.pdf und je Produkt eine ZIP-Datei <Ziel>/<produkt>.zip

Die PDFs gehören NICHT nach docs/ (sonst wären sie frei herunterladbar). Sie werden beim Zahlungsanbieter hochgeladen.
Schriften: nur PDF-Standardschriften (Times, Helvetica) – keine Einbettung fremder Schriftdateien nötig.
"""
import sys, zipfile
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import holidays as H
import ferien as F

from reportlab.lib.pagesizes import A4, A3, landscape
from reportlab.lib.units import mm
from reportlab.lib.colors import Color, black, white
from reportlab.pdfgen import canvas

YEAR = 2027
STAND = "Stand 5. November 2026 · Angaben ohne Gewähr"
RED = Color(0.769, 0.071, 0.184)
RED_SOFT = Color(0.984, 0.914, 0.925)
INK = Color(0.08, 0.08, 0.08)
MUTED = Color(0.37, 0.37, 0.35)
LINE = Color(0.80, 0.79, 0.76)
WEEKEND = Color(0.945, 0.937, 0.914)
FERIEN = Color(0.905, 0.933, 0.961)
M_AT = ["Jänner", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]
M_DE = ["Januar"] + M_AT[1:]
WD = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


def regions():
    for slug, name in H.AT_REGIONS.items():
        yield "at", slug, name
    for slug, (name, _) in H.DE_REGIONS.items():
        yield "de", slug, name


class Daten:
    def __init__(self, country, slug, name):
        self.country, self.slug, self.name = country, slug, name
        self.months = M_AT if country == "at" else M_DE
        self.bt = "Fenstertag" if country == "at" else "Brückentag"
        self.hol = {h["date"]: h for h in H.region_holidays(country, slug, YEAR)}
        self.br = {d for b in H.bridge_days(country, slug, YEAR) for d in b["days"]}
        self.ferien = {}
        for p in F.periods(country, slug):
            d = p["start"]
            while d <= p["end"]:
                if d.year == YEAR: self.ferien[d] = p["name"]
                d += timedelta(days=1)

    def legal(self, d): h = self.hol.get(d); return h if h and h["kind"] == "legal" else None
    def label(self, h): return (h["name"] + "*") if h and h["kind"] == "legal" and h["note"] else (h or {}).get("name", "")
    def notes(self): return sorted({h["note"] for h in self.hol.values() if h["kind"] == "legal" and h["note"]})
    def patron(self, d): h = self.hol.get(d); return h if h and h["kind"] != "legal" else None


def fit(c, text, font, size, maxw):
    """Kürzt Text mit „…“ auf die verfügbare Breite."""
    if c.stringWidth(text, font, size) <= maxw: return text
    while text and c.stringWidth(text + "…", font, size) > maxw: text = text[:-1]
    return text + "…"


def footer(c, W, D, extra=""):
    c.setFont("Helvetica", 7); c.setFillColor(MUTED)
    c.drawString(14 * mm, 9 * mm, "Kalenderkompass 24 · kalenderkompass24.de")
    c.drawRightString(W - 14 * mm, 9 * mm, f"{extra}{D.name} {YEAR} · {STAND}")


def legend(c, x, y, D, ferien=False):
    c.setFont("Helvetica", 7.5); items = []
    c.setFillColor(RED); c.rect(x, y - 1, 3 * mm, 3 * mm, stroke=0, fill=1); c.setFillColor(INK); c.drawString(x + 4.5 * mm, y, "gesetzlicher Feiertag"); x += 36 * mm
    c.setStrokeColor(RED); c.setLineWidth(0.8); c.rect(x, y - 1, 3 * mm, 3 * mm, stroke=1, fill=0); c.drawString(x + 4.5 * mm, y, "Landespatron / schulfrei"); x += 40 * mm
    c.setStrokeColor(INK); c.setLineWidth(1.4); c.rect(x, y - 1, 3 * mm, 3 * mm, stroke=1, fill=0); c.drawString(x + 4.5 * mm, y, D.bt); x += 26 * mm
    if ferien:
        c.setFillColor(FERIEN); c.rect(x, y - 1, 3 * mm, 3 * mm, stroke=0, fill=1); c.setFillColor(INK); c.drawString(x + 4.5 * mm, y, "Schulferien")


# ---------------------------------------------------------------- Wandkalender (A4 hoch, A3 skaliert)
def wand_jahr(c, D):
    W, Hh = A4
    c.setFillColor(INK); c.setFont("Times-Bold", 44); c.drawString(14 * mm, Hh - 30 * mm, str(YEAR))
    c.setFont("Helvetica", 11); c.setFillColor(MUTED); c.drawString(14 * mm, Hh - 38 * mm, f"Feiertage und {D.bt}e · {D.name}")
    c.setStrokeColor(INK); c.setLineWidth(1.6); c.line(14 * mm, Hh - 42 * mm, W - 14 * mm, Hh - 42 * mm)
    cw, ch = (W - 28 * mm) / 3, 46 * mm
    for m in range(12):
        col, row = m % 3, m // 3
        x0, y0 = 14 * mm + col * cw, Hh - 50 * mm - row * (ch + 3 * mm)
        c.setFillColor(INK); c.setFont("Times-Bold", 12); c.drawString(x0, y0, D.months[m])
        cell = (cw - 8 * mm) / 7
        c.setFont("Helvetica", 6.5); c.setFillColor(MUTED)
        for i, w in enumerate(WD): c.drawCentredString(x0 + cell * (i + .5), y0 - 6 * mm, w)
        d = date(YEAR, m + 1, 1); r = 0
        while d.month == m + 1:
            i = d.weekday(); cx = x0 + cell * (i + .5); cy = y0 - 11 * mm - r * 5.6 * mm
            if d in D.br:
                c.setStrokeColor(INK); c.setLineWidth(1); c.rect(cx - cell / 2 + .6, cy - 1.6 * mm, cell - 1.2, 4.8 * mm, stroke=1, fill=0)
            if D.legal(d):
                c.setFillColor(RED); c.rect(cx - cell / 2 + .6, cy - 1.6 * mm, cell - 1.2, 4.8 * mm, stroke=0, fill=1); c.setFillColor(white); c.setFont("Helvetica-Bold", 8)
            elif D.patron(d):
                c.setStrokeColor(RED); c.setLineWidth(.8); c.rect(cx - cell / 2 + .6, cy - 1.6 * mm, cell - 1.2, 4.8 * mm, stroke=1, fill=0); c.setFillColor(RED); c.setFont("Helvetica-Bold", 8)
            else:
                c.setFillColor(MUTED if i >= 5 else INK); c.setFont("Helvetica", 8)
            c.drawCentredString(cx, cy, str(d.day))
            if i == 6: r += 1
            d += timedelta(days=1)
    # Feiertagsliste
    y = 46.5 * mm
    legal = [h for h in D.hol.values() if h["kind"] == "legal"]
    c.setFont("Helvetica-Bold", 8); c.setFillColor(INK); c.drawString(14 * mm, y + 4 * mm, f"Gesetzliche Feiertage {YEAR}")
    c.setFont("Helvetica", 7.2)
    for k, h in enumerate(sorted(legal, key=lambda h: h["date"])):
        col, row = k // 6, k % 6
        c.drawString(14 * mm + col * 62 * mm, y - row * 3.6 * mm, f"{h['date'].day}. {D.months[h['date'].month-1][:3]}. {WD[h['date'].weekday()]} – {fit(c, D.label(h), 'Helvetica', 7.2, 44 * mm)}")
    for k, n in enumerate(D.notes()):
        c.setFont("Helvetica", 6.5); c.setFillColor(MUTED); c.drawString(14 * mm, 25 * mm - k * 3 * mm, f"* {n}")
    legend(c, 14 * mm, 20 * mm, D)
    footer(c, W, D)


def wand_monat(c, D, m):
    W, Hh = A4
    c.setFillColor(INK); c.setFont("Times-Bold", 34); c.drawString(14 * mm, Hh - 28 * mm, D.months[m])
    c.setFont("Times-Roman", 34); c.setFillColor(MUTED); c.drawRightString(W - 14 * mm, Hh - 28 * mm, str(YEAR))
    c.setStrokeColor(INK); c.setLineWidth(1.6); c.line(14 * mm, Hh - 33 * mm, W - 14 * mm, Hh - 33 * mm)
    first = date(YEAR, m + 1, 1); last = (date(YEAR + (m == 11), (m + 1) % 12 + 1, 1) - timedelta(days=1))
    weeks = ((first.weekday() + last.day - 1) // 7) + 1
    kw, x0, top, bottom = 8 * mm, 14 * mm, Hh - 40 * mm, 30 * mm
    cw = (W - 28 * mm - kw) / 7; chh = (top - 6 * mm - bottom) / weeks
    c.setFont("Helvetica-Bold", 8); c.setFillColor(MUTED)
    c.drawCentredString(x0 + kw / 2, top - 4 * mm, "KW")
    for i, w in enumerate(WD): c.drawCentredString(x0 + kw + cw * (i + .5), top - 4 * mm, w)
    gy = top - 6 * mm
    d = first; r = 0
    while d.month == m + 1:
        i = d.weekday(); x = x0 + kw + cw * i; y = gy - (r + 1) * chh
        if i == 0 or d == first:
            c.setFont("Helvetica", 7); c.setFillColor(MUTED); c.drawCentredString(x0 + kw / 2, y + chh - 5 * mm, str(d.isocalendar()[1]))
        c.setFillColor(WEEKEND if i >= 5 else white); c.setStrokeColor(LINE); c.setLineWidth(.5)
        c.rect(x, y, cw, chh, stroke=1, fill=1)
        lg, pa = D.legal(d), D.patron(d)
        if d in D.br:
            c.setStrokeColor(INK); c.setLineWidth(1.6); c.rect(x + 1, y + 1, cw - 2, chh - 2, stroke=1, fill=0)
        c.setFont("Helvetica-Bold", 13); c.setFillColor(RED if (lg or pa) else INK)
        c.drawString(x + 2.2 * mm, y + chh - 6.5 * mm, str(d.day))
        label = D.label(lg or pa) or (D.bt if d in D.br else "")
        if label:
            c.setFont("Helvetica", 6.6); c.setFillColor(RED if (lg or pa) else INK)
            c.drawString(x + 2.2 * mm, y + chh - 10.5 * mm, fit(c, label, "Helvetica", 6.6, cw - 4.4 * mm))
        if i == 6: r += 1
        d += timedelta(days=1)
    if any(D.legal(date(YEAR, m + 1, k)) and D.legal(date(YEAR, m + 1, k))["note"] for k in range(1, last.day + 1)):
        c.setFont("Helvetica", 6.5); c.setFillColor(MUTED); c.drawString(14 * mm, 25 * mm, "* " + "; ".join(D.notes()))
    legend(c, 14 * mm, 20 * mm, D)
    footer(c, W, D)


def wandkalender(D, out, size):
    W, Hh = size
    c = canvas.Canvas(str(out), pagesize=size); c.setTitle(f"Wandkalender {YEAR} – {D.name}"); c.setAuthor("Kalenderkompass 24")
    s = W / A4[0]
    for page in range(13):
        c.saveState(); c.scale(s, s)
        wand_jahr(c, D) if page == 0 else wand_monat(c, D, page - 1)
        c.restoreState(); c.showPage()
    c.save()


# ---------------------------------------------------------------- Familienplaner (A4 hoch je Monat, A3 skaliert)
def familie_monat(c, D, m):
    W, Hh = A4
    c.setFillColor(INK); c.setFont("Times-Bold", 26); c.drawString(14 * mm, Hh - 24 * mm, f"{D.months[m]} {YEAR}")
    c.setFont("Helvetica", 9); c.setFillColor(MUTED); c.drawRightString(W - 14 * mm, Hh - 24 * mm, f"Familienplaner · {D.name}")
    c.setStrokeColor(INK); c.setLineWidth(1.6); c.line(14 * mm, Hh - 28 * mm, W - 14 * mm, Hh - 28 * mm)
    x0, top = 14 * mm, Hh - 32 * mm
    dayw, notew = 15 * mm, 34 * mm
    pw = (W - 28 * mm - dayw - notew) / 5
    hh = 9 * mm
    c.setStrokeColor(LINE); c.setLineWidth(.5)
    for k in range(5):
        x = x0 + dayw + k * pw
        c.rect(x, top - hh, pw, hh, stroke=1, fill=0)
        c.setFont("Helvetica", 6.5); c.setFillColor(MUTED); c.drawString(x + 1.5 * mm, top - 3 * mm, "Name")
    c.setFont("Helvetica-Bold", 7); c.setFillColor(MUTED)
    c.drawString(x0 + dayw + 5 * pw + 1.5 * mm, top - 5.5 * mm, "Feiertag · Ferien")
    days = (date(YEAR + (m == 11), (m + 1) % 12 + 1, 1) - date(YEAR, m + 1, 1)).days
    rh = (top - hh - 26 * mm) / 31
    prev = None
    for k in range(days):
        d = date(YEAR, m + 1, k + 1); y = top - hh - (k + 1) * rh
        lg, pa, fe = D.legal(d), D.patron(d), D.ferien.get(d)
        fill = WEEKEND if d.weekday() >= 5 else (FERIEN if fe else white)
        c.setFillColor(fill); c.setStrokeColor(LINE); c.setLineWidth(.4)
        c.rect(x0, y, W - 28 * mm, rh, stroke=1, fill=1)
        for j in range(6): c.line(x0 + dayw + j * pw, y, x0 + dayw + j * pw, y + rh)
        if fe and d.weekday() >= 5:
            c.setFillColor(FERIEN); c.rect(x0 + dayw + 5 * pw, y, notew, rh, stroke=0, fill=1)
        c.setFont("Helvetica-Bold", 8.5); c.setFillColor(RED if (lg or pa) else INK)
        c.drawString(x0 + 1.5 * mm, y + rh / 2 - 1.2 * mm, f"{WD[d.weekday()]} {d.day}")
        note = D.label(lg or pa) or (fe if fe and fe != prev else "") or (D.bt if d in D.br else "")
        if note:
            c.setFont("Helvetica", 6.5); c.setFillColor(RED if (lg or pa) else INK)
            c.drawString(x0 + dayw + 5 * pw + 1.5 * mm, y + rh / 2 - 1 * mm, fit(c, note, "Helvetica", 6.5, notew - 3 * mm))
        prev = fe
    legend(c, 14 * mm, 18 * mm, D, ferien=True)
    c.setFont("Helvetica", 6.5); c.setFillColor(MUTED)
    c.drawString(14 * mm, 13.5 * mm, "Schulferien laut amtlichem Ferienkalender für das Schuljahr 2026/2027 (bis Ende der Sommerferien 2027). Spätere Ferien bitte selbst eintragen.")
    footer(c, W, D, "Familienplaner · ")


def familienplaner(D, out, size):
    W, Hh = size
    c = canvas.Canvas(str(out), pagesize=size); c.setTitle(f"Familienplaner {YEAR} – {D.name}"); c.setAuthor("Kalenderkompass 24")
    s = W / A4[0]
    for m in range(12):
        c.saveState(); c.scale(s, s); familie_monat(c, D, m); c.restoreState(); c.showPage()
    c.save()


# ---------------------------------------------------------------- Urlaubsplan fürs Team (A3 quer, Namen ausfüllbar)
def team(D, out):
    W, Hh = landscape(A3)
    c = canvas.Canvas(str(out), pagesize=(W, Hh)); c.setTitle(f"Urlaubsplan {YEAR} fürs Team – {D.name}"); c.setAuthor("Kalenderkompass 24")
    for q in range(4):
        start = date(YEAR, q * 3 + 1, 1); end = date(YEAR + (q == 3), (q * 3 + 3) % 12 + 1, 1) - timedelta(days=1)
        n = (end - start).days + 1
        c.setFillColor(INK); c.setFont("Times-Bold", 24); c.drawString(12 * mm, Hh - 20 * mm, f"Urlaubsplan {YEAR} · {q + 1}. Quartal")
        c.setFont("Helvetica", 9); c.setFillColor(MUTED); c.drawRightString(W - 12 * mm, Hh - 20 * mm, f"{D.name} · Feiertage und {D.bt}e eingetragen")
        c.setStrokeColor(INK); c.setLineWidth(1.6); c.line(12 * mm, Hh - 24 * mm, W - 12 * mm, Hh - 24 * mm)
        namew = 46 * mm; x0 = 12 * mm; dw = (W - 24 * mm - namew) / n
        top = Hh - 30 * mm; hh = 14 * mm; rows = 20; rh = (top - hh - 24 * mm) / rows
        # Kopf: Monate, Tage, Wochentage
        for k in range(n):
            d = start + timedelta(days=k); x = x0 + namew + k * dw
            if d.day == 1:
                c.setFont("Helvetica-Bold", 8); c.setFillColor(INK); c.drawString(x + .5 * mm, top - 3.5 * mm, D.months[d.month - 1])
                c.setStrokeColor(INK); c.setLineWidth(1); c.line(x, top, x, top - hh - rows * rh)
            lg, pa = D.legal(d), D.patron(d)
            col = RED if (lg or pa) else (MUTED if d.weekday() >= 5 else INK)
            c.setFillColor(col); c.setFont("Helvetica-Bold" if (lg or pa) else "Helvetica", 5.6)
            c.drawCentredString(x + dw / 2, top - 8.5 * mm, str(d.day))
            c.setFont("Helvetica", 4.6); c.drawCentredString(x + dw / 2, top - 12 * mm, WD[d.weekday()][0])
            if d in D.br:
                c.setStrokeColor(INK); c.setLineWidth(.9); c.rect(x + .3, top - hh + .8 * mm, dw - .6, 8 * mm, stroke=1, fill=0)
            fill = RED_SOFT if lg else (WEEKEND if d.weekday() >= 5 else None)
            if fill is not None:
                c.setFillColor(fill); c.rect(x, top - hh - rows * rh, dw, rows * rh, stroke=0, fill=1)
        # Raster
        c.setStrokeColor(LINE); c.setLineWidth(.35)
        for r in range(rows + 1):
            y = top - hh - r * rh; c.line(x0, y, W - 12 * mm, y)
        for k in range(n + 1):
            x = x0 + namew + k * dw; c.line(x, top - hh, x, top - hh - rows * rh)
        c.line(x0, top - hh, x0, top - hh - rows * rh)
        c.setFont("Helvetica-Bold", 7); c.setFillColor(MUTED); c.drawString(x0 + 1 * mm, top - 8.5 * mm, "Name")
        for r in range(rows):
            y = top - hh - (r + 1) * rh
            c.acroForm.textfield(name=f"q{q + 1}_name_{r + 1}", tooltip=f"Name {r + 1}", x=x0 + .8 * mm, y=y + .8 * mm, width=namew - 1.6 * mm,
                                 height=rh - 1.6 * mm, borderWidth=0, fillColor=white, textColor=INK, fontName="Helvetica", fontSize=9, forceBorder=False)
        c.setFont("Helvetica", 7); c.setFillColor(INK)
        c.drawString(12 * mm, 15 * mm, "So geht's: Urlaubstage mit Stift oder Marker ankreuzen. Namen lassen sich am Computer direkt ins PDF tippen.")
        legend(c, 12 * mm, 19.5 * mm, D)
        footer(c, W, D, "Urlaubsplan fürs Team · ")
        c.showPage()
    c.save()


PRODUCTS = {
    "wandkalender-2027": lambda D, d: [wandkalender(D, d / f"wandkalender-{YEAR}-{D.slug}-A4.pdf", A4), wandkalender(D, d / f"wandkalender-{YEAR}-{D.slug}-A3.pdf", A3)],
    "familienplaner-2027": lambda D, d: [familienplaner(D, d / f"familienplaner-{YEAR}-{D.slug}-A4.pdf", A4), familienplaner(D, d / f"familienplaner-{YEAR}-{D.slug}-A3.pdf", A3)],
    "urlaubsplan-team-2027": lambda D, d: [team(D, d / f"urlaubsplan-team-{YEAR}-{D.slug}-A3.pdf")],
}

LIESMICH = """Kalenderkompass 24 – {title}

Dieser Ordner enthält die Druckvorlage für alle 25 Bundesländer (9 in Österreich, 16 in Deutschland).
Öffne den Ordner deines Bundeslandes und drucke die PDF-Datei in A4 oder A3 – am besten mit
„Tatsächliche Größe“ bzw. „100 %“.

Feiertage nach den gesetzlichen Regelungen, {stand}.
Österreich: Arbeitsruhegesetz § 7; Landespatrone sind keine gesetzlichen Feiertage.
Deutschland: Feiertagsgesetze der Länder; regionale Feiertage einzelner Gemeinden sind im Kalender vermerkt.

Nur für den privaten bzw. innerbetrieblichen Gebrauch. Weiterverkauf und Veröffentlichung nicht gestattet.
kalenderkompass24.de
"""
TITLES = {"wandkalender-2027": f"Wandkalender {YEAR}", "familienplaner-2027": f"Familienplaner {YEAR}", "urlaubsplan-team-2027": f"Urlaubsplan {YEAR} fürs Team"}


def main(target):
    target = Path(target)
    for prod, make in PRODUCTS.items():
        base = target / prod
        for country, slug, name in regions():
            D = Daten(country, slug, name)
            d = base / ("oesterreich" if country == "at" else "deutschland") / slug
            d.mkdir(parents=True, exist_ok=True)
            make(D, d)
        (base / "LIESMICH.txt").write_text(LIESMICH.format(title=TITLES[prod], stand=STAND), encoding="utf-8")
        z = target / f"kalenderkompass24-{prod}.zip"
        with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in sorted(base.rglob("*")):
                if f.is_file(): zf.write(f, f.relative_to(base))
        print(f"{prod}: {sum(1 for _ in base.rglob('*.pdf'))} PDFs, {z.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ROOT.parent / "kk24-produkte")
