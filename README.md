# CS-350 Final Project: Thermostat Controller

This repository contains my CS-350 Thermostat Controller final project artifact. The system is a Raspberry Pi–based thermostat prototype that uses an AHT20 temperature/humidity sensor (I2C), a 16x2 LCD, three buttons (mode/up/down), two LEDs (heating/cooling), and UART output for periodic telemetry. :contentReference[oaicite:3]{index=3}

## Demo Video
https://youtu.be/uvZeKR94jVU

---

## Project Summary and Problem Solved
This project implements a thermostat-style control loop that reads temperature from the AHT20 sensor, displays system information on a 16x2 LCD, allows the user to change mode and setpoint using buttons, and indicates heating/cooling behavior using LEDs. The system also transmits a comma-delimited status string over UART every 30 seconds (state, temperature, setpoint). :contentReference[oaicite:4]{index=4}

---

## System Design (State Machine)
The software uses three modes/states: OFF, HEAT, and COOL, with transitions controlled by the mode button. The state machine is included in this repository. :contentReference[oaicite:5]{index=5}

### LED Behavior Requirements Implemented
HEAT:
- If temp < setpoint: red LED fades (actively heating)
- If temp ≥ setpoint: red LED solid (heating on but satisfied)

COOL:
- If temp > setpoint: blue LED fades (actively cooling)
- If temp ≤ setpoint: blue LED solid (cooling on but satisfied)

OFF:
- Both LEDs off :contentReference[oaicite:6]{index=6} :contentReference[oaicite:7]{index=7}

---

# Module Eight Journal Reflection

## What did you do particularly well?
I performed particularly well in systematic integration and troubleshooting. I verified requirements against the lab guide, used explicit pin mappings and a state-driven design, and validated behavior using observable outputs (LCD/LEDs) and timed UART telemetry. The implementation is structured with clear helper functions for sensor initialization, LCD updates, GPIO/button setup, LED update logic, UART output, and cleanup on exit. :contentReference[oaicite:8]{index=8}

## Where could you improve?
I can improve validation coverage during demonstrations by using a pre-record checklist that forces each required condition (HEAT running, HEAT satisfied, COOL running, COOL satisfied, OFF) and verifies the correct LED behavior before recording.

## What tools and/or resources are you adding to your support network?
- Lab guides/rubrics as the source of truth for requirements
- GPIO/I2C verification steps (pin mapping checks and I2C device detection)
- Repeatable test sequences for state transitions, LED behavior, LCD output, and UART telemetry

## What skills from this project will be particularly transferable to other projects and/or coursework?
- Embedded-style integration across GPIO, I2C, LCD, and UART :contentReference[oaicite:9]{index=9}
- State-machine design for predictable control behavior :contentReference[oaicite:10]{index=10}
- PWM-based LED signaling for “active vs satisfied” system states :contentReference[oaicite:11]{index=11}
- Structured debugging and incremental validation during integration

## How did you make this project maintainable, readable, and adaptable?
Maintainability was supported by separating responsibilities (sensor reads, LED updates, LCD updates, UART output, and button handling) into small functions and driving behavior through a small set of states. This makes it straightforward to extend the project (new states, different sensors, alternate display formats, different telemetry intervals) without rewriting large sections of code. :contentReference[oaicite:12]{index=12}

---

## Repository Contents
- Thermostat.py (main implementation) :contentReference[oaicite:13]{index=13}
- State Machine.drawio.pdf (state-machine diagram) :contentReference[oaicite:14]{index=14}
- Thermostat Lab.docx (project write-up) :contentReference[oaicite:15]{index=15}
