# Which product family a SKU belongs to. Add one line per new SKU; add a new
# family entry below only if it's a genuinely new kind of product.
SKU_FAMILY: dict[str, str] = {
    "333232": "display",
    "333352": "dev_board",
    "333032": "sensor_breakout",
}

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


def headline_fields(sku: str) -> list[str]:
    family = SKU_FAMILY.get(sku)
    if family is None:
        return []
    return FAMILY_HEADLINE_FIELDS.get(family, [])


# One factual line per family on how to connect the product, for the one-pager.
# Draft wording — grounded in confirmed spec fields (dev_environments,
# qwiic_compatible, breadboard_compatible, interface), not verified tone-of-voice copy.
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


def connect_line(sku: str) -> str:
    family = SKU_FAMILY.get(sku)
    return FAMILY_CONNECT_LINE.get(family, "")
