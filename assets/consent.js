/* Werbung und Statistik — beides läuft über Googles zertifizierte Einwilligungsverwaltung (TCF 2.2).
   Reihenfolge: zuerst dataLayer/gtag und die Consent-Mode-Grundwerte (alles "denied", ga-disable an),
   erst danach irgendein Google-Skript. Google Analytics misst nur,
   - wenn die DSGVO gilt: TCF Zweck 1 + Anbieter Google (755) zugestimmt UND Consent-Mode-Wert
     analyticsStoragePurposeConsentStatus === GRANTED (1);
   - außerhalb der DSGVO (gdprApplies false): Analyticswert GRANTED (1) oder NOT_APPLICABLE (3) UND
     die CMP meldet „kein US-Opt-out“ (usstatesoptout DOES_NOT_APPLY 1 / NOT_OPTED_OUT 2).
   Fehlend, UNKNOWN (0), DENIED (2), NOT_CONFIGURED (4) oder ein Fehler einer CMP-Schnittstelle = Nein.
   Ein eindeutiges TCF-Nein schaltet sofort ab, ohne vorher weitere CMP-Schnittstellen abzufragen.
   Werte: developers.google.com/funding-choices/fc-api-docs. Signals/Werbepersonalisierung in GA aus. */
(() => {
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

    sperren(){
      window[GA_OFF] = true;
      const tc = this.tcf;
      const speichern = !!(tc && tc.purpose && tc.purpose.consents && tc.purpose.consents[1]);
      gtag("consent", "update", speichern
        ? { analytics_storage: "denied" }
        : { analytics_storage: "denied", ad_storage: "denied", ad_user_data: "denied", ad_personalization: "denied" });
      this.zustand = "gesperrt";
    },

    pruefen(){
      const ok = this.erlaubt();
      if (ok === true && this.zustand !== "aktiv") this.starten();
      else if (ok === false && this.zustand !== "gesperrt") this.sperren();
      else if (ok === null && this.zustand === "aktiv") this.sperren();   // Dialog nach Widerruf wieder offen
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
      statistik.pruefen();
      if (tc.eventStatus === "useractioncomplete" || tc.eventStatus === "tcloaded") setTimeout(() => statistik.pruefen(), 300);
    });
  }
  window.googlefc.callbackQueue.push({
    CONSENT_MODE_DATA_READY: () => statistik.pruefen(),
    INITIAL_US_STATES_OPT_OUT_DATA_READY: () => statistik.pruefen()
  });

  // Link „Datenschutz-Einstellungen" im Seitenfuß öffnet den Google-Dialog erneut
  document.addEventListener("click", e => {
    if (!e.target.closest("[data-privacy-settings]")) return;
    window.googlefc.callbackQueue.push(() => {
      if (typeof window.googlefc.showRevocationMessage === "function") window.googlefc.showRevocationMessage();
    });
  });

  loadAds();
  watchConsent();
})();
