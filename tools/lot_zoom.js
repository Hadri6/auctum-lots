(function () {
  // Full-screen photo viewer for cards with items[].zoom: tap the photo, swipe/arrows for the next photo,
  // tap the image (or pinch on phones) to see it at full resolution.
  var links = document.querySelectorAll('a.zm');
  if (!links.length) return;
  var v = document.createElement('div');
  v.id = 'zv';
  v.innerHTML = '<div class="zb"><button type="button" data-a="x" aria-label="Close">✕</button><span class="zn" dir="ltr"></span>' +
    '<a class="zo" target="_blank" rel="noopener">Original</a><span><button type="button" data-a="p" aria-label="Previous">‹</button> ' +
    '<button type="button" data-a="n" aria-label="Next">›</button></span></div><div class="zw"><img alt=""></div>';
  document.body.appendChild(v);
  var img = v.querySelector('img'), num = v.querySelector('.zn'), orig = v.querySelector('.zo'), list = [], i = 0, x0 = null;
  function show() {
    v.classList.remove('big');
    img.src = list[i];
    orig.href = list[i];
    num.textContent = (i + 1) + ' / ' + list.length;
    v.querySelector('[data-a="p"]').style.visibility = list.length > 1 ? '' : 'hidden';
    v.querySelector('[data-a="n"]').style.visibility = list.length > 1 ? '' : 'hidden';
  }
  function step(d) { i = (i + d + list.length) % list.length; show(); }
  function close() { v.classList.remove('on'); document.body.style.overflow = ''; img.removeAttribute('src'); }
  links.forEach(function (a) {
    a.addEventListener('click', function (ev) {
      ev.preventDefault();
      try { list = JSON.parse(a.getAttribute('data-z')); } catch (e) { list = [a.href]; }
      i = 0; show(); v.classList.add('on'); document.body.style.overflow = 'hidden';
    });
  });
  v.addEventListener('click', function (ev) {
    var b = ev.target.closest('button');
    if (b) { var k = b.getAttribute('data-a'); if (k === 'x') close(); else step(k === 'n' ? 1 : -1); return; }
    if (ev.target === img) v.classList.toggle('big');
  });
  document.addEventListener('keydown', function (ev) {
    if (!v.classList.contains('on')) return;
    if (ev.key === 'Escape') close();
    else if (ev.key === 'ArrowRight') step(document.documentElement.dir === 'rtl' ? -1 : 1);
    else if (ev.key === 'ArrowLeft') step(document.documentElement.dir === 'rtl' ? 1 : -1);
  });
  var zw = v.querySelector('.zw');
  zw.addEventListener('touchstart', function (ev) { x0 = ev.touches.length === 1 && !v.classList.contains('big') ? ev.touches[0].clientX : null; }, { passive: true });
  zw.addEventListener('touchend', function (ev) {
    if (x0 === null || list.length < 2) return;
    var dx = ev.changedTouches[0].clientX - x0;
    if (Math.abs(dx) > 50) step(dx < 0 ? 1 : -1);
    x0 = null;
  }, { passive: true });
})();
