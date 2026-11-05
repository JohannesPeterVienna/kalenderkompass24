"""Kleiner Shop für digitale Druckvorlagen (PDF). Bezahlung über einen gehosteten Checkout (Vorschlag: Lemon Squeezy
als Merchant of Record – übernimmt Umsatzsteuer/OSS und Rechnung; alternativ Stripe Payment Links).

Solange kein Produkt einen Checkout-Link hat, gibt es den Shop nicht: shop.html wird nicht gebaut (404),
kein Link im Seitenfuß, nicht in der Sitemap. Wieder an: Checkout-Link und Preis eintragen und SHOP_FREIGEGEBEN
auf True setzen, sobald ein echter Kauf (nicht nur der Testmodus) funktioniert. Freigabe, Preise, Produktdateien und Rechtstexte entscheidet Johannes.

Der Checkout ist ein normaler Link zur Bezahlseite des Anbieters – auf kalenderkompass24.de wird dafür kein
fremdes Skript geladen (keine zusätzliche Einwilligung nötig).
"""

PRODUCTS = [
    {
        "slug": "wandkalender-2027",
        "title": "Wandkalender 2027 – Druckvorlage",
        "text": "Zwölf Monatsblätter und eine Jahresübersicht im Kalenderblatt-Stil: Feiertage rot, Fenster- bzw. Brückentage markiert, "
                "viel Platz zum Eintragen. Alle 25 Bundesländer (Österreich und Deutschland) in A4 und A3, druckfertig als PDF.",
        "format": "PDF · A4 und A3 · 13 Seiten",
        "price": "2,90 €",    # Preis festgelegt von Johannes am 5.11.2026
        "checkout": "",       # Checkout-Link des Zahlungsanbieters, erst nach Freigabe eintragen
    },
    {
        "slug": "familienplaner-2027",
        "title": "Familienplaner 2027 – Druckvorlage",
        "text": "Ein Blatt pro Monat mit fünf Spalten für Familienmitglieder, den Feiertagen deines Bundeslandes und den amtlichen "
                "Schulferien des Schuljahres 2026/2027 (bis Ende der Sommerferien). Zum Aufhängen an der Kühlschranktür.",
        "format": "PDF · A4 und A3 · 12 Seiten",
        "price": "4,90 €",
        "checkout": "",
    },
    {
        "slug": "urlaubsplan-team-2027",
        "title": "Urlaubsplan 2027 fürs Team",
        "text": "Vier Quartalsblätter für bis zu 20 Personen mit Feiertagen und Fenster- bzw. Brückentagen deines Bundeslandes, "
                "damit im Team früh sichtbar ist, wer wann frei hat. Namen lassen sich direkt ins PDF tippen.",
        "format": "PDF · A3 quer · 4 Seiten · Namen ausfüllbar",
        "price": "6,90 €",
        "checkout": "",
    },
]

# Schalter für den Shop: bleibt False, bis ein echter Kauf durchgeht (AdSense-Prüfung 5.11.2026: keine Seiten
# „In Vorbereitung“). Test-Checkout-Links allein schalten den Shop nicht frei.
SHOP_FREIGEGEBEN = False

SHOP_LIVE = SHOP_FREIGEGEBEN and any(p["checkout"] and p["price"] for p in PRODUCTS)
