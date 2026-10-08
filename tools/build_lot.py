"""Build a professional lot manifest page ("قائمة احترافية") in the Auctum visual identity.

Usage:  python tools/build_lot.py lots/<slug>
Input:  lots/<slug>/lot.json    lot metadata (title, subtitle, KPIs, group labels)
        lots/<slug>/items.json  normalized items (see tools/README.md)
        lots/<slug>/img/        optional photos referenced by items[].img
Output: <slug>/index.html + <slug>/img/  (published by GitHub Pages)

The page is a manifest only: no prices, no contact links, no source/liquidator names.
Private price list:  python tools/build_lot.py <lot_dir> --private <out_dir>
  items[].price (EUR, line total) / items[].price_label {en, ar} are shown only in this mode, and the output
  goes to <out_dir> (never into the public repo). A public build refuses items that carry prices.
"""
import collections
import html
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, 'tools')
E = html.escape


def t(en, ar, tag='span', cls=''):
    c = f' class="{cls}"' if cls else ''
    return f'<{tag}{c} data-en="{E(en)}" data-ar="{E(ar)}">{E(en)}</{tag}>'


# Practical loading capacity per container (not the nominal internal volume).
CONTAINERS = [
    ("40′ High Cube", "حاوية 40 قدم High Cube", 68.0, 26.5),
    ("20′ Standard", "حاوية 20 قدم عادية", 28.0, 24.0),
]


def _rng(v):
    if v is None:
        return None
    return (float(v[0]), float(v[1])) if isinstance(v, (list, tuple)) else (float(v), float(v))


def _fmt(lo, hi, unit=''):
    f = lambda x: f'{x:,.0f}'
    return f'≈ {f(lo)}{unit}' if round(lo) == round(hi) else f'≈ {f(lo)}–{f(hi)}{unit}'


def _fmt_t(lo, hi):
    """Tonnes with sensible precision: below 10 t one decimal, else whole tonnes."""
    f = (lambda x: f'{x:,.1f}') if hi < 10 else (lambda x: f'{x:,.0f}')
    return f'≈ {f(lo)} t' if f(lo) == f(hi) else f'≈ {f(lo)}–{f(hi)} t'


