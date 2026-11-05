"""Kleiner Shop für digitale Druckvorlagen (PDF). Bezahlung über einen gehosteten Checkout (Vorschlag: Lemon Squeezy
als Merchant of Record – übernimmt Umsatzsteuer/OSS und Rechnung; alternativ Stripe Payment Links).

Solange kein Produkt einen Checkout-Link hat, bleibt der Shop unsichtbar: noindex, nicht in Sitemap und Menü,
kein Link im Seitenfuß. Freigabe, Preise, Produktdateien und Rechtstexte entscheidet Johannes.

Der Checkout ist ein normaler Link zur Bezahlseite des Anbieters – auf kalenderkompass24.de wird dafür kein
fremdes Skript geladen (keine zusätzliche Einwilligung nötig).
"""

PRODUCTS = [
    {
        "slug": "wandkalender-2027",
        "title": "Wandkalender 2027 – Druckvorlage",
        "text": "Zwölf Monatsblätter und eine Jahresübersicht im Kalenderblatt-Stil: Feiertage rot, Fenster- bzw. Brückentage markiert, "
                "viel Platz zum Eintragen. Für dein Bundesland, in A4 und A3, druckfertig als PDF.",
        "format": "PDF · A4 und A3 · 13 Seiten",
        "price": "",          # Vorschlag 4,90 € – Entscheidung Johannes
        "checkout": "",       # Checkout-Link des Zahlungsanbieters, erst nach Freigabe eintragen
    },
    {
        "slug": "familienplaner-2027",
        "title": "Familienplaner 2027 – Druckvorlage",
        "text": "Monatsplaner mit bis zu fünf Spalten für Familienmitglieder, Schulferien deines Bundeslandes und Feiertagen. "
                "Zum Aufhängen an der Kühlschranktür.",
        "format": "PDF · A4 und A3 · 12 Seiten",
        "price": "",          # Vorschlag 6,90 €
        "checkout": "",
    },
    {
        "slug": "urlaubsplan-team-2027",
        "title": "Urlaubsplan 2027 fürs Team",
        "text": "Jahresübersicht für bis zu 20 Personen mit Feiertagen und Fenstertagen, damit im Team früh sichtbar ist, "
                "wer wann frei hat. Zum Ausdrucken oder als ausfüllbares PDF.",
        "format": "PDF · A3 quer · ausfüllbar",
        "price": "",          # Vorschlag 9,90 €
        "checkout": "",
    },
]

SHOP_LIVE = any(p["checkout"] and p["price"] for p in PRODUCTS)
