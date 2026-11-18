"""Feiertags-Rechenlogik gegen amtliche Quellen – python3 -m unittest tests/test_feiertage_amtlich.py

Was hier „amtlich“ heißt (alle am 18.11.2026 abgerufen und vollständig gelesen):
- Osterdaten 1980–2031: Osterfesttabelle der Physikalisch-Technischen Bundesanstalt (PTB), „Wann ist Ostern?“,
  https://www.ptb.de/cms/ptb/fachabteilungen/abt4/fb-44/ag-441/darstellung-der-gesetzlichen-zeit/wann-ist-ostern.html
  Dieselbe Seite nennt die Abstände: Ostersonntag + 39 = Christi Himmelfahrt, + 49 = Pfingstsonntag, + 60 = Fronleichnam.
- Österreich: § 7 Abs. 2 Arbeitsruhegesetz (RIS, https://www.ris.bka.gv.at/eli/bgbl/1983/144/P7/NOR40213419) – 13 Feiertage.
- Bayern: Art. 1 Feiertagsgesetz (https://www.gesetze-bayern.de/Content/Document/BayFTG).
- Berlin: Senatsverwaltung für Inneres und Sport, „Sonn- und Feiertagsrecht“
  (https://www.berlin.de/sen/inneres/buerger-und-staat/verfassungs-und-verwaltungsrecht/artikel.1435639.php).

Die Gesetze nennen Feiertage, keine Kalenderdaten. Die erwarteten Daten unten sind deshalb von Hand aus dem
PTB-Osterdatum und den festen Tagen der Gesetze abgeleitet und als Datum ausgeschrieben.
Die übrigen 14 deutschen Länder sind am Ende nur als Regressionsschutz erfasst (Zahl der Feiertage 2027);
ihre Landesgesetze waren am 18.11.2026 aus dieser Umgebung nicht abrufbar und wurden an diesem Tag nicht neu gelesen.
"""
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import holidays as H  # noqa: E402

# PTB-Osterfesttabelle, wörtlich übernommen (Jahr: "TT.MM.")
PTB = """1980 06.04. 1981 19.04. 1982 11.04. 1983 03.04. 1984 22.04. 1985 07.04. 1986 30.03. 1987 19.04. 1988 03.04.
1989 26.03. 1990 15.04. 1991 31.03. 1992 19.04. 1993 11.04. 1994 03.04. 1995 16.04. 1996 07.04. 1997 30.03.
1998 12.04. 1999 04.04. 2000 23.04. 2001 15.04. 2002 31.03. 2003 20.04. 2004 11.04. 2005 27.03. 2006 16.04.
2007 08.04. 2008 23.03. 2009 12.04. 2010 04.04. 2011 24.04. 2012 08.04. 2013 31.03. 2014 20.04. 2015 05.04.
2016 27.03. 2017 16.04. 2018 01.04. 2019 21.04. 2020 12.04. 2021 04.04. 2022 17.04. 2023 09.04. 2024 31.03.
2025 20.04. 2026 05.04. 2027 28.03. 2028 16.04. 2029 01.04. 2030 21.04. 2031 13.04.""".split()
PTB_OSTERN = {int(PTB[i]): date(int(PTB[i]), int(PTB[i + 1][3:5]), int(PTB[i + 1][0:2])) for i in range(0, len(PTB), 2)}


def D(s):
    return date.fromisoformat(s)


# § 7 Abs. 2 ARG, als Kalenderdaten ausgeschrieben
AT = {
    2026: ["2026-01-01", "2026-01-06", "2026-04-06", "2026-05-01", "2026-05-14", "2026-05-25", "2026-06-04",
           "2026-08-15", "2026-10-26", "2026-11-01", "2026-12-08", "2026-12-25", "2026-12-26"],
    2027: ["2027-01-01", "2027-01-06", "2027-03-29", "2027-05-01", "2027-05-06", "2027-05-17", "2027-05-27",
           "2027-08-15", "2027-10-26", "2027-11-01", "2027-12-08", "2027-12-25", "2027-12-26"],
    2028: ["2028-01-01", "2028-01-06", "2028-04-17", "2028-05-01", "2028-05-25", "2028-06-05", "2028-06-15",
           "2028-08-15", "2028-10-26", "2028-11-01", "2028-12-08", "2028-12-25", "2028-12-26"],
}
# Art. 1 Abs. 1 BayFTG: Nr. 1 im ganzen Staatsgebiet (12 Tage), Nr. 2 Mariä Himmelfahrt in überwiegend katholischen Gemeinden
BY = {
    2027: ["2027-01-01", "2027-01-06", "2027-03-26", "2027-03-29", "2027-05-01", "2027-05-06", "2027-05-17", "2027-05-27",
           "2027-08-15", "2027-10-03", "2027-11-01", "2027-12-25", "2027-12-26"],
    2028: ["2028-01-01", "2028-01-06", "2028-04-14", "2028-04-17", "2028-05-01", "2028-05-25", "2028-06-05", "2028-06-15",
           "2028-08-15", "2028-10-03", "2028-11-01", "2028-12-25", "2028-12-26"],
}
# Berlin: Neujahr, Frauentag, Karfreitag, Ostermontag, 1. Mai, Himmelfahrt, Pfingstmontag, 3. Oktober, 1. und 2. Weihnachtstag
BE = {
    2027: ["2027-01-01", "2027-03-08", "2027-03-26", "2027-03-29", "2027-05-01", "2027-05-06", "2027-05-17",
           "2027-10-03", "2027-12-25", "2027-12-26"],
    2028: ["2028-01-01", "2028-03-08", "2028-04-14", "2028-04-17", "2028-05-01", "2028-05-25", "2028-06-05",
           "2028-10-03", "2028-12-25", "2028-12-26"],
}


