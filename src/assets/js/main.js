(function () {
  "use strict";

  /* Mobile navigation toggle */
  var navToggle = document.getElementById("navToggle");
  var siteNav = document.getElementById("siteNav");
  if (navToggle && siteNav) {
    navToggle.addEventListener("click", function () {
      var open = siteNav.classList.toggle("is-open");
      navToggle.setAttribute("aria-expanded", open ? "true" : "false");
      navToggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    });
  }

  /* Reading progress bar (article pages only) */
  var body = document.getElementById("articleBody");
  var bar = document.getElementById("readingBar");
  if (body && bar) {
    var update = function () {
      var rect = body.getBoundingClientRect();
      var total = body.offsetHeight - window.innerHeight;
      if (total > 0) {
        var pct = Math.min(100, Math.max(0, (-rect.top / total) * 100));
        bar.style.width = pct + "%";
      }
    };
    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update, { passive: true });
    update();
  }

  /* FAQ accordion: close siblings when one opens */
  var faqs = document.querySelectorAll(".faq details");
  if (faqs.length) {
    faqs.forEach(function (d) {
      d.addEventListener("toggle", function () {
        if (d.open) {
          faqs.forEach(function (other) {
            if (other !== d) other.open = false;
          });
        }
      });
    });
  }
})();
