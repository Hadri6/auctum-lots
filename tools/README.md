# قائمة احترافية — Professional lot manifest

Turns a raw manifest (xlsx/csv/pdf, no photos, no formatting) into a bilingual (EN/AR) photo manifest page
in the Auctum identity, published at `https://hadri6.github.io/auctum-lots/<slug>/`.
Reference result: `minet/` (Meubles Minet furniture, 2026-10-01).

## Hard rules (founder, 2026-10-01)
- Manifest only: **no prices, no WhatsApp/phone/email/contact buttons**, no liquidator/estate/source names, no purchase price.
- Same visual identity every time: `tools/lot.css` + `tools/lot.js` + `tools/build_lot.py`. Do not restyle per lot.
- `noindex`; root `index.html` stays a neutral page that links to no lot (traders get only their lot's link).
- Under the last summary table every page shows a **shipping estimate** (founder, 2026-10-01): total volume and weight
  (approx.) and how many 40′ HC and 20′ containers the lot fills. Set `lot.json` → `"shipping": {"volume_m3": x | [lo, hi],
  "weight_t": y | [lo, hi], "note": {en, ar}, "no_20ft": false}`; the builder computes containers with practical capacity
  40′ HC ≈ 68 m³ / 26.5 t and 20′ ≈ 28 m³ / 24 t (whichever limit binds). Use exact volume/weight from the manifest when
  given (sum qty × unit volume/weight); otherwise estimate a range and say so in the note (e.g. long steel > 5.9 m → 40′ only).
- Optional per-line weight: `items[].weight_t` (number or `[lo, hi]` tonnes). When present it appears on each card
  ("Est. weight"), as a column in both summary tables, and the shipping total uses the sum of the lines unless
  `shipping.weight_t` is set. Use it whenever the manifest lacks weights for bulk goods (steel, parts): estimate per line from
  quantities/dimensions or inventory value ÷ typical €/kg for the product type; keep the basis in the private source script.
- The repo is public: everything under `lots/` and `<slug>/` is served. Use a **neutral slug and neutral photo file names**
  (e.g. `conveyor-steel`, `p_<ref>.jpg`) whenever the company name would reveal the estate; only a product brand
  (like `minet`) may appear. Parsing/photo scripts and raw lists live outside the repo in
  `C:\Users\G4M3R\Projects\auctum-lots-src\<slug>\` and write their output into `lots/<slug>/`.
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
   Firecrawl search. For generic industrial goods (no brand catalogue) use freely licensed images: Wikimedia Commons API
   (search English and German terms) and Openverse (`api.openverse.org/v1/images/?license_type=commercial&q=...`);
   review a contact sheet before using, and list author + licence per photo in `lot.json` `credits`.
   Every line should end up with at least a representative photo (founder, 2026-10-01). Match each line by brand + type + variant tokens; download, resize to ≤420 px JPEG q72
   into `lots/<slug>/img/`. Lines without a convincing match keep `img: null` (listed in a table).
3. **Write `lots/<slug>/lot.json`** (see `lots/minet/lot.json`): `slug`, `page_title`, `title{en,ar}`, `subtitle{en,ar}`,
   optional `groups_word`, `kpis[]` (e.g. volume/weight), `location{en,ar}`, `groups{key:{en,ar,short}}`, `note{en,ar}`, `unit`.
4. **Build:** `python tools/build_lot.py lots/<slug>` → writes `<slug>/index.html` + `<slug>/img/`.
5. **Check:** card count, every `ref` present, and no `€|wa.me|whatsapp|+49|@|liquidat|insolv|Konkurs` in the page.
6. **Publish:** `git add -A && git commit -m "lot: <slug>" && git push` → GitHub Pages rebuilds in ~1 min.
   Hand the founder the link `https://hadri6.github.io/auctum-lots/<slug>/` (tell them `?v=2` busts phone caches).

## Completeness status (founder, 2026-10-04)
Traders read a line like "LIT …" or a bed photo as a whole product. Whenever a manifest mixes complete goods with frames,
stand-alone parts or incomplete pieces, mark every line:
- `items[].status` – a key of `lot.json` → `"statuses": {key: {en, ar, cls, desc_en, desc_ar}}` (cls: ok, mod, kit, add,
  part, bad). The page then shows a chip on each card/row, a filter bar ("Show: …") and a "By completeness" summary
  table; within each group complete lines come first.
- `items[].note` `{en, ar}` – one line under the item name (what is / is not included).
- `items[].photo_label` `{en, ar}` – replaces the photo badge (orange) when the photo shows more than the line contains.
- `lot.json` → `"sets": {title, nav, intro, rows: [{en, ar, qty, detail: {en, ar}}], note}` – a "Read first" table at the top
  of the page: what is complete and what can be assembled from this lot alone.
Verify against the maker's own catalogue (Wayback Machine of the maker's site) before deciding what a line contains.
Reference: `minet/` (source script `auctum-lots-src/minet/build_items.py` + `lot_meta.py`).
