(function () {
  var b = document.getElementById('lang'), cur = 'en';
  function set(l) {
    cur = l;
    document.documentElement.lang = l;
    document.documentElement.dir = l === 'ar' ? 'rtl' : 'ltr';
    document.querySelectorAll('[data-' + l + ']').forEach(function (e) { e.textContent = e.getAttribute('data-' + l); });
    b.textContent = l === 'ar' ? 'English' : 'العربية';
    try { localStorage.setItem('lang', l); } catch (e) {}
  }
  b.onclick = function () { set(cur === 'en' ? 'ar' : 'en'); };
  var s = null;
  try { s = localStorage.getItem('lang'); } catch (e) {}
  if (!s && (navigator.language || '').indexOf('ar') === 0) s = 'ar';
  if (s === 'ar') set('ar');
})();
(function () {
  var f = document.getElementById('flt');
  if (!f) return;
  f.addEventListener('click', function (ev) {
    var b = ev.target.closest('button');
    if (!b) return;
    var k = b.getAttribute('data-f');
    f.querySelectorAll('button').forEach(function (x) { x.classList.toggle('on', x === b); });
    document.querySelectorAll('[data-st]').forEach(function (e) {
      e.classList.toggle('hid', !!k && e.getAttribute('data-st') !== k);
    });
    // Hide collection sections (and "more items" tables) left without any visible line; open tables when filtering.
    document.querySelectorAll('main section[id^="c-"]').forEach(function (s) {
      var any = s.querySelector('[data-st]:not(.hid)');
      s.classList.toggle('hid', !!k && !any);
      var d = s.querySelector('details');
      if (d) {
        var rowsVis = d.querySelector('tr[data-st]:not(.hid)');
        d.classList.toggle('hid', !!k && !rowsVis);
        if (k && rowsVis) d.open = true;
      }
    });
  });
})();
