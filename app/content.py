import re

from bs4 import BeautifulSoup

# "Dasduino" is NULA's retired name; its old product pages 404 to a generic
# catalog page now, so any mention is stale, not a real distinct product.
_DASDUINO_RE = re.compile(r"Dasduino(?:\s+Core)?", re.IGNORECASE)
_DEAD_DASDUINO_HOSTS = ("soldered.com/products/dasduino", "soldered.com/product/dasduino")

# Exact-string fixes, not a blanket "it's"->"its" rule (that would also break
# legitimate "it is" usages elsewhere).
_KNOWN_TYPOS = {
    "Due to it's ample connectivity": "Due to its ample connectivity",
}

_UNIT_TOKENS = ["mAh", "MHz", "kHz", "GB", "MB", "KB", "mA", "µA", "uA", "Hz", "ms", "V", "W", "s"]
_UNIT_RE = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)(" + "|".join(_UNIT_TOKENS) + r")\b")


def _fix_unit_spacing(text: str) -> str:
    def repl(match: re.Match) -> str:
        unit = match.group(2)
        if unit == "uA":
            unit = "µA"  # normalize ASCII "u" to the proper micro sign
        return f"{match.group(1)} {unit}"

    return _UNIT_RE.sub(repl, text)


def _normalize_text_node(text: str) -> str:
    text = _DASDUINO_RE.sub("NULA", text)
    for wrong, right in _KNOWN_TYPOS.items():
        text = text.replace(wrong, right)
    text = text.replace("!", ".")
    return _fix_unit_spacing(text)


def normalize_description(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for a in soup.find_all("a"):
        href = a.get("href", "")
        is_dead_link = any(host in href for host in _DEAD_DASDUINO_HOSTS)
        if is_dead_link or _DASDUINO_RE.search(a.get_text()):
            a.replace_with("NULA")

    for node in soup.find_all(string=True):
        node.replace_with(_normalize_text_node(str(node)))

    return str(soup)


def parse_technical_details(html: str) -> list[dict]:
    """Spec rows parsed from technical_details prose, for products with no spec_groups."""
    soup = BeautifulSoup(normalize_description(html), "html.parser")
    rows = []
    for li in soup.find_all("li"):
        strong = li.find("strong")
        if strong is None:
            label = li.get_text(" ", strip=True)
            value = ""
        else:
            label = strong.get_text(strip=True).rstrip(":").strip()
            strong.extract()
            value = li.get_text(" ", strip=True)
        if label:
            rows.append({"label": label, "value": value})
    return rows
