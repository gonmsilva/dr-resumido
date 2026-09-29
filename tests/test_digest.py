import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from dr_digest import render, store
from dr_digest.feeds import parse_feed
from dr_digest.filters import select

FIXTURES = Path(__file__).parent / "fixtures"


def load(series):
    name = "serie1" if series == "I" else "serie2"
    return parse_feed((FIXTURES / f"{name}.xml").read_bytes(), series)


class ParseTests(unittest.TestCase):
    def test_serie1_fields(self):
        date, items = load("I")
        self.assertEqual(date, "2026-09-28")
        first = items[0]
        self.assertEqual(first.id, "1174093370")
        self.assertEqual(first.type, "Resolução da Assembleia da República")
        self.assertEqual(first.number, "250/2026")
        self.assertEqual(first.issue, "188/2026")
        self.assertTrue(first.link.startswith("https://diariodarepublica.pt/dr/detalhe/"))

    def test_serie2_types(self):
        _, items = load("II")
        self.assertEqual(len(items), 327)
        self.assertIn("Anúncio de procedimento", {i.type for i in items})


class FilterTests(unittest.TestCase):
    def test_keeps_all_of_serie1(self):
        _, items = load("I")
        self.assertEqual(len(select(items)), len(items))

    def test_drops_serie2_noise(self):
        _, items = load("II")
        kept = select(items)
        self.assertLess(len(kept), 40)
        self.assertFalse(any(i.type == "Anúncio de procedimento" for i in kept))
        summaries = " ".join(i.summary for i in kept)
        self.assertIn("parceria público-privada", summaries)  # Cascais/Sintra PPP survives
        self.assertNotIn("procedimento concursal comum", summaries)


class ArchiveTests(unittest.TestCase):
    def test_issue_title_parsing(self):
        from dr_digest.archive import ISSUE_TITLE_RE
        m = ISSUE_TITLE_RE.search("Diário da República n.º 42/2026, Suplemento, Série I de 2026-03-02")
        self.assertEqual((m["num"], m["series"], bool(m["supl"])), ("42", "I", True))
        m = ISSUE_TITLE_RE.search("Diário da República n.º 189/2026, Série II de 2026-09-29")
        self.assertEqual((m["num"], m["series"], bool(m["supl"])), ("189", "II", False))

    def test_summary_html_is_stripped(self):
        from dr_digest.archive import _clean_summary
        raw = "<p>Altera a <a href='/dr/x'>Resolução n.º 134/2026</a>, de 24 de junho &amp; mais.</p>"
        self.assertEqual(_clean_summary(raw), "Altera a Resolução n.º 134/2026, de 24 de junho & mais.")


class StoreTests(unittest.TestCase):
    def test_save_dedupes_within_and_across_fetches(self):
        _, items = load("I")
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(store, "DATA", Path(tmp)):
            first = store.save_items(items)
            unique = len({i.id for i in items})
            self.assertEqual(first["2026-09-28"], unique)
            self.assertEqual(store.save_items(items)["2026-09-28"], 0)
            self.assertEqual(len(store.load_day("2026-09-28")["items"]), unique)


class RenderTests(unittest.TestCase):
    def setUp(self):
        _, s1 = load("I")
        _, s2 = load("II")
        self.day = {"date": "2026-09-28", "items": [
            {**i.to_dict(), "candidate": True} for i in s1 + s2]}
        self.digest = {
            "date": "2026-09-28",
            "overview": "A test day.",
            "highlights": [{"id": "1174092980", "headline": "PPP", "explanation": "Rail.",
                            "tags": ["infraestruturas"], "importance": "high"}],
            "other": [{"id": "1174093290", "note": "Fees.", "tags": ["impostos"]}],
        }

    def test_valid_digest(self):
        self.assertEqual(render.validate(self.digest, self.day), [])

    def test_rejects_invented_id_and_bad_tag(self):
        self.digest["highlights"][0]["id"] = "999"
        self.digest["highlights"][0]["tags"] = ["sports"]
        errors = render.validate(self.digest, self.day)
        self.assertTrue(any("unknown id" in e for e in errors))
        self.assertTrue(any("unknown tags" in e for e in errors))

    def test_other_items_need_tags(self):
        del self.digest["other"][0]["tags"]
        self.assertTrue(any("other[0]: tags" in e for e in render.validate(self.digest, self.day)))

    def test_topic_view_collects_tagged_items(self):
        body = render.render_app([("2026-09-28", self.digest, self.day)])
        self.assertIn('id="tema-infraestruturas"', body)
        start = body.index('id="tema-infraestruturas"')
        topic = body[start:body.index("</section>", start)]
        self.assertIn("PPP", topic)            # the highlight tagged infraestruturas
        self.assertNotIn("Fees.", topic)       # the item tagged impostos stays out
        self.assertIn('href="#tema-impostos"', body)  # topic bar links every topic
        self.assertIn("Ainda nada publicado neste tema.", body)  # empty topics say so

    def test_app_has_day_and_archive_views(self):
        body = render.render_app([("2026-09-28", self.digest, self.day)])
        self.assertIn('id="2026-09-28"', body)
        self.assertIn('id="archive"', body)
        self.assertIn("438/2026/1", body)  # full Série I list uses real act numbers
        self.assertNotIn("<html", render._fragment(render.TITLE, body))
        # .view sets display:flex, which would override the hidden attribute
        # and stack every day on one page unless this rule is present.
        self.assertIn("[hidden]{display:none!important}", render.CSS)


if __name__ == "__main__":
    unittest.main()
