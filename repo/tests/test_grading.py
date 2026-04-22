#!/usr/bin/env python3
"""
Local test harness for grading.json.

Simulates what a keyword-weighted grader would do with sample student answers.
Run this against your rubric before pushing to the classroom system.

Usage: python3 test_grading.py
"""

import json
from pathlib import Path

GRADING_FILE = Path(__file__).resolve().parent.parent / "lesson_package" / "grading.json"


def grade_answer(answer: str, question: dict) -> dict:
    """Score a student answer against a question's rubric."""
    scoring = question["scoring"]
    max_points = question["max_points"]
    answer_lower = answer.lower()
    word_count = len(answer.split())

    awarded = 0
    concepts_matched = []
    concepts_missed = []

    # Score each concept
    for concept in scoring["required_concepts"]:
        keywords = concept["keywords_any"]
        if any(kw.lower() in answer_lower for kw in keywords):
            awarded += concept["weight"]
            concepts_matched.append(concept["concept"])
        else:
            concepts_missed.append(concept["concept"])

    # Check disqualifiers
    disqualified = False
    for dq in scoring.get("automatic_disqualifiers", []):
        if any(p.lower() in answer_lower for p in dq["pattern_any"]):
            awarded = 0
            disqualified = True
            break

    # Length penalty
    lp = scoring.get("length_penalty", {})
    if lp and word_count < lp.get("under_word_count", 0):
        awarded = max(0, awarded - lp["penalty"])

    return {
        "score": min(awarded, max_points),
        "max": max_points,
        "concepts_matched": concepts_matched,
        "concepts_missed": concepts_missed,
        "disqualified": disqualified,
        "word_count": word_count,
    }


def main():
    with open(GRADING_FILE) as fp:
        rubric = json.load(fp)

    q1 = next(q for q in rubric["questions"] if q["question_id"] == "q1_why_not_exact")

    # Test cases: (label, expected_score_band, answer)
    cases = [
        (
            "Ideal full-credit answer",
            (9, 10),
            "The ESP32's delay function isn't perfectly precise; it relies on the RTOS tick. "
            "The CPU also handles background interrupts like USB and WiFi while the blink loop runs. "
            "Each interrupt steals a few microseconds, and over many cycles those errors accumulate into a measurable frequency offset."
        ),
        (
            "Partial credit — mentions software only",
            (3, 5),
            "The delay function just isn't perfectly precise so the timing drifts a little."
        ),
        (
            "Partial credit — mentions CPU busy only",
            (3, 5),
            "The CPU is doing other things like running WiFi in the background."
        ),
        (
            "Strong answer, different vocabulary",
            (7, 10),
            "The loop isn't the only thing running. There's RTOS overhead and ISR work happening between each delay, "
            "which throws off the timing by a tiny bit each pass."
        ),
        (
            "Should be disqualified — blames hardware",
            (0, 0),
            "The hardware is broken or the crystal oscillator is bad."
        ),
        (
            "Too short — length penalty",
            (0, 4),
            "delay isn't exact"
        ),
        (
            "Blank answer",
            (0, 0),
            ""
        ),
    ]

    print(f"Grading rubric: {q1['question_id']}")
    print(f"Max points: {q1['max_points']}\n")
    print(f"{'Test case':<48} {'Score':>8}   {'Expected':>10}   {'Pass?':<5}")
    print("-" * 80)

    all_pass = True
    for label, (lo, hi), answer in cases:
        result = grade_answer(answer, q1)
        got = result["score"]
        passed = lo <= got <= hi
        all_pass = all_pass and passed
        status = "ok" if passed else "FAIL"
        print(f"{label:<48} {got:>3}/{result['max']:<4} {f'{lo}-{hi}':>10}   {status:<5}")
        if not passed:
            print(f"    matched: {result['concepts_matched']}")
            print(f"    missed:  {result['concepts_missed']}")
            print(f"    disqualified: {result['disqualified']}, words: {result['word_count']}")

    print()
    print(f"Overall: {'all cases passed' if all_pass else 'some cases failed — review rubric'}")


if __name__ == "__main__":
    main()
