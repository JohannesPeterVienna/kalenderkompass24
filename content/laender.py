"""Länderspezifische Abschnitte für die deutschen Feiertagsseiten des Hauptjahres.

Jeder Text ist eigens für sein Land geschrieben (Rechtsgrundlage, Herkunft der Landesfeiertage,
regionale Besonderheiten, Pendeln über Landesgrenzen, Ferienbezug).
Rechtsangaben geprüft im Oktober 2026 an Gesetzblättern bzw. Landesrechtsportalen; ohne Gewähr.
Datumsangaben 2027 stammen aus holidays.py bzw. ferien.py; build.py prüft sie bei jedem Build
(check_claims_de): jede Angabe „Wochentag, Tag. Monat“ gegen den Kalender, die Zahl der Feiertage
und alle hier genannten Ferienzeiträume gegen ferien.py (siehe CLAIMS_DE).
Den berechneten Teil (Urlaubsblöcke, schulfreie Urlaubstage) erzeugt build.py (de_plan_html).
Stand: 4. November 2026.
"""

# Pflichtangaben je Text – build.py prüft sie gegen holidays.py und ferien.py.
# count: (Zahlwort im Text, Anzahl gesetzlicher Feiertage 2027)
# ferien: (Name in ferien.py, erster Tag, letzter Tag) – der Text muss den letzten Tag nennen
# frei: einzelne schulfreie Tage (müssen in einem Ferienzeitraum liegen)
CLAIMS_DE = {
    "berlin": {"count": ("zehn", 10),
               "ferien": [("Osterferien", "2027-03-22", "2027-04-02"), ("Pfingstferien", "2027-05-18", "2027-05-19")],
               "frei": ["2027-05-07"]},
    "bremen": {"count": ("zehn", 10),
               "ferien": [("Osterferien", "2027-03-22", "2027-04-03"), ("Sommerferien", "2027-07-08", "2027-08-18")],
               "frei": ["2027-05-07", "2027-05-18"]},
    "hamburg": {"count": ("zehn", 10),
                "ferien": [("Frühjahrsferien", "2027-03-01", "2027-03-12"), ("Himmelfahrt-/Pfingstferien", "2027-05-07", "2027-05-14"),
                           ("Sommerferien", "2027-07-01", "2027-08-11")],
                "frei": []},
    "hessen": {"count": ("zehn", 10),
               "ferien": [("Sommerferien", "2027-06-28", "2027-08-06"), ("Osterferien", "2027-03-22", "2027-04-02")],
               "frei": []},
    "mecklenburg-vorpommern": {"count": ("elf", 11),
                               "ferien": [("Winterferien", "2027-02-08", "2027-02-19"), ("Pfingstferien", "2027-05-14", "2027-05-18"),
                                          ("Sommerferien", "2027-07-05", "2027-08-14"), ("Osterferien", "2027-03-24", "2027-04-02")],
                               "frei": ["2027-05-07"]},
    "niedersachsen": {"count": ("zehn", 10),
                      "ferien": [("Osterferien", "2027-03-22", "2027-04-03"), ("Sommerferien", "2027-07-08", "2027-08-18")],
                      "frei": ["2027-05-07", "2027-05-18"]},
    "schleswig-holstein": {"count": ("zehn", 10),
                           "ferien": [("Osterferien", "2027-03-30", "2027-04-10"), ("Sommerferien", "2027-07-03", "2027-08-14"),
                                      ("Weihnachtsferien", "2026-12-21", "2027-01-06")],
                           "frei": ["2027-05-07"]},
    "thueringen": {"count": ("elf", 11),
                   "ferien": [("Sommerferien", "2027-07-10", "2027-08-20"), ("Osterferien", "2027-03-22", "2027-04-03")],
                   "frei": ["2027-05-07"]},
}

