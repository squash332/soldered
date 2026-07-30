# Soldered Datasheet Generator

A small hosted tool: pick a solde.red product, choose a template, download a print-ready
A4 PDF datasheet generated from live product data.

## Deployment and running locally

**Deployed:** [soldered.onrender.com](https://soldered.onrender.com) (Render Web Service,
Docker environment).

**To deploy:** push to GitHub, create a Render Web Service with environment **Docker**
(the `Dockerfile` handles the Pango/Cairo/GDK-Pixbuf system libs WeasyPrint needs).
Render sets `$PORT` automatically. No env vars, no login.

**To run locally:**
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open `http://127.0.0.1:8000`. WeasyPrint needs Pango/Cairo/GDK-Pixbuf at the OS level
(Debian/Ubuntu: `sudo apt-get install libpango-1.0-0 libpangocairo-1.0-0 libcairo2 libgdk-pixbuf2.0-0`).

## Missing-data strategy (R3)

**Hide a section entirely when solde.red has no data for it**, rather than printing
"N/A" — e.g. `Variants` only renders with >1 variant, `Pinout` only if an image exists.
The brief says "don't invent sections... cover what's published, stop there," and a
visible "N/A" would imply a checked-and-absent value we can't actually distinguish from
"scraper missed it." Individual spec *fields* are never null once a section exists, so
no per-field missing-value case was needed.

## One-pager content decisions (R2)

Headline specs + "getting started"/"what it does" lines are chosen per **product
family**, derived from the product's own category breadcrumbs (`app/family_config.py`),
not a SKU list — so a new SKU in a known family needs zero code changes:
- **Display** (Inkplate 6): size, resolution, color, refresh rate, microcontroller.
- **Dev board** (NULA): microcontroller, clock, wireless, supply voltage, sleep current.
- **Sensor breakout** (SHTC3): sensor IC, measurement type/range/accuracy, interface, voltage.

Only 3 of the real catalog's ~10+ categories are hand-configured. Anything else gets a
**generic fallback** instead of an empty page: first 5–6 spec fields in source order;
a connect-line built only from fields actually present (omitted if none exist); "what it
does" falls back to Typical Applications' opening sentence if one exists. Verified
against SKU 333084 (Breadboard Power Supply, an unconfigured category) — full 1-page
one-pager, zero fabrication.

**A third case: some products have no structured spec fields at all** (SKU 333277, a
battery — `spec_groups` is genuinely empty in solde.red's own data, not a scraper miss).
The one-pager used to render a dangling "Key specifications" heading over an empty
table; now that heading is conditional, and both templates fall back to parsing the
prose `technical_details` list (voltage, capacity, connector, dimensions) into spec rows
when `spec_groups` is empty — real published data that was being scraped but never
shown. Only fires when `spec_groups` is empty, so it never duplicates the structured
table for every other product. The connect-line fallback also checks these parsed rows
for a "connector" mention as a last resort — it originally only checked structured
fields (`qwiic_compatible`, etc.), which don't exist for this product either, so
"Getting started" was silently missing even after the specs table was fixed.

## What was tested

- All 3 required SKUs × both templates (6 PDFs) — text-extracted and visually rendered,
  one-pagers confirmed exactly 1 page.
- Error paths (bad SKU, bad template) redirect with a message, no 500s.
- Missing-section handling confirmed per product (SHTC3 has no `Variants`, Inkplate no
  `Pinout`).
- Three non-graded SKUs specifically to test R1/R3 ("must handle any product"): 333238
  (Inkplate 6COLOR, same family), 333084 (Power & Batteries, unconfigured family), and
  333277 (a battery with zero structured spec fields) — see "How AI was used" for the
  bugs these caught.

**Not tested / left as-is:** only `en` locale used (`de`/`hr` scraped but unused, no
language selector); only 5 SKUs across 4 categories exercised — the fallback should hold
for the other ~8 categories but isn't individually verified; Typical Applications is
still curated per-SKU only, so the "what it does" fallback stays empty for any
non-graded, non-fallback-eligible SKU; no automated test suite.

## Data quality issues found in solde.red's own data

- **Inkplate 6:** description says "22uA," spec field says `25`. **NULA:** description
  says "7µA," spec field says `16` — over 2× off. Same product, disagreeing sources.
- Several numeric fields (`sleep_current_ua`, `supply_voltage_min/max_v`) ship with no
  `unit` at all; inferred from the field name (`app/labels.py`), not authoritative.
- NULA/SHTC3 pinout images still show the retired "easyC" branding — baked into the
  image, can't fix at the templating layer.
- SHTC3 links to `soldered.com/products/dasduino-core` — confirmed dead (redirects to a
  generic catalog page). Fixed: replaced with "NULA," dead link dropped.
- Inkplate's resource list has a duplicate entry ("Arduino: Get Started") — left as
  published.
- Checked on a 4th SKU (6COLOR) to see if issues are systemic: confirmed yes, left
  unfixed given time constraints — "Micropython" casing, boast-adjacent language
  ("the ideal choice," "a unique innovation"), and garbled source grammar all recur and
  read like solde.red's own copy, not tool bugs.

## How AI was used, and where it was wrong

Built end-to-end with Claude Code: scraping, models, routes, templates, README. Notable
mistakes, all caught by checking real output rather than trusting the code:

1. Assumed spec categories needed HTML-structure parsing per the brief's framing — the
   specs actually live in a clean JSON blob. Caught by fetching live pages before coding.
2. First normalization pass only humanized short enum codes, missing bare units
   ("Sleep Current Ua: 16"), raw field labels, and unformatted prose notation. Caught by
   a full field-by-field QA pass, not spot-checks.
3. The fix for missing degree symbols used a "digit+C" regex that then corrupted "I2C"
   into "I2°C" — caught only by re-verifying every field again immediately after the fix.
4. Scraped prose had exclamation marks, a grammar typo, and a dead "Dasduino Core" link —
   fixed narrowly (exact-string fixes, not a blanket rewrite) to avoid new errors; the
   dead-link claim was verified by actually fetching the URL, not assumed from a naming rule.
5. **Most significant, two-stage miss:** an early `family_config.py` mapped SKU→family
   with a hardcoded 3-SKU dict, while the README simultaneously claimed genuine
   per-family (not per-SKU) logic — both statements were individually true but
   contradicted each other in effect, and it only surfaced by testing a 4th SKU. The
   "fix" (deriving family from spec-group shape) was itself an unverified genericity
   claim: it only worked because that SKU coincidentally shared its family's spec shape.
   A second non-graded SKU from a truly unconfigured category exposed the same failure
   one level deeper. Properly fixed by scraping the actual category breadcrumb data and
   adding a real fallback path — this time tested against a case designed to break it.
   A third non-graded SKU (a product with zero structured spec fields, not just an
   unconfigured category) then caught a related bug in the fallback itself: the
   one-pager's "Key specifications" heading was unconditional, so an empty result still
   rendered a dangling header over a blank table — same "declared general, not actually
   tested against the edge case" pattern, one layer further down the stack.

## What was left out / would do differently with more time

- Real search across all ~270 products instead of a static seed list.
- A principled unit-taxonomy instead of a finite suffix lookup table.
- A significantly more reviewed tone-of-voice pass over scraped prose instead of pattern-matching.
- Automated tests (pytest) against saved HTML fixtures.
- A language selector for the already-scraped `de`/`hr` data.
- Testing against a non-graded, uncategorized SKU from the very start — both stages of
  the family-lookup bug would have surfaced immediately instead of late.
- Verifying the fallback path against more than one unconfigured category.
