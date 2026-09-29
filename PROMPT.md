# Daily run instructions

These are the instructions the daily scheduled Claude task follows. Edit them
to change what the digest focuses on.

Work from `~/Projects/dr-digest`.

1. Run `python3 -m dr_digest fetch`. It archives the latest Série I and
   Série II issues. If it fails (site down, no network), stop and report.
2. Run `python3 -m dr_digest pending`. For **each** date it prints, do steps
   3–4. If it prints nothing, the digest is already up to date: skip to step 5.
3. Run `python3 -m dr_digest candidates <DATE>` and read every line. Série I
   is all legislation; the Série II lines have already had procurement notices
   and public-sector HR paperwork filtered out.
4. Write `digests/<DATE>.json` (schema below), then run
   `python3 -m dr_digest render`. If it reports errors for that date, fix the
   JSON and render again.
5. Run `python3 -m dr_digest publish`. It commits the new data and digests
   and pushes them to GitHub, which rebuilds the public site
   (https://gonmsilva.github.io/dr-resumido/). Then publish
   `site/artifact.html` as the "Diário da República Resumido" artifact (see
   "Publishing" below).
6. Reply with the overview sentence(s) for each new date and the number of
   highlights, nothing more.

## What counts as a highlight

The reader lives in Portugal and follows the news for three reasons: what
changes daily life for residents, what moves markets and business, and what
affects housing and property. A highlight is something a well-informed reader
would want to know today.

Most days have 2–6 highlights. A quiet day can have 0–1: say so honestly
rather than padding. Do **not** highlight: routine collective-agreement
extensions (portarias de extensão), individual appointments below board
level, internal regulations of universities or parishes, parliament travel
authorisations. Local regulations only count if they are in Lisbon or Porto
or change taxes and fees.

## Topics

Every highlight and every `other` item gets topic tags from this list. The
page has a view per topic that collects items across all days, so tag
consistently.

| tag | covers |
|-----|--------|
| `impostos` | IRS, IVA, IMI, IMT, municipal taxes and fees, the State Budget, public spending authorisations |
| `banca` | banks, Banco de Portugal, Fundo de Resolução, insurance, CMVM, investment funds, state-owned financial companies |
| `infraestruturas` | rail, metro, roads, ports, airports, public works, PPPs and concessions |
| `habitacao` | rent, mortgages, PDM, loteamentos, urban planning, licensing, construction rules, public land |
| `social` | pensions, benefits, social security, families, disability, ageing |
| `trabalho` | wages, collective bargaining, labour rules, public-sector employment rules |
| `energia` | electricity, fuel, water, climate, protected land (REN/RAN), environmental rules |
| `empresas` | support and licences for companies, agriculture, fisheries, tourism, industry, defence industry |
| `saude` | SNS, hospitals, medicines, health professions |
| `educacao` | schools, higher education, research, vocational training |
| `justica` | courts, Tribunal Constitucional rulings, codes and legal regimes |
| `estado` | government structure, public administration, municipalities and parishes, elections |

- Use the subject first, then any second or third topic that genuinely
  applies. Example: a Constitutional Court ruling on IMI is
  `["impostos", "habitacao", "justica"]`.
- Highlights take 1–3 tags; `other` items take 1–2.

## Digest schema

```json
{
  "date": "2026-09-28",
  "overview": "Duas ou três frases sobre o que o dia trouxe.",
  "highlights": [
    {
      "id": "1174092980",
      "headline": "Título curto e concreto",
      "explanation": "1–3 frases: o que faz e a quem afeta.",
      "tags": ["infraestruturas", "empresas"],
      "importance": "high"
    }
  ],
  "other": [
    { "id": "1174093290", "note": "Uma linha sobre algo menor mas que vale a pena ver.", "tags": ["impostos", "estado"] }
  ]
}
```

- `id` must be an id from the candidates list, in square brackets. Never
  invent one. Links and act numbers are filled in from the data by id.
- `tags`: topic keys from the table above (1–3 for highlights, 1–2 for `other`).
- `importance`: `high` (affects many people or a lot of money) or `medium`.
- `other`: 0–8 items. Leave out anything that is plainly routine.
- Write in European Portuguese (português de Portugal), plain and direct,
  as a good newspaper would. No legalese.
- Work only from the summaries. If a summary is too vague to say what
  something does, describe it at that level. Don't guess at details.

## Publishing

`site/artifact.html` is one self-contained page holding every day in the
archive. Publish it with the Artifact tool. The first time, publish without a
`url`, then save the returned URL to `artifact_url.txt`. After that, always
publish with `url` set to the contents of `artifact_url.txt` so the link never
changes.
