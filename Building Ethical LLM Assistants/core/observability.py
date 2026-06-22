"""
Observability dashboard — stand-in for Grafana.

Computes three metrics from the session log:
  1. Flagged-interaction volume  (total vs flagged)
  2. Violation taxonomy          (flag type → count)
  3. Token savings               (estimated tokens saved by pre-LLM blocking)

All token counts are estimates (len(text)//4) and are labeled accordingly.
In MOCK_MODE the numbers are illustrative — the caveat string says so.

OWASP LLM10: Unbounded Consumption / "Denial of Wallet" mitigation is the
economic framing for the token-savings metric.
"""


def summarize_logs(logs: list[dict]) -> dict:
    """
    Summarize a list of log entries into the observability dashboard metrics.

    Args:
        logs: list of dicts from make_log_entry()

    Returns:
        {
            total_requests,
            flagged_count,
            blocked_pre_llm_count,
            violation_taxonomy,
            total_tokens_saved_estimated,
            mock_mode,
            caveat,
        }
    """
    total_requests = len(logs)
    flagged_count = 0
    blocked_pre_llm_count = 0
    total_tokens_saved = 0
    taxonomy: dict[str, int] = {}
    has_mock = False

    for entry in logs:
        if entry.get("mock"):
            has_mock = True

        all_flags = list(entry.get("input_flags") or []) + list(entry.get("output_flags") or [])

        if all_flags or entry.get("blocked_pre_llm") or entry.get("escalated"):
            flagged_count += 1

        if entry.get("blocked_pre_llm"):
            blocked_pre_llm_count += 1

        saved = entry.get("tokens_saved_estimated") or 0
        total_tokens_saved += saved

        for flag in all_flags:
            taxonomy[flag] = taxonomy.get(flag, 0) + 1

        if entry.get("escalated"):
            taxonomy["escalated"] = taxonomy.get("escalated", 0) + 1

    caveat = "estimated · illustrative in MOCK" if has_mock else "estimated"

    return {
        "total_requests": total_requests,
        "flagged_count": flagged_count,
        "blocked_pre_llm_count": blocked_pre_llm_count,
        "violation_taxonomy": taxonomy,
        "total_tokens_saved_estimated": total_tokens_saved,
        "mock_mode": has_mock,
        "caveat": caveat,
    }
