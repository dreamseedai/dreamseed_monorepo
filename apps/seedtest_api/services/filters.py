import re
from typing import List

_splitter = re.compile(r"[\s,]+")


def parse_str_list(raw: str | None) -> List[str]:
    """Parse a comma/whitespace mixed string into a list of lowercase strings.

    Examples:
      "algebra, geometry proof" -> ["algebra", "geometry", "proof"]
      "  a,  b   c  , d  " -> ["a", "b", "c", "d"]
    """
    if not raw:
        return []
    parts = [p.strip() for p in _splitter.split(raw.strip()) if p and p.strip()]
    return parts


def parse_int_list(raw: str | None) -> List[int]:
    """Parse a comma/whitespace mixed string into a list of ints.

    Non-integer tokens are ignored to be lenient for configs.
    """
    if not raw:
        return []
    items: List[int] = []
    for tok in _splitter.split(raw.strip()):
        tok = tok.strip()
        if not tok:
            continue
        try:
            items.append(int(tok))
        except ValueError:
            # lenient: ignore bad token
            continue
    return items
