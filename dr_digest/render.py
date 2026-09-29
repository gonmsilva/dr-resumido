"""Validate digests and render them to static HTML."""

from __future__ import annotations

import html
from datetime import date as Date

from . import store

# Topic categories, in the order they appear in the topic bar.
# Keys are what digests use in "tags"; PROMPT.md explains each one to the summarizer.
CATEGORIES = {
    "impostos": "Impostos e finanças públicas",
    "banca": "Banca, seguros e mercados",
    "infraestruturas": "Infraestruturas e transportes",
    "habitacao": "Habitação e urbanismo",
    "social": "Segurança social e apoios",
    "trabalho": "Trabalho e emprego",
    "energia": "Energia e ambiente",
    "empresas": "Economia e empresas",
    "saude": "Saúde",
    "educacao": "Educação e ciência",
    "justica": "Justiça e tribunais",
    "estado": "Estado e autarquias",
}
CATEGORY_NOTES = {
    "impostos": "IRS, IVA, IMI, IMT, taxas, Orçamento do Estado e despesa pública.",
    "banca": "Bancos, Banco de Portugal, seguros, CMVM, fundos e mercados financeiros.",
    "infraestruturas": "Ferrovia, metro, estradas, portos, aeroportos, obras públicas e PPP.",
    "habitacao": "Rendas, crédito à habitação, PDM, loteamentos, licenciamento e construção.",
    "social": "Pensões, subsídios, prestações sociais, famílias, deficiência e envelhecimento.",
    "trabalho": "Salários, contratação coletiva, emprego público e regras laborais.",
    "energia": "Eletricidade, combustíveis, água, clima, REN e ordenamento ambiental.",
    "empresas": "Apoios e licenças a empresas, agricultura, pescas, turismo, indústria e defesa.",
    "saude": "SNS, hospitais, medicamentos e profissões de saúde.",
    "educacao": "Escolas, ensino superior, investigação e formação profissional.",
    "justica": "Tribunais, acórdãos do Tribunal Constitucional, códigos e regimes legais.",
    "estado": "Organização do Governo, administração pública, autarquias e eleições.",
}
IMPORTANCE = ("high", "medium")
MONTHS_PT = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
             "agosto", "setembro", "outubro", "novembro", "dezembro"]
WEEKDAYS_PT = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
               "sexta-feira", "sábado", "domingo"]


def validate(digest: dict, day: dict) -> list[str]:
    """Return a list of problems; empty means the digest can be rendered."""
    errors: list[str] = []
    ids = {i["id"] for i in day["items"]}
    if digest.get("date") != day["date"]:
        errors.append(f"date {digest.get('date')!r} does not match data file {day['date']!r}")
    if not isinstance(digest.get("overview"), str) or not digest["overview"].strip():
        errors.append("overview must be a non-empty string")

    for n, h in enumerate(digest.get("highlights", [])):
        where = f"highlights[{n}]"
        if h.get("id") not in ids:
            errors.append(f"{where}: unknown id {h.get('id')!r}")
        for field in ("headline", "explanation"):
            if not str(h.get(field, "")).strip():
                errors.append(f"{where}: missing {field}")
        errors += _check_tags(where, h.get("tags"), 3)
        if h.get("importance") not in IMPORTANCE:
            errors.append(f"{where}: importance must be one of {IMPORTANCE}")

    for n, o in enumerate(digest.get("other", [])):
        if o.get("id") not in ids:
            errors.append(f"other[{n}]: unknown id {o.get('id')!r}")
        if not str(o.get("note", "")).strip():
            errors.append(f"other[{n}]: missing note")
        errors += _check_tags(f"other[{n}]", o.get("tags"), 2)
    return errors


def _check_tags(where: str, tags, most: int) -> list[str]:
    if not isinstance(tags, list) or not 1 <= len(tags) <= most:
        return [f"{where}: tags must list 1–{most} categories"]
    bad = [t for t in tags if t not in CATEGORIES]
    return [f"{where}: unknown tags {bad} (allowed: {list(CATEGORIES)})"] if bad else []


def _e(s) -> str:
    return html.escape(str(s), quote=True)


def _long_date(iso: str) -> str:
    d = Date.fromisoformat(iso)
    return f"{WEEKDAYS_PT[d.weekday()].capitalize()}, {d.day} de {MONTHS_PT[d.month - 1]} de {d.year}"


