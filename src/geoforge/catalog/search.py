from __future__ import annotations

import re
from typing import Any, Iterable

from .loader import load_catalog

_TOKEN = re.compile(r"[a-zа-яё0-9]+", re.IGNORECASE)

_STOP = frozenset(
    {
        "a",
        "an",
        "the",
        "to",
        "for",
        "of",
        "and",
        "or",
        "with",
        "using",
        "in",
        "on",
        "by",
        "нужна",
        "нужен",
        "нужно",
        "для",
        "как",
    }
)

_EXPAND: dict[str, frozenset[str]] = {}

def _link(group: Iterable[str]) -> None:
    tokens = frozenset(group)
    for token in tokens:
        _EXPAND[token] = tokens


_link(("stair", "stairs", "staircase", "stairway", "steps", "step", "ступень", "ступени", "лестница", "лестницы"))
_link(("walk", "walkable", "walking", "tread", "landing", "марш"))
_link(("floor", "floors", "этаж", "этажа", "этажи", "этажами", "between", "между"))
_link(("ladder", "ladders", "climb", "climbable", "climbing", "rung", "rungs", "перекладина", "перекладины", "карабкаться", "карабкается", "приставная"))
_link(("hand", "hands", "руками", "руки"))
_link(("rail", "railing", "railings", "перила", "ограждение", "ограждения", "posts"))
_link(("balcony", "balconies", "балкон", "балконы"))
_link(("road", "roads", "дорога", "дороги", "sidewalk", "street"))
_link(("desk", "table", "tables", "стол", "стола", "рабочий"))
_link(("room", "rooms", "комната"))
_link(("wall", "walls", "стена", "стены"))
_link(("door", "doors", "дверь", "двери", "doorway"))
_link(("window", "windows", "окно", "окна"))
_link(("chair", "chairs", "стул", "стулья"))
_link(("beam", "beams", "балка"))
_link(("column", "columns", "колонна", "колонны"))
_link(("box", "cube", "prism"))

WALKABLE_SIGNALS = frozenset(
    {
        "walk",
        "walkable",
        "walking",
        "step",
        "steps",
        "tread",
        "landing",
        "floor",
        "floors",
        "этаж",
        "этажа",
        "этажи",
        "этажами",
        "ступени",
        "ступень",
        "between",
        "между",
        "staircase",
        "stairway",
        "industrial",
        "промышленная",
        "промышленный",
    }
)
LADDER_SIGNALS = frozenset(
    {
        "ladder",
        "ladders",
        "climb",
        "climbable",
        "climbing",
        "rung",
        "rungs",
        "hand",
        "hands",
        "vertical",
        "lean",
        "перекладина",
        "перекладины",
        "карабкаться",
        "карабкается",
        "приставная",
        "руками",
        "руки",
    }
)

_STATUS_WEIGHT = {"NATIVE": 1.15, "ADAPTED": 1.08, "REFERENCE": 0.92, "UNSUPPORTED": 0.35}


def tokenize(text: str) -> list[str]:
    tokens = [token.lower() for token in _TOKEN.findall(text)]
    return [token for token in tokens if len(token) >= 2 and token not in _STOP]


def expand(tokens: Iterable[str]) -> set[str]:
    result = set(tokens)
    for token in list(result):
        result.update(_EXPAND.get(token, ()))
    return result


def search_generators(query: str, *, limit: int = 5) -> list[dict[str, Any]]:
    query_tokens = tokenize(query)
    query_expanded = expand(query_tokens)
    walkable_hits = len(query_expanded & WALKABLE_SIGNALS)
    ladder_hits = len(query_expanded & LADDER_SIGNALS)
    ranked: list[dict[str, Any]] = []
    for entry in load_catalog():
        raw = _raw_score(entry, query_tokens, query_expanded)
        if entry["id"] == "architecture.stairs.walkable":
            raw += 2.4 * walkable_hits - 1.8 * ladder_hits
        elif entry["id"] == "architecture.stairs.climbable_ladder":
            raw += 2.4 * ladder_hits - 1.8 * walkable_hits
        if raw <= 0:
            continue
        score = raw * _STATUS_WEIGHT[entry["status"]]
        ranked.append(
            {
                "id": entry["id"],
                "score": score,
                "status": entry["status"],
                "meaning": entry["meaning"],
                "variants": list(entry.get("variants") or []),
                "kind": entry.get("kind"),
            }
        )
    ranked.sort(key=lambda item: (-item["score"], item["id"]))
    top = ranked[: max(1, limit)]
    peak = top[0]["score"] if top else 1.0
    for item in top:
        item["score"] = round(min(1.0, item["score"] / peak), 4)
    return top


def _raw_score(entry: dict[str, Any], query_tokens: list[str], query_expanded: set[str]) -> float:
    haystacks = {
        "id": (tokenize(entry["id"].replace(".", " ")), 3.2),
        "name": (tokenize(entry.get("name", "")), 2.6),
        "tags": (tokenize(" ".join(entry.get("tags") or [])), 2.2),
        "aliases": (tokenize(" ".join(entry.get("aliases") or [])), 2.0),
        "meaning": (tokenize(entry.get("meaning", "")), 1.1),
        "variants": (tokenize(" ".join(entry.get("variants") or [])), 1.0),
        "category": (tokenize(str(entry.get("category") or "").replace("/", " ")), 1.6),
        "capability": (tokenize(str(entry.get("capability") or "").replace(".", " ")), 1.5),
        "source_project": (tokenize(str(entry.get("source_project") or "")), 0.6),
        "symbol": (tokenize(str(entry.get("symbol") or "")), 0.7),
        "not_this": (tokenize(entry.get("not_this") or ""), -0.8),
    }
    score = 0.0
    for tokens, weight in haystacks.values():
        overlap = query_expanded & expand(tokens)
        if not overlap:
            continue
        score += weight * len(overlap)
    if entry["id"] in query_tokens or entry["id"] in " ".join(query_tokens):
        score += 8.0
    return score
