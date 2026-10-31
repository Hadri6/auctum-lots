// Price calculator (lot.json "price_calc"): quantity per model → tier price, line total, lot total and load estimate.
(function () {
  var box = document.getElementById('calc');
  if (!box) return;
  var P = JSON.parse(document.getElementById('calc-data').textContent);
  var rows = [].slice.call(box.querySelectorAll('.cr'));
  function ar() { return document.documentElement.lang === 'ar'; }
  function L(el, en, a) { el.setAttribute('data-en', en); el.setAttribute('data-ar', a); el.textContent = ar() ? a : en; }
  function n(v, d) { return v.toLocaleString('en-US', { maximumFractionDigits: d || 0, minimumFractionDigits: d || 0 }); }
  function eur(v) { return '€ ' + n(v); }
  function rng(lo, hi, d, u) { return '≈ ' + (n(lo, d) === n(hi, d) ? n(lo, d) : n(lo, d) + '–' + n(hi, d)) + u; }
  function qty(r) {
    var c = r._c, v = parseInt(r._i.value, 10);
    return v > 0 ? Math.min(c.max, Math.ceil(v / c.pallet) * c.pallet) : 0;
  }
  function tier(c, q) {
    var i = 0;
    P.tiers.forEach(function (t, k) { if (k < c.tiers.length && q >= t.min) i = k; });
    return i;
  }
  function calc() {
    var full = {}, used = {}, tq = 0, tp = 0, te = 0, kg = [0, 0], m3 = [0, 0];
    rows.forEach(function (r) {
      var l = r._c.lot, q = qty(r);
      if (full[l] === undefined) full[l] = true;
      if (q !== r._c.max) full[l] = false;
      if (q) used[l] = true;
    });
    rows.forEach(function (r) {
      var c = r._c, q = qty(r), u = r.querySelector('.cu'), tl = r.querySelector('.ct'), lt = r.querySelector('.cl');
      r.classList.toggle('on', q > 0);
      if (!q) { L(u, '', ''); L(tl, '', ''); L(lt, '–', '–'); return; }
      var isFull = full[c.lot], i = tier(c, q), p = isFull ? c.full : c.tiers[i], tn = isFull ? P.full : P.tiers[i];
      var pal = q / c.pallet, adj = parseInt(r._i.value, 10) !== q;
      L(u, eur(p) + ' / pc', eur(p) + ' / قطعة');
      L(tl, tn.en + ' · ' + n(q) + ' pcs = ' + n(pal) + ' pallets' + (adj ? ' (rounded to full pallets)' : ''),
        tn.ar + ' · ' + n(q) + ' قطعة = ' + n(pal) + ' منصّة' + (adj ? ' (مقرّبة لمنصّات كاملة)' : ''));
      L(lt, eur(p * q), eur(p * q));
      tq += q; tp += pal; te += p * q;
      kg[0] += q * c.unit_kg[0]; kg[1] += q * c.unit_kg[1]; m3[0] += q * c.unit_m3[0]; m3[1] += q * c.unit_m3[1];
    });
    box.querySelectorAll('.chint').forEach(function (h) {
      var l = h.getAttribute('data-lot');
      if (full[l]) L(h, '✓ Complete-lot price applied', '✓ طُبِّق سعر الدفعة كاملة');
      else if (used[l]) L(h, 'Complete-lot price only if every model of this lot is taken in full',
        'سعر الدفعة كاملة فقط عند أخذ كل موديلات هذه الدفعة بكامل كميتها');
      else L(h, '', '');
    });
    L(document.getElementById('t-q'), n(tq), n(tq));
    L(document.getElementById('t-p'), n(tp), n(tp));
    var w = tq ? rng(kg[0] / 1000, kg[1] / 1000, kg[1] < 10000 ? 1 : 0, ' t') : '–';
    L(document.getElementById('t-w'), w, w);
    var cont = [0, 1].map(function (k) { return Math.max(1, Math.ceil(Math.max(m3[k] / P.cap[0], kg[k] / 1000 / P.cap[1]))); });
    var cn = cont[0] === cont[1] ? '' + cont[0] : cont[0] + '–' + cont[1];
    var v = tq ? rng(m3[0], m3[1], 0, ' m³') : '–';
    L(document.getElementById('t-v'), tq ? v + ' · ' + cn + ' × 40′ HC' : '–', tq ? v + ' · ' + cn + ' × 40′ HC' : '–');
    L(document.getElementById('t-e'), eur(te), eur(te));
  }
  rows.forEach(function (r) {
    r._c = JSON.parse(r.getAttribute('data-c'));
    r._i = r.querySelector('input');
    r._i.addEventListener('input', calc);
    r._i.addEventListener('change', function () { var q = qty(r); r._i.value = q || ''; calc(); });
    r.querySelector('.call').addEventListener('click', function () { r._i.value = r._c.max; calc(); });
  });
  box.querySelectorAll('.cfull').forEach(function (b) {
    b.addEventListener('click', function () {
      rows.forEach(function (r) { if (r._c.lot === b.getAttribute('data-lot')) r._i.value = r._c.max; });
      calc();
    });
  });
  document.getElementById('creset').addEventListener('click', function () {
    rows.forEach(function (r) { r._i.value = ''; });
    calc();
  });
  calc();
})();
