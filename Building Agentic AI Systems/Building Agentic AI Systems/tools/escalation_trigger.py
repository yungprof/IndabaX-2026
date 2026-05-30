"""
tools/escalation_trigger.py
─────────────────────────────────────────────────────────────────────────────
Tool: escalation_trigger

Evaluates whether a patient's condition warrants immediate escalation
to emergency services or a higher-tier facility, and what the
recommended action is.

This tool represents the "human-in-the-loop" concept from the theory
session — the agent pausing to flag critical cases rather than
attempting to handle them autonomously.

YOUR TASKS:
  REQUIRED  Ex 1 — Implement evaluate_escalation (the full function)
  REQUIRED  Ex 1 — Add this tool's schema to agent/core.py TOOL_SCHEMAS
─────────────────────────────────────────────────────────────────────────────
"""

import json
from pathlib import Path

_DATA_PATH = Path(__file__).parent.parent / "data" / "symptoms.json"
_SYMPTOMS_DB = json.loads(_DATA_PATH.read_text())

# Conditions that always require immediate hospital-level care
ALWAYS_ESCALATE = {"snakebite", "hypertension_crisis", "maternal_complication", "cholera"}

# Urgency levels that require escalation
ESCALATE_URGENCY = {"high", "critical"}


def evaluate_escalation(
    condition_id: str,
    severity: str,
    patient_context: dict | None = None,
) -> dict:
    """
    Evaluate whether this case requires immediate escalation.

    Parameters
    ----------
    condition_id    : Condition ID from symptom_checker, e.g. "malaria"
    severity        : One of: "mild", "moderate", "severe", "critical"
    patient_context : Optional dict with keys: age_group, is_pregnant

    Returns
    -------
    {
        "escalate": bool,             # True = this needs immediate escalation
        "reason": str,                # why escalation is or isn't needed
        "action": str,                # what the patient should do RIGHT NOW
        "contact": str | None,        # emergency contact if applicable
        "recommended_level": int,     # facility level needed
    }

    ╔══════════════════════════════════════════════════════════════════════╗
    ║  EXERCISE 1 (REQUIRED) — Implement this function                    ║
    ║                                                                      ║
    ║  Escalation rules to implement:                                     ║
    ║                                                                      ║
    ║  1. If condition_id is in ALWAYS_ESCALATE → escalate = True         ║
    ║                                                                      ║
    ║  2. If severity is "severe" or "critical" → escalate = True         ║
    ║                                                                      ║
    ║  3. If patient_context["is_pregnant"] is True AND severity is       ║
    ║     anything other than "mild" → escalate = True                    ║
    ║                                                                      ║
    ║  4. If patient_context["age_group"] is "child" AND severity is      ║
    ║     "moderate" or worse → escalate = True                           ║
    ║                                                                      ║
    ║  5. If none of the above → escalate = False                         ║
    ║                                                                      ║
    ║  For the "action" field:                                            ║
    ║    - escalate=True  → "Go to the nearest hospital immediately."     ║
    ║    - escalate=False → "Visit your CHPS compound or health centre."  ║
    ║                                                                      ║
    ║  For the "contact" field:                                           ║
    ║    - If escalate=True → "0800-111-222" (Ghana national ambulance)   ║
    ║    - If escalate=False → None                                       ║
    ║                                                                      ║
    ║  For "recommended_level":                                           ║
    ║    - escalate=True  → 3 (district hospital minimum)                 ║
    ║    - escalate=False → look up the condition's recommended_level     ║
    ║      from _SYMPTOMS_DB, defaulting to 1                             ║
    ║                                                                      ║
    ║  Hint: find the condition in the DB with:                           ║
    ║    next((c for c in _SYMPTOMS_DB["conditions"]                      ║
    ║          if c["id"] == condition_id), None)                         ║
    ╚══════════════════════════════════════════════════════════════════════╝
    """
    patient_context = patient_context or {}

    # TODO: implement escalation logic
    raise NotImplementedError(
        "evaluate_escalation is not implemented yet. "
        "Complete Exercise 1 in tools/escalation_trigger.py"
    )
