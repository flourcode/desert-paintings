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
