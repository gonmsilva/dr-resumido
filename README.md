# dr-digest

Daily highlights (in Portuguese) from Portugal's Diário da República.

Every morning a scheduled Claude task:

1. archives that day's Série I and Série II RSS feeds into `data/`
   (the feeds only ever hold the latest issue, so a missed day is gone from RSS);
2. filters Série II down from ~300 items to ~30 by dropping procurement
   notices and public-sector HR paperwork (`dr_digest/filters.py`);
3. writes `digests/<date>.json`, the highlights, following `PROMPT.md`;
4. renders every day into one page and republishes the private artifact
   whose URL is in `artifact_url.txt`. Open that link in the Claude app on any device.

No dependencies beyond Python 3.10+.

```
python3 -m dr_digest fetch             # archive today's feeds
python3 -m dr_digest pending           # dates with data but no digest
python3 -m dr_digest candidates DATE   # what the summarizer reads
python3 -m dr_digest render            # validate digests, build site/
python3 -m unittest discover -s tests -t .
```

## Backfilling past days

`python3 -m dr_digest backfill 2026-01-01 2026-09-27` archives older issues
(both series, including supplements) by calling the internal endpoints the
diariodarepublica.pt pages use (`dr_digest/archive.py`). The items come out
identical to the RSS ones, so filtering and digests work the same. After a
backfill, `pending` lists the new dates; write their digests as usual, using
`check DATE` to validate one digest without rebuilding the site.

The request bodies in `dr_digest/templates/screenservices.json` were captured
from the site and carry its version tokens. If the site is redeployed,
backfill stops with "the site was redeployed". Re-capture them by opening
diariodarepublica.pt in a browser, recording the POST bodies of
`GetDRByDataCalendarioAndCheckUserLog` (home page) and
`Conteudo_Det_Diario/DataActionGetDadosAndApplicationSettings` (any issue
page), and saving them in the same shape. The daily RSS run doesn't depend
on this.

`site/index.html` opens locally in a browser; `site/artifact.html` is the
same page without the document skeleton, for publishing.

To change what counts as a highlight, edit `PROMPT.md`. To change what gets
filtered out before the summarizer sees it, edit `dr_digest/filters.py`.
