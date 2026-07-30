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

# Free-text spec values (e.g. measurement_range/measurement_accuracy) carry raw
# notation the site never converts. General text-level fixes, not per-field:
# any "+/-" becomes "±", and any "<number> C" (single or as an X to Y range)
# becomes proper degree-Celsius notation.
_PLUS_MINUS = re.compile(r"\+/-\s*")
# (?<![\w.]) keeps this from firing inside a code like "I2C" or "SHTC3", where
# the digit right before "C" is glued to a letter rather than standing alone
# as a measurement.
_TEMP_RANGE = re.compile(r"(?<![\w.])(-?\d+(?:\.\d+)?)\s+to\s+(-?\d+(?:\.\d+)?)\s*C\b")
_TEMP_SINGLE = re.compile(r"(?<![\w.])(-?\d+(?:\.\d+)?)\s*C\b")


def _normalize_unit_notation(text: str) -> str:
    text = _PLUS_MINUS.sub("±", text)
    text = _TEMP_RANGE.sub(r"\1°C to \2°C", text)
    text = _TEMP_SINGLE.sub(r"\1°C", text)
    return text


def display_value(field: SpecField) -> str:
    """Human-readable text for a spec field, never the raw enum code."""
    raw = field.value
    if isinstance(raw, str) and field.display_value == raw:
        if raw in ENUM_LABELS:
            text = ENUM_LABELS[raw]
        elif _HEX_CODE.match(raw):
            text = raw  # standard hex notation is already the human-readable form
        elif _SNAKE_CODE.match(raw):
            text = raw.replace("_", " ").title()
        else:
            text = field.display_value
    else:
        text = field.display_value

    return _normalize_unit_notation(text)


# Renames for solde.red's auto-generated (title-cased snake_case) field labels
# that read poorly in a customer-facing document. Keyed by field `name`, so a
# field carries its fixed label wherever it appears (headline specs or full
# spec tables), not per-template.
FIELD_LABEL_OVERRIDES: dict[str, str] = {
    "mcu_part_number": "Microcontroller",
    "rtc_onboard": "Real-time clock",
    "has_enclosure": "Enclosure included",
    "ic_part_number": "Sensor IC",
    "sleep_current_ua": "Sleep current",
}


def field_label(field: SpecField) -> str:
    return FIELD_LABEL_OVERRIDES.get(field.name, field.label)


# Unit inferred from a field-name suffix when solde.red's own `unit` value is
# empty. General rule keyed on unit *type*, not a per-field patch, so a new
# field like `standby_current_ua` next month is covered automatically.
UNIT_SUFFIX_MAP: dict[str, str] = {
    "_ua": "µA",
    "_ma": "mA",
    "_mhz": "MHz",
    "_mb": "MB",
    "_kb": "KB",
    "_v": "V",
}


def field_unit(field: SpecField) -> str:
    if field.unit:
        return field.unit
    for suffix, unit in UNIT_SUFFIX_MAP.items():
        if field.name.endswith(suffix):
            return unit
    return ""


def _field_text(field: SpecField) -> str:
    value = display_value(field)
    unit = field_unit(field)
    return f"{value} {unit}" if unit else value


# Pairs of raw fields that read better combined into a single spec row than as
# two separate ones. Keyed by the field `name`s involved, so it applies
# uniformly wherever that pair of fields shows up (headline specs or full spec
# tables), not per template.
FIELD_COMBINATIONS: list[dict] = [
    {
        "fields": ("display_resolution_w", "display_resolution_h"),
        "label": "Resolution",
        "format": lambda vals: f"{vals[0]} × {vals[1]} px",
    },
    {
        "fields": ("supply_voltage_min_v", "supply_voltage_max_v"),
        "label": "Supply voltage",
        "format": lambda vals: (
            f"{vals[0]} V" if vals[0] == vals[1] else f"{vals[0]}–{vals[1]} V"
        ),
    },
]


def display_rows(fields: list[SpecField]) -> list[dict]:
    """Render-ready {label, value} rows: combined pairs merged, labels
    overridden, units filled in — the single place spec tables and headline
    specs both go through, so they can't drift apart."""
    by_name = {f.name: f for f in fields}
    order = {f.name: i for i, f in enumerate(fields)}
    consumed: set[str] = set()
    rows = []

    for combo in FIELD_COMBINATIONS:
        names = combo["fields"]
        if all(n in by_name for n in names):
            vals = [by_name[n].value for n in names]
            rows.append(
                {
                    "label": combo["label"],
                    "value": combo["format"](vals),
                    "_order": order[names[0]],
                }
            )
            consumed.update(names)

    for f in fields:
        if f.name in consumed:
            continue
        rows.append({"label": field_label(f), "value": _field_text(f), "_order": order[f.name]})

    rows.sort(key=lambda r: r["_order"])
    for r in rows:
        del r["_order"]
    return rows
