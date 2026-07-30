# Soldered Datasheet Generator

A small hosted tool: pick a solde.red product, choose a template, download a print-ready
A4 PDF datasheet generated from live product data.

## Deployment and running locally

**Deployed:** not yet live. This environment had no Render CLI/API access, so the app is
built, tested, and Docker-ready, but the actual Render service still needs to be created
manually (see below).

**To deploy to Render:**
1. Push this repo to GitHub (or GitLab/Bitbucket).
2. In Render, create a new **Web Service** from that repo, environment **Docker** (the
   `Dockerfile` in the repo root handles everything, including the Pango/Cairo/GDK-Pixbuf
   system libraries WeasyPrint needs — no build-command overrides required).
3. Render sets `$PORT` automatically; the Dockerfile's `CMD` already reads it.
4. No environment variables or secrets are required — no login, no external services.

**To run locally:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open `http://127.0.0.1:8000`, pick a product (or type any SKU), choose a template, and
generate. WeasyPrint needs Pango/Cairo/GDK-Pixbuf installed at the OS level; on
Debian/Ubuntu: `sudo apt-get install libpango-1.0-0 libpangocairo-1.0-0 libcairo2 libgdk-pixbuf2.0-0`.

## Missing-data strategy (R3)

**Decision: hide a section entirely when solde.red has no data for it, rather than
printing "N/A" or a placeholder.** Concretely: `Variants` only renders if a product has
more than one variant; `Pinout` only renders if a pinout image exists; `What's in the
box` and `Resources and downloads` only render if their respective HTML sections exist
on the source page. Confirmed working — e.g. the SHTC3 breakout has no `Variants`
heading at all (not an empty table), and Inkplate 6 has no `Pinout` section (it doesn't
have exposed pins).

**Reasoning:** the brief explicitly says "don't invent sections to fill pages — cover
what's published, stop there." A visible "N/A" implies the data was checked and is
genuinely absent, which we can't always distinguish from "our scraper didn't find it."
Hiding the section is the conservative choice for a customer-facing document, and it
composes cleanly with the fact that spec *categories* themselves already differ per
product family (a display has no `measurement` group; a sensor has no `display` group).

For individual spec *fields* within a present section, the site itself never sends a
field with a null/missing value — every field returned always has a value — so no
per-field missing-value case was needed in practice.

## One-pager content decisions (R2)

Headline specs and the "getting started" line are chosen per **product family**, not
per SKU (`app/family_config.py`), so extending to a new SKU in the same family later is
a one-line change:

- **Display family** (Inkplate 6): display size, resolution, color mode, refresh rate,
  microcontroller — the specs a buyer scanning a datasheet actually decides on.
- **Dev board family** (NULA DeepSleep): microcontroller, clock speed, wireless,
  supply voltage, sleep current — the numbers that matter for a battery-powered project.
- **Sensor breakout family** (SHTC3): sensor IC, what it measures, range, accuracy,
  interface, supply voltage — accuracy and range are the headline numbers for a sensor.

The "getting started" line is one factual sentence per family (not per SKU), grounded in
confirmed spec fields (`dev_environments`, `qwiic_compatible`, `breadboard_compatible`,
interface type) rather than invented copy.

## What was tested

- All 3 required SKUs × both templates (6 PDFs), generated via the running app and
  inspected both as extracted text (`pdftotext`) and rendered images (`pdftoppm`) at
  each stage of development.
- One-pagers confirmed to be exactly 1 page for all 3 SKUs (`pypdf` page count).
- Error paths: an unknown SKU and an unknown template both redirect to the form with a
  readable error message — no 500s.
- Missing-section handling confirmed per-product (see R3 above): sections that don't
  apply to a given family genuinely don't render, rather than rendering empty.
