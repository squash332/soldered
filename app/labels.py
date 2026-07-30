import re

from app.models import SpecField

# Explicit mapping for raw enum-style values solde.red does not humanize itself.
# Keyed by raw value, not field name, since values like "yes"/"no" recur across
# unrelated fields.
ENUM_LABELS: dict[str, str] = {
    "yes": "Yes",
    "no": "No",
    "none": "None",
    "wifi4": "Wi-Fi 4 (802.11n)",
    "classic_and_ble": "Bluetooth Classic + BLE",
    "jst_2pin": "JST 2-pin connector",
    "3v3": "3.3 V",
    "3v3_5v": "3.3 V or 5 V",
    "3v3_or_5v": "3.3 V or 5 V",
    "grayscale": "Grayscale",
}

_HEX_CODE = re.compile(r"^0x[0-9a-fA-F]+$")
_SNAKE_CODE = re.compile(r"^[a-z0-9]+(_[a-z0-9]+)*$")


def display_value(field: SpecField) -> str:
    """Human-readable text for a spec field, never the raw enum code."""
    raw = field.value
    if not isinstance(raw, str) or field.display_value != raw:
        return field.display_value

    if raw in ENUM_LABELS:
        return ENUM_LABELS[raw]

    if _HEX_CODE.match(raw):
        return raw  # standard hex notation is already the human-readable form

    if _SNAKE_CODE.match(raw):
        return raw.replace("_", " ").title()

    return field.display_value
