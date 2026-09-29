"""dr-digest command line.

    python3 -m dr_digest fetch             archive today's feeds into data/
    python3 -m dr_digest pending           dates with data but no digest yet
    python3 -m dr_digest candidates DATE   compact list of items to summarize
    python3 -m dr_digest render            validate digests and build site/
    python3 -m dr_digest check DATE        validate one digest without building
    python3 -m dr_digest backfill FROM TO  archive past issues (YYYY-MM-DD, inclusive)
    python3 -m dr_digest publish           commit data/ and digests/ and push (rebuilds the public site)
"""

from __future__ import annotations

import subprocess
import sys
from datetime import date as Date, timedelta

from . import feeds, render, store


def cmd_fetch() -> int:
    all_items = []
    for series, url in feeds.FEEDS.items():
        try:
            date, items = feeds.parse_feed(feeds.fetch(url), series)
        except Exception as exc:  # network or malformed XML: report, keep going
            print(f"Série {series}: fetch failed: {exc}", file=sys.stderr)
            continue
        print(f"Série {series}: {len(items)} items for {date}")
        all_items += items
    if not all_items:
        return 1
    for date, n in sorted(store.save_items(all_items).items()):
        print(f"{date}: {n} new items archived")
    return 0


def cmd_pending() -> int:
    for date in store.pending_dates():
        print(date)
    return 0


def cmd_candidates(date: str) -> int:
    day = store.load_day(date)
    if day is None:
        print(f"no data for {date}", file=sys.stderr)
        return 1
    kept = [i for i in day["items"] if i.get("candidate")]
    dropped = len(day["items"]) - len(kept)
    print(f"# {date} — {len(kept)} candidates ({dropped} routine Série II items filtered out)")
    for i in kept:
        label = f"{i['type']} n.º {i['number']}" if i["number"] else i["type"]
        print(f"[{i['id']}] Série {i['series']} | {label} | {i['summary']}")
    return 0


def cmd_render() -> int:
    dates, problems = render.render_all()
    print(f"rendered {len(dates)} day(s) → {store.SITE / 'index.html'}")
    for date, errs in problems.items():
        print(f"{date}: NOT rendered", file=sys.stderr)
        for e in errs:
            print(f"  - {e}", file=sys.stderr)
    return 1 if problems else 0


def cmd_check(date: str) -> int:
    digest, day = store.load_digest(date), store.load_day(date)
    if digest is None or day is None:
        print(f"{date}: missing {'digest' if digest is None else 'data'}", file=sys.stderr)
        return 1
    errs = render.validate(digest, day)
    for e in errs:
        print(f"  - {e}", file=sys.stderr)
    print(f"{date}: {'OK' if not errs else f'{len(errs)} problem(s)'}")
    return 1 if errs else 0


def cmd_backfill(start: str, end: str) -> int:
    from . import archive  # only needed here; keeps the daily path RSS-only

    d, last = Date.fromisoformat(start), Date.fromisoformat(end)
    failures = 0
    while d <= last:
        iso = d.isoformat()
        try:
            items = archive.fetch_day(iso)
        except archive.ArchiveError as exc:
            print(f"{iso}: {exc}", file=sys.stderr)
            return 1  # site changed: stop rather than skip every remaining day
        except Exception as exc:  # network hiccup: note it and move on
            print(f"{iso}: failed ({exc})", file=sys.stderr)
            failures += 1
        else:
            if items:
                n = store.save_items(items).get(iso, 0)
                print(f"{iso}: {len(items)} items ({n} new)")
            else:
                print(f"{iso}: no issue")
        d += timedelta(days=1)
    return 1 if failures else 0


def cmd_publish() -> int:
    """Commit new archive and digest files and push; GitHub Pages rebuilds the site."""
    def git(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", "-C", str(store.ROOT), *args], capture_output=True, text=True)

    git("add", "data", "digests")
    staged = git("diff", "--cached", "--name-only").stdout.split()
    if not staged:
        print("nothing new to publish")
        return 0
    dates = sorted({p.rsplit("/", 1)[-1][:10] for p in staged if p.startswith("digests/")})
    msg = f"Digest {', '.join(dates)}" if dates else "Update archive"
    for step in (("commit", "-m", msg), ("push", "--quiet")):
        r = git(*step)
        if r.returncode:
            print(f"git {step[0]} failed:\n{r.stderr or r.stdout}", file=sys.stderr)
            return 1
    print(f"published: {msg} ({len(staged)} files)")
    return 0


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    cmd, args = argv[0], argv[1:]
    if cmd == "fetch":
        return cmd_fetch()
    if cmd == "pending":
        return cmd_pending()
    if cmd == "candidates" and len(args) == 1:
        return cmd_candidates(args[0])
    if cmd == "render":
        return cmd_render()
    if cmd == "check" and len(args) == 1:
        return cmd_check(args[0])
    if cmd == "backfill" and len(args) == 2:
        return cmd_backfill(*args)
    if cmd == "publish":
        return cmd_publish()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
