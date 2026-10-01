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
