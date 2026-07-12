"""
Tests for the fact-gate markdown-to-plain-text pass.

Fixtures are verbatim failure classes from the 2026-07-11 real-LLM browser
test (finding L8): literal **, ###, pipe tables, &nbsp;, and mojibake leaked
onto court PDFs.
"""
from app.services.fact_gate.markdown_strip import strip_markdown


class TestStripMarkdown:
    def test_unwraps_paired_bold(self):
        out, corrections = strip_markdown("2.1 Petitioner is **Jacob Delgado**.")
        assert out == "2.1 Petitioner is Jacob Delgado."
        assert len(corrections) == 1
        assert corrections[0].type == "markdown"
        assert corrections[0].severity == "info"

    def test_unwraps_paired_underscores_and_backticks(self):
        out, _ = strip_markdown("__Respondent__ sent a text reading `not happening today`.")
        assert out == "Respondent sent a text reading not happening today."

    def test_drops_heading_markers_keeps_text(self):
        out, _ = strip_markdown("### DECLARATION OF FACTS\nOn June 14, 2026, Respondent did not appear.")
        assert out.startswith("DECLARATION OF FACTS")
        assert "#" not in out
        assert "On June 14, 2026, Respondent did not appear." in out

    def test_pipe_table_becomes_labeled_lines(self):
        table = (
            "| Child | Date of Birth |\n"
            "|---|---|\n"
            "| Sofia Delgado | March 22, 2018 |\n"
            "| Mateo Delgado | November 5, 2020 |"
        )
        out, _ = strip_markdown(table)
        assert "|" not in out
        assert "Child: Sofia Delgado; Date of Birth: March 22, 2018" in out
        assert "Child: Mateo Delgado; Date of Birth: November 5, 2020" in out

    def test_html_entities_unescaped(self):
        out, _ = strip_markdown("Custody&nbsp;exchange at 5:00&nbsp;p.m.")
        assert "&nbsp;" not in out
        assert out == "Custody exchange at 5:00 p.m."

    def test_mojibake_repaired(self):
        out, _ = strip_markdown("Respondentâ€™s counsel said â€œno.â€")
        assert "â" not in out
        assert "Respondent's" in out
        assert '"no."' in out

    def test_code_fences_removed_content_kept(self):
        out, _ = strip_markdown("```\nDeclaration text stays.\n```")
        assert "`" not in out
        assert "Declaration text stays." in out

    def test_clean_text_untouched_and_no_correction(self):
        text = "On June 14, 2026, Petitioner waited 45 minutes at the exchange."
        out, corrections = strip_markdown(text)
        assert out == text
        assert corrections == []

    def test_one_aggregate_correction_for_many_changes(self):
        messy = "### Title\n**Bold** and __marked__ text&nbsp;here.\n| A | B |\n|---|---|\n| 1 | 2 |"
        _, corrections = strip_markdown(messy)
        assert len(corrections) == 1

    def test_idempotent(self):
        messy = (
            "### Title\n"
            "**Bold** and __marked__ and `code` plus&nbsp;entity and â€™ quote.\n"
            "| A | B |\n"
            "|---|---|\n"
            "| 1 | 2 |"
        )
        once, _ = strip_markdown(messy)
        twice, corrections = strip_markdown(once)
        assert twice == once
        assert corrections == []
