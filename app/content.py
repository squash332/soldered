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

_KNOWN_TYPOS = {
    "Due to it's ample connectivity": "Due to its ample connectivity",
}


def normalize_description(html: str) -> str:
    """Tone-of-voice pass over scraped description HTML: drop forced
    exclamation marks, fix known proofreading errors, and replace mentions of
    the retired "Dasduino" product line with its current name, NULA."""
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a"):
        href = a.get("href", "")
        is_dead_link = any(host in href for host in _DEAD_DASDUINO_HOSTS)
        if is_dead_link or _DASDUINO_RE.search(a.get_text()):
            a.replace_with("NULA")

    text = str(soup)
    text = _DASDUINO_RE.sub("NULA", text)
    for wrong, right in _KNOWN_TYPOS.items():
        text = text.replace(wrong, right)
    text = text.replace("!", ".")
    return text
