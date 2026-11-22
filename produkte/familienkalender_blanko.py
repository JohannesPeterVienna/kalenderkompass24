"""Erzeugt die kostenlose, regionsunabhängige A4-Vorlage mit sechs Schreibspalten."""
from calendar import monthrange
from datetime import date
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas

MONTHS = ("Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
          "September", "Oktober", "November", "Dezember")
WEEKDAYS = ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")
INK, ACCENT, GRID, WEEKEND = map(HexColor, ("#202124", "#AE1831", "#929699", "#EEEEED"))


def build_sample(year, month, target):
    width, height = A4
    margin = 11 * mm
    right = width - margin
    day_edge = margin + 15 * mm
    column = (right - day_edge) / 6
    grid_top = height - 30 * mm
    header_bottom = grid_top - 12 * mm
    sheet = Canvas(str(target), pagesize=A4, pageCompression=1, invariant=1)
    sheet.setTitle(f"Familienkalender {year} mit 6 Spalten")
    sheet.setAuthor("Kalenderkompass 24")
    name = MONTHS[month - 1]
    days = monthrange(year, month)[1]
    row = (header_bottom - 20 * mm) / days
    sheet.setFillColor(ACCENT)
    sheet.setFont("Helvetica-Bold", 9)
    sheet.drawString(margin, height - 13 * mm, "FAMILIENKALENDER")
    sheet.setFillColor(INK)
    sheet.setFont("Times-Bold", 26)
    sheet.drawString(margin, height - 24 * mm, f"{name} {year}")
    sheet.setFont("Helvetica", 9)
    sheet.drawRightString(right, height - 23 * mm, "6 Spalten zum Selbsteintragen")
    sheet.setFont("Helvetica", 7)
    sheet.drawString(margin + 2 * mm, grid_top - 8 * mm, "Datum")
    for index in range(6):
        sheet.drawString(day_edge + index * column + 2 * mm, grid_top - 3.8 * mm, "Name / Bereich")
    for day in range(1, days + 1):
        weekday = date(year, month, day).weekday()
        bottom = header_bottom - day * row
        if weekday >= 5:
            sheet.setFillColor(WEEKEND)
            sheet.rect(margin, bottom, right - margin, row, stroke=0, fill=1)
        sheet.setFillColor(INK)
        sheet.setFont("Helvetica-Bold" if weekday >= 5 else "Helvetica", 9)
        sheet.drawString(margin + 1.8 * mm, bottom + row / 2 - 3, f"{WEEKDAYS[weekday]} {day:02d}")
    sheet.setStrokeColor(GRID)
    sheet.setLineWidth(.45)
    for index in range(days + 1):
        y = header_bottom - row * index
        sheet.line(margin, y, right, y)
    sheet.line(margin, grid_top, right, grid_top)
    for x in [margin] + [day_edge + i * column for i in range(7)]:
        sheet.line(x, grid_top, x, header_bottom - days * row)
    sheet.setFillColor(INK)
    sheet.setFont("Helvetica", 8)
    sheet.drawString(margin, 14 * mm, "Samstag und Sonntag sind grau hinterlegt.")
    sheet.drawString(margin, 9.5 * mm, "kalenderkompass24.de/familienplaner.html")
    sheet.drawRightString(right, 9.5 * mm, "Musterblatt")
    sheet.showPage()
    sheet.save()


if __name__ == "__main__":
    build_sample(2027, 1, Path(__file__).resolve().parents[1] / "assets/familienkalender-januar-2027-6-spalten.pdf")
