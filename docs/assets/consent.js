/* Werbung und Statistik — beides läuft über Googles zertifizierte Einwilligungsverwaltung (TCF 2.2).
   Reihenfolge: zuerst dataLayer/gtag und die Consent-Mode-Grundwerte (alles "denied", ga-disable an),
   erst danach irgendein Google-Skript. Google Analytics misst nur,
   - wenn die DSGVO gilt: TCF Zweck 1 + Anbieter Google (755) zugestimmt UND Consent-Mode-Wert
     analyticsStoragePurposeConsentStatus === GRANTED (1);
   - außerhalb der DSGVO (gdprApplies false): Analyticswert GRANTED (1) oder NOT_APPLICABLE (3) UND
     die CMP meldet „kein US-Opt-out“ (usstatesoptout DOES_NOT_APPLY 1 / NOT_OPTED_OUT 2).
   Fehlend, UNKNOWN (0), DENIED (2), NOT_CONFIGURED (4) oder ein Fehler einer CMP-Schnittstelle = Nein.
   Ein eindeutiges TCF-Nein schaltet sofort ab, ohne vorher weitere CMP-Schnittstellen abzufragen.
   Werte: developers.google.com/funding-choices/fc-api-docs. Signals/Werbepersonalisierung in GA aus.

   Übergang seit 4.11.2026 – das „Statistik-Blatt“: Liefert Googles Dialog nach 3 s keine echte TCF-Entscheidung
   (kein __tcfapi oder Dialog "hidden"/"disabled" ohne useractioncomplete bzw. tcloaded mit tcString) und gilt
   nicht eindeutig gdprApplies === false, fragen wir selbst – nur nach Google Analytics, nie nach Werbung.
   ad_storage/ad_user_data/ad_personalization fasst das Blatt nie an. Eine echte Google-Entscheidung hat immer
   Vorrang; dann gilt allein die Logik oben und die eigene Wahl wird ignoriert. GPC: Statistik aus, kein Blatt.
   Auf Seiten ohne Werbung (data-ohne-werbung: Impressum, Datenschutz, 404) lädt nichts von Google; dort lässt
   sich die Blatt-Wahl nur ändern oder widerrufen. Gespeichert wird localStorage "kk24-statistik":
   { v: 1, wahl: "ja"|"nein", zeit: ms, google?: ms } – 12 Monate gültig. */
