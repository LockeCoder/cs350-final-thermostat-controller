# cs350-final-thermostat-controller
## Final Project
This repository contains my CS-350 Thermostat Controller final project artifact. The system is a Raspberry Pi–based thermostat prototype that uses an AHT20 temperature/humidity sensor (I2C), a 16x2 LCD, three buttons (mode/up/down), two LEDs (heating/cooling), and a UART output for periodic telemetry.
## Demo Video
https://youtu.be/uvZeKR94jVU
## Project Summary and Problem Solved.
This project implements a thermostat-like management loop that reads temperature from an AHT20 sensor, displays device information on a 16x2 LCD, permits the person to exchange modes and setpoints using buttons, and shows heating/cooling using LEDs. The machine also sends a standing string over the UART every 30 seconds.
## System Design 
The software program makes use of three modes/states: OFF, HEAT, and COOL, with transitions managed via the mode button. The country-device behavior is documented inside the diagram blanketed in this repo.
## LED behavior requirements implemented
HEAT:

If temp < setpoint → red LED fades (actively heating)

If temp >= setpoint → red LED solid (heating on but satisfied)

COOL:

If temp > setpoint → blue LED fades (actively cooling)

If temp <= setpoint → blue LED solid (cooling on but satisfied)

OFF: both LEDs off
## What I Did Particularly Well
I built the system around clear, testable requirements. I implemented them directly in code with explicit pin mappings, state logic, and timed behaviors (LCD updates, UART output interval, and PWM-based LED fading). The implementation includes clean hardware mapping comments, structured helper functions (sensor init, LCD init, GPIO/button setup, LED update logic, UART output), and safe cleanup on exit.
## Where I Could Improve
I can improve how I validate and demonstrate every required behavior during recordings. In earlier feedback, I demonstrated some LED states but did not capture every “running vs. satisfied” indicator consistently in the demo. In the future, I would use a short pre-record checklist that forces each condition (heat running, heat satisfied, cool running, cool satisfied, off) and verifies it visually before recording.
## Tools/Resources Added to My Support Network

•	Lab guides/rubrics as the “source of truth” for requirements

•	GPIO and I2C validation steps (pin mapping verification, device detection)

•	Debug output + repeatable test sequences for state transitions and UI/LED behavior
## Transferable Skills

•	Embedded-style integration across GPIO, I2C, LCD, and UART

•	State-machine design for predictable control behavior

•	PWM-based LED signaling for “active vs. satisfied” system states

•	Structured debugging and incremental validation during integration
## Maintainability, Readability, and Adaptability
Maintenance was supported by separating responsibilities (sensor readings, LED updates, LCD updates, UART outputs and button callbacks) into smaller tasks and driving behavior through a small set of states. This makes it easy to extend the project (new states, different sensors, alternative display formats, different telemetry intervals) without rewriting the entire program.
## Repository Contents

•	Thermostat.py (main implementation)

•	State Machine.drawio.pdf (state-machine diagram)

•	Thermostat Lab.docx (project write-up)

