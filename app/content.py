import re

from bs4 import BeautifulSoup

# "Dasduino" is the retired name of the product line NULA replaced (see
# handoff brief: "NULA, not Dasduino"). Its old product pages, including
# soldered.com/products/dasduino-core referenced in the SHTC3 copy, now
# redirect to a generic catalog page rather than a live product — confirmed
# by fetching both URL variants. Any scraped copy still naming it is stale
# pre-rebrand text, not a reference to a distinct product still sold today.
_DASDUINO_RE = re.compile(r"Dasduino(?:\s+Core)?", re.IGNORECASE)
_DEAD_DASDUINO_HOSTS = ("soldered.com/products/dasduino", "soldered.com/product/dasduino")

# Specific, verified proofreading fixes in the scraped copy — corrected as
# exact strings rather than a general "it's" -> "its" rule, since a blanket
# rule would also wrongly rewrite legitimate "it's" (= "it is") elsewhere.
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
    """Tone-of-voice pass over scraped description HTML: drop forced
    exclamation marks, fix known proofreading errors, space numbers apart
    from units the site glues together, and replace mentions of the retired
    "Dasduino" product line with its current name, NULA.

    Runs only on text nodes, never on the serialized HTML string, so it can't
    corrupt an href/src attribute that happens to contain a matching
    substring (e.g. a URL slug like ".../16x2-i2c-...")."""
    soup = BeautifulSoup(html, "html.parser")

    for a in soup.find_all("a"):
        href = a.get("href", "")
        is_dead_link = any(host in href for host in _DEAD_DASDUINO_HOSTS)
        if is_dead_link or _DASDUINO_RE.search(a.get_text()):
            a.replace_with("NULA")

    for node in soup.find_all(string=True):
        node.replace_with(_normalize_text_node(str(node)))

    return str(soup)