(() => {
  // ——— Regeln des Statistik-Blatts ohne DOM (geprüft in tests/einwilligung.test.js) ———
  const BLATT_KEY = "kk24-statistik";
  const BLATT_VERSION = 1;
  const BLATT_WARTEN = 3000;           // so lange bekommt Googles Dialog Zeit, bevor das Blatt entscheidet
  const TAG = 864e5;
  const regel = {
    echteEntscheidung(tc){
      return !!tc && (tc.eventStatus === "useractioncomplete" ||
        (tc.eventStatus === "tcloaded" && typeof tc.tcString === "string" && tc.tcString !== ""));
    },
    gueltigBis(zeit){ const d = new Date(zeit); d.setMonth(d.getMonth() + 12); return d.getTime(); },
    frisch(zeit, jetzt){ return typeof zeit === "number" && zeit <= jetzt + TAG && jetzt < regel.gueltigBis(zeit); },
    eigeneWahl(eintrag, jetzt){
      if (!eintrag || typeof eintrag !== "object" || eintrag.v !== BLATT_VERSION) return null;
      if (eintrag.wahl !== "ja" && eintrag.wahl !== "nein") return null;
      return regel.frisch(eintrag.zeit, jetzt) ? eintrag.wahl : null;
    },
    googleGewaehlt(eintrag, jetzt){
      return !!eintrag && typeof eintrag === "object" && eintrag.v === BLATT_VERSION && regel.frisch(eintrag.google, jetzt);
    },
    googleZeigt(tc){
      if (!tc) return false;
      if (tc.displayStatus === "visible") return true;
      return tc.eventStatus === "cmpuishown" && tc.displayStatus !== "hidden" && tc.displayStatus !== "disabled";
    },
    // "gpc" | "google" (bestehende TCF-Logik gilt) | "warten" (Google-Dialog offen/erwartet) | "fragen" | "ja" | "nein"
    lage({ tc, gpc, eintrag, jetzt }){
      if (gpc) return "gpc";
      if (tc && tc.gdprApplies === false) return "google";
      if (regel.echteEntscheidung(tc)) return "google";
      if (regel.googleZeigt(tc)) return "warten";
      if (!tc && regel.googleGewaehlt(eintrag, jetzt)) return "warten";   // früher im Google-Dialog gewählt: auf die CMP warten
      return regel.eigeneWahl(eintrag, jetzt) || "fragen";
    },
    gaCookies(text){
      return String(text || "").split(";").map(s => s.split("=")[0].trim()).filter(n => /^_ga(_.+)?$/.test(n));
    },
    domains(host){
      const teile = String(host || "").split("."), out = [""];
      for (let i = 0; i < teile.length - 1; i++){ const d = teile.slice(i).join("."); out.push(d, "." + d); }
      return out;
    }
  };
  if (typeof window === "undefined"){ if (typeof module === "object") module.exports = { regel, BLATT_KEY, BLATT_VERSION, BLATT_WARTEN }; return; }

  const ohneWerbung = !!(document.currentScript && document.currentScript.hasAttribute("data-ohne-werbung"));
  const PUB = "ca-pub-7811071715414905";
  const GA = "G-T00HRG2YVF";
  const GOOGLE_VENDOR = 755;
  const GA_OFF = `ga-disable-${GA}`;

  window.dataLayer = window.dataLayer || [];
  if (typeof window.gtag !== "function") window.gtag = function(){ window.dataLayer.push(arguments); };
  window[GA_OFF] = true;
  // Indexierbare Seiten setzen die Grundwerte schon inline im <head> (vor dem statischen AdSense-Skript).
  if (!window.kkConsentDefault) {
    gtag("consent", "default", {
      ad_storage: "denied", ad_user_data: "denied", ad_personalization: "denied",
      analytics_storage: "denied", wait_for_update: 500
    });
    window.kkConsentDefault = true;
  }
  window.googlefc = window.googlefc || {};
  window.googlefc.callbackQueue = window.googlefc.callbackQueue || [];

  // Anzeigenblöcke: Block-IDs werden nach der AdSense-Freigabe hier eingetragen.
  const SLOTS = { billboard: "", rect: "", half: "", superbanner: "", sky: "" };
  // Feste IAB-Formate: Superbanner 728×90, Wide Skyscraper 160×600. Die übrigen Plätze sind responsiv
  // (Billboard 970×250 / Leaderboard 728×90 / Mobile 320×100, Half Page 300×600, Medium Rectangle 300×250).
  const FIXED = { superbanner: [728, 90], sky: [160, 600] };

  const gpc = navigator.globalPrivacyControl === true;

  function loadAds(){
    if (gpc) { (window.adsbygoogle = window.adsbygoogle || []).pauseAdRequests = 1; return; }
    // Auf indexierbaren Seiten steht das AdSense-Skript schon statisch im <head> – nicht doppelt laden.
    if (!document.querySelector('script[src*="pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"]')) {
      const s = document.createElement("script");
      s.async = true; s.crossOrigin = "anonymous";
      s.src = `https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${PUB}`;
      document.head.appendChild(s);
    }
    document.querySelectorAll(".ad[data-ad]").forEach(box => {
      const id = SLOTS[box.dataset.ad];
      if (!id) return;
      box.classList.add("on");
      if (box.offsetParent === null) { box.classList.remove("on"); return; }   // auf diesem Bildschirm ausgeblendet
      const ins = document.createElement("ins");
      ins.className = "adsbygoogle"; ins.dataset.adClient = PUB; ins.dataset.adSlot = id;
      const fixed = FIXED[box.dataset.ad];
      if (fixed) { ins.style.cssText = `display:inline-block;width:${fixed[0]}px;height:${fixed[1]}px`; }
      else {
        ins.style.display = "block";
        ins.dataset.adFormat = box.dataset.ad === "half" ? "vertical" : "auto";
        ins.dataset.fullWidthResponsive = "true";
      }
      box.appendChild(ins);
      (window.adsbygoogle = window.adsbygoogle || []).push({});
    });
  }

  // Statistik-Zustand: "unentschieden" → "aktiv" / "gesperrt"
  const statistik = {
    zustand: "unentschieden",
    skriptDa: false,
    tcf: null,

    consentMode(){
      // 0 UNKNOWN, 1 GRANTED, 2 DENIED, 3 NOT_APPLICABLE, 4 NOT_CONFIGURED
      try {
        const fc = window.googlefc;
        if (typeof fc.getGoogleConsentModeValues !== "function") return 0;
        const wert = fc.getGoogleConsentModeValues().analyticsStoragePurposeConsentStatus;
        return typeof wert === "number" ? wert : 0;
      } catch (_) { return 0; }
    },

    usOptOut(){
      // googlefc.usstatesoptout.InitialUsStatesOptOutStatusEnum: 1 DOES_NOT_APPLY, 2 NOT_OPTED_OUT, 3 OPTED_OUT.
      // Nur 1 oder 2 bestätigen "kein Opt-out"; noch nicht gemeldet (0), 3 oder ein Fehler sperren.
      try {
        const u = window.googlefc.usstatesoptout;
        if (!u || typeof u.getInitialUsStatesOptOutStatus !== "function") return true;
        const st = u.getInitialUsStatesOptOutStatus();
        return st !== 1 && st !== 2;
      } catch (_) { return true; }
    },

    erlaubt(){
      if (gpc) return false;
      if (blatt.zustaendig()){ const w = blatt.wahl(); return w === "ja" ? true : w === "nein" ? false : null; }
      const tc = this.tcf;
      if (!tc) return null;                                   // CMP noch stumm: Grundwerte bleiben "denied"
      if (tc.gdprApplies === false){
        const cm = this.consentMode();
        return (cm === 1 || cm === 3) && !this.usOptOut();
      }
      if (tc.eventStatus !== "tcloaded" && tc.eventStatus !== "useractioncomplete") return null;
      const p1 = !!(tc.purpose && tc.purpose.consents && tc.purpose.consents[1]);
      const v = !!(tc.vendor && tc.vendor.consents && tc.vendor.consents[GOOGLE_VENDOR]);
      if (!p1 || !v) return false;                            // eindeutiges Nein – keine weitere CMP-Abfrage
      return this.consentMode() === 1;
    },

    starten(){
      window[GA_OFF] = false;
      gtag("consent", "update", { analytics_storage: "granted" });
      if (!this.skriptDa){
        this.skriptDa = true;
        gtag("js", new Date());
        const s = document.createElement("script"); s.async = true;
        s.src = `https://www.googletagmanager.com/gtag/js?id=${GA}`;
        document.head.appendChild(s);
      }
      gtag("config", GA, { allow_google_signals: false, allow_ad_personalization_signals: false });
      this.zustand = "aktiv";
    },

    sperren(nurStatistik){
      window[GA_OFF] = true;
      if (nurStatistik){                                       // Statistik-Blatt: nur Analytics, Werbewerte bleiben unberührt
        gtag("consent", "update", { analytics_storage: "denied" });
        analyseKekseAbreissen();
        this.zustand = "gesperrt";
        return;
      }
      const tc = this.tcf;
      const speichern = !!(tc && tc.purpose && tc.purpose.consents && tc.purpose.consents[1]);
      gtag("consent", "update", speichern
        ? { analytics_storage: "denied" }
        : { analytics_storage: "denied", ad_storage: "denied", ad_user_data: "denied", ad_personalization: "denied" });
      this.zustand = "gesperrt";
    },

    pruefen(){
      if (ohneWerbung) return;                                 // Seiten ohne Werbung: kein Google-Skript, auch keine Statistik
      const eigen = blatt.zustaendig();
      const ok = this.erlaubt();
      if (ok === true && this.zustand !== "aktiv") this.starten();
      else if (ok === false && this.zustand !== "gesperrt") this.sperren(eigen);
      else if (ok === null && this.zustand === "aktiv") this.sperren(eigen);   // Dialog nach Widerruf wieder offen
    }
  };

  function analyseKekseAbreissen(){
    let namen = [];
    try { namen = regel.gaCookies(document.cookie); } catch (_) { return; }
    const hosts = regel.domains(location.hostname);
    namen.forEach(n => hosts.forEach(d => {
      document.cookie = `${n}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; max-age=0; path=/${d ? "; domain=" + d : ""}`;
    }));
  }

  // Lokaler Speicher für die Blatt-Wahl; ohne Speicher gilt die Wahl wenigstens für diesen Seitenaufruf
  const ablage = {
    notfall: null,
    lesen(){
      try { const r = localStorage.getItem(BLATT_KEY); return r ? JSON.parse(r) : null; }
      catch (_) { return this.notfall; }
    },
    schreiben(e){
      this.notfall = e;
      try { localStorage.setItem(BLATT_KEY, JSON.stringify(e)); } catch (_) {}
    },
    loeschen(){
      this.notfall = null;
      try { localStorage.removeItem(BLATT_KEY); } catch (_) {}
    }
  };

  // Das Statistik-Blatt: eigenes Übergangsfenster im Stil eines Abreißkalenders, unten rechts, blockiert nichts
  const blatt = {
    bereit: false,          // ab BLATT_WARTEN (oder nach einer Wahl) darf das Blatt über die Statistik entscheiden
    el: null,
    ausloeser: null,

    lageJetzt(){ return regel.lage({ tc: statistik.tcf, gpc, eintrag: ablage.lesen(), jetzt: Date.now() }); },
    zustaendig(){
      if (ohneWerbung || !this.bereit) return false;
      const l = this.lageJetzt();
      return l === "ja" || l === "nein" || l === "fragen";
    },
    wahl(){ const l = this.lageJetzt(); return l === "ja" || l === "nein" ? l : null; },

    datum(ms){
      try { return new Date(ms).toLocaleDateString(document.documentElement.lang || "de-AT", { day: "numeric", month: "long", year: "numeric" }); }
      catch (_) { return new Date(ms).toISOString().slice(0, 10); }
    },

    bauen(){
      if (this.el) return this.el;
      const el = document.createElement("section");
      el.className = "kk-blatt";
      el.id = "kk-blatt";
      el.hidden = true;
      el.setAttribute("role", "dialog");
      el.setAttribute("aria-modal", "false");
      el.setAttribute("aria-labelledby", "kk-blatt-titel");
      el.setAttribute("aria-describedby", "kk-blatt-text");
      el.addEventListener("keydown", e => { if (e.key === "Escape"){ e.preventDefault(); this.schliessen(); } });   // Escape = keine Wahl
      el.addEventListener("click", e => {
        const k = e.target.closest("[data-kk-wahl]");
        if (!k) return;
        if (k.dataset.kkWahl === "zu") this.schliessen(); else this.entscheiden(k.dataset.kkWahl);
      });
      const ansage = document.createElement("p");
      ansage.className = "kk-blatt-ansage";
      ansage.setAttribute("role", "status");
      const skip = document.querySelector(".skip");
      // früh im Tab-Ablauf (direkt nach „Zum Inhalt“), optisch unten fixiert – kein Layout-Shift
      if (skip && skip.parentNode === document.body) skip.after(el, ansage); else document.body.prepend(el, ansage);
      this.el = el; this.ansage = ansage;
      return el;
    },

    inhalt(art){
      const kopf = `<p class="kk-blatt__kopf" aria-hidden="true"><span>Kalenderkompass 24</span><span>Statistik</span></p>`;
      if (art === "gpc") return kopf + `<h2 id="kk-blatt-titel" tabindex="-1">Statistik bleibt aus</h2>
<div id="kk-blatt-text"><p>Dein Browser sendet das Signal „Global Privacy Control“. Wir halten uns daran: Google Analytics bleibt ausgeschaltet, und wir fragen dich nicht nach einer Zustimmung. Mehr in der <a href="/privacy.html#statistik-fenster">Datenschutzerklärung</a>.</p></div>
<div class="kk-blatt__wahl"><button type="button" class="kk-blatt__knopf" data-kk-wahl="zu">Schließen</button></div>`;
      if (art === "google") return kopf + `<h2 id="kk-blatt-titel" tabindex="-1">Deine Auswahl liegt bei Google</h2>
<div id="kk-blatt-text"><p>Du hast im Einwilligungsdialog von Google entschieden. Diesen Dialog öffnen wir nur auf Inhaltsseiten, weil wir hier keinen Google-Code laden.</p><p><a href="/#datenschutz-einstellungen">Datenschutz-Einstellungen auf der Startseite öffnen</a></p></div>
<div class="kk-blatt__wahl"><button type="button" class="kk-blatt__knopf" data-kk-wahl="zu">Schließen</button></div>`;
      const w = regel.eigeneWahl(ablage.lesen(), Date.now());
      const e = ablage.lesen();
      const stand = w === "ja" ? `Zugestimmt am ${this.datum(e.zeit)}`
        : w === "nein" ? `Abgelehnt am ${this.datum(e.zeit)}`
        : this.ausloeser ? "Noch keine Auswahl" : "";
      const hier = ohneWerbung ? ". Hier wird nichts gemessen; die Wahl gilt für die Inhaltsseiten." : "";
      return kopf + `<h2 id="kk-blatt-titel" tabindex="-1">Statistik erlauben?</h2>
<div id="kk-blatt-text"><p>Reine Reichweitenmessung mit Google Analytics (Google Ireland Ltd.): Google setzt Cookies, Daten auch in den USA möglich. Keine Zustimmung zu Werbung. Widerruf jederzeit unten über „Datenschutz-Einstellungen“. <a href="/privacy.html#statistik-fenster">Datenschutzerklärung</a></p></div>
${stand || hier ? `<p class="kk-blatt__stand">${stand}${stand ? hier : hier.slice(3)}</p>` : ""}
<div class="kk-blatt__wahl"><button type="button" class="kk-blatt__knopf" data-kk-wahl="ja">Zustimmen</button><button type="button" class="kk-blatt__knopf" data-kk-wahl="nein">Ablehnen</button></div>
<button type="button" class="kk-blatt__zu" data-kk-wahl="zu" aria-label="Schließen, ohne zu entscheiden">×</button>`;
    },

    zeigen(art, ausloeser){
      if (!document.body) return;
      const el = this.bauen();
      this.ausloeser = ausloeser || null;
      el.dataset.art = art;
      el.innerHTML = this.inhalt(art);
      el.hidden = false;
      this.platz();
      if (this.ausloeser){ const t = el.querySelector("#kk-blatt-titel"); if (t) t.focus({ preventScroll: true }); }
    },

    offen(){ return !!(this.el && !this.el.hidden); },

    // Platz unter dem Seitenfuß freihalten, solange das Blatt offen ist – Impressum & Co. bleiben erreichbar
    platz(){
      const b = document.body;
      if (!b || !b.style) return;
      if (this.offen()){
        b.style.paddingBottom = `${Math.ceil(this.el.getBoundingClientRect().height) + 24}px`;
        if (!this.hoertGroesse){ this.hoertGroesse = true; window.addEventListener("resize", () => this.platz()); }
      } else b.style.paddingBottom = "";
    },

    schliessen(){
      if (!this.offen()) return;
      const hatteFokus = this.el.contains(document.activeElement);
      this.el.hidden = true;
      this.platz();
      if (hatteFokus && this.ausloeser && document.contains(this.ausloeser)) this.ausloeser.focus({ preventScroll: true });
      this.ausloeser = null;
    },

    entscheiden(wahl){
      if (wahl !== "ja" && wahl !== "nein") return;
      if (gpc) { this.schliessen(); return; }
      const alt = ablage.lesen();
      const e = { v: BLATT_VERSION, wahl, zeit: Date.now() };
      if (regel.googleGewaehlt(alt, e.zeit)) e.google = alt.google;
      ablage.schreiben(e);
      if (wahl === "nein") analyseKekseAbreissen();
      this.bereit = true;
      statistik.pruefen();
      this.schliessen();
      if (this.ansage) this.ansage.textContent = wahl === "nein" ? "Gespeichert: Die Statistik ist ausgeschaltet."
        : ohneWerbung ? "Gespeichert: Zustimmung zur Statistik. Gemessen wird erst auf unseren Inhaltsseiten."
        : "Gespeichert: Die Statistik mit Google Analytics ist eingeschaltet.";
    },

    // nach BLATT_WARTEN: Googles Dialog hat nichts entschieden → gespeicherte Wahl anwenden oder fragen
    start(){
      if (ohneWerbung) return;
      this.bereit = true;
      const l = this.lageJetzt();
      if (l === "nein") analyseKekseAbreissen();
      statistik.pruefen();
      if (location.hash === "#datenschutz-einstellungen") this.einstellungen(null);
      else if (l === "fragen" && !this.offen()) this.zeigen("frage", null);
    },

    // jede TCF-Meldung: echte Google-Entscheidung ersetzt die eigene Wahl (wird gelöscht, nur der Zeitpunkt bleibt)
    tcfMeldung(tc){
      if (tc.gdprApplies === false) ablage.loeschen();          // DSGVO gilt laut Google nicht: bestehende Logik, eigene Wahl weg
      else if (regel.echteEntscheidung(tc)) ablage.schreiben({ v: BLATT_VERSION, google: Date.now() });
      const l = this.lageJetzt();
      if ((l === "google" || l === "warten") && this.offen() && this.el.dataset.art !== "gpc") this.schliessen();
    },

    // nach jeder Prüfung: Google hat entschieden und die Statistik ist aus → Analytics-Cookies abreißen
    nachGoogle(tc){
      if (regel.echteEntscheidung(tc) && statistik.zustand === "gesperrt") analyseKekseAbreissen();
    },

    // Knopf „Datenschutz-Einstellungen“
    einstellungen(knopf){
      const l = this.lageJetzt();
      if (l === "gpc" && !(regel.echteEntscheidung(statistik.tcf) && !ohneWerbung)) return this.zeigen("gpc", knopf);
      if (l === "gpc" || l === "google" || l === "warten"){
        if (ohneWerbung) return this.zeigen("google", knopf);
        window.googlefc.callbackQueue.push(() => {
          if (typeof window.googlefc.showRevocationMessage === "function") window.googlefc.showRevocationMessage();
        });
        return;
      }
      this.zeigen("frage", knopf);
    }
  };

  function watchConsent(tries = 0){
    if (typeof window.__tcfapi !== "function"){
      if (tries < 40) setTimeout(() => watchConsent(tries + 1), 250);
      return;
    }
    window.__tcfapi("addEventListener", 2, (tc, ok) => {
      if (!ok || !tc) return;
      statistik.tcf = tc;
      blatt.tcfMeldung(tc);
      statistik.pruefen();
      blatt.nachGoogle(tc);
      if (tc.eventStatus === "useractioncomplete" || tc.eventStatus === "tcloaded") setTimeout(() => { statistik.pruefen(); blatt.nachGoogle(statistik.tcf); }, 300);
    });
  }
  window.googlefc.callbackQueue.push({
    CONSENT_MODE_DATA_READY: () => statistik.pruefen(),
    INITIAL_US_STATES_OPT_OUT_DATA_READY: () => statistik.pruefen()
  });

  // Link „Datenschutz-Einstellungen" im Seitenfuß öffnet den Google-Dialog erneut –
  // im Übergang (kein Google-Dialog, keine Google-Entscheidung) stattdessen das Statistik-Blatt
  document.addEventListener("click", e => {
    const knopf = e.target.closest("[data-privacy-settings]");
    if (!knopf) return;
    blatt.einstellungen(knopf);
  });

  if (ohneWerbung) return;                                   // Impressum, Datenschutz, 404: keine Werbung, kein Google-Skript
  loadAds();
  watchConsent();
  setTimeout(() => blatt.start(), BLATT_WARTEN);
})();
