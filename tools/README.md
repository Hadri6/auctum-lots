# قائمة احترافية — Professional lot manifest

Turns a raw manifest (xlsx/csv/pdf, no photos, no formatting) into a bilingual (EN/AR) photo manifest page
in the Auctum identity, published at `https://hadri6.github.io/auctum-lots/<slug>/`.
Reference result: `minet/` (Meubles Minet furniture, 2026-10-01).

## Hard rules (founder, 2026-10-01)
- Manifest only: **no prices, no WhatsApp/phone/email/contact buttons**, no liquidator/estate/source names, no purchase price.
- Same visual identity every time: `tools/lot.css` + `tools/lot.js` + `tools/build_lot.py`. Do not restyle per lot.
- `noindex`; root `index.html` stays a neutral page that links to no lot (traders get only their lot's link).
- Every page ends with a **summary-of-contents table** (founder, 2026-10-01): by product type (items, quantity, share, total)
  and, when there are several groups, by group. The builder generates it automatically from `type_en/type_ar` and `group`,
  so give every line a meaningful type — keep generic "Item"/"Furniture" to a minimum and use one spelling per type.

## Steps
1. **Read the manifest** and normalize every line into `lots/<slug>/items.json`:
   ```json
   [{"ref": "12", "name": "original item text", "qty": 7, "group": "collection-or-category key",
     "type_en": "Wardrobe", "type_ar": "خزانة ملابس", "img": "img/xxx.jpg" , "photo": "exact"}]
   ```
   - `ref`: the manifest's own line/rank number (stable reference for traders).
   - `group`: collection, brand or category key (lowercase); lines with no group → `"autres"` (shown last as "Other items").
   - `type_en` / `type_ar`: plain product type in both languages.
   - `img`: path relative to `lots/<slug>/`, or `null`. `photo`: `"exact"` (same product) or `"rep"` (representative).
2. **Find photos** (optional but expected): identify maker/brand from the codes and names, then look for the maker's
   catalogue images — official site, Wayback Machine (`web.archive.org/cdx/search/cdx?url=<site>/*`), retailer catalogues
   (e.g. the `images4.memoiredimages.fr/user/images/galerie_<maker>_*` CDN used by French furniture shops),
   Firecrawl search. Match each line by brand + type + variant tokens; download, resize to ≤420 px JPEG q72
   into `lots/<slug>/img/`. Lines without a convincing match keep `img: null` (listed in a table).
3. **Write `lots/<slug>/lot.json`** (see `lots/minet/lot.json`): `slug`, `page_title`, `title{en,ar}`, `subtitle{en,ar}`,
   optional `groups_word`, `kpis[]` (e.g. volume/weight), `location{en,ar}`, `groups{key:{en,ar,short}}`, `note{en,ar}`, `unit`.
4. **Build:** `python tools/build_lot.py lots/<slug>` → writes `<slug>/index.html` + `<slug>/img/`.
5. **Check:** card count, every `ref` present, and no `€|wa.me|whatsapp|+49|@|liquidat|insolv|Konkurs` in the page.
6. **Publish:** `git add -A && git commit -m "lot: <slug>" && git push` → GitHub Pages rebuilds in ~1 min.
   Hand the founder the link `https://hadri6.github.io/auctum-lots/<slug>/` (tell them `?v=2` busts phone caches).