def _act_label(item: dict) -> str:
    return f"{item['type']} n.º {item['number']}" if item.get("number") else item["type"]


FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500'
         '&family=Literata:opsz,wght@7..72,500;7..72,600&family=Public+Sans:wght@400;500;600&display=swap">')

CSS = """
:root{--bg:#f3f6f4;--surface:#ffffff;--ink:#16201c;--muted:#5a6762;--line:#d9e1dd;
--accent:#0b5d3b;--accent-soft:#e1efe7;--high:#b3261e;--high-soft:#fbe7e5;--chip:#e9eeeb;
--serif:"Literata",Georgia,serif;--sans:"Public Sans",-apple-system,"Segoe UI",Roboto,sans-serif;
--mono:"IBM Plex Mono",ui-monospace,Menlo,monospace;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0f1412;--surface:#161d1a;
--ink:#e4ebe7;--muted:#93a39c;--line:#27312d;--accent:#62c393;--accent-soft:#16291f;
--high:#f28b82;--high-soft:#351a18;--chip:#1f2824;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#0f1412;--surface:#161d1a;--ink:#e4ebe7;--muted:#93a39c;--line:#27312d;
--accent:#62c393;--accent-soft:#16291f;--high:#f28b82;--high-soft:#351a18;--chip:#1f2824;color-scheme:dark}
*{box-sizing:border-box}
[hidden]{display:none!important}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 var(--sans);-webkit-font-smoothing:antialiased}
main{max-width:720px;margin:0 auto;padding-inline:16px;padding-block:24px 72px}
a{color:var(--accent);text-underline-offset:2px}
a:focus-visible,summary:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:4px}
.view{display:flex;flex-direction:column;gap:0}
.kicker{font:500 12px/1 var(--mono);letter-spacing:.06em;text-transform:uppercase;color:var(--accent);margin:0}
h1{font:600 clamp(26px,5.2vw,36px)/1.15 var(--serif);text-wrap:balance;margin:10px 0 6px}
.meta{color:var(--muted);font-size:14px;margin:0 0 18px;font-variant-numeric:tabular-nums}
.nav{display:flex;justify-content:space-between;gap:12px;font-size:14px;font-weight:500;
padding-block:10px;border-block:1px solid var(--line);margin-bottom:24px}
.nav a{text-decoration:none}
.overview{font:400 19px/1.55 var(--serif);max-width:62ch;margin:0 0 8px}
h2{font:500 12px/1 var(--mono);letter-spacing:.06em;text-transform:uppercase;color:var(--muted);
margin:36px 0 12px}
.cards{display:flex;flex-direction:column;gap:12px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:18px 20px;
display:flex;flex-direction:column;gap:8px}
.card h3{font:600 19px/1.3 var(--serif);text-wrap:balance;margin:0}
.card p{margin:0;max-width:65ch}
.src{font-size:13px;color:var(--muted);display:flex;flex-wrap:wrap;gap:6px 8px;align-items:center;margin-top:4px}
.act{font:400 12.5px/1.4 var(--mono)}
.chip{border-radius:4px;padding:2px 7px;font-size:12px;font-weight:500;line-height:1.4}
.chip.high{background:var(--high-soft);color:var(--high)}
.chip.tag{background:var(--accent-soft);color:var(--accent)}
ul.plain{list-style:none;padding:0;margin:0}
ul.plain li{padding:11px 0;border-bottom:1px solid var(--line)}
ul.plain li:last-child{border-bottom:0}
.small{font-size:13.5px;color:var(--muted)}
details{border:1px solid var(--line);border-radius:8px;padding:12px 16px;background:var(--surface)}
summary{cursor:pointer;font-weight:500}
details ul{margin-top:8px}
.day{display:flex;flex-direction:column;gap:4px;text-decoration:none;color:inherit;
padding:16px 0;border-bottom:1px solid var(--line)}
.day strong{font:600 17px/1.3 var(--serif);color:var(--ink)}
.day:hover strong{color:var(--accent)}
.day span{color:var(--muted);font-size:14.5px}
.empty{color:var(--muted);font-style:italic}
.topbar{position:sticky;top:env(safe-area-inset-top,0px);z-index:5;background:var(--bg);
border-bottom:1px solid var(--line)}
.topbar-inner{max-width:720px;margin:0 auto;padding-inline:16px;padding-block:10px;display:flex;
align-items:center;gap:14px}
.brand{font:600 15px/1 var(--serif);color:var(--ink);text-decoration:none;white-space:nowrap}
.brand span{color:var(--accent)}
.topics{display:flex;gap:6px;overflow-x:auto;scrollbar-width:none;-webkit-overflow-scrolling:touch;
mask-image:linear-gradient(90deg,#000 92%,transparent)}
.topics::-webkit-scrollbar{display:none}
.topics a{flex:none;font-size:13px;font-weight:500;color:var(--muted);text-decoration:none;
padding:5px 10px;border-radius:999px;border:1px solid var(--line);background:var(--surface);white-space:nowrap}
.topics a b{font-weight:500;color:var(--accent);font-variant-numeric:tabular-nums;margin-left:2px}
.topics a.zero{opacity:.55}
.topics a:hover{border-color:var(--accent);color:var(--ink)}
.topics a[aria-current]{background:var(--accent);border-color:var(--accent);color:var(--bg)}
.topics a[aria-current] b{color:var(--bg)}
a.chip{text-decoration:none}
a.chip.tag:hover{outline:1px solid var(--accent)}
ul.plain li .src{margin-top:6px}
.count{font:500 13px/1.4 var(--mono);color:var(--muted);margin:0 0 4px}
h2.date{text-transform:none;letter-spacing:0;font:600 16px/1.3 var(--serif);margin:32px 0 12px}
h2.date a{color:var(--ink);text-decoration:none}
h2.date a:hover{color:var(--accent)}
.foot{margin-top:56px;padding-top:16px;border-top:1px solid var(--line);font-size:13px;color:var(--muted)}
.foot p{margin:0 0 6px;max-width:65ch}
@media (prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}
"""


