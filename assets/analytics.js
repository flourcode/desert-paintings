/*
  Google Analytics 4 for desertpaintings.com

  1. In Google Analytics, create a GA4 property and a Web data stream for https://desertpaintings.com
  2. Copy the Measurement ID (it looks like G-XXXXXXXXXX)
  3. Paste it between the quotes below, commit, and push. Amplify redeploys automatically.

  Until an ID is filled in, this file does nothing.
*/
(function () {
  var GA_MEASUREMENT_ID = "G-V4488DFLDH";

  if (!GA_MEASUREMENT_ID) return;
  if (location.hostname === "localhost" || location.hostname === "127.0.0.1") return;

  var s = document.createElement("script");
  s.async = true;
  s.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(GA_MEASUREMENT_ID);
  document.head.appendChild(s);

  window.dataLayer = window.dataLayer || [];
  window.gtag = function () { window.dataLayer.push(arguments); };
  window.gtag("js", new Date());
  window.gtag("config", GA_MEASUREMENT_ID);

  // Events worth knowing about for a small art site
  document.addEventListener("click", function (e) {
    var t = e.target;
    if (t.closest && t.closest("#copy-email")) {
      window.gtag("event", "email_copy", { page_path: location.pathname });
      return;
    }
    var f = t.closest && t.closest("[data-filter]");
    if (f) { window.gtag("event", "filter_paintings", { filter: f.getAttribute("data-filter") }); return; }
    var a = t.closest && t.closest("a[href]");
    if (a && /youtube\.com/.test(a.href)) {
      window.gtag("event", "youtube_click", { link_url: a.href, page_path: location.pathname });
    }
  });
  // Someone copying the email address by hand counts as interest too
  document.addEventListener("copy", function () {
    var sel = String(window.getSelection());
    if (sel.indexOf("mark.flournoy@gmail.com") > -1) window.gtag("event", "email_copy", { page_path: location.pathname, method: "select" });
  });
})();
