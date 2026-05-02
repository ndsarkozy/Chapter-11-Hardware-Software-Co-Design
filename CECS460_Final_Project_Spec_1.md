# CECS 460 — System on a Chip

## Final Project Specification & Grading Rubric

**Chapter Enhancement Capstone for the Interactive Classroom System**

Instructor: Dan Cregg  ·  Spring 2026  ·  Final Project = 30% of course grade

---

## 1. Project Overview

This capstone reframes the final project as a reusable course-improvement effort. Each team will enhance one previously assigned CECS 460 textbook chapter and convert it into a polished, reusable interactive classroom module for future semesters. This assignment asks you to use what you learned in CECS 460 to improve CECS 460 itself.

The original syllabus describes the final project as a capstone challenge in which teams build toward a cohesive SoC-based system, present a working prototype, and submit a final design report. In this version, the 'working prototype' is a next-semester-ready instructional module built for the Interactive Classroom System and aligned to one of the earlier textbook chapters.

> **Why this model works:** The classroom platform was built so new chapters can be added through content files rather than server rewrites, which makes chapter enhancement a realistic, high-value capstone target.

**Every team must:**

- Enhance a specific chapter for future classroom use rather than creating a brand-new standalone product.
- Demonstrate CECS 460 skills: technical accuracy, design tradeoffs, verification, communication, and system integration thinking.
- Deliver working ESP32 firmware alongside the lesson content, hardware integration is required, not optional.
- Design the lab activity so students modify the provided firmware to complete it, with a server-side pass indication confirming successful completion.
- Produce a final deliverable that is usable next semester with minimal instructor cleanup.

---

## 2. Team Structure & Chapter Assignment

Teams may have up to two students. With 23 students in the class, the expected structure is 11–12 teams. The instructor will assign chapters to balance coverage across the book and avoid duplication.

**Default model:**

- One team per chapter for Chapters 1–12.
- If the class settles at 11 teams, the instructor will either combine Chapters 1–2 into a Foundations team, or reserve Chapter 1 as instructor-owned material and assign Chapters 2–12 to student teams.

Students may be asked for chapter preferences, but final assignment authority remains with the instructor.

**Contribution statement (required):**

- Each team must submit a contribution statement identifying who handled content design, implementation, testing, documentation, and presentation tasks. This is graded as part of Section 8.

### Chapter Assignment — Default 12-Team Model

| Team    | Chapter    | Chapter Title                                                              |
| ------- | ---------- | -------------------------------------------------------------------------- |
| Team 1  | Chapter 1  | Introduction to SoC Concepts                                               |
| Team 2  | Chapter 2  | History of Digital Design and Wafer Fabrication                            |
| Team 3  | Chapter 3  | CPU Architectures and Core Comparisons                                     |
| Team 4  | Chapter 4  | Interrupt Structures, Stacks and Execution Context                         |
| Team 5  | Chapter 5  | Memory Types and Hierarchies                                               |
| Team 6  | Chapter 6  | Communication Peripherals and External Bus Types                           |
| Team 7  | Chapter 7  | Bus Architectures and Interconnects                                        |
| Team 8  | Chapter 8  | Power Management: Power-On Reset, Brown-Out Detection and Regulation       |
| Team 9  | Chapter 9  | Temperature Considerations and Sensing                                     |
| Team 10 | Chapter 10 | Clocks: System, Internal, External, PLL, RTC, Timers and Watchdog          |
| Team 11 | Chapter 11 | Hardware/Software Co-Design and Design Flow                                |
| Team 12 | Chapter 12 | Verification, Testing and Debugging                                        |

---

## 3. Required Deliverables

Every team must submit the following complete package. All items are required, missing items will reduce your score in the relevant grading section.

**Interactive Chapter Lesson Package**

`lesson.json` (step flow and push-question content), `grading.json` (assessment logic and answer keys), and any needed chapter assets or reference files. This is the core deployment artifact for the classroom system.

**ESP32 Firmware Source Code**

A complete, buildable ESP32 firmware project (ESP-IDF or PlatformIO) that students will flash and modify during the lab. Must include a README with build and flash instructions. The firmware must communicate with the classroom server to report lab pass/fail status.

**Student Lab Activity with Firmware Tasks**

The lab must require students to make specific, meaningful changes to the provided firmware to complete it. The activity must clearly state what to modify, what constitutes a correct result, and how the server pass indication is triggered.

**Instructor Guide (1–2 pages)**