TITLE = "Diário da República Resumido"

FOOTER = ('<footer class="foot"><p>Resumos escritos automaticamente por inteligência artificial a partir '
          'dos sumários oficiais publicados no <a href="https://diariodarepublica.pt" target="_blank" '
          'rel="noopener">Diário da República</a>. Podem conter erros: o texto que faz fé é sempre o '
          'publicado no Diário da República, acessível pela ligação de cada ato.</p>'
          '<p>Projeto independente, sem ligação à INCM nem ao Estado.</p></footer>')

# Days kept in the single page (about 20 KB each); older digests stay on disk.
MAX_DAYS = 400

SCRIPT = """
(function(){
  var views = [].slice.call(document.querySelectorAll('section.view'));
  var links = [].slice.call(document.querySelectorAll('.topics a'));
  function show(){
    var id = location.hash.slice(1) || views[0].id;
    var hit = document.getElementById(id);
    if (!hit || !hit.classList.contains('view')) hit = views[0];
    views.forEach(function(v){ v.hidden = v !== hit; });
    links.forEach(function(a){
      var on = a.getAttribute('href') === '#' + hit.id ||
               (a.dataset.latest && hit.id === views[0].id);
      if (on) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
    });
    window.scrollTo(0, 0);
  }
  window.addEventListener('hashchange', show);
  show();
})();
"""


def _fragment(title: str, body: str) -> str:
    """Page content without the document skeleton (the Artifact host adds it)."""
    return f"<title>{_e(title)}</title>\n{FONTS}\n<style>{CSS}</style>\n{body}\n<script>{SCRIPT}</script>\n"


