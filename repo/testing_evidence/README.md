# Testing Evidence

This folder holds evidence that the module works end-to-end. Expected contents once the hardware run is complete:

- `step1_serial_monitor.png` — Arduino IDE Serial Monitor showing the 1 Hz blink period/frequency printout (typical: `Period: 1002 ms | Frequency: 0.9980 Hz`)
- `step2_serial_monitor.png` — Serial Monitor showing the software-polled sample rate under load (typical: `[SW] Sample rate: 42.3 Hz`)
- `step2_lcd_lag.mp4` (or `.gif`) — short clip of the LCD visibly lagging behind the potentiometer
- `step4_serial_monitor.png` — Serial Monitor showing the DMA sample rate with the same CPU load running (typical: `[DMA] Sample rate: 428.6 Hz`) and the `[MQTT] Lab PASS sent!` line
- `step4_dashboard_pass.png` — instructor dashboard at `/cecs460/instructor` showing the slot scored as a pass for `q4_lab_pass`
- `grading_tests_passing.txt` — stdout from `python3 tests/test_grading.py` (35 cases, all passing)
- `classroom_walkthrough/` — screenshots of the lesson rendering in the classroom system (one per step)

The dashboard pass screenshot (`step4_dashboard_pass.png`) is required for full credit on Section 6 of the rubric ("Report or instructor guide includes a screenshot or log confirming the server pass indication").

None of the hardware screenshots are in the repo yet — they get captured during the final hardware run.