def shipping_table(lot, item_weight=None):
    """Shipping estimate under the last summary table: total volume/weight and how many containers it fills.
    When items carry weights and lot.json gives no total, the item sum is used."""
    sh = lot.get('shipping')
    if not sh:
        return ''
    vol, wt = _rng(sh.get('volume_m3')), _rng(sh.get('weight_t')) or item_weight
    rows = ''
    if vol:
        rows += f'<tr><td>{t("Total volume (approx.)", "الحجم الإجمالي (تقريبي)")}</td><td>{_fmt(*vol, " m³")}</td></tr>'
    if wt:
        rows += f'<tr><td>{t("Total weight (approx.)", "الوزن الإجمالي (تقريبي)")}</td><td>{_fmt(*wt, " t")}</td></tr>'
    for en, ar, cap_v, cap_w in CONTAINERS:
        if en.startswith('20') and sh.get('no_20ft'):
            continue
        need = []
        for i in (0, 1):
            n = max((vol[i] / cap_v) if vol else 0, (wt[i] / cap_w) if wt else 0)
            need.append(max(1, -(-n // 1)))  # ceil, at least one container
        lo, hi = int(need[0]), int(need[1])
        val = f'{lo}' if lo == hi else f'{lo}–{hi}'
        rows += f'<tr><td>{t(en + " containers", ar)}</td><td><b>{val}</b></td></tr>'
    note = sh.get('note', {'en': 'Estimate based on the inventory data; final loading plan confirmed before shipment.',
                           'ar': 'تقدير مبني على بيانات الجرد؛ يُؤكَّد مخطط التحميل النهائي قبل الشحن.'})
    basis = t('Container capacity used: 40′ HC ≈ 68 m³ / 26.5 t, 20′ ≈ 28 m³ / 24 t (practical loading).',
              'السعة المعتمدة: 40 قدم HC ≈ 68 م³ / 26.5 طن، 20 قدم ≈ 28 م³ / 24 طن (تحميل عملي).')
    return (f'<h3 id="shipping">{t("Shipping estimate", "تقدير الشحن")}</h3><div class="sum">'
            f'<table><tbody>{rows}</tbody></table></div>'
            f'<div class="note">{t(note["en"], note["ar"])}<br>{basis}</div>')


def build(lot_dir, out_dir=None, private=False):
    lot = json.load(open(os.path.join(lot_dir, 'lot.json'), encoding='utf8'))
    items = json.load(open(os.path.join(lot_dir, 'items.json'), encoding='utf8'))
    slug = lot['slug']
    if not private and any(it.get('price') is not None for it in items):
        sys.exit('items carry prices: build them only with --private <out_dir> (public pages never show prices)')
    out = os.path.abspath(out_dir) if out_dir else os.path.join(ROOT, slug)
    if private and os.path.commonpath([out, ROOT]) == ROOT:
        sys.exit('--private output must be outside the public repo')
    if os.path.isdir(os.path.join(out, 'img')):
        shutil.rmtree(os.path.join(out, 'img'))
    os.makedirs(os.path.join(out, 'img'), exist_ok=True)

    labels = lot.get('groups', {})
    other = lot.get('other_group', 'autres')
    groups = collections.defaultdict(list)
    for it in items:
        groups[it.get('group') or other].append(it)
    order = sorted(groups, key=lambda k: (k == other, -sum(x['qty'] for x in groups[k])))
    if lot.get('group_order'):  # optional explicit order (e.g. most valuable groups first)
        pref = lot['group_order']
        order = sorted(order, key=lambda k: (k == other, pref.index(k) if k in pref else len(pref)))

    def label(k):
        if k in labels:
            return labels[k]['en'], labels[k]['ar']
        if k == other:
            return 'Other items', 'قطع أخرى'
        return f'{k.upper()} collection', f'تشكيلة {k.upper()}'

    def short(k):
        return labels.get(k, {}).get('short') or ('Others' if k == other else k.upper())

    copied = set()

    def photo(it):
        p = it.get('img')
        if not p:
            return None
        src = os.path.join(lot_dir, p)
        if not os.path.exists(src):
            return None
        name = os.path.basename(src)
        if name not in copied:
            shutil.copy(src, os.path.join(out, 'img', name))
            copied.add(name)
        return 'img/' + name

    # Optional completeness status per line (lot.json "statuses": {key: {en, ar, cls, desc_en, desc_ar}}):
    # shown as a chip on cards/rows, as a filter bar and as a summary table.
    statuses = lot.get('statuses', {})

    def st_chip(it):
        s = statuses.get(it.get('status'))
        return t(s['en'], s['ar'], cls=f'st {s.get("cls", it["status"])}') if s else ''

    def st_attr(it):
        return f' data-st="{E(it["status"])}"' if it.get('status') in statuses else ''

    def note_html(it):
        n = it.get('note')
        return t(n['en'], n['ar'], tag='div', cls='nt') if n else ''

    def money(v):
        return f'€ {v:,.0f}'

    def psum(lst):
        return sum(x.get('price') or 0 for x in lst)

    def pr_html(it):
        if not private:
            return ''
        if it.get('price') is not None:
            return f'<div class="pr">{t("Price", "السعر")} <b>{money(it["price"])}</b></div>'
        pl = it.get('price_label')
        return f'<div class="pr">{t(pl["en"], pl["ar"], tag="b")}</div>' if pl else ''

    def pcell(it):
        if not private:
            return ''
        if it.get('price') is not None:
            return f'<td class="num">{money(it["price"])}</td>'
        pl = it.get('price_label')
        return f'<td>{t(pl["en"], pl["ar"]) if pl else "–"}</td>'

    def pcol(lst):
        return f'<td class="num">{money(psum(lst))}</td>' if private else ''

    pth = t('Price (EUR)', 'السعر (يورو)', tag='th') if private else ''

    unit_en, unit_ar = lot.get('unit', ['pcs', 'قطعة'])
    total_qty = sum(it['qty'] for it in items)
    nav = ''.join(f'<a href="#c-{k}">{E(short(k))} <span>{sum(x["qty"] for x in groups[k])}</span></a>' for k in order)

    # Optional per-item weight (tonnes, number or [lo, hi]) → shown on cards, summary tables and shipping estimate.
    has_w = any(it.get('weight_t') is not None for it in items)

    def wsum(lst):
        ws = [_rng(x.get('weight_t')) for x in lst if x.get('weight_t') is not None]
        return (sum(a for a, _ in ws), sum(b for _, b in ws)) if ws else None

    sec = ''
    for k in order:
        # With statuses: complete pieces first, components and incomplete pieces last; then by quantity.
        st_order = list(statuses)
        L = sorted(groups[k], key=lambda x: (st_order.index(x['status']) if x.get('status') in st_order else 0,
                                             0 if lot.get('keep_order') else -x['qty']))  # keep_order: items.json order
        cards, rows, nrows = '', '', 0
        for it in L:
            ten, tar = it.get('type_en') or 'Item', it.get('type_ar') or 'صنف'
            src = photo(it)
            ref = f"#{it['ref']}"
            # Small lots (lot.json "all_cards": true) show photo-less lines as cards with a placeholder too.
            if src or lot.get('all_cards'):
                if src:
                    pl = it.get('photo_label')  # per-line override, e.g. "Photo shows the complete bed"
                    badge = (t(pl['en'], pl['ar'], cls='tag warn') if pl else
                             t('Product photo', 'صورة المنتج', cls='tag ok') if it.get('photo') == 'exact'
                             else t('Representative photo', 'صورة توضيحية', cls='tag rep'))
                    visual = f'<img loading="lazy" src="{src}" alt="{E(ten)}">{badge}'
                else:
                    visual = f'<div class="ph">{t(ten, tar)}</div>'
                w = _rng(it.get('weight_t'))
                wline = (f'<div class="wt">{t("Est. weight", "الوزن التقديري")} <b>{_fmt_t(*w)}</b></div>' if w else '')
                cards += (f'<figure class="card"{st_attr(it)}>{visual}<figcaption>{st_chip(it)}'
                          f'<div class="ty">{t(ten, tar)}</div><div class="nm" dir="ltr">{E(it["name"])}</div>'
                          f'{note_html(it)}{wline}{pr_html(it)}'
                          f'<div class="row"><span class="q"><b>{it["qty"]:,}</b> {t(unit_en, unit_ar)}</span>'
                          f'<span class="ref">Ref {E(ref)}</span></div></figcaption></figure>')
            else:
                nrows += 1
                w = _rng(it.get('weight_t'))
                wcell = f'<td>{_fmt_t(*w) if w else "–"}</td>' if has_w else ''
                scell = f'<td>{st_chip(it)}</td>' if statuses else ''
                ncell = (f'<td><span dir="ltr">{E(it["name"])}</span>{note_html(it)}</td>' if it.get('note')
                         else f'<td dir="ltr">{E(it["name"])}</td>')
                rows += (f'<tr{st_attr(it)}><td>Ref {E(ref)}</td>{ncell}'
                         f'<td>{t(ten, tar)}</td>{scell}<td>{it["qty"]:,}</td>{wcell}{pcell(it)}</tr>')
        en, ar = label(k)
        sec += (f'<section id="c-{k}"><h2>{t(en, ar)} <small>{len(L)} {t("items", "صنف")} · '
                f'{sum(x["qty"] for x in L):,} {t(unit_en, unit_ar)}</small></h2>')
        if cards:
            sec += f'<div class="grid">{cards}</div>'
        if rows:
            head = (f'<thead><tr><th>Ref</th>{t("Item", "الصنف", tag="th")}{t("Type", "النوع", tag="th")}'
                    f'{t("Status", "الحالة", tag="th") if statuses else ""}{t("Qty", "الكمية", tag="th")}{t("Est. weight", "الوزن التقديري", tag="th") if has_w else ""}{pth}</tr></thead>')
            if cards:
                sec += (f'<details{" open" if private else ""}>{t(f"More items without photo ({nrows})", f"أصناف أخرى بدون صورة ({nrows})", tag="summary")}'
                        f'<table>{head}<tbody>{rows}</tbody></table></details>')
            else:
                sec += f'<table>{head}<tbody>{rows}</tbody></table>'
        sec += '</section>'

    # Summary of all contents at the end of the page: by product type, then by group.
    by_type = collections.OrderedDict()
    for it in items:
        key = (it.get('type_en') or 'Item', it.get('type_ar') or 'صنف')
        by_type.setdefault(key, []).append(it)

    def wcol(lst):
        if not has_w:
            return ''
        w = wsum(lst)
        return f'<td>{_fmt_t(*w) if w else "–"}</td>'

    type_rows = ''.join(f'<tr><td>{t(en, ar)}</td><td>{len(L):,}</td><td>{sum(x["qty"] for x in L):,}</td>'
                        f'<td>{sum(x["qty"] for x in L) * 100 / total_qty:.1f}%</td>{wcol(L)}{pcol(L)}</tr>'
                        for (en, ar), L in sorted(by_type.items(), key=lambda x: -sum(i['qty'] for i in x[1])))
    total_row = (f'<tr class="tot"><td>{t("Total", "المجموع")}</td><td>{len(items):,}</td>'
                 f'<td>{total_qty:,}</td><td>100%</td>{wcol(items)}{pcol(items)}</tr>')
    head = (f'<thead><tr>{t("{0}", "{1}", tag="th")}{t("Items", "الأصناف", tag="th")}'
            f'{t(f"Quantity ({unit_en})", f"الكمية ({unit_ar})", tag="th")}{t("Share", "النسبة", tag="th")}'
            f'{t("Est. weight", "الوزن التقديري", tag="th") if has_w else ""}{pth}</tr></thead>')
    summary = f'<section id="summary"><h2>{t("Summary of contents", "ملخص المحتويات")}</h2>'
    if statuses:
        st_rows = ''
        for key, s in statuses.items():
            L = [x for x in items if x.get('status') == key]
            if not L:
                continue
            q = sum(x['qty'] for x in L)
            desc = t(s['desc_en'], s['desc_ar'], tag='div', cls='nt') if s.get('desc_en') else ''
            st_rows += (f'<tr><td>{st_chip({"status": key})}{desc}</td><td>{len(L):,}</td><td>{q:,}</td>'
                        f'<td>{q * 100 / total_qty:.1f}%</td>{wcol(L)}{pcol(L)}</tr>')
        stt = lot.get('status_title', {'en': 'By completeness', 'ar': 'حسب اكتمال القطعة'})
        summary += (f'<h3>{t(stt["en"], stt["ar"])}</h3><div class="sum">'
                    f'<table>{head.replace("{0}", "Status").replace("{1}", "الحالة")}<tbody>{st_rows}{total_row}</tbody></table></div>')
    summary += (f'<h3>{t("By product type", "حسب نوع القطعة")}</h3><div class="sum">'
               f'<table>{head.replace("{0}", "Product type").replace("{1}", "نوع القطعة")}<tbody>{type_rows}{total_row}</tbody></table></div>')
    if len(groups) > 1:
        grp_word = lot.get('groups_word', ['Group', 'المجموعة'])
        grp_rows = ''
        for k in order:
            q = sum(x['qty'] for x in groups[k])
            en, ar = label(k)
            grp_rows += (f'<tr><td><a href="#c-{k}">{t(en, ar)}</a></td><td>{len(groups[k]):,}</td>'
                         f'<td>{q:,}</td><td>{q * 100 / total_qty:.1f}%</td>{wcol(groups[k])}{pcol(groups[k])}</tr>')
        summary += (f'<h3>{t("By " + grp_word[0].lower().rstrip("s"), "حسب " + grp_word[1])}</h3><div class="sum">'
                    f'<table>{head.replace("{0}", grp_word[0].rstrip("s")).replace("{1}", grp_word[1])}'
                    f'<tbody>{grp_rows}{total_row}</tbody></table></div>')
    summary += shipping_table(lot, wsum(items) if has_w else None)
    summary += '</section>'
    sec += summary
    nav += f'<a href="#summary">{t("Summary", "الملخص")}</a>'

    # Optional "read first" block at the top of the page (lot.json "sets"): what can be assembled into complete
    # products from the lines of this lot. Rows: {en, ar, qty, detail: {en, ar}}.
    sets, top = lot.get('sets'), ''
    if sets:
        srows = ''.join(f'<tr><td>{t(r["en"], r["ar"], tag="b")}'
                        f'{t(r["detail"]["en"], r["detail"]["ar"], tag="div", cls="nt") if r.get("detail") else ""}</td>'
                        f'<td>{E(str(r["qty"]))}</td></tr>' for r in sets['rows'])
        intro = t(sets['intro']['en'], sets['intro']['ar'], tag='p', cls='intro') if sets.get('intro') else ''
        snote = t(sets['note']['en'], sets['note']['ar'], tag='div', cls='note') if sets.get('note') else ''
        top = (f'<section id="sets" class="sets"><h2>{t(sets["title"]["en"], sets["title"]["ar"])}</h2>{intro}'
               f'<div class="sum"><table><thead><tr>{t("What", "الصنف", tag="th")}'
               f'{t(*sets.get("col", ["Quantity", "الكمية"]), tag="th")}</tr></thead><tbody>{srows}</tbody></table></div>{snote}</section>')
        nav = f'<a href="#sets">{t(sets.get("nav", {}).get("en", "Read first"), sets.get("nav", {}).get("ar", "اقرأ أولاً"))}</a>' + nav
    if statuses:
        btns = ''.join(f'<button data-f="{E(k)}">{t(s["en"], s["ar"])} <span>'
                       f'{sum(x["qty"] for x in items if x.get("status") == k):,}</span></button>'
                       for k, s in statuses.items() if any(x.get('status') == k for x in items))
        top += (f'<div class="flt" id="flt">{t("Show:", "عرض:", cls="lbl")}<button data-f="" class="on">'
                f'{t("All", "الكل")}</button>{btns}</div>')
    sec = top + sec

    ql_en, ql_ar = lot.get('qty_label', ['Pieces', 'قطعة'])
    kpis = [(ql_en, ql_ar, (f'{total_qty:,}' if lot.get('qty_exact') else f'≈ {total_qty:,}')), ('Items', 'صنف', f'{len(items):,}')]
    if len(groups) > 1:
        kpis.append(('Groups' if lot.get('groups_word') is None else lot['groups_word'][0],
                     'مجموعة' if lot.get('groups_word') is None else lot['groups_word'][1],
                     str(len([g for g in groups if g != other]))))
    if private:
        kpis.append(('Package price', 'سعر الحزمة', money(psum(items))))
    for extra in lot.get('kpis', []):
        kpis.append((extra['en'], extra['ar'], extra['value']))
    kpi_html = ''.join(f'<div>{t(a, b)}<b>{E(v)}</b></div>' for a, b, v in kpis)
    loc = lot.get('location')
    if loc:
        kpi_html += f'<div>{t("Location", "الموقع")}{t(loc["en"], loc["ar"], tag="b")}</div>'

    note = lot.get('note', {'en': 'Photos are catalogue pictures of the same models; finishes and colours may differ. Subject to prior sale.',
                            'ar': 'الصور من كتالوج نفس الموديلات وقد يختلف اللون أو التشطيب. البضاعة متاحة حتى نفادها.'})
    credits = f'<footer class="credits">{E(lot["credits"])}</footer>\n' if lot.get('credits') else ''
    css = open(os.path.join(TOOLS, 'lot.css'), encoding='utf8').read()
    js = open(os.path.join(TOOLS, 'lot.js'), encoding='utf8').read()
    if private:
        css += ('.pr{margin-top:6px;font-size:14px;color:var(--mut)}.pr b{color:var(--acc);font-size:17px}'
                'td.num{text-align:end;white-space:nowrap;font-variant-numeric:tabular-nums}')
    page = f'''<!doctype html><html lang="en" dir="ltr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(lot["page_title"])}</title>
<meta name="description" content="{E(lot["subtitle"]["en"])}">
<meta name="robots" content="noindex"><style>{css}</style></head><body>
<header><div class="top"><div class="brand">AUCTUM GMBH · GERMANY</div><button class="lang" id="lang">العربية</button></div>
{t(lot["title"]["en"], lot["title"]["ar"], tag="h1")}
{t(lot["subtitle"]["en"], lot["subtitle"]["ar"], tag="div", cls="sub")}
<div class="kpi">{kpi_html}</div>
{t(note["en"], note["ar"], tag="div", cls="note")}
</header>
<nav>{nav}</nav><main>{sec}</main>
{credits}<script>{js}</script></body></html>'''
    open(os.path.join(out, 'index.html'), 'w', encoding='utf8').write(page)
    print(f'built {slug}/index.html: {len(items)} items, {total_qty} {unit_en}, {len(copied)} photos, '
          f'{sum(1 for it in items if photo(it))} items with photo')


if __name__ == '__main__':
    a = sys.argv[1:]
    if '--private' in a:
        i = a.index('--private')
        build(os.path.abspath(a[0]), out_dir=a[i + 1], private=True)
    else:
        build(os.path.abspath(a[0]))
