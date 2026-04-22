# Contributing

This module is designed to evolve. Future students, TAs, and instructors are welcome to improve steps, add extension activities, or fix bugs. Here's how.

## Before you start

Read [`docs/instructor_guide.md`](docs/instructor_guide.md) so you understand what the module is trying to teach and why each step is shaped the way it is. Pedagogical changes (reordering steps, cutting concepts) should be discussed with the instructor before implementation — the "overwhelm → rescue" arc matters more than any individual detail.

## Quick fixes (typos, wiring clarifications, better diagrams)

1. Fork the repo
2. Make your change on a branch named `fix/short-description`
3. Open a PR against `main` with a one-line description

## Adding or modifying graded questions

If you change `grading.json`:

1. Add a test case to `tests/test_grading.py` that exercises your change
2. Run `python3 tests/test_grading.py` and confirm all cases pass
3. Include the test output in your PR description

## Adding a new step or extension activity

1. Open an issue first describing what you want to add and why
2. Once agreed, implement the step following the pattern of Step 1:
   - Content block(s) in `lesson.json`
   - Grading rubric in `grading.json` (if it has a graded question)
   - Starter code in `hardware/starter_code/stepN_*/`
   - Paper handout in `lab/stepN_handout.md`
   - Instructor notes in `lesson_package/instructor_notes/stepN.md`
3. Add test cases for any new grading rubric

## Style

- Markdown: sentence case in headings, 80-100 char line wrap where practical
- JSON: 2-space indent, keys in the order shown in existing files
- Arduino sketches: follow the comment style in `step1_baseline.ino`

## Reporting bugs

Open a GitHub issue using the bug template. Include:

- Which step you were on
- What you expected to happen
- What actually happened
- Your classroom system version (if relevant)
- Scope capture or screenshot if applicable
