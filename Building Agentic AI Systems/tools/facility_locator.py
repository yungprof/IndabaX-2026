"""
tools/facility_locator.py
─────────────────────────────────────────────────────────────────────────────
Tool: facility_locator

Searches the Ghana facilities database (data/facilities.json) to find
the most appropriate health facility given a location and required
care level.

YOUR TASKS:
  REQUIRED  Ex 1 — Implement _find_best_facility (the search logic)
  OPTIONAL  Ex 8 (Advanced) — Add distance-based sorting using coordinates
─────────────────────────────────────────────────────────────────────────────
"""

import json
from pathlib import Path

_DATA_PATH = Path(__file__).parent.parent / "data" / "facilities.json"
_FACILITIES_DB = json.loads(_DATA_PATH.read_text())


def find_facility(
    required_level: int,
    district: str | None = None,
    region: str | None = None,
    needs_emergency: bool = False,
) -> dict:
    """
    Find the best matching health facility.

    Parameters
    ----------
    required_level   : Minimum facility level (1–4).
    district         : Patient's district (optional).
    region           : Patient's region (optional).
    needs_emergency  : If True, only return facilities with emergency services.

    Returns
    -------
    {
        "found": bool,
        "facility": {               # present only if found=True
            "name": str,
            "type": str,
            "district": str,
            "region": str,
            "level": int,
            "services": list[str],
            "emergency": bool,
        } | None,
        "level_description": str,  # description of the recommended tier
        "message": str,            # human-readable summary for the agent
    }
    """
    facilities = _FACILITIES_DB["facilities"]
    level_descriptions = _FACILITIES_DB["facility_levels"]

    best = _find_best_facility(
        facilities=facilities,
        required_level=required_level,
        district=district,
        region=region,
        needs_emergency=needs_emergency,
    )

    level_desc = level_descriptions.get(str(required_level), "")

    if best:
        return {
            "found": True,
            "facility": {
                "name": best["name"],
                "type": best["type"],
                "district": best["district"],
                "region": best["region"],
                "level": best["level"],
                "services": best["services"],
                "emergency": best["emergency"],
            },
            "level_description": level_desc,
            "message": (
                f"Recommended facility: {best['name']} ({best['type'].replace('_', ' ').title()}) "
                f"in {best['district']}, {best['region']}. "
                f"Services: {', '.join(best['services'][:4])}."
            ),
        }
    else:
        return {
            "found": False,
            "facility": None,
            "level_description": level_desc,
            "message": (
                f"No facility found near {district or region or 'your location'} "
                f"at level {required_level}. "
                f"Please ask at your local CHPS compound for the nearest referral centre."
            ),
        }


def _find_best_facility(
    facilities: list[dict],
    required_level: int,
    district: str | None,
    region: str | None,
    needs_emergency: bool,
) -> dict | None:
    """
    Search and rank facilities to find the best match.

    ╔══════════════════════════════════════════════════════════════════════╗
    ║  EXERCISE 1 (REQUIRED) — Implement this function                    ║
    ║                                                                      ║
    ║  Matching priority (highest to lowest):                             ║
    ║    1. Facility level >= required_level                              ║
    ║       (always required — do not return a facility below the level)  ║
    ║    2. If needs_emergency=True, facility["emergency"] must be True   ║
    ║    3. District match (case-insensitive substring)                   ║
    ║    4. Region match (case-insensitive substring)                     ║
    ║    5. If no location given, return the first qualifying facility     ║
    ║                                                                      ║
    ║  Scoring suggestion:                                                ║
    ║    district match  → +3 points                                      ║
    ║    region match    → +2 points                                      ║
    ║    exact level fit → +1 point (level == required_level, not higher) ║
    ║                                                                      ║
    ║  Return the highest-scoring facility, or None if none qualify.      ║
    ║                                                                      ║
    ║  OPTIONAL (Exercise 8 — Advanced):                                  ║
    ║    Add a distance calculation using the coordinates field:           ║
    ║    facility["coordinates"]["lat"] / ["lng"]                         ║
    ║    You'll need to accept a patient lat/lng and use the              ║
    ║    Haversine formula (or a simple Euclidean approximation).         ║
    ╚══════════════════════════════════════════════════════════════════════╝

    Returns the best-matching facility dict, or None.
    """
    # TODO: implement facility search and ranking logic
    return None
