"""Fetch and parse the Diário da República daily RSS feeds.

The feeds only ever hold the most recent issue, so anything we want to keep
has to be archived on the day it is published.
"""

from __future__ import annotations

import re
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass

FEEDS = {
    "I": "https://files.diariodarepublica.pt/rss/serie1-html.xml",
    "II": "https://files.diariodarepublica.pt/rss/serie2-html.xml",
}

USER_AGENT = "Mozilla/5.0 (dr-digest; personal daily reader)"

# "Portaria n.º 438/2026/1  -  Diário da República n.º 188/2026, Série I de 2026-09-28"
TITLE_RE = re.compile(
    r"^(?P<act>.+?)\s+-\s+Diário da República n\.º\s*(?P<issue>[\w/.-]+),"
    r"\s*Série\s+(?P<series>I{1,2})\s+de\s+(?P<date>\d{4}-\d{2}-\d{2})"
)
# "Portaria n.º 438/2026/1" -> type "Portaria", number "438/2026/1"
ACT_RE = re.compile(r"^(?P<type>.+?)\s+n\.º\s*(?P<number>\S+)$")
CHANNEL_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


@dataclass
class Item:
    id: str
    series: str
    type: str
    number: str
    issue: str
    date: str
    summary: str
    link: str

    def to_dict(self) -> dict:
        return asdict(self)


def fetch(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _clean(text: str | None) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def parse_feed(xml_bytes: bytes, series: str) -> tuple[str | None, list[Item]]:
    """Return (issue date from the channel header, items)."""
    root = ET.fromstring(xml_bytes)
    channel = root.find("channel")
    if channel is None:
        return None, []

    m = CHANNEL_DATE_RE.search(channel.findtext("description") or "")
    channel_date = m.group(1) if m else None

    items: list[Item] = []
    for node in channel.findall("item"):
        title = _clean(node.findtext("title"))
        link = _clean(node.findtext("link"))
        summary = _clean(node.findtext("description"))

        act, issue, date = title, "", channel_date or ""
        tm = TITLE_RE.match(title)
        if tm:
            act, issue, date = tm["act"].strip(), tm["issue"], tm["date"]

        am = ACT_RE.match(act)
        act_type, number = (am["type"].strip(), am["number"]) if am else (act, "")

        # The trailing number in the detail URL is DR's stable document id.
        idm = re.search(r"-(\d+)/?$", link)
        item_id = idm.group(1) if idm else f"{series}-{number or len(items)}"

        items.append(Item(item_id, series, act_type, number, issue, date, summary, link))
    return channel_date, items


def fetch_all() -> dict[str, tuple[str | None, list[Item]]]:
    return {series: parse_feed(fetch(url), series) for series, url in FEEDS.items()}
