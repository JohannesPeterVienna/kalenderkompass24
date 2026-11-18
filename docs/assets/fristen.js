/* Kalenderkompass 24 – Fristenrechner. Rechnet im Browser; nichts wird übertragen.
   Die Rechenfunktionen (oben) laufen auch unter Node für die Tests (tests/fristen.test.js). */
(function (root) {
  "use strict";
  var ISO = /^\d{4}-\d{2}-\d{2}$/;
  var EINHEITEN = { tage: ["Tag", "Tage"], wochen: ["Woche", "Wochen"], monate: ["Monat", "Monate"], jahre: ["Jahr", "Jahre"] };
  var WT = ["Sonntag", "Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag"];
  var MON = ["Jänner", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"];
  var SPRACHE = "at";   // "de": Januar statt Jänner
  var MIN_JAHR = 2026, MAX_JAHR = 2030;   // Feiertagsdaten liegen für diese Jahre vor

  /* Datum als UTC-Mitternacht: keine Sommerzeit-Sprünge beim Tagezählen. */
  function parse(s) {
    if (typeof s !== "string" || !ISO.test(s)) return null;
    var p = s.split("-").map(Number), d = new Date(Date.UTC(p[0], p[1] - 1, p[2]));
    return (d.getUTCFullYear() === p[0] && d.getUTCMonth() === p[1] - 1 && d.getUTCDate() === p[2]) ? d : null;
  }
  function iso(d) { return d.toISOString().slice(0, 10); }
  function plus(d, n) { return new Date(d.getTime() + n * 864e5); }
  function monatsletzter(y, m) { return new Date(Date.UTC(y, m + 1, 0)).getUTCDate(); }

  /* Ostersonntag (gregorianisch) – geprüft gegen die Osterfesttabelle der PTB 1980–2031. */
  function ostern(jahr) {
    var a = jahr % 19, b = Math.floor(jahr / 100), c = jahr % 100, d = Math.floor(b / 4), e = b % 4,
      f = Math.floor((b + 8) / 25), g = Math.floor((b - f + 1) / 3), h = (19 * a + b - d - g + 15) % 30,
      i = Math.floor(c / 4), k = c % 4, l = (32 + 2 * e + 2 * i - h - k) % 7, m = Math.floor((a + 11 * h + 22 * l) / 451),
      x = h + l - 7 * m + 114;
    return new Date(Date.UTC(jahr, Math.floor(x / 31) - 1, (x % 31) + 1));
  }
  function karfreitag(jahr) { return plus(ostern(jahr), -2); }

  /* Tag, der „nach seiner Zahl“ dem Ausgangstag n Monate später entspricht; fehlt er, der Monatsletzte. */
  function monateWeiter(d, n) {
    var y = d.getUTCFullYear(), m = d.getUTCMonth() + n, tag = d.getUTCDate();
    y += Math.floor(m / 12); m = ((m % 12) + 12) % 12;
    var letzter = monatsletzter(y, m);
    return { datum: new Date(Date.UTC(y, m, Math.min(tag, letzter))), fehlt: tag > letzter };
  }

  /* Rechnerisches Fristende ohne Verschiebung.
     modus "ereignis": Der Tag des Ereignisses zählt nicht mit (§ 902 Abs. 1 ABGB, § 187 Abs. 1 BGB).
     modus "tagesbeginn": Der erste Tag zählt mit (§ 187 Abs. 2, § 188 Abs. 2 zweite Alternative BGB). */
  function rohEnde(start, n, einheit, modus) {
    var tb = modus === "tagesbeginn";
    if (einheit === "tage") return { datum: plus(start, tb ? n - 1 : n), fehlt: false };
    if (einheit === "wochen") return { datum: plus(start, 7 * n - (tb ? 1 : 0)), fehlt: false };
    var r = monateWeiter(start, einheit === "jahre" ? 12 * n : n);
    if (tb && !r.fehlt) r.datum = plus(r.datum, -1);
    return r;
  }

  /* Warum verschiebt dieser Tag das Fristende? Rückgabe: Text oder "". */
  function grund(d, regel, feiertage) {
    var w = d.getUTCDay(), s = iso(d);
    if (w === 6 && regel.sa) return "Samstag";
    if (w === 0 && regel.so) return "Sonntag";
    if (regel.ft && feiertage[s]) return "gesetzlicher Feiertag (" + feiertage[s].name + ")";
    if (regel.kf && s === iso(karfreitag(d.getUTCFullYear()))) return "Karfreitag";
    if (regel.d24 && d.getUTCMonth() === 11 && d.getUTCDate() === 24) return "24. Dezember";
    return "";
  }

  /* feiertage: { "2027-05-27": { name, note } } – nur gesetzliche Feiertage der gewählten Region. */
  function berechne(e, regel, feiertage) {
    var start = parse(e.start), n = Number(e.n);
    if (!start) return { fehler: "Bitte ein gültiges Datum für den Fristbeginn eingeben." };
    if (!Number.isInteger(n) || n < 1 || n > 999) return { fehler: "Die Länge der Frist muss eine ganze Zahl von 1 bis 999 sein." };
    if (!EINHEITEN[e.einheit]) return { fehler: "Unbekannte Einheit." };
    if (!regel) return { fehler: "Unbekannte Vorschrift." };
    var modus = e.modus === "tagesbeginn" && regel.tagesbeginn ? "tagesbeginn" : "ereignis";
    var roh = rohEnde(start, n, e.einheit, modus);
    // bis 20. Dezember des letzten Jahres: so bleibt jede Verschiebung innerhalb der vorhandenen Feiertagsdaten
    if (start.getUTCFullYear() < MIN_JAHR || iso(roh.datum) > MAX_JAHR + "-12-20")
      return { fehler: "Der Rechner hat Feiertagsdaten für Fristen, die frühestens am 1.1." + MIN_JAHR + " beginnen und spätestens am 20.12." + MAX_JAHR + " enden." };
    var ende = roh.datum, schritte = [], g, bedingt = false;
    while ((g = grund(ende, regel, feiertage))) {
      // Notiz nur, wenn wirklich der Feiertag verschiebt (nicht, wenn der Tag ohnehin Samstag oder Sonntag ist)
      var note = g.indexOf("gesetzlicher Feiertag") === 0 ? (feiertage[iso(ende)] || {}).note || "" : "";
      if (note) bedingt = true;
      schritte.push({ datum: iso(ende), grund: g, note: note });
      ende = plus(ende, 1);
    }
    // Feiertag, der nur in einem Teil des Landes gilt: zweites Ergebnis für Orte, an denen er kein Feiertag ist
    var alternativ = "";
    if (bedingt) {
      var ohne = {}, x = roh.datum;
      Object.keys(feiertage).forEach(function (k) { if (!feiertage[k].note) ohne[k] = feiertage[k]; });
      while (grund(x, regel, ohne)) x = plus(x, 1);
      if (iso(x) !== iso(ende)) alternativ = iso(x);
    }
    return { start: iso(start), roh: iso(roh.datum), fehlt: roh.fehlt, ende: iso(ende), alternativ: alternativ, schritte: schritte, modus: modus,
      n: n, einheit: e.einheit, kalendertage: Math.round((ende - start) / 864e5) };
  }

  function lang(s, mitWt) {
    var d = parse(s), m = SPRACHE === "de" && d.getUTCMonth() === 0 ? "Januar" : MON[d.getUTCMonth()];
    return (mitWt === false ? "" : WT[d.getUTCDay()] + ", ") + d.getUTCDate() + ". " + m + " " + d.getUTCFullYear();
  }
  function sprache(land) { SPRACHE = land === "de" ? "de" : "at"; }
  function dauer(n, einheit) { return n + " " + EINHEITEN[einheit][n === 1 ? 0 : 1]; }

  /* Hinweise, die über die reine Rechnung hinausgehen. regionaleTage: { iso: Text } für Feiertage, die nur in Teilen des Landes gelten. */
  function hinweise(r, regel, e, feiertage, regionaleTage) {
    var out = [];
    if (r.fehlt) out.push("Der entsprechende Tag fehlt im letzten Monat; die Frist endet deshalb am Monatsletzten.");
    if (!regel.d24 && r.ende.slice(5) === "12-24") out.push("Der 24. Dezember ist kein gesetzlicher Feiertag und in dieser Vorschrift nicht genannt; die Frist endet an diesem Tag.");
    r.schritte.forEach(function (s) {
      if (s.note) out.push(lang(s.datum, false) + ": " + s.note + "." + (r.alternativ ? " Wo der Tag kein Feiertag ist, ist " + lang(r.alternativ) + " der letzte Tag der Frist." : ""));
    });
    [r.roh, r.ende].forEach(function (s, i) {
      if (regionaleTage && regionaleTage[s] && !feiertage[s] && (i === 0 || s !== r.roh)) out.push(lang(s, false) + ": " + regionaleTage[s]);
    });
    if (regel.land === "de" && !e.region) out.push("Ohne Bundesland rechnet der Rechner nur mit den neun bundesweiten Feiertagen. Wähle das Land des Erklärungs-, Leistungs- oder Gerichtsorts.");
    return out;
  }

  /* Tage, die nur in Teilen eines Landes Feiertag sind (nicht in den Daten enthalten). */
  function regionaleTage(land, region, jahre) {
    var out = {};
    jahre.forEach(function (y) {
      var fl = iso(plus(ostern(y), 60));
      if (land === "de" && region === "sachsen") out[fl] = "Fronleichnam ist in einigen überwiegend katholischen Gemeinden der Oberlausitz gesetzlicher Feiertag; dort verschiebt sich das Fristende.";
      if (land === "de" && region === "thueringen") out[fl] = "Fronleichnam ist in Teilen des Eichsfelds gesetzlicher Feiertag; dort verschiebt sich das Fristende.";
      if (land === "de" && region === "bayern") out[y + "-08-08"] = "Der 8. August (Friedensfest) ist nur in der Stadt Augsburg gesetzlicher Feiertag (Art. 1 Abs. 2 BayFTG); dort verschiebt sich das Fristende.";
    });
    return out;
  }

  var API = { parse: parse, iso: iso, plus: plus, ostern: ostern, karfreitag: karfreitag, monateWeiter: monateWeiter, rohEnde: rohEnde,
    grund: grund, berechne: berechne, hinweise: hinweise, regionaleTage: regionaleTage, lang: lang, sprache: sprache, dauer: dauer, MIN_JAHR: MIN_JAHR, MAX_JAHR: MAX_JAHR };
  if (typeof module !== "undefined" && module.exports) { module.exports = API; return; }
  root.KKFristen = API;

  /* ------------------------------------------------------------------ Oberfläche */
  var doc = root.document, box = doc.querySelector("[data-fristen]");
  var esc = function (s) { return String(s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); };
  function filterTabelle() {
    var t = doc.querySelector("[data-fr-tabelle]"); if (!t) return;
    var q = doc.querySelector("[data-fr-suche]"), l = doc.querySelector("[data-fr-land]"), zahl = doc.querySelector("[data-fr-zahl]");
    function lauf() {
      var w = (q.value || "").toLowerCase().trim(), land = l.value, n = 0;
      t.querySelectorAll("tbody tr").forEach(function (tr) {
        var ok = (!land || tr.dataset.land === land) && (!w || tr.textContent.toLowerCase().indexOf(w) >= 0);
        tr.hidden = !ok; n += ok;
      });
      zahl.textContent = n === 1 ? "1 Vorschrift" : n + " Vorschriften";
    }
    q.addEventListener("input", lauf); l.addEventListener("change", lauf); lauf();
  }
  filterTabelle();
  if (!box) return;

  var $ = function (s) { return box.querySelector(s); };
  var F = { land: $("[name=land]"), region: $("[name=region]"), regel: $("[name=regel]"), start: $("[name=start]"), n: $("[name=n]"), einheit: $("[name=einheit]"), modus: $("[name=modus]") };
  var JAHRE = [2026, 2027, 2028, 2029, 2030];
  var aus = $("[data-fr-aus]"), meld = $("[data-fr-meldung]"), REGELN = [], BEISPIELE = [], DATA = null, letzte = null, zurueckgesetzt = false;
  var KEINE_BERATUNG = "Rechenhilfe, keine Rechtsberatung – Fristbeginn und anwendbare Vorschrift selbst prüfen";

  function regel() { return REGELN.filter(function (r) { return r.id === F.regel.value; })[0]; }
  function feiertage(land, region, jahre) {
    var out = {};
    jahre.forEach(function (y) {
      (DATA.h[land + ":" + (region || "") + ":" + y] || []).forEach(function (h) { if (h[2] === "legal") out[h[0]] = { name: h[1], note: h[3] }; });
    });
    return out;
  }
  function fuelleRegionen() {
    var c = DATA.countries[F.land.value], alt = F.region.value;
    F.region.innerHTML = '<option value="">' + (F.land.value === "de" ? "bundesweit (ohne Landesfeiertage)" : "ganz Österreich") + "</option>" +
      Object.keys(c.regions).map(function (k) { return '<option value="' + esc(k) + '">' + esc(c.regions[k]) + "</option>"; }).join("");
    F.region.value = c.regions[alt] ? alt : "";
  }
  function fuelleRegeln() {
    var alt = F.regel.value, liste = REGELN.filter(function (r) { return r.land === F.land.value; });
    F.regel.innerHTML = liste.map(function (r) { return '<option value="' + esc(r.id) + '">' + esc(r.kurz + " – " + r.name) + "</option>"; }).join("");
    if (liste.some(function (r) { return r.id === alt; })) F.regel.value = alt;
    modusAnpassen();
  }
  function modusAnpassen() {
    var r = regel(), ok = !!(r && r.tagesbeginn);
    F.modus.querySelector("[value=tagesbeginn]").disabled = !ok;
    if (!ok && F.modus.value === "tagesbeginn") { F.modus.value = "ereignis"; zurueckgesetzt = true; }   // sichtbar melden, nicht stillschweigend
    else if (ok) zurueckgesetzt = false;
  }
  function eingabe() { return { land: F.land.value, region: F.region.value, regel: F.regel.value, start: F.start.value, n: F.n.value.trim(), einheit: F.einheit.value, modus: F.modus.value }; }
  function linkFuer(e) {
    var p = new URLSearchParams();
    // region immer mitschreiben, auch leer: der Link soll beim Empfänger dasselbe Ergebnis zeigen
    ["land", "region", "regel", "start", "n", "einheit", "modus"].forEach(function (k) { if (k === "region" || (e[k] !== "" && e[k] != null)) p.set(k, e[k] || ""); });
    return root.location.origin + root.location.pathname + "?" + p.toString();
  }
  function textFuer(e, r, rg, hin) {
    var z = [(r.alternativ ? "Fristende: " + lang(r.alternativ) + " (Ablauf des Tages) – wo " + bedingterName(r) + " Feiertag ist: " + lang(r.ende) : "Fristende: " + lang(r.ende) + " (Ablauf des Tages)"),
      "Frist: " + dauer(r.n, r.einheit) + " ab " + lang(r.start) + (r.modus === "tagesbeginn" ? " (Tag zählt mit)" : " (Tag zählt nicht mit)"),
      "Vorschrift: " + rg.name + " · " + (DATA.countries[e.land].regions[e.region] || (e.land === "de" ? "Deutschland bundesweit" : "Österreich")),
      "Rechnerisches Ende: " + lang(r.roh)];
    r.schritte.forEach(function (s) { z.push("– " + lang(s.datum) + ": " + s.grund + ", verschiebt"); });
    hin.forEach(function (h) { z.push("Hinweis: " + h); });
    z.push(KEINE_BERATUNG + ". " + linkFuer(e));
    return z.join("\n");
  }
  function bedingterName(r) {
    var s = r.schritte.filter(function (x) { return x.note; })[0];
    return s ? s.grund.replace(/^gesetzlicher Feiertag \(|\)$/g, "") : "der Tag";
  }
  function streifen(r, ft, rg) {
    var a = plus(parse(r.roh), -2), b = plus(parse(r.ende), 1), z = "";   // r.alternativ liegt immer zwischen r.roh und r.ende
    for (var d = a; d <= b; d = plus(d, 1)) {
      var s = iso(d), g = grund(d, rg, ft), k = (s === r.ende || s === r.alternativ) ? "ziel" : g ? "frei" : "";
      z += '<li class="fr-tag ' + k + '"' + (s === r.ende ? ' aria-current="date"' : "") + "><b>" + WT[d.getUTCDay()].slice(0, 2) + "</b><span>" + d.getUTCDate() + "." + (d.getUTCMonth() + 1) + ".</span><em>" +
        esc((s === r.ende || s === r.alternativ) ? "Fristende" : s === r.roh ? "rechnerisch" : g ? g.split(" (")[0] : "") + "</em></li>";
    }
    return '<ol class="fr-streifen" aria-label="Tage rund um das Fristende">' + z + "</ol>";
  }
  function rechne() {
    if (!DATA) return;
    var e = eingabe(), rg = regel();
    sprache(e.land);
    meld.textContent = "";
    var ft = feiertage(e.land, e.region, JAHRE);
    var r = berechne(e, rg, ft);
    if (r.fehler) { letzte = null; aus.innerHTML = '<p class="plan-sum fr-fehler">' + esc(r.fehler) + "</p>"; return; }
    var hin = hinweise(r, rg, e, ft, regionaleTage(e.land, e.region, JAHRE));
    if (zurueckgesetzt) hin.unshift("„Der erste Tag zählt mit“ gibt es nur bei Vorschriften, die auf § 187 Abs. 2 BGB verweisen. Für die gewählte Vorschrift rechnet der Rechner deshalb mit „zählt nicht mit“.");
    letzte = { e: e, r: r, rg: rg, hin: hin };
    var ort = DATA.countries[e.land].regions[e.region] || (e.land === "de" ? "Deutschland (bundesweit)" : "Österreich");
    var p1 = r.modus === "tagesbeginn"
      ? "Die Frist beginnt mit dem Anfang von " + lang(r.start) + "; dieser Tag zählt mit (§ 187 Abs. 2 BGB)."
      : "Das Ereignis fällt auf " + lang(r.start) + ". Dieser Tag zählt nicht mit; die Frist läuft ab dem Folgetag.";
    var p2 = dauer(r.n, r.einheit) + " später endet die Frist rechnerisch mit Ablauf von <b>" + esc(lang(r.roh)) + "</b>" +
      (r.einheit === "tage" ? "." : r.fehlt ? " – der entsprechende Tag fehlt in diesem Monat, es gilt der Monatsletzte." :
        r.modus === "tagesbeginn" ? " – dem Tag vor dem, der dem Anfangstag entspricht (§ 188 Abs. 2 BGB)." : " – dem Tag, der nach Benennung oder Zahl dem Ereignistag entspricht.");
    var p3 = r.schritte.length
      ? "Dieser Tag verschiebt das Ende: " + r.schritte.map(function (x) { return esc(lang(x.datum, false).replace(/ \d{4}$/, "")) + " ist " + esc(x.grund); }).join("; ") + ". Der nächste Tag, der nicht dazugehört, ist " + esc(lang(r.ende)) + "."
      : "Dieser Tag ist nach der gewählten Vorschrift weder Samstag, Sonntag noch ein anderer Tag, der das Ende verschiebt. Es bleibt dabei.";
    var kopf = r.alternativ
      ? '<p class="plan-sum">Letzter Tag der Frist: <b>' + esc(lang(r.alternativ)) + '</b><br><span class="fr-oder">wo ' + esc(bedingterName(r)) + ' gesetzlicher Feiertag ist: </span><b>' + esc(lang(r.ende)) + "</b></p>"
      : '<p class="plan-sum">Letzter Tag der Frist: <b>' + esc(lang(r.ende)) + "</b></p>";
    aus.innerHTML = kopf + '<p class="small fr-beratung">' + esc(KEINE_BERATUNG) + ' (<a href="#grenzen">Grenzen des Rechners</a>).</p>' +
      '<p class="small muted">' + esc(rg.name) + " · " + esc(ort) + " · " + r.kalendertage + " Kalendertage nach dem Fristbeginn · die Frist läuft bis zum Ablauf dieses Tages</p>" +
      streifen(r, ft, rg) + '<ol class="fr-schritte"><li>' + esc(p1) + "</li><li>" + p2 + "</li><li>" + p3 + "</li></ol>" +
      (hin.length ? '<ul class="fr-hinweise">' + hin.map(function (h) { return "<li>" + esc(h) + "</li>"; }).join("") + "</ul>" : "") +
      '<p class="small muted">' + esc(rg.hinweis) + " Quelle: " + rg.quellen.map(function (q) { return '<a href="' + esc(q[1]) + '" rel="noopener">' + esc(q[0]) + "</a>"; }).join(", ") + ".</p>";
  }
  function setze(v) {
    if (v.land === "at" || v.land === "de") { F.land.value = v.land; fuelleRegionen(); fuelleRegeln(); }
    if (typeof v.region === "string" && (v.region === "" || DATA.countries[F.land.value].regions[v.region])) F.region.value = v.region;
    if (REGELN.some(function (r) { return r.id === v.regel && r.land === F.land.value; })) F.regel.value = v.regel;
    modusAnpassen();
    if (parse(String(v.start || ""))) F.start.value = v.start;
    if (/^\d{1,3}$/.test(String(v.n || "")) && +v.n >= 1) F.n.value = String(+v.n);
    if (EINHEITEN[v.einheit]) F.einheit.value = v.einheit;
    if (v.modus === "tagesbeginn" && regel() && regel().tagesbeginn) F.modus.value = "tagesbeginn"; else if (v.modus) F.modus.value = "ereignis";
    zurueckgesetzt = false;
  }
  function kopiere(text, ok) {
    var fertig = function () { meld.textContent = ok; };
    if (root.navigator.clipboard && root.navigator.clipboard.writeText) root.navigator.clipboard.writeText(text).then(fertig, function () { meld.textContent = "Kopieren nicht möglich – bitte den Text markieren: " + text; });
    else meld.textContent = "Kopieren nicht möglich – bitte den Text markieren: " + text;
  }
  function ics() {
    var r = letzte.r, tag = r.alternativ || r.ende;   // bei zwei möglichen Enden das frühere
    var d = tag.replace(/-/g, ""), nd = iso(plus(parse(tag), 1)).replace(/-/g, "");
    var t = function (s) { return String(s).replace(/[\;,]/g, "\\$&").replace(/\r?\n/g, "\\n"); };
    var z = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Kalenderkompass 24//Fristenrechner//DE", "BEGIN:VEVENT", "UID:frist-" + d + "-" + r.start + "-" + r.n + r.einheit + "@kalenderkompass24.de",
      "DTSTAMP:" + new Date().toISOString().replace(/[-:]/g, "").slice(0, 15) + "Z", "DTSTART;VALUE=DATE:" + d, "DTEND;VALUE=DATE:" + nd,
      "SUMMARY:" + t("Fristende (" + dauer(r.n, r.einheit) + " ab " + lang(r.start, false) + ")"),
      "DESCRIPTION:" + t(letzte.rg.name + ". " + (r.alternativ ? "Wo " + bedingterName(r) + " gesetzlicher Feiertag ist, endet die Frist erst am " + lang(r.ende) + ". " : "") + KEINE_BERATUNG + ". Berechnet mit dem Fristenrechner von Kalenderkompass 24."), "END:VEVENT", "END:VCALENDAR"];
    var a = doc.createElement("a"); a.href = URL.createObjectURL(new Blob([z.join("\r\n") + "\r\n"], { type: "text/calendar" }));
    a.download = "fristende-" + tag + ".ics"; doc.body.appendChild(a); a.click(); a.remove(); setTimeout(function () { URL.revokeObjectURL(a.href); }, 1000);
  }

  box.addEventListener("change", function (ev) {
    if (ev.target === F.land) { fuelleRegionen(); fuelleRegeln(); }
    if (ev.target === F.regel) modusAnpassen();
    if (ev.target === F.modus) zurueckgesetzt = false;
    rechne();
  });
  box.addEventListener("input", function (ev) { if (ev.target === F.n || ev.target === F.start) rechne(); });
  box.addEventListener("submit", function (ev) { ev.preventDefault(); rechne(); });
  box.addEventListener("click", function (ev) {
    var b = ev.target.closest("button[data-fr]"); if (!b) return;
    if (!letzte) { meld.textContent = "Erst eine gültige Frist eingeben."; return; }
    if (b.dataset.fr === "link") kopiere(linkFuer(letzte.e), "Link kopiert. Er enthält die eingegebenen Werte.");
    if (b.dataset.fr === "text") kopiere(textFuer(letzte.e, letzte.r, letzte.rg, letzte.hin), "Ergebnis als Text kopiert.");
    if (b.dataset.fr === "ics") { ics(); meld.textContent = "Kalenderdatei erstellt."; }
    if (b.dataset.fr === "druck") root.print();
  });
  doc.addEventListener("click", function (ev) {
    var b = ev.target.closest("[data-fr-beispiel]"); if (!b || !DATA) return;
    var v = BEISPIELE[+b.dataset.frBeispiel]; if (!v) return;
    setze(v); rechne(); box.scrollIntoView({ block: "start" }); F.start.focus({ preventScroll: true });
  });

  Promise.all([fetch("/data/feiertage.json").then(function (r) { return r.json(); }), fetch("/data/fristen.json").then(function (r) { return r.json(); })]).then(function (x) {
    DATA = x[0]; REGELN = x[1].regeln; BEISPIELE = x[1].beispiele;
    var gemerkt = ""; try { gemerkt = root.localStorage.getItem("kk24-region") || ""; } catch (err) { /* ohne Speicher */ }
    var g = gemerkt.split(":");
    F.land.value = g[0] === "de" ? "de" : "at"; fuelleRegionen(); fuelleRegeln();
    if (F.land.value === "at") F.regel.value = "at-avg";   // Vorgabe = Beispiel 1
    if (g[1] && DATA.countries[F.land.value].regions[g[1]]) F.region.value = g[1];
    var q = new URLSearchParams(root.location.search), v = {};
    ["land", "region", "regel", "start", "n", "einheit", "modus"].forEach(function (k) { if (q.has(k)) v[k] = q.get(k); });
    if (Object.keys(v).length) {
      if (!("region" in v)) v.region = "";   // Link ohne Region = ohne Bundesland, nicht das hier gemerkte
      setze(v);
    }
    rechne();
  }).catch(function () { aus.innerHTML = '<p class="plan-sum fr-fehler">Die Feiertagsdaten konnten nicht geladen werden. Bitte die Seite neu laden.</p>'; });
})(typeof window !== "undefined" ? window : globalThis);
