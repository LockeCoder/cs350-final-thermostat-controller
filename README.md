# CS350-final-thermostat-controller
Thermostat controller final project artifact (CS-350).

This repository includes the CS-350 final project artifact that demonstrates embedded systems fundamentals: GPIO input/output, I2C sensor integration, LCD output, UART telemetry, and state-driven program design.

## Artifact 1 (Primary): Thermostat Controller Final Project
**What it is:** A thermostat-style controller that reads temperature/humidity data from an AHT20 sensor over I2C, displays system status on a 16x2 LCD, and uses buttons (mode/up/down) to change operating mode and adjust the set point. LEDs indicate heating/cooling behavior based on the current mode and temperature conditions. UART output provides periodic telemetry.

## Demo video: https://youtu.be/uvZeKR94jVU

## System Design (State Machine)
The software uses three modes/states: **OFF**, **HEAT**, and **COOL**, with transitions controlled by the mode button. The state-machine design is documented in the diagram included in this repository.

### LED behavior requirements implemented
**HEAT:**
- If `temp < setpoint` → red LED fades (actively heating)
- If `temp >= setpoint` → red LED solid (heating on but satisfied)

**COOL:**
- If `temp > setpoint` → blue LED fades (actively cooling)
- If `temp <= setpoint` → blue LED solid (cooling on but satisfied)

**OFF:**
- Both LEDs off

---

# Module Eight Journal Reflection

## Summarize the project and what problem it was solving
This artifact demonstrates the construction of an embedded-style control system on a Raspberry Pi that integrates multiple hardware components: LCD output, button input, LED status indicators, and I2C sensor communication. The problem being solved is creating a reliable, testable thermostat-style application that reads real-world data, presents it clearly to the user, and responds to user input with predictable state-driven behavior while also producing periodic telemetry.

## What did you do particularly well?
I performed particularly well at implementing clear requirements and validating behavior through structured integration. I built the system around explicit pin mappings, state logic, timed behaviors (LCD refresh and UART output interval), and PWM-based LED behavior to represent “active vs. satisfied” states. I also used runtime output and repeatable test sequences to verify button presses, state transitions, and sensor-driven behavior.

## Where could you improve?
I can improve how I validate and demonstrate every required behavior under time pressure, especially during recordings. In the future, I will use a short pre-record checklist that forces each condition (heat running, heat satisfied, cool running, cool satisfied, off) and verifies it visually before recording.

## What tools and/or resources are you adding to your support network?
I am adding a more formal verification workflow: wiring validation checklists, consistent I2C verification steps (device detection and address confirmation), and repeatable test scripts/checklists for triggering each state transition, LED condition, and LCD behavior prior to submission. I will continue using lab guides/rubrics as requirement references and use targeted debug output to confirm runtime behavior.

## What skills from this project will be particularly transferable to other projects and/or coursework?

### Transferable skills include:
- Hardware/software integration (GPIO input/output + I2C sensor communication + LCD output + UART telemetry)
- Debugging discipline (baseline → isolate → test one change → verify)
- State-machine design for predictable control behavior
- PWM-based LED signaling for “active vs. satisfied” system states
- Validation practices using observable outputs (LCD/LED) and repeatable test sequences

These apply directly to future embedded projects and any system that requires reliable integration and troubleshooting.

## How did you make this project maintainable, readable, and adaptable?
I kept the project maintainable by separating responsibilities (sensor reads, LED updates, LCD updates, UART output, and button handling) and driving behavior through a small set of states. This structure makes it easier to extend the project (new states, different sensors, alternate display formats, different telemetry intervals) without rewriting large sections of code.

## Repository Contents
- `Thermostat.py` (main implementation)
- `State Machine.drawio.pdf` (state-machine diagram)
- `Thermostat Lab.docx` (project write-up)
