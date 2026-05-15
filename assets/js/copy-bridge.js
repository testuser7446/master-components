/* copy-bridge.js — postMessage bridge for the Component Library */
(function () {

  /* ── Copy HTML ─────────────────────────────────────────────────────── */
  window.addEventListener('message', function (e) {
    if (!e.data) return;

    if (e.data.type === 'requestHTML') {
      var bodyClone = document.body.cloneNode(true);

      ['back-nav', 'back-nav-bar'].forEach(function (id) {
        var el = bodyClone.querySelector('#' + id);
        if (el) el.remove();
      });

      Array.from(bodyClone.querySelectorAll('[class]')).forEach(function (el) {
        var cls = el.getAttribute('class') || '';
        if (cls.indexOf('fixed') !== -1 && cls.indexOf('top-0') !== -1) el.remove();
      });

      var section = bodyClone.querySelector('section');
      var html = section ? section.outerHTML.trim() : bodyClone.innerHTML.trim();

      try { e.source.postMessage({ type: 'htmlResponse', html: html }, '*'); } catch (err) {}
    }
  });


})();
