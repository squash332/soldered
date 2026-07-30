from datetime import timedelta
from pathlib import Path

from app.models import Product, utcnow
from app.scraper import fetch_product

CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"


def _cache_path(sku: str) -> Path:
    return CACHE_DIR / f"{sku}.json"


def get_or_fetch(sku: str, max_age_hours: int = 24, force: bool = False) -> Product:
    path = _cache_path(sku)
    if not force and path.exists():
        cached = Product.model_validate_json(path.read_text())
        if utcnow() - cached.fetched_at < timedelta(hours=max_age_hours):
            return cached

    product = fetch_product(sku)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(product.model_dump_json(indent=2))
    return product