Explain what was changed, why it is better, hardware setup requirements (ESP32 wiring, flash procedure, server connection), and how an instructor deploys it next semester with no prior knowledge of your implementation.

**Final Report (3–5 pages PDF)**

Summarize the chapter, the design decisions you made, the files you created or modified, your testing process, and your recommendations for future improvement.

**Live Demo at Final Expo**

Demonstrate the chapter running in the classroom system and the ESP32 lab live, including at least one student-style firmware modification and the resulting server pass indication. Both team members must participate.

**Recorded Demonstration Video (5–10 min)**

Walkthrough covering the module from both a student and instructor perspective, including flashing the firmware, completing the lab modification, and seeing the server pass confirmation.

**Contribution Statement**

Clearly identify each member's work across all project phases: content design, firmware development, server integration, testing, documentation, and presentation.

> ESP32 firmware and the server pass indication are required for every team, not a stretch goal. The chapter topic determines what the firmware does, but the lab-completion handshake with the server is mandatory for every submission.

---

## 4. Minimum Technical Requirements

To keep projects consistent and deployable, every module must include all of the following:

**Lesson content layer:**

- At least 5 instructional steps in the lesson flow.
- At least 2 interactive question moments embedded in the lesson or push-question flow.
- At least 2 short-answer prompts in `grading.json`, each with a complete answer key or rubric.
- At least 1 instructor-facing support asset (diagram, timing figure, reference code, or deployment note).

**ESP32 firmware layer (required):**

- A buildable ESP32 firmware project that students flash at the start of the lab activity.
- Students must make at least one meaningful firmware modification to complete the lab (e.g., change a threshold, implement a missing function, configure a peripheral, add an output condition).
- The firmware must report lab completion status to the classroom server. A visible pass indication in the server dashboard is required for a student to receive lab credit.
- Build and flash instructions must be included in the README so any student can replicate the setup from scratch.

**Integration:**

- The server pass indication must be triggered by the ESP32 firmware, not by manual instructor entry.
- Evidence of end-to-end testing: document that the firmware builds, flashes, runs on an ESP32, and the server records a pass correctly.

---

## 5. Platform Expectations & Constraints

The Interactive Classroom System separates content from its engine. Your classroom content layer and your ESP32 firmware must both integrate cleanly without breaking existing functionality.

**Classroom content layer:**

- Prefer content-layer extensions over Flask or MQTT engine rewrites.
- Do not introduce external cloud dependencies or internet-required workflows in the lesson content.
- Do not add new Python dependencies unless explicitly approved by the instructor.
- Preserve the drop-in model: adding your chapter should not require the engine to be redesigned.
- Keep lesson identifiers, filenames, and references consistent so the module deploys cleanly.

**ESP32 firmware and server integration:**

- The firmware must use the existing server communication protocol (MQTT or HTTP as appropriate) to post the lab pass status.
- Do not hardcode IP addresses or credentials that would break when deployed on a different machine. Use configuration files or build-time constants.
- The server-side pass entry must appear in the student-facing dashboard without requiring instructor intervention.
- Firmware must not interfere with other teams' lab sessions or the shared server state.

---

## 6. Recommended Workflow

| Phase     | Timing               | What to Complete                                                                                                                                                                                                |
| --------- | -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 1   | Week 13              | Read the assigned chapter closely, identify weaknesses, propose improvements, and sketch the lesson flow. Submit a one-paragraph scope statement to the instructor.                                             |
| Phase 2   | Week 13–14           | Build `lesson.json`, `grading.json`, the revised activity, and supporting assets. Test the module in the classroom system with a classmate playing student.                                                     |
| Phase 3   | Week 14              | Refine wording, grading logic, visuals, and classroom usability. Record the demo video. Prepare the instructor guide and final report.                                                                          |
| Phase 4   | Week 15 / Final Exam | Deliver the live expo demo. Submit the full package (ZIP, report, video) to LMS before the deadline. Submit peer review ballot within 24 hours.                                                                 |

---

## 7. Grading Summary

The project is assessed across nine sections totaling 100 points. Partial credit is awarded within each criterion at the instructor's discretion. Criteria are independent, strong performance in one section does not compensate for a zero in another.

### Point Summary

