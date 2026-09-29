"""Fetch past issues from diariodarepublica.pt for backfilling.

The RSS feeds only hold the latest issue. For older dates we call the same
internal endpoints the website's own pages use: one lists the issues
published on a date (main issue and supplements, both series), the other
lists every act in one issue with its summary.

The request bodies in templates/screenservices.json were captured from the
site. They carry the site's module and API version tokens; when the site is
redeployed those change and the calls fail with a version error. Re-capture
the templates then (see README).
"""

from __future__ import annotations

import copy
import html
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

from .feeds import USER_AGENT, Item

BASE = "https://diariodarepublica.pt"
TEMPLATES = json.loads((Path(__file__).parent / "templates" / "screenservices.json").read_text("utf-8"))
TEMPLATE_ISSUE_ID = TEMPLATES["issue"]["body"]["screenData"]["variables"]["DiarioId"]

# "Diário da República n.º 42/2026, Suplemento, Série I de 2026-03-02"
ISSUE_TITLE_RE = re.compile(r"n\.º\s*(?P<num>\d+)/(?P<year>\d{4}),\s*(?P<supl>Suplemento,\s*)?Série\s+(?P<series>I{1,2})\b")


class ArchiveError(RuntimeError):
    pass


def _post(path: str, body: dict, timeout: int = 60) -> dict:
    # The site rejects anonymous calls without the header; any value, even
    # empty, is accepted.
    req = urllib.request.Request(
        BASE + path, data=json.dumps(body).encode("utf-8"), method="POST",
        headers={"Content-Type": "application/json; charset=UTF-8", "Accept": "application/json",
                 "X-CSRFToken": "", "User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    try:
        out = json.loads(raw)
    except json.JSONDecodeError:
        raise ArchiveError(f"{path}: expected JSON, got {raw[:80]!r}")
    info = out.get("versionInfo", {})
    if info.get("hasModuleVersionChanged") or info.get("hasApiVersionChanged"):
        raise ArchiveError("the site was redeployed; re-capture templates/screenservices.json")
    if "exception" in out:
        raise ArchiveError(f"{path}: {out['exception'].get('message')}")
    return out["data"]


def issues_on(date: str) -> list[dict]:
    """Issues published on a date: [{id, series, number, supplement}]."""
    body = copy.deepcopy(TEMPLATES["calendar"]["body"])
    body["screenData"]["variables"]["DataPublicacaoDRToShow"] = date
    data = _post(TEMPLATES["calendar"]["url"], body)
    hits = json.loads(data["Json_Out"])["hits"]["hits"]
    issues = []
    for h in hits:
        src = h["_source"]
        m = ISSUE_TITLE_RE.search(src.get("conteudoTitle", ""))
        if not m or src.get("dataPublicacao") != date:
            continue
        issues.append({"id": str(src["dbId"]), "series": m["series"],
                       "number": f"{m['num']}/{m['year']}", "supplement": bool(m["supl"])})
    return issues


def _clean_summary(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s or ""))).strip()


def issue_items(issue: dict, date: str) -> list[Item]:
    """Every act in one issue, shaped like the RSS items."""
    body = json.loads(json.dumps(TEMPLATES["issue"]["body"]).replace(TEMPLATE_ISSUE_ID, issue["id"]))
    body["screenData"]["variables"]["IsSerieI"] = issue["series"] == "I"
    data = _post(TEMPLATES["issue"]["url"], body)
    items = []
    for d in data["DetalheConteudo"]["List"]:
        link = d.get("LinkSitemap") or ""
        # Same id as the RSS parser: the trailing number of the detail URL.
        idm = re.search(r"-(\d+)/?$", link)
        act_id = idm.group(1) if idm else (d.get("DiplomaLegisId") or f"cp-{d.get('ContratoPublicoId')}")
        act_type = (d.get("TipoDiploma") or "").strip()
        if not act_type and d.get("ContratoPublicoId", "0") != "0":
            act_type = "Anúncio de procedimento"  # public tenders come back untyped
        # RSS summaries are "<issuer> <summary>"; keep the same shape.
        summary = " ".join(x for x in (_clean_summary(d.get("Emissor")), _clean_summary(d.get("Sumario"))) if x)
        items.append(Item(
            id=act_id, series=issue["series"], type=act_type,
            number=(d.get("Numero") or "").strip(), issue=issue["number"], date=date,
            summary=summary, link=BASE + link if link.startswith("/") else link))
    return items


def fetch_day(date: str, pause: float = 0.5) -> list[Item]:
    items: list[Item] = []
    for issue in issues_on(date):
        items += issue_items(issue, date)
        time.sleep(pause)  # be gentle with a public service
    return items
