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
    scoring = question["scoring"]
    max_points = question["max_points"]
    answer_lower = answer.lower()
    word_count = len(answer.split())

    awarded = 0
    concepts_matched = []
    concepts_missed = []

    for concept in scoring["required_concepts"]:
        keywords = concept["keywords_any"]
        if any(kw.lower() in answer_lower for kw in keywords):
            awarded += concept["weight"]
            concepts_matched.append(concept["concept"])
        else:
            concepts_missed.append(concept["concept"])

    disqualified = False
    for dq in scoring.get("automatic_disqualifiers", []):
        if any(p.lower() in answer_lower for p in dq["pattern_any"]):
            awarded = 0
            disqualified = True
            break

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


def run_cases(question, cases):
    all_pass = True
    print(f"\n{'─'*80}")
    print(f"Question: {question['question_id']}  (max {question['max_points']} pts)")
    print(f"{'─'*80}")
    print(f"{'Test case':<48} {'Score':>8}   {'Expected':>10}   {'Pass?'}")
    print(f"{'─'*80}")

    for label, (lo, hi), answer in cases:
        result = grade_answer(answer, question)
        got = result["score"]
        passed = lo <= got <= hi
        all_pass = all_pass and passed
        status = "ok" if passed else "FAIL"
        print(f"{label:<48} {got:>3}/{result['max']:<4} {f'{lo}-{hi}':>10}   {status}")
        if not passed:
            print(f"    matched:      {result['concepts_matched']}")
            print(f"    missed:       {result['concepts_missed']}")
            print(f"    disqualified: {result['disqualified']}, words: {result['word_count']}")

    return all_pass