| Section                                | Deliverable / Focus                              | Max Pts |
| -------------------------------------- | ------------------------------------------------ | :-----: |
| 1 — Content & Technical Accuracy       | Lesson quality, chapter alignment                |   15    |
| 2 — Interactive Lesson Design          | Step flow, classroom usability                   |   15    |
| 3 — Assessment & Grading Design        | Questions, rubrics, grading logic                |   12    |
| 4 — Lab / Activity Enhancement         | Revised or new learning activity                 |   12    |
| 5 — Platform Implementation            | lesson.json, grading.json, firmware ZIP          |   12    |
| 6 — Testing & Verification             | Evidence of testing, debugging                   |    8    |
| 7 — Demo & Presentation Quality        | Live expo, recorded video, clarity               |   10    |
| 8 — Documentation & Contribution       | Report, instructor guide, team statement         |    6    |
| 9 — Peer Review ✦                      | Fun · Engagement · Creativity                    |   10    |
| **TOTAL** (+ up to 13 bonus pts)       |                                                  | **100** |

### Grading Scale

| Score Range | Grade | Meaning                                         |
| :---------: | :---: | ----------------------------------------------- |
| 90–100%     | A     | Exceeds expectations in all major areas         |
| 80–89%      | B     | Meets expectations; minor gaps in one area      |
| 70–79%      | C     | Partially meets expectations; notable gaps      |
| 60–69%      | D     | Several significant deficiencies                |
| 0–59%       | F     | Does not meet minimum requirements              |

---

## 8. Detailed Grading Rubric

### 1 — Content & Technical Accuracy ( / 15 pts)

| Criterion                  | Expectations, what earns full credit                                                                                                                                                  | Points |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :----: |
| Chapter Fidelity           | Content is accurate, up-to-date, and free from factual errors. All claims are traceable to the textbook chapter or credible supplementary sources.                                    |   6    |
| Depth & Coverage           | Chapter concepts are treated with appropriate rigor for the CECS 460 level. No major concepts from the chapter are omitted without justification.                                     |   5    |
| Instructional Alignment    | Lesson objectives, questions, and activities are clearly tied to the assigned chapter. At least one CLO2 or CLO3 concept (system-level design, HW/SW interaction) is addressed.       |   4    |

> ⚑ All technical content must be verified against the textbook chapter. Errors introduced during enhancement that did not exist in the original will reduce this score.

### 2 — Interactive Lesson Design ( / 15 pts)

| Criterion             | Expectations                                                                                                                                                                | Points |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :----: |
| Step Flow             | Lesson includes at least 5 instructional steps in a clear, logical sequence. Pacing is appropriate for a single class session; no abrupt jumps.                             |   5    |
| Engagement            | At least 2 interactive question moments are embedded in the lesson or push-question flow. The lesson would hold a student's attention if run live in class.                 |   5    |
| Classroom Readiness   | Module loads and renders correctly in the Interactive Classroom System with no server rewrites. The experience is browser-first; no internet-required or cloud-dependent.   |   5    |

> ⚑ The instructor must be able to deploy the `lesson.json` in the classroom system without modification. Modules that require engine rewrites will not receive full credit here.

### 3 — Assessment & Grading Design ( / 12 pts)

| Criterion         | Expectations                                                                                                                                                                                                          | Points |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :----: |
| Question Quality  | At least 2 short-answer prompts are included in `grading.json`. Questions are clear, unambiguous, and technically answerable without guessing. Each question specifies an expected answer or rubric for grading.      |   6    |
| Grading Logic     | `grading.json` logic is complete, consistent, and correctly structured for the platform. Answer keys or rubrics are fair, specific, and appropriate for a CECS 460 student.                                           |   4    |
| Reusability       | Questions and rubrics can be reused by the next semester's instructor without modification. Grading criteria do not depend on unstated assumptions or team-specific context.                                           |   2    |

### 4 — Lab / Activity Enhancement ( / 12 pts)

| Criterion                    | Expectations                                                                                                                                                                                                              | Points |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :----: |
| Firmware Modification Task   | Lab clearly specifies what firmware change(s) the student must make. The required change is non-trivial: it tests understanding of the chapter concept, not just copy-paste. Starter firmware compiles and runs correctly before any student modifications. | 5 |
| Server Pass Indication       | Completing the firmware task triggers a visible pass status in the classroom server dashboard. The pass condition is unambiguous: a student knows definitively whether they have passed or not. The mechanism is robust, false positives are not possible. | 4 |
| Improvement & Practicality   | Lab activity is demonstrably better than the original chapter lab. Activity fits within a reasonable lab session; setup instructions are clear enough for a student to follow without instructor help.                    |   3    |

> ⚑ A lab where the server pass is triggered manually by the instructor, or where a student can pass without making the required firmware change, will not receive full credit in this section.

