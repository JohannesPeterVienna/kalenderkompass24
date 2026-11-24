"""Was die Feiertagsgesetze einzelner Länder regeln – nur Angaben aus dem amtlichen Gesetzestext.

Jeder Eintrag ist am 24. November 2026 am verlinkten amtlichen Landesrechtsportal gelesen worden
(BAYERN.RECHT, BRAVORS, RECHT.NRW.DE, REVOSax). Baden-Württemberg, Rheinland-Pfalz, Saarland und
Sachsen-Anhalt fehlen, weil ihre Landesrechtsportale an diesem Tag aus der Arbeitsumgebung nicht
erreichbar waren; ergänzt wird erst, wenn der Wortlaut dort gelesen ist.
"""

ABRUF = "24. November 2026"

# slug: (Kurzname des Gesetzes, amtliche Fundstelle, Link, Text)
GESETZE_DE = {
    "bayern": (
        "Feiertagsgesetz (FTG)",
        "Gesetz über den Schutz der Sonn- und Feiertage vom 21. Mai 1980, BayRS 1131-3-I",
        "https://www.gesetze-bayern.de/Content/Document/BayFTG/true",
        """<p>Art. 1 Abs. 1 nennt zwölf Feiertage, die im ganzen Staatsgebiet gelten, und dazu Mariä Himmelfahrt „in Gemeinden mit überwiegend katholischer Bevölkerung“. Welche Gemeinden das sind, stellt das Landesamt für Statistik nach dem Ergebnis der letzten Volkszählung fest; die Gemeinde macht es ortsüblich bekannt (Art. 1 Abs. 3). In der Stadt Augsburg ist außerdem der 8. August (Friedensfest) gesetzlicher Feiertag (Art. 1 Abs. 2).</p>
<p><strong>Stille Tage</strong> sind nach Art. 3 Aschermittwoch, Gründonnerstag, Karfreitag, Karsamstag, Allerheiligen, der Volkstrauertag, der Totensonntag, der Buß- und Bettag und der Heilige Abend. Der Schutz beginnt um 2 Uhr, am Karfreitag und Karsamstag um 0 Uhr und am Heiligen Abend um 14 Uhr. Öffentliche Unterhaltungsveranstaltungen sind dann nur erlaubt, wenn der ernste Charakter des Tages gewahrt ist; Sportveranstaltungen sind erlaubt, außer am Karfreitag und am Buß- und Bettag. Am Karfreitag sind in Räumen mit Schankbetrieb musikalische Darbietungen jeder Art verboten.</p>
<p>Wo Mariä Himmelfahrt kein gesetzlicher Feiertag ist, und am Buß- und Bettag haben Beschäftigte, die dem jeweiligen Bekenntnis angehören, nach Art. 4 das Recht, von der Arbeit fernzubleiben – ausgenommen Arbeiten, die auch an Feiertagen erlaubt sind oder für den Betrieb oder unaufschiebbare Behördengeschäfte nötig sind.</p>"""),
    "brandenburg": (
        "Feiertagsgesetz Brandenburg (FTG)",
        "Gesetz über die Sonn- und Feiertage vom 21. März 1991 (GVBl. I/91, Nr. 6, S. 44), zuletzt geändert durch Gesetz vom 30. April 2015 (GVBl. I/15, Nr. 13)",
        "https://bravors.brandenburg.de/gesetze/ftg_2015",
        """<p>§ 2 Abs. 1 zählt zwölf gesetzlich anerkannte Feiertage auf – neben den neun bundesweiten den Ostersonntag, den Pfingstsonntag und das Reformationsfest am 31. Oktober. Gedenk- und Trauertage sind nach § 2 Abs. 2 der Volkstrauertag, der Totensonntag und der 8. Mai als Tag der Befreiung vom Nationalsozialismus und der Beendigung des Zweiten Weltkrieges in Europa; der 8. Mai gehört damit nicht zu den gesetzlich anerkannten Feiertagen nach Absatz 1.</p>
<p><strong>Tanzverbote:</strong> Öffentliche Tanzveranstaltungen und Veranstaltungen in Räumen mit Schankbetrieb, die über den Schank- und Speisebetrieb hinausgehen, sind nach § 6 Abs. 2 am Karfreitag von 0 Uhr bis Karsamstag 4 Uhr verboten, am Volkstrauertag und am Totensonntag von 4 bis 24 Uhr und am Heiligen Abend von 13 bis 24 Uhr. An religiösen Feiertagen, die nicht gesetzlich anerkannt sind, muss der Arbeitgeber Angehörigen der Kirche oder Religionsgemeinschaft Gelegenheit zum Gottesdienstbesuch geben, wenn keine unaufschiebbaren Aufgaben oder zwingenden betrieblichen Gründe entgegenstehen (§ 7).</p>"""),
    "nordrhein-westfalen": (
        "Feiertagsgesetz NW",
        "Gesetz über die Sonn- und Feiertage in der Fassung der Bekanntmachung vom 23. April 1989 (GV. NW. S. 222), geändert durch Gesetze vom 17. April 1991 (GV. NW. S. 200) und 20. Dezember 1994 (GV. NW. S. 1114)",
        "https://recht.nrw.de/lrgv/gesetz/01012000-bekanntmachung-der-neufassung-des-gesetzes-ueber-die-sonn-und-feiertage/",
        """<p>§ 2 Abs. 1 nennt elf Feiertage; zusätzlich zu den neun bundesweiten sind das der Fronleichnamstag („Donnerstag nach dem Sonntag Trinitatis“) und der Allerheiligentag. Den 1. Mai bezeichnet das Gesetz als „Tag des Bekenntnisses zu Freiheit und Frieden, sozialer Gerechtigkeit, Völkerversöhnung und Menschenwürde“. Gedenk- und Trauertage sind der Volkstrauertag und der Totensonntag (§ 2 Abs. 2).</p>
<p><strong>Stille Feiertage</strong> (§ 6): Am Volkstrauertag sind unter anderem Märkte, Sportveranstaltungen und der Betrieb von Spielhallen von 5 bis 13 Uhr verboten, Musik und Unterhaltung in Gaststätten sowie Tanz von 5 bis 18 Uhr. An Allerheiligen und am Totensonntag gilt das Verbot für alle diese Veranstaltungen von 5 bis 18 Uhr, am Karfreitag bis 6 Uhr des folgenden Tages; dann sind auch nicht öffentliche unterhaltende Veranstaltungen außerhalb von Wohnungen verboten.</p>"""),
    "sachsen": (
        "Sonn- und Feiertagsgesetz (SächsSFG)",
        "Gesetz über Sonn- und Feiertage im Freistaat Sachsen vom 10. November 1992 (SächsGVBl. S. 536), zuletzt geändert durch Gesetz vom 23. April 2025 (SächsGVBl. S. 146)",
        "https://www.revosax.sachsen.de/vorschrift/3997-SaechsSFG",
        """<p>§ 1 zählt die gesetzlichen Feiertage auf, darunter das Reformationsfest und den Buß- und Bettag. Fronleichnam ist nur in den Regionen gesetzlicher Feiertag, die das Staatsministerium des Innern durch Rechtsverordnung bestimmt. Gedenk- und Trauertage sind der Volkstrauertag, der Totensonntag und – seit der Änderung von 2025 – der 8. Mai als Tag der Befreiung vom Nationalsozialismus und der Beendigung des Zweiten Weltkriegs in Europa (§ 2). Gemeinden können durch Satzung einen örtlichen Gedenktag an die friedliche Revolution 1989 bestimmen (§ 2a).</p>
<p><strong>Religiöse Feiertage</strong> nach § 3 sind unter anderem das Erscheinungsfest (6. Januar), Gründonnerstag, Fronleichnam (soweit nicht gesetzlicher Feiertag), Mariä Himmelfahrt und Allerheiligen. An ihnen dürfen Schülerinnen, Schüler und Auszubildende dem Unterricht fernbleiben, Beschäftigte der Arbeit, wenn keine zwingenden betrieblichen Erfordernisse entgegenstehen – jeweils soweit es für den Hauptgottesdienst ihrer Religionsgemeinschaft nötig ist. Am Karfreitag, am Buß- und Bettag, am Volkstrauertag und am Totensonntag sind öffentliche Tanzveranstaltungen und Vergnügungen verboten, die dem ernsten Charakter dieser Tage zuwiderlaufen – am Karfreitag den ganzen Tag, sonst von 3 bis 24 Uhr; öffentliche Sportveranstaltungen am Karfreitag ganztägig, an den anderen Tagen bis 11 Uhr (§ 6).</p>"""),
}


def gesetz_html(slug):
    g = GESETZE_DE.get(slug)
    if not g: return ""
    kurz, fund, url, text = g
    return (f'<h4>Was das {kurz} regelt</h4>{text}'
            f'<p class="small muted">Quelle: <a href="{url}" rel="noopener">{fund}</a>, amtliche Fassung, abgerufen am {ABRUF}.</p>')
