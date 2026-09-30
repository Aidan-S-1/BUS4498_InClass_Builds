#!/usr/bin/env python3
"""Synthetic teaching tool for the HackTrack T3 Skill. Requires Python 3; standard library only.

Applies the baseline scoring weights from references/scoring-rules.md to a CSV of
registrants and prints one JSON object per registrant with the score, label, the
signals that were used, the signals that were unknown, and any flags.

Run:
    python scripts/score_registrants.py registrants.csv
    python scripts/score_registrants.py registrants.csv --weights weights.json

Expected CSV columns (header row required; extra columns are ignored):
    registrant_id      any text, must be present
    days_before_event  whole number of days between registration and the event
    signup_type        solo | team
    team_name          text, may be blank
    cancelled          yes | no  (blank = no)
    contact_count      0, 1, or 2; leave BLANK if the count is missing
    past_attended      number of prior CPVC events this person checked in to
    past_no_show       number of prior events registered for but not checked in to
    confirmation       yes | maybe | no | none | unknown  (blank = none)

Expected output for the sample row  R001,2,team,Byte Club,no,1,1,0,yes :
    {"registrant_id": "R001", "score": 100, "label": "likely", ...}
    (40 baseline + 35 yes + 15 attended + 10 late signup + 10 team = 110, clamped to 100)

The script does NOT interpret free-text replies, resolve conflicts, or send
messages. Do those steps in the Skill procedure; then rerun the script with the
adjusted confirmation value if a reply was reinterpreted.
"""
import argparse
import csv
import json
import sys

DEFAULT_WEIGHTS = {
    "baseline": 40,
    "confirmation": {"yes": 35, "maybe": 10, "none": 0, "unknown": 0},
    "confirmation_no_override": 5,
    "past_attended": 15,
    "past_no_show": -15,
    "timing_late_days": 3,
    "timing_late": 10,
    "timing_early_days": 14,
    "timing_early": -5,
    "team": 10,
    "cancelled_override": 0,
    "label_likely": 65,
    "label_uncertain": 35,
    "contact_limit": 2,
}


def load_weights(path):
    weights = json.loads(json.dumps(DEFAULT_WEIGHTS))
    if path:
        with open(path, encoding="utf-8") as handle:
            override = json.load(handle)
        if not isinstance(override, dict):
            raise ValueError("Weights file must contain a JSON object.")
        for key, value in override.items():
            if key == "confirmation" and isinstance(value, dict):
                weights["confirmation"].update(value)
            elif key in weights:
                weights[key] = value
            else:
                raise ValueError(f"Unknown weight: {key}")
    return weights


def as_int(value, field, registrant_id):
    text = (value or "").strip()
    if text == "":
        return None
    try:
        return int(float(text))
    except ValueError:
        raise ValueError(f"{registrant_id}: {field} must be a number, got {text!r}")


def score_row(row, weights):
    registrant_id = (row.get("registrant_id") or "").strip()
    if not registrant_id:
        raise ValueError("Every row needs a registrant_id.")
    score = weights["baseline"]
    used, unknown, flags = [], [], []

    confirmation = (row.get("confirmation") or "none").strip().lower() or "none"
    if confirmation not in ("yes", "maybe", "no", "none", "unknown"):
        raise ValueError(f"{registrant_id}: confirmation must be yes, maybe, no, none, or unknown, got {confirmation!r}")
    if confirmation in ("none", "unknown"):
        unknown.append("confirmation")
    else:
        used.append(f"confirmation={confirmation}")
    if confirmation != "no":
        score += weights["confirmation"][confirmation]

    attended = as_int(row.get("past_attended"), "past_attended", registrant_id)
    no_show = as_int(row.get("past_no_show"), "past_no_show", registrant_id)
    if attended is None and no_show is None:
        unknown.append("history")
    elif (attended or 0) > 0:
        score += weights["past_attended"]
        used.append(f"history=attended {attended} prior event(s)")
    elif (no_show or 0) > 0:
        score += weights["past_no_show"]
        used.append(f"history=registered before, no check-in ({no_show})")
    else:
        unknown.append("history")

    days = as_int(row.get("days_before_event"), "days_before_event", registrant_id)
    if days is None:
        unknown.append("timing")
    elif days <= weights["timing_late_days"]:
        score += weights["timing_late"]
        used.append(f"timing=registered {days} day(s) before (late)")
    elif days > weights["timing_early_days"]:
        score += weights["timing_early"]
        used.append(f"timing=registered {days} days before (early)")
    else:
        used.append(f"timing=registered {days} days before (neutral)")

    signup = (row.get("signup_type") or "").strip().lower()
    team_name = (row.get("team_name") or "").strip()
    if signup == "team" and team_name:
        score += weights["team"]
        used.append(f"team={team_name}")
    elif signup in ("solo", ""):
        used.append("team=solo")
    else:
        used.append(f"team={signup}")

    cancelled = (row.get("cancelled") or "no").strip().lower() in ("yes", "true", "1")
    if cancelled:
        score = weights["cancelled_override"]
        used.append("cancelled=yes (override)")
    elif confirmation == "no":
        score = weights["confirmation_no_override"]
        used.append("confirmation=no (override)")

    score = max(0, min(100, int(round(score))))
    if score >= weights["label_likely"]:
        label = "likely"
    elif score >= weights["label_uncertain"]:
        label = "uncertain"
    else:
        label = "unlikely"

    contact = as_int(row.get("contact_count"), "contact_count", registrant_id)
    if contact is None:
        flags.append("contact count missing: treated as at the two-message limit until an organizer confirms it")
        contact_for_limit = weights["contact_limit"]
    else:
        contact_for_limit = contact
    candidate = (
        label == "uncertain"
        and confirmation in ("none", "unknown")
        and contact_for_limit < weights["contact_limit"]
        and not cancelled
    )

    return {
        "registrant_id": registrant_id,
        "score": score,
        "label": label,
        "signals_used": used,
        "signals_unknown": unknown,
        "contact_count": contact,
        "confirmation_candidate": candidate,
        "candidate_priority": abs(score - 50) if candidate else None,
        "flags": flags,
    }


def main():
    parser = argparse.ArgumentParser(description="Score registrants' likelihood of attending.")
    parser.add_argument("csv_path")
    parser.add_argument("--weights", help="JSON file that overrides the default weights")
    args = parser.parse_args()
    try:
        weights = load_weights(args.weights)
        with open(args.csv_path, newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
        if not rows:
            raise ValueError("The CSV has no registrant rows.")
        results = [score_row(row, weights) for row in rows]
        seen = {}
        for result in results:
            seen.setdefault(result["registrant_id"], 0)
            seen[result["registrant_id"]] += 1
        for result in results:
            if seen[result["registrant_id"]] > 1:
                result["flags"].append("duplicate registrant_id in the list: possible identity question for the organizers")
        candidates = sorted(
            (r for r in results if r["confirmation_candidate"]),
            key=lambda r: (r["candidate_priority"], r["registrant_id"]),
        )
        print(json.dumps({
            "weights_used": weights,
            "registrants_scored": len(results),
            "labels": {
                "likely": sum(r["label"] == "likely" for r in results),
                "uncertain": sum(r["label"] == "uncertain" for r in results),
                "unlikely": sum(r["label"] == "unlikely" for r in results),
            },
            "confirmation_candidates": [r["registrant_id"] for r in candidates],
            "results": results,
        }, indent=2))
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
