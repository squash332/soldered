import json
import re

import requests
from bs4 import BeautifulSoup

from app.models import (
    BoxItem,
    Product,
    ResourceLink,
    SpecField,
    SpecGroup,
    Variant,
    utcnow,
)

BASE_URL = "https://solde.red"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120 Safari/537.36"
)
LOCALE = "en"


class ProductNotFoundError(Exception):
    pass


def fetch_product(sku: str) -> Product:
    url = f"{BASE_URL}/{sku}"
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
    if resp.status_code == 404:
        raise ProductNotFoundError(f"No product found for SKU {sku}")
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")
    locales_tag = soup.find("script", id="locales-data")
    if locales_tag is None:
        raise ProductNotFoundError(f"SKU {sku} page has no product data")

    try:
        locales = json.loads(locales_tag.string)
        data = locales[LOCALE]
    except (json.JSONDecodeError, KeyError) as exc:
        raise ProductNotFoundError(f"Could not parse product data for SKU {sku}") from exc

    spec_groups = [
        SpecGroup(
            key=group["key"],
            label=group["label"],
            fields=[SpecField(**f) for f in group["fields"]],
        )
        for group in data.get("spec_groups", [])
    ]

    return Product(
        sku=sku,
        name=data["name"],
        short_description=data.get("short_description", ""),
        long_description=data.get("long_description", ""),
        technical_details=data.get("technical_details", ""),
        spec_groups=spec_groups,
        in_the_box=_parse_in_the_box(soup),
        pinout_image_url=_parse_pinout(soup),
        resources=_parse_resources(soup),
        variants=_parse_variants(soup),
        fetched_at=utcnow(),
    )


def _parse_in_the_box(soup: BeautifulSoup) -> list[BoxItem]:
    section = soup.find(id="in-the-box")
    if section is None:
        return []
    items = []
    for card in section.select(".packing-card"):
        qty_el = card.select_one(".packing-qty")
        name_el = card.select_one(".packing-name")
        desc_el = card.select_one(".packing-desc")
        if name_el is None:
            continue
        # strip nested badges (e.g. SKU chip) from the name text
        name_el_copy = BeautifulSoup(str(name_el), "lxml")
        for sku_span in name_el_copy.select(".packing-sku"):
            sku_span.decompose()
        name = name_el_copy.get_text(" ", strip=True)
        items.append(
            BoxItem(
                name=name,
                quantity=qty_el.get_text(strip=True) if qty_el else None,
                description=desc_el.get_text(" ", strip=True) if desc_el else None,
            )
        )
    return items


def _parse_pinout(soup: BeautifulSoup) -> str | None:
    section = soup.find(id="pinout")
    if section is None:
        return None
    img = section.select_one(".pinout-image, img")
    return img["src"] if img and img.has_attr("src") else None


def _parse_resources(soup: BeautifulSoup) -> list[ResourceLink]:
    section = soup.find(id="resources")
    if section is None:
        return []
    links = []
    for card in section.select(".resource-card"):
        category = card.get("data-cat", "")
        for item in card.select(".resource-item"):
            label_el = item.select_one(".resource-item-label")
            badge_el = item.select_one(".resource-item-badge")
            links.append(
                ResourceLink(
                    category=category,
                    label=label_el.get_text(strip=True) if label_el else item.get_text(strip=True),
                    href=item.get("href", ""),
                    badge=badge_el.get_text(strip=True) if badge_el else None,
                )
            )
    return links


def _parse_variants(soup: BeautifulSoup) -> list[Variant]:
    tag = soup.find("script", id="variants-data")
    if tag is None or not tag.string:
        return []
    try:
        raw = json.loads(tag.string)
    except json.JSONDecodeError:
        return []
    variants = []
    for v in raw:
        name = v.get("names", {}).get(LOCALE) or v.get("names", {}).get("en") or ""
        variants.append(
            Variant(sku=v["sku"], name=name, thumbnail_url=v.get("thumbnail_url"))
        )
    return variants
