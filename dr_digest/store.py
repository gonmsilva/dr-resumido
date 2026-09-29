"""On-disk layout.

data/YYYY-MM-DD.json     every item published that day (archived from RSS)
digests/YYYY-MM-DD.json  the written summary for that day (made by Claude)
site/                    rendered HTML
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .feeds import Item
from .filters import is_candidate

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DIGESTS = ROOT / "digests"
SITE = ROOT / "site"


def _write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def load_day(date: str) -> dict | None:
    path = DATA / f"{date}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def save_items(items: list[Item]) -> dict[str, int]:
    """Merge items into their day's archive. Returns {date: new item count}."""
    by_date: dict[str, list[Item]] = {}
    for it in items:
        by_date.setdefault(it.date, []).append(it)

    added: dict[str, int] = {}
    for date, day_items in by_date.items():
        day = load_day(date) or {"date": date, "items": []}
        known = {i["id"] for i in day["items"]}
        new = []
        for it in day_items:  # the feeds occasionally repeat an item
            if it.id not in known:
                known.add(it.id)
                new.append(it)
        for it in new:
            d = it.to_dict()
            d["candidate"] = is_candidate(it)
            day["items"].append(d)
        day["fetched_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        _write_json(DATA / f"{date}.json", day)
        added[date] = len(new)
    return added


def load_digest(date: str) -> dict | None:
    path = DIGESTS / f"{date}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def data_dates() -> list[str]:
    return sorted(p.stem for p in DATA.glob("????-??-??.json"))


def digest_dates() -> list[str]:
    return sorted(p.stem for p in DIGESTS.glob("????-??-??.json"))


def pending_dates() -> list[str]:
    done = set(digest_dates())
    return [d for d in data_dates() if d not in done]