class Ostern(unittest.TestCase):
    def test_tabelle_vollstaendig(self):
        self.assertEqual(sorted(PTB_OSTERN), list(range(1980, 2032)))
        self.assertTrue(all(d.weekday() == 6 for d in PTB_OSTERN.values()), "jeder Ostertermin ist ein Sonntag")

    def test_osterformel_gegen_ptb(self):
        for jahr, erwartet in PTB_OSTERN.items():
            self.assertEqual(H.easter(jahr), erwartet, jahr)

    def test_bewegliche_feiertage_abstaende_laut_ptb(self):
        for jahr, os_ in PTB_OSTERN.items():
            at = {n: d for d, n in H.at_holidays(jahr)}
            self.assertEqual(at["Christi Himmelfahrt"], os_ + timedelta(39), jahr)
            self.assertEqual(at["Pfingstmontag"], os_ + timedelta(49 + 1), jahr)
            self.assertEqual(at["Fronleichnam"], os_ + timedelta(60), jahr)
            self.assertEqual(at["Ostermontag"], os_ + timedelta(1), jahr)
            self.assertEqual(at["Christi Himmelfahrt"].weekday(), 3)
            self.assertEqual(at["Fronleichnam"].weekday(), 3)


class Oesterreich(unittest.TestCase):
    def test_dreizehn_feiertage_nach_arg(self):
        for jahr, erwartet in AT.items():
            self.assertEqual(sorted(d for d, _ in H.at_holidays(jahr)), sorted(map(D, erwartet)), jahr)
            for region in [""] + list(H.AT_REGIONS):
                self.assertEqual(sorted(H.off_days("at", region, jahr)), sorted(map(D, erwartet)), (jahr, region))

    def test_karfreitag_und_landespatrone_sind_keine_gesetzlichen_feiertage(self):
        for jahr in AT:
            self.assertNotIn(PTB_OSTERN[jahr] - timedelta(2), H.off_days("at", "wien", jahr))
        self.assertNotIn(date(2027, 11, 15), H.off_days("at", "wien", 2027))
        patrone = [h for h in H.region_holidays("at", "wien", 2027) if h["kind"] == "patron"]
        self.assertEqual([h["date"] for h in patrone], [date(2027, 11, 15)])


class Deutschland(unittest.TestCase):
    def test_bayern_nach_feiertagsgesetz(self):
        for jahr, erwartet in BY.items():
            self.assertEqual(sorted(H.off_days("de", "bayern", jahr)), sorted(map(D, erwartet)), jahr)
            himmelfahrt = [h for h in H.region_holidays("de", "bayern", jahr) if h["name"] == "Mariä Himmelfahrt"][0]
            self.assertIn("überwiegend katholischer Bevölkerung", himmelfahrt["note"])
            self.assertNotIn(date(jahr, 8, 8), H.off_days("de", "bayern", jahr), "Augsburger Friedensfest gilt nur in Augsburg")

    def test_berlin_nach_senatsverwaltung(self):
        for jahr, erwartet in BE.items():
            self.assertEqual(sorted(H.off_days("de", "berlin", jahr)), sorted(map(D, erwartet)), jahr)

    def test_karfreitag_ueberall_und_zwei_tage_vor_ostern(self):
        for jahr in (2026, 2027, 2028, 2029, 2030):
            for slug in H.DE_REGIONS:
                self.assertIn(PTB_OSTERN[jahr] - timedelta(2), H.off_days("de", slug, jahr), (jahr, slug))

    def test_regressionsschutz_anzahl_je_land_2027(self):
        # Kein amtlicher Abgleich: hält nur den am 18.11.2026 vorgefundenen Stand fest.
        erwartet = {"baden-wuerttemberg": 12, "bayern": 13, "berlin": 10, "brandenburg": 12, "bremen": 10, "hamburg": 10,
                    "hessen": 10, "mecklenburg-vorpommern": 11, "niedersachsen": 10, "nordrhein-westfalen": 11,
                    "rheinland-pfalz": 11, "saarland": 12, "sachsen": 11, "sachsen-anhalt": 11, "schleswig-holstein": 10,
                    "thueringen": 11}
        self.assertEqual({s: len(H.off_days("de", s, 2027)) for s in H.DE_REGIONS}, erwartet)


class Brueckentage(unittest.TestCase):
    def test_fenstertage_2027_oesterreich(self):
        einzel = sorted(b["days"][0] for b in H.bridge_days("at", "wien", 2027) if b["vacation"] == 1)
        # Do 6.5. (Christi Himmelfahrt), Do 27.5. (Fronleichnam), Di 26.10. (Nationalfeiertag) – Daten siehe AT[2027]
        self.assertEqual(einzel, [date(2027, 5, 7), date(2027, 5, 28), date(2027, 10, 25)])
        for b in H.bridge_days("at", "wien", 2027):
            frei = H.off_days("at", "wien", 2027) | H.off_days("at", "wien", 2028) | H.off_days("at", "wien", 2026)
            tage = [b["start"] + timedelta(i) for i in range(b["free"])]
            self.assertEqual(sum(1 for t in tage if H.is_workday(t, frei)), b["vacation"])


if __name__ == "__main__":
    unittest.main()