### 5 — Platform Implementation & Reusability ( / 12 pts)

| Criterion             | Expectations                                                                                                                                                                                                                                                          | Points |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :----: |
| Package Completeness  | ZIP contains: `lesson.json`, `grading.json`, ESP32 firmware project, revised activity file, all support assets, and the instructor guide. No broken references, missing assets, placeholder files, or hardcoded paths. Firmware README includes: build tool version, flash command, wiring diagram or pin table, and server connection setup. | 5 |
| Drop-In Compliance    | Lesson content layer does not require Flask, MQTT engine, or Python dependency changes. Filenames, lesson IDs, and references follow the platform's naming conventions. Firmware uses configuration constants (not hardcoded IPs/credentials) so it deploys cleanly on the lab machine. | 4 |
| Asset & Code Quality  | Firmware source is organized and commented well enough for a future TA to understand and modify it. At least 1 instructor-facing support asset is included (diagram, timing figure, reference code, deployment note). All linked files render or load correctly when deployed. | 3 |

> ⚑ The ZIP is the single source of truth for deployment. If the instructor cannot build the firmware, flash it to an ESP32, and drop the lesson into the system cleanly next semester, this section is affected regardless of content quality.

### 6 — Testing & Verification ( / 8 pts)

| Criterion                              | Expectations                                                                                                                                                                                                                                                  | Points |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :----: |
| Firmware & Server Pass Testing         | Team documents a complete end-to-end test: firmware built, flashed to an ESP32, lab task completed, and server pass recorded. At least one failure mode was encountered and resolved during testing. Report or instructor guide includes a screenshot or log confirming the server pass indication. | 5 |
| Content & Assessment Verification      | All `lesson.json` steps were exercised in the classroom system with no broken flows. All `grading.json` prompts were test-answered and validated against expected responses. Grading logic was confirmed against at least two sample student responses (one correct, one incorrect). | 3 |

### 7 — Demo & Presentation Quality ( / 10 pts)

| Criterion        | Expectations                                                                                                                                                                  | Points |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :----: |
| Live Expo Demo   | Chapter runs live in the classroom system with no crashes or broken flows. Team clearly walks through the lesson, assessment layer, and key design decisions. Both team members contribute to the demonstration. | 6 |
| Recorded Video   | Short walkthrough video (5–10 min) covers the module from a student and instructor perspective. Video is clear, audible, and does not require the live system to understand. |   4    |

> ⚑ Demo must be performed in person during the scheduled final expo slot.

### 8 — Documentation & Teamwork ( / 6 pts)

| Criterion                          | Expectations                                                                                                                                                                                                                                       | Points |
| ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :----: |
| Final Report                       | 3–5 page PDF covering: chapter summary, design decisions, system files created, testing process, and recommendations for future semesters. Writing is clear and professional; no placeholder sections.                                              |   3    |
| Instructor Guide & Contribution    | Instructor guide (1–2 pp) explains what changed, why it is better, and how to deploy it next semester. Contribution statement clearly identifies each member's role: content design, implementation, testing, documentation, presentation.         |   3    |

### 9 — Peer Review ✦ Fun · Engagement · Creativity ( / 10 pts)

| Criterion    | Expectations                                                                                                                                                                                                       | Points |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | :----: |
| Fun          | Did this module make the expo session genuinely enjoyable? Score 1 (dry, hard to engage) → 4 (memorable, you'd recommend it to next semester's class). Consider: humor, interactivity, novel framing, real-world relevance. | __ / 4 |
| Engagement   | How well did the team communicate their chapter and what they improved? Score 1 (unprepared, hard to follow) → 3 (captivating, you understood everything and wanted to know more). Consider: clarity, confidence, audience interaction, quality of explanation. | __ / 3 |
| Creativity   | How inventive was the enhancement or its presentation? Score 1 (minimal changes, no novel elements) → 3 (genuinely inventive approach to the chapter). Consider: original activity design, unexpected use of platform features, clever pedagogical choices. | __ / 3 |

> ⚑ Scores are averaged across all peer reviewers. You do not rate your own team. All ratings are anonymous. Outlier scores inconsistent with the class average may be adjusted by the instructor.

**TOTAL: 100 pts**

### Bonus Opportunities (up to +11 pts total)