def main():
    with open(GRADING_FILE) as fp:
        rubric = json.load(fp)

    questions = {q["question_id"]: q for q in rubric["questions"]}

    # ── Q1: Why not exactly 1 Hz? ────────────────────────────────────────────
    q1_cases = [
        ("Full credit — all three concepts", (9, 10),
         "The ESP32's delay function isn't perfectly precise; it relies on the RTOS tick. "
         "The CPU also handles background interrupts like USB and WiFi while the blink loop runs. "
         "Each interrupt steals a few microseconds, and over many cycles those errors accumulate into a measurable frequency offset."),
        ("Partial — software imprecision only", (3, 5),
         "The delay function just isn't perfectly precise so the timing drifts a little."),
        ("Partial — CPU busy only", (3, 5),
         "The CPU is doing other things like running WiFi in the background."),
        ("Strong answer, different vocabulary", (7, 10),
         "The loop isn't the only thing running. There's RTOS overhead and ISR work happening between each delay, "
         "which throws off the timing by a tiny bit each pass."),
        ("Disqualified — blames hardware", (0, 0),
         "The hardware is broken or the crystal oscillator is bad."),
        ("Too short — length penalty", (0, 4),
         "delay isn't exact"),
        ("Blank", (0, 0), ""),
    ]

    # ── Q2: Why does the LCD lag? ─────────────────────────────────────────────
    q2_cases = [
        ("Full credit — shared resource + load blocks + lag", (9, 10),
         "The CPU is a shared resource — only one task runs at a time on a single core. "
         "Each loop iteration, the processor spends most of its time running the floating-point load "
         "before it ever gets to analogRead(). The ADC read has to wait in line behind the load task, "
         "so it happens much less frequently and the display lags behind the knob."),
        ("Partial — CPU busy, no mechanism", (4, 6),
         "The load task is running so the CPU is too busy to read the ADC quickly."),
        ("Partial — mentions sharing but not lag", (7, 9),
         "The CPU can only do one thing at a time so the load and ADC share the processor."),
        ("Full credit different wording", (8, 10),
         "Both tasks compete for the same processor. The CPU is occupied running thousands of math "
         "iterations when it should be sampling the potentiometer. That starves the ADC loop and the "
         "display falls behind."),
        ("Too short", (0, 4), "CPU is busy"),
        ("Blank", (0, 0), ""),
    ]

    # ── Q3: What does the sample rate mean? ───────────────────────────────────
    q3_cases = [
        ("Full credit — rate + misses requirement + consequence", (9, 10),
         "The sample rate shows how many times per second the CPU successfully read the ADC — about 42 Hz in my case. "
         "If the requirement were 50 samples per second and the system only manages 42, it misses its deadline: "
         "some sensor readings never happen, so the display operates on stale data. "
         "In a safety-critical system that missed reading could mean a threshold is crossed undetected."),
        ("Partial — rate meaning only", (3, 5),
         "The sample rate tells me how frequently the ADC is being read each second."),
        ("Partial — misses requirement, no consequence", (7, 9),
         "I measured 42 Hz. If the requirement is 50 Hz that's not enough — the system fails to meet it."),
        ("Full credit, concise", (8, 10),
         "My measured 40 Hz means the CPU only read the sensor 40 times per second. "
         "A 50 Hz requirement would not be met — the system would miss readings and produce incorrect output. "
         "In a motor controller this would break the control loop entirely."),
        ("Too short", (0, 4), "The rate is low"),
        ("Blank", (0, 0), ""),
    ]

    # ── Q4: What did DMA do differently? ──────────────────────────────────────
    q4_cases = [
        ("Full credit — autonomous + parallel + rate improved", (9, 10),
         "In Step 3 the CPU polled the ADC itself inside the loop, limited to about 42 Hz by the load task. "
         "In Step 4 the DMA controller samples the ADC autonomously at 10 kHz and fills a buffer without touching the CPU; "
         "the loop just reads what is already there. Because DMA and the load task run in parallel on separate hardware, "
         "the load no longer affects the sample rate — my Step 4 rate jumped to over 400 Hz."),
        ("Partial — autonomous only", (4, 6),
         "DMA handles the ADC sampling automatically so the CPU doesn't have to do it."),
        ("Partial — parallel only, triggers two concepts", (6, 9),
         "DMA runs at the same time as the CPU load so both happen simultaneously."),
        ("Full credit, different wording", (8, 10),
         "The DMA controller works independently — it fills a buffer with ADC readings on its own without interrupting the CPU. "
         "The CPU just picks up the buffer contents. This means the load task and ADC sampling happen in parallel, "
         "which is why my sample rate went from 40 Hz to over 400 Hz with identical hardware."),
        ("Too short", (0, 4), "DMA is faster"),
        ("Blank", (0, 0), ""),
    ]

    # ── Q5: Your partitioning rule ────────────────────────────────────────────
    q5_cases = [
        ("Full credit — measure + requirement + own data", (9, 10),
         "A function should move to hardware only when measurement shows software cannot meet the system requirement — "
         "not just because hardware is faster. In Step 3 I measured 42 Hz with software polling; "
         "if the requirement were 50 Hz, that is a real failure. "
         "Step 4 confirmed DMA fixed it by removing the CPU from the data path, "
         "so the rule is: try software first, measure under realistic load, and only add hardware when the number proves you need it."),
        ("Partial — no own data reference", (6, 8),
         "Start in software and only move to hardware when the software is too slow to meet requirements."),
        ("Partial — mentions data but no rule", (6, 8),
         "I measured 42 Hz in Step 3 and 430 Hz in Step 4. DMA was way faster."),
        ("Wrong rule — always use hardware", (0, 3),
         "Always use hardware acceleration when available because it is always faster than software."),
        ("Full credit, concise", (8, 10),
         "Move to hardware when measurement under realistic load shows software misses its deadline. "
         "My Step 3 sample rate was 40 Hz; Step 4 with DMA was 420 Hz — the same load, but the CPU was no longer in the data path. "
         "The trigger is a missed requirement, not just the existence of a faster hardware option."),
        ("Too short", (0, 4), "Use hardware when slow"),
        ("Blank", (0, 0), ""),
    ]

    all_pass = True
    all_pass &= run_cases(questions["q1_why_not_exact"], q1_cases)
    all_pass &= run_cases(questions["q2_why_lag"], q2_cases)
    all_pass &= run_cases(questions["q3_diagnose"], q3_cases)
    all_pass &= run_cases(questions["q4_accelerator"], q4_cases)
    all_pass &= run_cases(questions["q5_partition"], q5_cases)

    print(f"\n{'═'*80}")
    print(f"Overall: {'ALL CASES PASSED' if all_pass else 'SOME CASES FAILED — review rubric'}")
    print(f"{'═'*80}")


if __name__ == "__main__":
    main()
