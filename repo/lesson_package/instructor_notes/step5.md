# Instructor Notes — Step 5: The Partition Decision

## What this step demonstrates
Synthesis: students formulate their own HW/SW partitioning rule using the data they collected in Steps 2–4. No new hardware or firmware — this is a reflection and generalization step.

## Expected student output
A 2–3 sentence rule that includes: (1) measure under realistic load first, (2) trigger is software failing to meet a requirement, (3) reference to their own Step 3/4 numbers. The rule should NOT be "always use hardware when available" — that misses the start-in-software principle.

## Discussion prompt
Ask the class: "If your Step 3 rate was 80 Hz and the requirement was only 50 Hz, would you add DMA?" Most students correctly say no. Follow up: "What if the requirement were 100 Hz?" Now the answer is yes. The point: the decision is always requirement-driven, never just capability-driven.

## Common wrong rules students write
- "Use hardware when software is too slow" — partial credit, no measurement required
- "Always use hardware for ADC" — wrong, ignores the start-in-software principle
- "Add DMA whenever possible" — penalize, this is the anti-pattern the lesson was built to counter

## Graded question
Q5 (`q5_partition`): write their own partitioning decision rule and reference their measured data. Full credit requires: measure first, trigger is missed requirement, reference to own Step 3/4 rates. The question is intentionally open-ended — there is no single right answer. Award credit for any answer that shows the student internalized the measurement-first discipline.

## Timing
This step takes 10–15 minutes. Some students will write a sentence and be done; prompt them to defend their rule with their own numbers.