| Bonus Item                       | How to Earn It                                                                                                                                                  | Points    |
| -------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | :-------: |
| Exceptional Visual Design        | Module includes original diagrams, animations, or interactive UI elements that are markedly clearer or more engaging than the existing textbook figures.        | +3        |
| Advanced Server Integration      | Firmware reports richer telemetry beyond a simple pass/fail, e.g., timing data, sensor readings, or per-step progress, and the server dashboard displays it meaningfully. | +3 |
| Outstanding Module Quality       | Instructor/panel award for a module that goes well beyond the baseline in depth, polish, classroom usability, and firmware sophistication.                       | +up to 5  |

---

## 9. Peer Review — How It Works

After all expo demos are complete, every student independently rates each team (except their own) using the Microsoft Forms link provided in the course LMS. Scores are averaged across all raters. The instructor will drop any obvious outlier scores that do not reflect genuine evaluation.

**Process:**

- Ballots are submitted anonymously through the Microsoft Forms link provided. The window closes 24 hours after the final expo session.
- The average peer score (out of 10) is added directly to the project total.
- Teams that miss the 24-hour window receive a zero for their own peer review ballot submission.

**What each criterion asks:**

- **Fun**, would you recommend this module to a friend taking CECS 460 next semester?
- **Engagement**, did the team pull you into the chapter? Did you actually want to learn more?
- **Creativity**, was there something genuinely inventive about the enhancement or the way it was presented?

### Peer Review Ballot — Rating Scale

| Criterion    | 1 — Weak | 2 — Fair | 3 — Good | 4 — Excellent          |
| ------------ | :------: | :------: | :------: | :--------------------: |
| Fun          | 1        | 2        | 3        | **4 pts — memorable**  |
| Engagement   | 1        | 2        | 3        | **3 pts — captivating**|
| Creativity   | 1        | 2        | 3        | **3 pts — inventive**  |

---

## 10. Academic Integrity & Policies

### AI Tools

You may use AI-assisted tools (GitHub Copilot, ChatGPT, Claude, etc.) as productivity aids. However, you are responsible for every line of content and every claim in your report. If asked during Q&A, you must be able to explain any part of your module. Submitting AI-generated content as a substitute for genuine instructional design is a violation of the CSULB Academic Integrity Policy.

### Teamwork

Both team members must participate in the live demo. If the instructor cannot verify a member's contribution during Q&A, that individual's demo score may be adjusted independently. The contribution statement must be accurate, misrepresenting participation is an academic integrity violation.

### Late Submissions

No late submissions are accepted. This is an end-of-semester project and the timeline allows no flexibility. Peer review ballots submitted after the 24-hour post-expo window receive a zero for that reviewer.

### Open-Source Content & Attribution

You may use existing textbook content, diagrams, and open-source materials as a starting point, but your enhancement must add original instructional value, not just reformat existing content into JSON. All non-original material must be cited in the instructor guide and report.

### Project Originality

Stronger projects make thoughtful instructional decisions, not just technical conversions. The project should improve the course in a meaningful way. Teams should aim to leave behind something the next class can actually use.

---

## 11. Submission Checklist

Use this before your final submission. Every item is required for full credit.

- [ ] ZIP contains: `lesson.json`, `grading.json`, ESP32 firmware project folder, activity file, all assets, and instructor guide
- [ ] ESP32 firmware builds without errors using the documented toolchain and version
- [ ] Firmware README: build command, flash command, pin/wiring table, server connection config
- [ ] End-to-end test confirmed: firmware flashed → lab task completed → server pass recorded in dashboard
- [ ] Screenshot or log of successful server pass included in the report or instructor guide
- [ ] Student lab activity clearly states what firmware change is required and what a correct result looks like
- [ ] Instructor guide covers hardware setup and step-by-step deployment for next semester
- [ ] Final report (3–5 pages, PDF) covers design decisions, firmware rationale, testing, and recommendations
- [ ] Recorded demo video (5–10 min) includes firmware flash and live server pass demonstration
- [ ] All `lesson.json` steps tested and render correctly in the classroom system
- [ ] All `grading.json` prompts validated against correct and incorrect sample responses
- [ ] Slides or presentation outline for the live expo
- [ ] Contribution statement identifies each member's role across all phases
- [ ] Demo ESP32 and server tested the day before the expo slot
- [ ] Both team members prepared to answer questions about firmware, server integration, and content
- [ ] Peer review ballot submitted within 24 hours of the final expo session

---

*Questions? Post to the course discussion board or contact the instructor well before the deadline. End-of-semester timing means issues cannot be resolved after the fact.*

California State University, Long Beach  |  Department of Computer Engineering & Computer Science  |  Spring 2026
