from datetime import date
from io import BytesIO

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from app.cache import get_or_fetch
from app.content import normalize_description
from app.family_config import connect_line, headline_fields
from app.labels import display_rows
from app.scraper import ProductNotFoundError
from app.seed_products import SEED_PRODUCTS
from app.typical_applications import typical_applications

app = FastAPI(title="Soldered Datasheet Generator")

TEMPLATES_DIR = "app/templates"
jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html"]),
)
jinja_env.filters["display_rows"] = display_rows
jinja_env.filters["normalize_desc"] = normalize_description

TEMPLATE_FILES = {"onepager": "onepager.html", "full": "full.html"}
TEMPLATE_LABELS = {"onepager": "One-pager", "full": "Full datasheet"}


@app.get("/", response_class=HTMLResponse)
def index(error: str | None = None):
    template = jinja_env.get_template("form.html")
    return template.render(seed_products=SEED_PRODUCTS, error=error)


@app.get("/pdf")
def generate_pdf(sku: str = Query(...), template: str = Query("onepager")):
    sku = sku.strip()
    if template not in TEMPLATE_FILES:
        return RedirectResponse(f"/?error=Unknown template '{template}'")

    try:
        product = get_or_fetch(sku)
    except ProductNotFoundError:
        return RedirectResponse(f"/?error=No product found for SKU '{sku}'")

    context = {
        "product": product,
        "template_label": TEMPLATE_LABELS[template],
        "generated_date": date.today().isoformat(),
        "connect_line": connect_line(sku),
        "typical_applications": typical_applications(sku),
    }
    if template == "onepager":
        fields = [product.field(name) for name in headline_fields(sku)]
        context["headline_rows"] = display_rows([f for f in fields if f is not None])

    html = jinja_env.get_template(TEMPLATE_FILES[template]).render(**context)
    pdf_bytes = HTML(string=html, base_url="https://solde.red").write_pdf()

    filename = f"{sku}-{template}.pdf"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.post("/refresh/{sku}")
def refresh(sku: str):
    try:
        get_or_fetch(sku, force=True)
    except ProductNotFoundError:
        return RedirectResponse(f"/?error=No product found for SKU '{sku}'", status_code=303)
    return RedirectResponse("/", status_code=303)
