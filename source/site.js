// Desert Paintings: place filters on the index and the copy-email button.
(function () {
  var group = document.querySelector(".filters");
  if (group) {
    var cards = Array.prototype.slice.call(document.querySelectorAll(".card[data-tags]"));
    var count = document.querySelector("[data-count]");
    group.addEventListener("click", function (e) {
      var b = e.target.closest("[data-filter]");
      if (!b) return;
      var f = b.getAttribute("data-filter"), shown = 0;
      group.querySelectorAll("[data-filter]").forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
      cards.forEach(function (c) {
        var on = f === "all" || (" " + c.getAttribute("data-tags") + " ").indexOf(" " + f + " ") > -1;
        c.hidden = !on; if (on) shown++;
      });
      if (count) count.textContent = "Index · " + shown + (shown === 1 ? " painting" : " paintings");
    });
  }
  // Share: the phone's share sheet where available, otherwise copy the link
  document.addEventListener("click", function (e) {
    var b = e.target.closest && e.target.closest("[data-share]");
    if (!b) return;
    var url = b.getAttribute("data-url"), title = b.getAttribute("data-title");
    var label = b.textContent;
    var flash = function (text) { b.textContent = text; setTimeout(function () { b.textContent = label; }, 1800); };
    var copy = function () {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(function () { flash("Link copied"); }, function () { window.prompt("Copy this link:", url); });
      } else { window.prompt("Copy this link:", url); }
    };
    if (navigator.share && window.matchMedia("(pointer: coarse)").matches) {
      navigator.share({ title: title, url: url }).catch(function () {});
    } else { copy(); }
  });

  var btn = document.getElementById("copy-email");
  if (btn) {
    btn.addEventListener("click", function () {
      var el = document.getElementById("email"), text = el.textContent.trim();
      var done = function () { btn.textContent = "Copied"; setTimeout(function () { btn.textContent = "Copy"; }, 1600); };
      var select = function () { var r = document.createRange(); r.selectNodeContents(el); var s = getSelection(); s.removeAllRanges(); s.addRange(r); };
      try { navigator.clipboard.writeText(text).then(done, select); } catch (err) { select(); }
    });
  }
})();
