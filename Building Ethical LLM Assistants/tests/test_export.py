"""
Tests for the assessment export function.
"""
import os
os.environ["MOCK_MODE"] = "true"

from core.export import export_assessment, ASSESSMENT_TEMPLATE
from core.logging import make_log_entry


def _make_entry(**kwargs):
    return make_log_entry(**kwargs)


def test_export_with_no_logs_and_no_text_uses_template():
    result = export_assessment("", [], date="2026-06-25")
    # All three dimension headers present
    assert "## Dimension 1: Technical Robustness" in result
    assert "## Dimension 2: Ethical Alignment" in result
    assert "## Dimension 3: Observability" in result


def test_export_includes_evidence_section():
    logs = [_make_entry(mock=True, stage="guardrails")]
    result = export_assessment("", logs, date="2026-06-25")
    assert "## Evidence" in result
    assert "Observability Dashboard" in result
    assert "Run Logs" in result


def test_export_with_participant_text_uses_it():
    participant_text = "# My Assessment\n\nDimension 1: The base assistant..."
    result = export_assessment(participant_text, [], date="2026-06-25")
    assert "My Assessment" in result
    assert "## Evidence" in result


def test_export_observability_table_has_correct_counts():
    logs = [
        _make_entry(mock=True, input_flags=["injection_attempt"], blocked_pre_llm=True, tokens_saved_estimated=30),
        _make_entry(mock=True, output_flags=["guarantee"]),
        _make_entry(mock=True),
    ]
    result = export_assessment("", logs, date="2026-06-25")
    assert "| Total requests | 3 |" in result
    assert "| Flagged interactions | 2 |" in result
    assert "| Blocked pre-LLM | 1 |" in result
    assert "| Tokens saved (estimated) | 30 |" in result


def test_export_violation_taxonomy_in_evidence():
    logs = [
        _make_entry(mock=True, input_flags=["injection_attempt"]),
        _make_entry(mock=True, output_flags=["guarantee", "guarantee"]),
    ]
    result = export_assessment("", logs, date="2026-06-25")
    assert "injection_attempt" in result
    assert "guarantee" in result
    assert "LLM01" in result
    assert "LLM09" in result


def test_export_mock_caveat_appears():
    logs = [_make_entry(mock=True)]
    result = export_assessment("", logs, date="2026-06-25")
    assert "MOCK" in result
    assert "illustrative" in result


def test_export_includes_owasp_tags_in_recommendations_table():
    result = export_assessment("", [], date="2026-06-25")
    assert "OWASP" in result


def test_export_includes_stakeholder_prompts():
    result = export_assessment("", [], date="2026-06-25")
    assert "Indigenous Data Sovereignty" in result
    assert "Democratic Objection" in result
    # Must mention at least one Ghanaian language
    assert "Twi" in result


def test_export_providers_listed():
    result = export_assessment("", [], providers_used=["anthropic", "gemma"], date="2026-06-25")
    assert "anthropic" in result
    assert "gemma" in result


def test_export_returns_valid_markdown_string():
    result = export_assessment("", [], date="2026-06-25")
    assert isinstance(result, str)
    assert len(result) > 500  # substantial content
