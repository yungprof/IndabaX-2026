"""
tools/symptom_checker.py
─────────────────────────────────────────────────────────────────────────────
Tool: symptom_checker

Looks up reported symptoms against the Ghana condition database
(data/symptoms.json) and returns the best-matching conditions
with urgency levels and triage notes.

YOUR TASKS:
  REQUIRED  Ex 1 — Implement _match_conditions (the core matching logic)
  OPTIONAL  Ex 7 (Advanced) — Improve scoring with weighted symptom matching
─────────────────────────────────────────────────────────────────────────────
"""

import json
from pathlib import Path

# Load data once at import time
_DATA_PATH = Path(__file__).parent.parent / "data" / "symptoms.json"
_SYMPTOMS_DB = json.loads(_DATA_PATH.read_text())


def check_symptoms(
    symptoms: list[str],
    patient_context: dict | None = None,
) -> dict:
    """
    Match reported symptoms to known conditions in the Ghana symptom database.

    Parameters
    ----------
    symptoms        : List of symptom strings, e.g. ["fever", "headache", "chills"]
    patient_context : Optional dict with keys: age_group, is_pregnant

    Returns
    -------
    {
        "matches": [
            {
                "condition": str,
                "condition_id": str,
                "urgency": str,           # "low" | "moderate" | "high" | "critical"
                "confidence": str,        # "high" | "medium" | "low"
                "triage_notes": str,
                "recommended_facility_level": int,
                "severe_indicators_present": bool,
                "matched_symptoms": list[str],
            },
            ...  # up to 3 matches, ranked by confidence
        ],
        "has_severe_indicator": bool,   # True if ANY severe symptom was found
        "raw_symptoms": list[str],      # echo back for traceability
    }
    """
    patient_context = patient_context or {}
    symptoms_lower = [s.lower().strip() for s in symptoms]

    matches = _match_conditions(symptoms_lower, patient_context)
    has_severe = any(m["severe_indicators_present"] for m in matches)

    return {
        "matches": matches[:3],
        "has_severe_indicator": has_severe,
        "raw_symptoms": symptoms_lower,
    }


def _match_conditions(symptoms: list[str], patient_context: dict) -> list[dict]:
    """
    Core matching logic: score each condition in the database against
    the reported symptoms and return ranked results.

    ╔══════════════════════════════════════════════════════════════════════╗
    ║  EXERCISE 1 (REQUIRED) — Implement this function                    ║
    ║                                                                      ║
    ║  Steps to implement:                                                 ║
    ║                                                                      ║
    ║  1. Iterate through each condition in _SYMPTOMS_DB["conditions"]    ║
    ║                                                                      ║
    ║  2. For each condition, count how many of the reported `symptoms`   ║
    ║     appear in condition["symptoms"]["primary"] or ["secondary"]     ║
    ║     Use simple substring or exact matching to start.                ║
    ║                                                                      ║
    ║  3. Check whether any reported symptom appears in                   ║
    ║     condition["symptoms"]["severe_indicators"]                      ║
    ║                                                                      ║
    ║  4. Score each condition:                                           ║
    ║     - primary match = 2 points                                      ║
    ║     - secondary match = 1 point                                     ║
    ║     - severe indicator match = +3 points (and set severe flag)      ║
    ║                                                                      ║
    ║  5. Assign confidence based on score:                               ║
    ║     - score >= 4  → "high"                                          ║
    ║     - score >= 2  → "medium"                                        ║
    ║     - score >= 1  → "low"                                           ║
    ║     - score == 0  → skip (don't include in results)                 ║
    ║                                                                      ║
    ║  6. Special case: if patient_context["is_pregnant"] is True,        ║
    ║     boost "maternal_complication" score by 3.                       ║
    ║                                                                      ║
    ║  7. Return results sorted by score descending. If no conditions     ║
    ║     matched, return the "unknown" condition as a fallback.          ║
    ║                                                                      ║
    ║  OPTIONAL (Exercise 7 — Advanced):                                  ║
    ║     Add fuzzy matching so "headche" still matches "headache".       ║
    ║     Consider the difflib.get_close_matches() standard library fn.  ║
    ╚══════════════════════════════════════════════════════════════════════╝

    Parameters
    ----------
    symptoms        : Lowercased symptom list.
    patient_context : Dict, may contain age_group, is_pregnant.

    Returns
    -------
    List of match dicts, sorted by confidence (highest first).
    """
    # TODO: implement matching logic (see exercise above)
    results = []

    # Fallback: return unknown condition if nothing matched
    if not results:
        unknown = next(
            (c for c in _SYMPTOMS_DB["conditions"] if c["id"] == "unknown"),
            None,
        )
        if unknown:
            results.append({
                "condition": unknown["name"],
                "condition_id": unknown["id"],
                "urgency": unknown["urgency"],
                "confidence": "low",
                "triage_notes": unknown["triage_notes"],
                "recommended_facility_level": unknown["recommended_level"],
                "severe_indicators_present": False,
                "matched_symptoms": [],
            })

    return results