def _page(title: str, body: str) -> str:
    return ('<!doctype html>\n<html lang="pt-PT">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f"</head>\n<body>\n{_fragment(title, body)}</body>\n</html>\n")


def _link(item: dict, text: str) -> str:
    return f'<a href="{_e(item["link"])}" target="_blank" rel="noopener">{_e(text)}</a>'


def _topic_chips(tags: list[str]) -> str:
    return "".join(f'<a class="chip tag" href="#tema-{t}">{_e(CATEGORIES[t])}</a>' for t in tags)


def _highlight_card(h: dict, it: dict) -> str:
    chips = '<span class="chip high">Importante</span>' if h["importance"] == "high" else ""
    chips += _topic_chips(h["tags"])
    return ('<article class="card">'
            f"<h3>{_e(h['headline'])}</h3>"
            f"<p>{_e(h['explanation'])}</p>"
            f'<div class="src">{chips}'
            f'<span class="act">{_link(it, f"{_act_label(it)} · Série {it['series']}")}</span></div>'
            "</article>")


def _other_item(o: dict, it: dict) -> str:
    return (f'<li>{_e(o["note"])} <span class="small">— {_link(it, _act_label(it))}</span>'
            f'<div class="src">{_topic_chips(o["tags"])}</div></li>')


def render_topbar(latest: str, counts: dict[str, int]) -> str:
    parts = ['<header class="topbar"><div class="topbar-inner">',
             f'<a class="brand" href="#{latest}">DR <span>Resumido</span></a>',
             '<nav class="topics" aria-label="Temas">',
             f'<a href="#{latest}" data-latest="1">Último dia</a>']
    for key, label in CATEGORIES.items():
        n = counts.get(key, 0)
        cls = ' class="zero"' if n == 0 else ""
        parts.append(f'<a href="#tema-{key}"{cls}>{_e(label)} <b>{n}</b></a>')
    parts.append('<a href="#archive">Arquivo</a></nav></div></header>')
    return "".join(parts)


def render_day(digest: dict, day: dict, prev_date: str | None, next_date: str | None) -> str:
    """One day as a <section>; navigation uses #date anchors within the page."""
    items = {i["id"]: i for i in day["items"]}
    s1 = [i for i in day["items"] if i["series"] == "I"]
    s2 = [i for i in day["items"] if i["series"] == "II"]
    s2_kept = sum(1 for i in s2 if i.get("candidate"))
    issue = next((i["issue"] for i in day["items"] if i.get("issue")), "")

    nav = ['<nav class="nav">',
           f'<a href="#{prev_date}">← Anterior</a>' if prev_date else "<span></span>",
           '<a href="#archive">Todos os dias</a>',
           f'<a href="#{next_date}">Seguinte →</a>' if next_date else "<span></span>",
           "</nav>"]

    parts = [
        f'<section class="view" id="{day["date"]}">',
        '<p class="kicker">Diário da República · Resumo do dia</p>',
        f"<h1>{_e(_long_date(day['date']))}</h1>",
        f'<p class="meta">DR n.º {_e(issue)} · {len(s1)} atos na Série I · '
        f"{len(s2)} na Série II ({s2_kept} analisados, {len(s2) - s2_kept} de rotina filtrados)</p>",
        "".join(nav),
        f'<p class="overview">{_e(digest["overview"])}</p>',
    ]

    highlights = sorted(digest.get("highlights", []),
                        key=lambda h: IMPORTANCE.index(h["importance"]))
    parts.append('<h2>Destaques</h2><div class="cards">')
    if not highlights:
        parts.append('<p class="empty">Nada de relevo hoje.</p>')
    parts += [_highlight_card(h, items[h["id"]]) for h in highlights]
    parts.append("</div>")

    others = digest.get("other", [])
    if others:
        parts.append('<h2>Também publicado</h2><ul class="plain">')
        parts += [_other_item(o, items[o["id"]]) for o in others]
        parts.append("</ul>")

    parts.append(f'<h2>Série I completa</h2><details><summary>Os {len(s1)} atos da Série I</summary><ul class="plain">')
    for it in s1:
        parts.append(f'<li><span class="act">{_link(it, _act_label(it))}</span><div class="small">{_e(it["summary"])}</div></li>')
    parts.append("</ul></details></section>")
    return "\n".join(parts)


def render_topic(key: str, days: list[tuple[str, dict, dict]]) -> str:
    """Everything tagged with one category, newest day first."""
    parts = [f'<section class="view" id="tema-{key}">',
             '<p class="kicker">Tema</p>', f"<h1>{_e(CATEGORIES[key])}</h1>",
             f'<p class="meta">{_e(CATEGORY_NOTES[key])}</p>']
    n_high = n_other = n_days = 0
    body: list[str] = []
    for date, digest, day in days:
        items = {i["id"]: i for i in day["items"]}
        hs = sorted((h for h in digest.get("highlights", []) if key in h["tags"]),
                    key=lambda h: IMPORTANCE.index(h["importance"]))
        os_ = [o for o in digest.get("other", []) if key in o["tags"]]
        if not hs and not os_:
            continue
        n_days += 1
        n_high += len(hs)
        n_other += len(os_)
        body.append(f'<h2 class="date"><a href="#{date}">{_e(_long_date(date))}</a></h2>')
        if hs:
            body.append('<div class="cards">' + "".join(_highlight_card(h, items[h["id"]]) for h in hs) + "</div>")
        if os_:
            body.append('<ul class="plain">' + "".join(_other_item(o, items[o["id"]]) for o in os_) + "</ul>")
    if body:
        parts.append(f'<p class="count">{n_high} destaque{"s" if n_high != 1 else ""} e '
                     f'{n_other} outro{"s" if n_other != 1 else ""} ato{"s" if n_other != 1 else ""} '
                     f'em {n_days} dia{"s" if n_days != 1 else ""}</p>')
        parts += body
    else:
        parts.append('<p class="empty">Ainda nada publicado neste tema.</p>')
    parts.append("</section>")
    return "\n".join(parts)


def render_archive(entries: list[tuple[str, dict]]) -> str:
    """entries newest first."""
    parts = ['<section class="view" id="archive">',
             '<p class="kicker">Diário da República</p>', "<h1>Todos os dias</h1>",
             f'<p class="meta">{len(entries)} dia{"s" if len(entries) != 1 else ""} no arquivo</p>']
    month = None
    for date, digest in entries:
        if date[:7] != month:
            month = date[:7]
            parts.append(f'<h2 class="date">{MONTHS_PT[int(month[5:]) - 1].capitalize()} de {month[:4]}</h2>')
        n = len(digest.get("highlights", []))
        overview = digest["overview"]
        snippet = overview if len(overview) <= 220 else overview[:217].rsplit(" ", 1)[0] + "…"
        parts.append(
            f'<a class="day" href="#{date}"><strong>{_e(_long_date(date))} · '
            f"{n} destaque{'s' if n != 1 else ''}</strong><span>{_e(snippet)}</span></a>"
        )
    parts.append("</section>")
    return "\n".join(parts)


def render_app(valid: list[tuple[str, dict, dict]]) -> str:
    """Body markup for the whole archive (input oldest→newest)."""
    valid = valid[-MAX_DAYS:]
    if not valid:
        return (f'<main><section class="view" id="archive"><h1>{TITLE}</h1>'
                '<p class="empty">Ainda não há resumos.</p></section></main>')
    dates = [d for d, _, _ in valid]
    newest_first = list(reversed(valid))

    counts: dict[str, int] = {}
    for _, digest, _ in valid:
        for entry in digest.get("highlights", []) + digest.get("other", []):
            for t in entry["tags"]:
                counts[t] = counts.get(t, 0) + 1

    sections = []
    for n in range(len(valid) - 1, -1, -1):  # newest first: it is the default view
        date, digest, day = valid[n]
        prev_d = dates[n - 1] if n > 0 else None
        next_d = dates[n + 1] if n + 1 < len(dates) else None
        sections.append(render_day(digest, day, prev_d, next_d))
    sections += [render_topic(key, newest_first) for key in CATEGORIES]
    sections.append(render_archive([(d, g) for d, g, _ in newest_first]))
    return (render_topbar(dates[-1], counts) + "\n<main>\n" + "\n".join(sections)
            + "\n" + FOOTER + "\n</main>")


def render_all() -> tuple[list[str], dict[str, list[str]]]:
    """Validate every digest and write site/index.html. Returns (rendered dates, {date: errors})."""
    valid: list[tuple[str, dict, dict]] = []
    problems: dict[str, list[str]] = {}
    for date in store.digest_dates():
        digest, day = store.load_digest(date), store.load_day(date)
        if day is None:
            problems[date] = ["no data file for this date"]
            continue
        errs = validate(digest, day)
        if errs:
            problems[date] = errs
            continue
        valid.append((date, digest, day))

    store.SITE.mkdir(parents=True, exist_ok=True)
    body = render_app(valid)
    # index.html opens locally; artifact.html is the same page for publishing.
    (store.SITE / "index.html").write_text(_page(TITLE, body), encoding="utf-8")
    (store.SITE / "artifact.html").write_text(_fragment(TITLE, body), encoding="utf-8")
    return [d for d, _, _ in valid], problems