LAND = {
"berlin": """
<p><strong>Rechtsgrundlage:</strong> Das <a href="https://gesetze.berlin.de/bsbe/document/jlr-FeiertGBErahmen" rel="noopener">Berliner Gesetz über die Sonn- und Feiertage (FTG)</a> zählt in § 1 Abs. 1 zehn gesetzliche Feiertage auf. Die <a href="https://www.berlin.de/sen/inneres/buerger-und-staat/verfassungs-und-verwaltungsrecht/artikel.1435639.php" rel="noopener">Senatsverwaltung für Inneres</a> veröffentlicht dieselbe Liste.</p>
<p><strong>Der Frauentag ist Berlins eigener Feiertag.</strong> Das Abgeordnetenhaus hat ihn Anfang 2019 als neue Nummer 2 in § 1 eingefügt (Änderungsgesetz vom 30. Januar 2019, GVBl. S. 22; Entwurf: <a href="https://www.parlament-berlin.de/ados/18/IIIPlen/vorgang/d18-1522.pdf" rel="noopener">Drucksache 18/1522</a>). Berlin war damit das erste Land mit diesem Feiertag; außer Berlin kennt ihn nur Mecklenburg-Vorpommern. 2027 ist der Frauentag Montag, der 8. März – ein langes Wochenende vom 6. bis 8. März, ohne einen Urlaubstag einzusetzen.</p>
<h3>Woher die Berliner Feiertage kommen</h3>
<p>Neun der zehn Feiertage gelten in ganz Deutschland. Die meisten sind christlichen Ursprungs: Karfreitag und Ostermontag erinnern an Tod und Auferstehung Jesu, Christi Himmelfahrt liegt 39 Tage nach dem Ostersonntag, der Pfingstmontag 50 Tage danach. Weltlich sind der 1. Mai als Tag der Arbeit und der 3. Oktober, an dem 1990 die deutsche Einheit wirksam wurde – für eine Stadt, die bis dahin durch die Mauer geteilt war, ein besonders naheliegender Feiertag.</p>
<p>Der Frauentag geht auf die sozialistische Frauenbewegung zurück. Clara Zetkin schlug 1910 auf einer internationalen Konferenz in Kopenhagen einen jährlichen Frauentag vor; der erste fand am 19. März 1911 statt, unter anderem in Deutschland und Österreich. Seit 1921 wird er am 8. März begangen.</p>
<p>Für Gedenkjubiläen hat Berlin außerdem einmalige Feiertage beschlossen: den 8. Mai 2020 zum 75. und den 8. Mai 2025 zum 80. Jahrestag des Kriegsendes (<a href="https://www.parlament-berlin.de/ados/19/IIIPlen/vorgang/d19-1359.pdf" rel="noopener">Drucksache 19/1359</a>). Solche Tage gelten nur für das jeweilige Jahr und stehen deshalb nicht in unserer Tabelle.</p>
<h3>Pendeln zwischen Berlin und Brandenburg</h3>
<p>Für Beschäftigte zählen die Feiertage am Arbeitsort, nicht am Wohnort. Brandenburg hat keinen Frauentag, dafür den Reformationstag sowie Ostersonntag und Pfingstsonntag als ausdrückliche Feiertage. Wer in Potsdam wohnt und in Berlin arbeitet, hat am 8. März frei; wer umgekehrt in Berlin wohnt und in Brandenburg arbeitet, nicht. 2027 fällt der 31. Oktober auf einen Sonntag – der Unterschied wirkt sich in diesem Jahr also nur beim Frauentag aus.</p>
<p><strong>Mit den Schulferien kombiniert:</strong> Die Berliner Osterferien (22. März bis 2. April 2027) umschließen Karfreitag und Ostermontag, und der Freitag nach Christi Himmelfahrt, der 7. Mai, ist an den Schulen ein freier Brückentag. Nach Pfingsten haben die Schulen am 18. und 19. Mai geschlossen. Alle Termine stehen bei den <a href="/schulferien-2026-2027-berlin.html">Schulferien 2026/2027 in Berlin</a>.</p>
""",

"bremen": """
<p><strong>Rechtsgrundlage:</strong> Maßgeblich ist das Bremer <em>Gesetz über die Sonn- und Feiertage</em> vom 12. November 1954. Es gilt für das ganze Land, also für Bremen und Bremerhaven gleichermaßen.</p>
<p><strong>Reformationstag seit 2018.</strong> Mit dem Änderungsgesetz vom 26. Juni 2018 hat die Bürgerschaft den Reformationstag als Buchstabe j in § 2 Abs. 1 aufgenommen (<a href="https://www.gesetzblatt.bremen.de/fastmedia/218/2018_06_28_GBl_Nr_0063_signed.pdf" rel="noopener">Brem.GBl. Nr. 63 vom 28. Juni 2018</a>); das Gesetz trat am Tag nach der Verkündung in Kraft. Die Regierungschefs von Bremen, Hamburg, Niedersachsen und Schleswig-Holstein hatten sich Anfang 2018 auf einen gemeinsamen zusätzlichen Feiertag im Norden verständigt.</p>
<h3>Was hinter dem 31. Oktober steht</h3>
<p>Der Tag erinnert an den 31. Oktober 1517, an dem Martin Luther seine 95 Thesen gegen den Ablasshandel veröffentlichte. Ob er sie tatsächlich an die Tür der Wittenberger Schlosskirche schlug, ist unter Historikern umstritten; als Beginn der Reformation gilt das Datum trotzdem. Zum 500. Jubiläum war der 31. Oktober 2017 einmalig in ganz Deutschland Feiertag. Weil der Norden im Vergleich zum Süden deutlich weniger Feiertage hatte, einigten sich die vier Nordländer danach auf ihn als dauerhaften zusätzlichen Feiertag.</p>
<p>Die übrigen neun Bremer Feiertage sind die bundesweit einheitlichen. Fronleichnam, Allerheiligen und Heilige Drei Könige sind in Bremen keine gesetzlichen Feiertage.</p>
<p><strong>2027 ist ein mageres Jahr:</strong> Von den zehn Feiertagen liegen nur fünf auf Werktagen – Neujahr, Karfreitag, Ostermontag, Christi Himmelfahrt und Pfingstmontag. Der 1. Mai, der Tag der Deutschen Einheit, der Reformationstag und beide Weihnachtstage fallen aufs Wochenende, ein Ersatztag ist im Bremer Gesetz nicht vorgesehen. Nach dem Pfingstmontag am 17. Mai folgt 2027 damit kein einziger werktäglicher Feiertag mehr.</p>
<h3>Zwischen den Jahren 2027</h3>
<p>Weil Weihnachten aufs Wochenende fällt, sind Freitag, 24. Dezember, und Freitag, 31. Dezember 2027, gewöhnliche Arbeitstage. Wer die Woche vom 27. bis 31. Dezember freinimmt, braucht fünf Urlaubstage und hat vom Samstag, 25. Dezember, bis Sonntag, 2. Januar 2028, neun Tage am Stück frei – Neujahr 2028 ist ein Samstag. Mit dem 24. Dezember dazu sind es sechs Urlaubstage für zehn freie Tage. Viele Tarifverträge stellen den 24. und 31. Dezember ganz oder teilweise frei; das ist hier nicht eingerechnet.</p>
<p><strong>Schulferien und Umland:</strong> Bremen und Niedersachsen legen ihre Ferien gemeinsam fest und haben auch dieselben zehn Feiertage – für Pendlerinnen und Pendler aus dem Umland gibt es also keine Unterschiede. 2027 liegen die Osterferien vom 22. März bis 3. April, schulfrei sind außerdem der 7. Mai und der Dienstag nach Pfingsten (18. Mai); die Sommerferien laufen vom 8. Juli bis 18. August. Details bei den <a href="/schulferien-2026-2027-bremen.html">Schulferien 2026/2027 in Bremen</a>.</p>
""",

"hamburg": """
<p><strong>Rechtsgrundlage:</strong> Das Hamburger <a href="https://www.landesrecht-hamburg.de/bsha/document/jlr-FeiertGHArahmen" rel="noopener">Feiertagsgesetz</a> zählt die gesetzlichen Feiertage in § 1 auf.</p>
<p><strong>Der 31. Oktober steht dort ohne Namen.</strong> Das Fünfte Gesetz zur Änderung des Feiertagsgesetzes vom 12. März 2018 hat als neue Nummer 8 schlicht „31. Oktober“ eingefügt (<a href="https://www.luewu.de/wp-content/uploads/2025/08/GVBL_HH_2018-9.pdf" rel="noopener">HmbGVBl. 2018 S. 63</a>). Der Antrag dazu (<a href="https://www.buergerschaft-hh.de/parldok/dokument/61406/ein_zusaetzlicher_feiertag_fuer_hamburg_den_31_oktober_als_neu_verstandenen_tag_der_reformation_im_feiertagsgesetz_verankern.pdf" rel="noopener">Drucksache 21/12153</a>) trug den Titel „Ein zusätzlicher Feiertag für Hamburg: Den 31. Oktober als neu verstandenen Tag der Reformation im Feiertagsgesetz verankern“. Dass im Gesetz nur das Datum steht, ist gewollt: Der Tag soll für alle Hamburgerinnen und Hamburger frei sein, unabhängig von der Konfession.</p>
<h3>Ein Feiertag für die ganze Metropolregion</h3>
<p>Vor 2018 hatte Hamburg nur die neun bundesweiten Feiertage. Mit dem 31. Oktober zog die Stadt im selben Jahr nach wie Schleswig-Holstein, Niedersachsen und Bremen. Für die Metropolregion ist das praktisch: Wer aus Pinneberg, Norderstedt, Stade oder Buchholz zur Arbeit nach Hamburg fährt, hat auf beiden Seiten der Landesgrenze genau dieselben zehn Feiertage. Maßgeblich wären sonst die Feiertage am Arbeitsort.</p>
<p>Fronleichnam und Allerheiligen sind in Hamburg keine gesetzlichen Feiertage, obwohl die Stadt seit 1995 Sitz eines katholischen Erzbistums ist. Katholische Gottesdienste finden an diesen Tagen statt, Beschäftigte arbeiten aber normal.</p>
<p><strong>2027 im Überblick:</strong> Fünf der zehn Feiertage liegen auf Werktagen. Der einzige klassische Brückentag ist Freitag, der 7. Mai, nach Christi Himmelfahrt. Der 1. Mai fällt auf einen Samstag, der Reformationstag auf einen Sonntag.</p>
<h3>Hamburgs Ferien folgen eigenen Regeln</h3>
<p>Statt Osterferien gibt es Frühjahrsferien vom 1. bis 12. März 2027 – Karfreitag und Ostermontag liegen also außerhalb der Ferien, und wer über Ostern mit Schulkindern verreisen will, hat nur das lange Osterwochenende. Dafür sind die Schulen vom 7. bis 14. Mai geschlossen (Himmelfahrt-/Pfingstferien). Eltern, die diese Zeit mitnehmen, brauchen sechs Urlaubstage (7. und 10. bis 14. Mai) und haben vom 6. bis zum Pfingstmontag am 17. Mai zwölf Tage am Stück frei. Die Sommerferien dauern vom 1. Juli bis 11. August. Alle Termine: <a href="/schulferien-2026-2027-hamburg.html">Schulferien 2026/2027 in Hamburg</a>.</p>
""",

"hessen": """
<p><strong>Rechtsgrundlage:</strong> Das <a href="https://www.rv.hessenrecht.hessen.de/bshe/document/jlr-FeiertGHErahmen" rel="noopener">Hessische Feiertagsgesetz (HFeiertagsG)</a> in der Fassung vom 29. Dezember 1971 nennt in § 1 Abs. 1 neben den Sonntagen zehn gesetzliche Feiertage.</p>
<p><strong>Fronleichnam ja, Allerheiligen nein.</strong> Hessen ist das einzige Land, in dem Fronleichnam landesweit gilt, Allerheiligen aber nicht – Baden-Württemberg, Bayern, Nordrhein-Westfalen, Rheinland-Pfalz und das Saarland haben beides. Einen Reformationstag kennt das hessische Gesetz ebenfalls nicht.</p>
<h3>Fronleichnam: Herkunft und Bedeutung</h3>
<p>Fronleichnam ist das katholische Fest des Leibes und Blutes Christi. Papst Urban IV. führte es 1264 für die ganze Kirche ein. Es liegt immer am Donnerstag nach dem Dreifaltigkeitssonntag, also 60 Tage nach dem Ostersonntag, und wandert deshalb mit Ostern – 2027 ist es Donnerstag, der 27. Mai. Typisch sind Prozessionen durch geschmückte Straßen; in Hessen etwa in den Bischofsstädten Fulda und Limburg und in vielen katholisch geprägten Orten. Der Name kommt vom mittelhochdeutschen „vrône lîcham“, dem Leib des Herrn.</p>
<h3>Pendeln im Rhein-Main-Gebiet</h3>
<p>Für Beschäftigte zählen die Feiertage am Arbeitsort. Im Rhein-Main-Gebiet sorgt das jedes Jahr für Unterschiede: Mainz und das übrige Rheinland-Pfalz sowie das bayerische Aschaffenburg haben Allerheiligen frei, Frankfurt, Wiesbaden und Darmstadt nicht. 2027 fällt der 1. November auf einen Montag – auf der einen Seite des Rheins ein langes Wochenende, auf der anderen ein normaler Arbeitstag. Zum Nachbarn Thüringen ist der Unterschied doppelt: Wer in Kassel arbeitet, hat an Fronleichnam frei, wer in Eisenach arbeitet, dafür am Reformationstag und am Weltkindertag.</p>
<p><strong>2027 bringt zwei Brücken im Mai.</strong> Christi Himmelfahrt am 6. Mai und Fronleichnam am 27. Mai sind Donnerstage. Mit je einem Urlaubstag am 7. und am 28. Mai entstehen zwei verlängerte Wochenenden mit vier freien Tagen. Sechs der zehn Feiertage fallen in diesem Jahr auf Werktage.</p>
<p><strong>Schulferien:</strong> Hessen startet 2027 gemeinsam mit Rheinland-Pfalz und dem Saarland früher als alle anderen Länder in den Sommer – die Ferien laufen vom 28. Juni bis 6. August. Pfingstferien und einen landesweit freien Brückentag gibt es nach den amtlichen Terminen nicht; die Osterferien dauern vom 22. März bis 2. April und umfassen damit die ganze Woche vor Ostern. Mehr bei den <a href="/schulferien-2026-2027-hessen.html">Schulferien 2026/2027 in Hessen</a>.</p>
""",

"mecklenburg-vorpommern": """
<p><strong>Rechtsgrundlage:</strong> Das <a href="https://www.landesrecht-mv.de/bsmv/document/jlr-FeiertGMVrahmen" rel="noopener">Feiertagsgesetz Mecklenburg-Vorpommern (FTG M-V)</a> vom 8. März 2002 listet in § 2 Abs. 1 elf gesetzliche Feiertage – einen mehr als die Nachbarn Schleswig-Holstein und Niedersachsen.</p>
<p><strong>Frauentag seit 2023.</strong> Das Vierte Gesetz zur Änderung des Feiertagsgesetzes vom 7. Juli 2022 hat den „Frauentag (8. März)“ als neue Nummer 2 eingefügt (<a href="https://www.dokumentation.landtag-mv.de/parldok/dokument/53736/gesetz_und_verordnungsblatt_2022_31.pdf" rel="noopener">GVOBl. M-V Nr. 31 vom 12. Juli 2022</a>). Erstmals frei war damit der 8. März 2023. Mecklenburg-Vorpommern folgte Berlin, das den Tag schon 2019 eingeführt hatte; andere Länder haben ihn bisher nicht. 2027 ist der Frauentag Montag, der 8. März, und bringt ein langes Wochenende vom 6. bis 8. März.</p>
<h3>Zwei Feiertage mit Geschichte</h3>
<p>Der 8. März wurde schon in der DDR jedes Jahr als Internationaler Frauentag begangen, mit Blumen und Feiern in den Betrieben – arbeitsfrei war er dort aber nicht.</p>
<p><strong>Reformationstag schon länger.</strong> Anders als in Hamburg, Bremen, Niedersachsen und Schleswig-Holstein ist der 31. Oktober hier kein Ergebnis der Nordländer-Einigung von 2018. Er gilt in allen ostdeutschen Flächenländern – auch in Brandenburg, Sachsen, Sachsen-Anhalt und Thüringen – und erinnert an Luthers Thesen vom 31. Oktober 1517. 2027 fällt er allerdings auf einen Sonntag, ebenso wie der Tag der Deutschen Einheit. Sechs Feiertage liegen auf Werktagen.</p>
<h3>Wer über die Landesgrenze pendelt</h3>
<p>Maßgeblich sind die Feiertage am Arbeitsort. Wer in Schwerin wohnt und in Hamburg oder Lübeck arbeitet, hat am Frauentag keinen freien Tag, weil Hamburg und Schleswig-Holstein ihn nicht kennen. Wer dagegen aus Vorpommern nach Berlin pendelt, hat ihn auch dort frei. Für Urlauberinnen und Urlauber an der Ostseeküste gilt: An Feiertagen bleiben viele Geschäfte geschlossen; Ausnahmen für Bäderorte regelt das Land eigens.</p>
<p><strong>Schulferien:</strong> Die Winterferien dauern vom 8. bis 19. Februar 2027 und enden also knapp vor dem Frauentag. Die Osterferien laufen vom 24. März bis 2. April, die Pfingstferien vom 14. bis 18. Mai verbinden sich mit dem Pfingstmontag, und am 7. Mai ist ein schulfreier Brückentag. Sommerferien: 5. Juli bis 14. August. Alle Daten bei den <a href="/schulferien-2026-2027-mecklenburg-vorpommern.html">Schulferien 2026/2027 in Mecklenburg-Vorpommern</a>.</p>
""",

"niedersachsen": """
<p><strong>Rechtsgrundlage:</strong> Das <a href="https://voris.wolterskluwer-online.de/search?query=NFeiertagsG" rel="noopener">Niedersächsische Gesetz über die Feiertage (NFeiertagsG)</a> nennt in § 2 Abs. 1 die „staatlich anerkannten Feiertage“ mit den Buchstaben a bis j – zusammen zehn.</p>
<p><strong>Vom kirchlichen zum staatlichen Feiertag.</strong> Bis 2018 war der Reformationstag in Niedersachsen nur ein kirchlicher Feiertag nach § 7. Die Landesregierung hat ihn mit dem Gesetzentwurf <a href="https://www.landtag-niedersachsen.de/Drucksachen/Drucksachen%5F18%5F02500/00501-01000/18-00827.pdf" rel="noopener">Drucksache 18/827</a> als Buchstabe h in § 2 verschoben; der Landtag stimmte im Juni 2018 zu, die Fassung gilt seit dem 29. Juni 2018.</p>
<h3>Eine umstrittene Wahl</h3>
<p>Der Reformationstag erinnert an Luthers 95 Thesen vom 31. Oktober 1517. Dass gerade er der neue Feiertag wurde, war in Niedersachsen nicht unumstritten. Im Gespräch waren auch andere Tage, und Kritik kam unter anderem von jüdischen Gemeinden, die auf Luthers judenfeindliche Schriften hinwiesen. Den Ausschlag gab die Absprache mit Bremen, Hamburg und Schleswig-Holstein, im Norden einen gemeinsamen Feiertag einzuführen.</p>
<p><strong>Fronleichnam und Allerheiligen</strong> bleiben in Niedersachsen kirchliche Feiertage ohne allgemeine Arbeitsruhe. Nach § 7 Abs. 2 gilt der besondere Schutz des Gesetzes für sie aber dort den ganzen Tag, wo sie bisher als ganztägige kirchliche Feiertage üblich waren – etwa in katholisch geprägten Gegenden wie dem Emsland. Ein allgemeiner Anspruch auf Arbeitsfreiheit folgt daraus nicht.</p>
<h3>Pendeln nach Nordrhein-Westfalen und Hessen</h3>
<p>Für Beschäftigte zählen die Feiertage am Arbeitsort. An der Grenze zu Nordrhein-Westfalen – etwa zwischen Osnabrück und Münster oder im Raum Bad Pyrmont – unterscheiden sich die Kalender deutlich: NRW hat Fronleichnam und Allerheiligen, Niedersachsen den Reformationstag. 2027 ist Fronleichnam Donnerstag, der 27. Mai, und Allerheiligen Montag, der 1. November; beide Tage sind in Niedersachsen normale Arbeitstage. Der Reformationstag fällt dagegen auf einen Sonntag, sodass Beschäftigte mit Arbeitsplatz in Niedersachsen 2027 zwei werktägliche Feiertage weniger haben als ihre Kolleginnen und Kollegen in NRW. Nach Bremen gibt es keine Unterschiede – beide Länder haben dieselben zehn Feiertage.</p>
<p><strong>2027:</strong> Nur fünf der zehn Feiertage liegen auf Werktagen. <strong>Ferien:</strong> Niedersachsen hat dieselben Termine wie Bremen – Osterferien 22. März bis 3. April, schulfrei am 7. und 18. Mai, Sommerferien 8. Juli bis 18. August. Siehe <a href="/schulferien-2026-2027-niedersachsen.html">Schulferien 2026/2027 in Niedersachsen</a>.</p>
""",

"schleswig-holstein": """
<p><strong>Rechtsgrundlage:</strong> Das <a href="https://www.gesetze-rechtsprechung.sh.juris.de/bssh/document/jlr-SoFeiertGSHrahmen" rel="noopener">Gesetz über Sonn- und Feiertage (SFTG)</a> vom 28. Juni 2004 nennt in § 2 Abs. 1 zehn Feiertage.</p>
<p><strong>Reformationstag seit 2018.</strong> Der Landtag hat den 31. Oktober im Frühjahr 2018 als neue Nummer 8 eingefügt. Der zugrunde liegende <a href="https://www.landtag.ltsh.de/infothek/wahl19/umdrucke/00600/umdruck-19-00641.pdf" rel="noopener">Änderungsantrag (Umdruck 19/641)</a> begründet das ausdrücklich mit einem gemeinsamen Feiertag der Nordländer und den vielen Pendlern in der Metropolregion Hamburg. Zugleich wurde seine bisherige Nennung in § 6 Abs. 2 gestrichen.</p>
<h3>Der Buß- und Bettag: abgeschafft, aber nicht vergessen</h3>
<p>Ab 1995 wurde der Buß- und Bettag als gesetzlicher Feiertag überall außer in Sachsen gestrichen, um die Arbeitgeber bei der Finanzierung der neuen Pflegeversicherung zu entlasten. Ganz verschwunden ist er aus dem schleswig-holsteinischen Recht nicht: Das SFTG nennt ihn eigens, Gottesdienste sind an diesem Tag geschützt, und Beschäftigte können für ihn unbezahlte Freistellung verlangen (§ 7). Er liegt immer am Mittwoch vor dem 23. November – 2027 ist das Mittwoch, der 17. November.</p>
<h3>Pendeln und Grenzlage</h3>
<p>Mit Hamburg und Niedersachsen hat Schleswig-Holstein genau dieselben zehn Feiertage. Wer aus dem Hamburger Umland in die Stadt pendelt, muss also nicht umrechnen. Anders an der Grenze zu Mecklenburg-Vorpommern: Dort ist der 8. März Feiertag, in Schleswig-Holstein nicht – entscheidend ist der Arbeitsort. Und wer in Dänemark arbeitet, richtet sich nach den dänischen Feiertagen, die sich von den deutschen unterscheiden.</p>
<p><strong>2027 und die Ferien:</strong> Fünf Feiertage fallen auf Werktage. Die Osterferien beginnen erst am Dienstag nach Ostern, dem 30. März, und dauern bis 10. April. Eltern, die die erste Ferienwoche freinehmen, kommen mit vier Urlaubstagen (30. März bis 2. April) auf zehn freie Tage vom Karfreitag, 26. März, bis Sonntag, 4. April. Winterferien gibt es nicht, die Weihnachtsferien 2026/27 reichen vom 21. Dezember bis 6. Januar. Pfingstferien gibt es ebenfalls nicht; frei ist aber der 7. Mai nach Christi Himmelfahrt. Sommer: 3. Juli bis 14. August. Mehr bei den <a href="/schulferien-2026-2027-schleswig-holstein.html">Schulferien 2026/2027 in Schleswig-Holstein</a>.</p>
""",

"thueringen": """
<p><strong>Rechtsgrundlage:</strong> Das <a href="https://landesrecht.thueringen.de/bsth/document/jlr-FeiertGTHrahmen" rel="noopener">Thüringer Feier- und Gedenktagsgesetz (ThürFGtG)</a> vom 21. Dezember 1994 regelt die Feiertage in § 2.</p>
<p><strong>Weltkindertag – nur in Thüringen.</strong> Seit 2019 (Änderungsgesetz vom 26. März 2019) ist „der 20. September als Weltkindertag“ gesetzlicher Feiertag. Kein anderes Land hat ihn. 2027 fällt er auf einen Montag, Thüringen bekommt damit vom 18. bis 20. September ein zusätzliches langes Wochenende.</p>
<h3>Woher der Weltkindertag kommt</h3>
<p>Die Generalversammlung der Vereinten Nationen empfahl 1954 allen Staaten, einen Tag für Kinder einzuführen; das Datum überließ sie den Ländern. In der Bundesrepublik wurde es der 20. September, in der DDR der Internationale Kindertag am 1. Juni. Thüringen hat sich 2019 für den 20. September entschieden. Der Feiertag soll an die Rechte von Kindern erinnern, die die UN-Kinderrechtskonvention festschreibt.</p>
<h3>Reformationstag im Land Luthers</h3>
<p>Der Reformationstag gehört zu den landesweiten Feiertagen und hat in Thüringen besonderes Gewicht: Martin Luther studierte in Erfurt und trat dort ins Augustinerkloster ein, und auf der Wartburg bei Eisenach übersetzte er 1521/22 das Neue Testament ins Deutsche. 2027 fällt der 31. Oktober allerdings auf einen Sonntag. Insgesamt hat Thüringen elf gesetzliche Feiertage, sechs davon an Werktagen.</p>
<p><strong>Fronleichnam nur regional.</strong> Nach § 2 Abs. 2 kann das zuständige Ministerium Fronleichnam per Verordnung für Gemeinden mit überwiegend katholischer Bevölkerung festlegen. Bis dahin gilt nach § 10 Abs. 1 der alte Zustand weiter: Wo Fronleichnam 1994 Feiertag war – vor allem in katholischen Orten des Eichsfelds –, bleibt er es. 2027 ist das Donnerstag, der 27. Mai. Unser Kalender zählt den Tag nicht mit, weil er nicht landesweit gilt.</p>
<p><strong>Pendeln:</strong> Maßgeblich sind die Feiertage am Arbeitsort. Nach Hessen und Bayern pendelt man in Länder ohne Reformationstag und ohne Weltkindertag, dafür mit Fronleichnam. Sachsen und Sachsen-Anhalt haben den Reformationstag, den Weltkindertag aber nicht.</p>
<p><strong>Ferien:</strong> Thüringen geht gemeinsam mit Sachsen und Sachsen-Anhalt am 10. Juli in die Sommerferien (bis 20. August 2027); später starten nur Nordrhein-Westfalen, Baden-Württemberg und Bayern. Osterferien: 22. März bis 3. April, schulfrei auch am 7. Mai. Alle Termine bei den <a href="/schulferien-2026-2027-thueringen.html">Schulferien 2026/2027 in Thüringen</a>.</p>
""",
}
