from app.labels import display_value
from app.models import Product
from app.typical_applications import typical_applications

# Derived from Product.categories (solde.red's breadcrumbs), not a SKU list,
# so a new SKU in an existing family needs no code change.
CATEGORY_TO_FAMILY: dict[str, str] = {
    "Inkplate": "display",
    "Microcontrollers & Dev Boards": "dev_board",
    "Sensors & Modules": "sensor_breakout",
}


def family_for_product(product: Product) -> str | None:
    for category in product.categories:
        if category in CATEGORY_TO_FAMILY:
            return CATEGORY_TO_FAMILY[category]
    return None


# Headline spec fields (by field `name`) shown on the one-pager, per family.
FAMILY_HEADLINE_FIELDS: dict[str, list[str]] = {
    "display": [
        "display_size_inch",
        "display_resolution_w",
        "display_resolution_h",
        "display_color",
        "full_refresh_seconds",
        "mcu_part_number",
    ],
    "dev_board": [
        "mcu_part_number",
        "mcu_clock_mhz",
        "wifi",
        "bluetooth",
        "supply_voltage",
        "sleep_current_ua",
    ],
    "sensor_breakout": [
        "ic_part_number",
        "measurement_types",
        "measurement_range",
        "measurement_accuracy",
        "interface",
        "supply_voltage_min_v",
        "supply_voltage_max_v",
    ],
}


def headline_fields(product: Product) -> list[str]:
    """Curated list for a configured family, else the first 6 fields present (never empty)."""
    family = family_for_product(product)
    configured = FAMILY_HEADLINE_FIELDS.get(family)
    if configured:
        return configured
    return [f.name for f in product.all_fields()][:6]


# Draft wording, not yet tone-of-voice reviewed.
FAMILY_CONNECT_LINE: dict[str, str] = {
    "display": (
        "Connect it to your computer with a USB-C cable, then load your first "
        "image using the Arduino library or the MicroPython module."
    ),
    "dev_board": (
        "Connect it to your computer with a USB-C cable, then flash it using "
        "the Arduino IDE, MicroPython, or ESP-IDF."
    ),
    "sensor_breakout": (
        "Connect it to your board with the qwiic connector or the "
        "breadboard-compatible header pins, then read data over I2C."
    ),
}


def connect_line(product: Product, technical_details_rows: list[dict] | None = None) -> str:
    """Configured per-family sentence, else a generic line grounded in whatever connection fields exist."""
    family = family_for_product(product)
    configured = FAMILY_CONNECT_LINE.get(family)
    if configured:
        return configured
    line = _generic_connect_line(product)
    if line:
        return line
    return _connect_line_from_technical_details(technical_details_rows or [])


def _connect_line_from_technical_details(rows: list[dict]) -> str:
    for row in rows:
        if "connector" in row["label"].lower():
            label = row["label"]
            phrase = label[0].lower() + label[1:] if label else label
            return f"Connect it via the {phrase}."
    return ""


def _generic_connect_line(product: Product) -> str:
    dev_envs = product.field("dev_environments")
    if dev_envs is not None:
        return (
            f"Connect it to your computer with a USB-C cable, then flash it "
            f"using {display_value(dev_envs)}."
        )

    connectors = []
    qwiic = product.field("qwiic_compatible")
    if qwiic is not None and str(qwiic.value).lower() == "yes":
        connectors.append("the qwiic connector")
    breadboard = product.field("breadboard_compatible")
    if breadboard is not None and str(breadboard.value).lower() == "yes":
        connectors.append("the breadboard-compatible header pins")
    if not connectors:
        return ""

    via = " or ".join(connectors)
    interface = product.field("interface")
    if interface is not None:
        return f"Connect it via {via}, then read data over {display_value(interface)}."
    return f"Connect it via {via}."


# None = deliberately no line, distinct from "unconfigured" (which falls back to Typical Applications).
FAMILY_WHAT_IT_DOES: dict[str, str | None] = {
    "display": (
        "Suits projects that show information for long periods without "
        "draining a battery — signage, weather displays, status boards."
    ),
    "dev_board": (
        "Suits battery-powered projects that spend most of their time "
        "asleep — sensors, trackers, remote monitors."
    ),
    "sensor_breakout": None,
}


def what_it_does(product: Product) -> str | None:
    """Configured per-family sentence, else the opening sentence of Typical Applications."""
    family = family_for_product(product)
    if family in FAMILY_WHAT_IT_DOES:
        return FAMILY_WHAT_IT_DOES[family]

    text = typical_applications(product.sku)
    if not text:
        return None
    first_sentence = text.split(". ", 1)[0].strip()
    if not first_sentence.endswith("."):
        first_sentence += "."
    return first_sentence