- A full QA pass re-reading every rendered field across all 3 SKUs after each fix,
  specifically to catch regressions the fix itself might introduce (see "where AI was
  wrong" below — this caught a real bug before it shipped).

**Unresolved / not tested:**
- Only the `en` locale is used; `de`/`hr` data exists in the scraped JSON but isn't
  wired into the UI (no language selector).
- Only the 3 graded SKUs and their immediate families have been exercised end-to-end.
  A genuinely new product family (a fourth kind of product) would need one line added
  to `family_config.py` and would benefit from re-running the same field-by-field check
  described above before trusting its output.
- No automated test suite (pytest) — verification was done via ad hoc scripts run
  against the live app, not checked-in tests.

## Data quality issues found in solde.red's own data

- **Inkplate 6:** marketing copy says "22uA" deep-sleep current; the structured spec
  field (`sleep_current_ua`) says `25`. Both can't be right.
- **NULA DeepSleep ESP32-S3:** marketing copy says "7µA deep sleep current"; the
  structured spec field says `16` — over a 2× discrepancy between the site's own prose
  and its own structured data for the same number.
- Several numeric fields ship with an empty `unit` in the API despite clearly having
  one (`sleep_current_ua`, `supply_voltage_min_v/max_v`) — the unit is only implied by
  the field name. We infer it from a name-suffix table (`app/labels.py`) rather than
  leaving the number bare, but this is inference, not authoritative data.
- The NULA and SHTC3 pinout diagrams are raster images hosted on solde.red's CMS and
  still show the retired "easyC" branding (superseded by "qwiic"). This can't be fixed
  at the templating layer since it's baked into the image, not text we control.
- SHTC3's description links to `soldered.com/products/dasduino-core` — confirmed dead
  (redirects to a generic category page, not a live product). "Dasduino" is the retired
  name of the product line NULA replaced, so this is stale pre-rebrand copy, not a
  reference to a real, still-sold, distinct product. Fixed in `app/content.py` by
  replacing the mention (and dropping the dead link) with "NULA."
- Inkplate 6's resource list has "Arduino: Get Started (DOCS)" listed twice — a
  duplicate on solde.red's side. Left as published rather than silently deduplicating,
  consistent with the "cover what's published, don't invent" rule — worth a second look
  if this recurs on other products.

## How AI was used, and where it was wrong

This project was built with Claude Code end-to-end: scraping/parsing design, the
Pydantic model, FastAPI routes, Jinja2/WeasyPrint templates, and this README. Several
mistakes surfaced along the way, all caught by actually checking output against ground
truth rather than trusting the code's own logic:

1. The original handoff brief assumed spec categories had to be parsed from HTML
   structure since "categories differ per family." That was half-right: categories do
   differ per family, but the specs themselves live in a clean embedded JSON blob, not
   scattered HTML — caught only by directly fetching and inspecting the live pages
   before writing the scraper, rather than trusting the brief's framing at face value.
2. The first version of the unit/label-normalization layer (`app/labels.py`) only
   humanized short enum-style codes (like `wifi4` → "Wi-Fi 4"). It missed three classes
   of problems: numeric fields with no unit shown at all (`Sleep Current Ua: 16`), raw
   snake_case field *labels* leaking straight into headings ("Mcu Part Number"), and
   unformatted notation buried inside free-text spec values ("Temperature -40 to 125 C"
   instead of "-40°C to 125°C"). These were only caught by a QA pass that read every
   rendered field on every SKU, not by spot-checking one or two.
3. Fixing the temperature-notation issue with a general "digit followed by C" regex
   introduced a *new* bug: it matched the "2C" inside "I2C" and corrupted an interface
   field to "I2°C". This was only caught because the fix was re-verified against every
   field on every SKU again immediately after writing it, rather than only checking the
   one field that motivated the change — a direct illustration of why a "general rule"
   still needs boundary conditions, not just broader matching.
4. Scraped marketing description text was initially rendered untouched into a
   professional datasheet, including forced exclamation marks, a grammar error ("Due to
   it's ample connectivity"), and a mention of "Dasduino Core" with a dead outbound
   link. The exclamation marks and the specific known typo were fixed as narrow,
   deterministic rules (not a general "rewrite prose" pass, which risks introducing new
   errors). The "Dasduino Core" reference required an actual live check — fetching the
   linked URL to confirm it redirects to a generic catalog page — rather than assuming
   from the naming convention alone that it was safe to rewrite.
5. The unit-suffix and field-label-override tables are still finite lookup tables, not
   a truly general solution — a genuinely new unit type or a differently-named field on
   a future product will not be covered automatically and needs a one-line addition,
   the same way `family_config.py` does for headline specs.

## What was left out / would do differently with more time

- A real search/index across all ~270 solde.red products instead of a static 3-SKU seed
  list (the picker still accepts any SKU typed directly).
- A more principled unit-type system (e.g. a small unit-taxonomy keyed on physical
  quantity) instead of a finite string-suffix lookup table.
- A broader, reviewed tone-of-voice normalization pass over scraped prose, ideally with
  a human edit rather than automated pattern-matching, since automated rewriting of
  "boast-adjacent" language risks its own false positives (as seen with the "I2C" bug).
- Automated tests (pytest) covering the scraper against saved HTML fixtures, so a future
  solde.red redesign fails loudly instead of silently.
- A language selector surfacing the `de`/`hr` locale data that's already scraped but
  currently unused.
