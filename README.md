# CS-350 Final Thermostat Controller

Thermostat controller final project artifact for CS-350.

This repository contains my CS-350 final project artifact demonstrating embedded systems fundamentals, including GPIO input/output, I2C sensor integration, LCD output, UART telemetry, PWM LED behavior, and state-driven program design.

## Project Scope

This repository contains the full CS-350 thermostat controller artifact.

The project implements a thermostat-style controller that reads temperature and humidity data from an AHT20 sensor over I2C, displays system status on a 16x2 LCD, and uses physical GPIO buttons to change the operating mode and adjust the temperature set point.

The controller uses:

- A mode button to cycle between OFF, HEAT, and COOL
- Up and down buttons to adjust the set point
- Red and blue LEDs to indicate heating and cooling behavior
- PWM LED fading to represent active heating/cooling states
- UART output to provide periodic telemetry

## Demo Video

[Demo video](https://youtu.be/uvZeKR94jVU)

## System Design: State Machine

The software uses three modes/states:

- OFF
- HEAT
- COOL

Transitions are controlled by the mode button. The state-machine design is documented in the included `StateMachine.drawio.pdf` file.

## LED Behavior Requirements Implemented

### HEAT

- If temperature is below the set point, the red LED fades to indicate active heating.
- If temperature is at or above the set point, the red LED remains solid to indicate heating is on but satisfied.

### COOL

- If temperature is above the set point, the blue LED fades to indicate active cooling.
- If temperature is at or below the set point, the blue LED remains solid to indicate cooling is on but satisfied.

### OFF

- Both LEDs remain off.

## Hardware Used

- Raspberry Pi 4B
- AHT20 temperature/humidity sensor
- 16x2 LCD display
- GPIO push buttons
- Red LED for heating status
- Blue LED for cooling status
- Breadboard and jumper wires

## Technologies Used

- Python 3
- Raspberry Pi GPIO
- I2C communication
- UART telemetry
- PWM output
- LCD display control
- State-machine design

## Repository Contents

- `Thermostat.py`: Main thermostat controller implementation
- `StateMachine.drawio.pdf`: State-machine diagram
- `Thermostat Lab.docx`: Project write-up
- `README.md`: Repository documentation
- `LICENSE`: MIT license
- `.gitignore`: Git ignore configuration

## How It Works

1. The Raspberry Pi initializes the AHT20 sensor, LCD, GPIO buttons, LEDs, and UART connection.
2. The AHT20 sensor provides temperature and humidity data over I2C.
3. The LCD displays the current date/time, temperature, thermostat mode, and set point.
4. The mode button cycles the system through OFF, HEAT, and COOL.
5. The up and down buttons adjust the set point.
6. The red and blue LEDs indicate heating or cooling behavior.
7. UART output sends periodic comma-delimited telemetry.

## Skills Demonstrated

- Python programming for hardware-integrated systems
- Embedded systems fundamentals
- Raspberry Pi hardware integration
- GPIO input/output handling
- I2C sensor communication
- UART telemetry output
- PWM LED signaling
- LCD display integration
- State-machine-based program design
- Hardware/software troubleshooting
- Requirements-based validation
- Technical documentation

## Module Eight Journal Reflection

### Summarize the Project and What Problem It Was Solving

This artifact demonstrates the construction of an embedded-style control system on a Raspberry Pi that integrates multiple hardware components: LCD output, button input, LED status indicators, and I2C sensor communication.

The problem being solved is creating a reliable, testable thermostat-style application that reads real-world data, presents it clearly to the user, and responds to user input with predictable state-driven behavior while also producing periodic telemetry.

### What Did You Do Particularly Well?

I performed particularly well at implementing clear requirements and validating behavior through structured integration.

I built the system around explicit pin mappings, state logic, timed behaviors such as LCD refresh and UART output interval, and PWM-based LED behavior to represent active versus satisfied states.

I also used runtime output and repeatable test sequences to verify button presses, state transitions, and sensor-driven behavior.

### Where Could You Improve?

I can improve how I validate and demonstrate every required behavior under time pressure, especially during recordings.

In the future, I will use a short pre-record checklist that forces each condition: heat running, heat satisfied, cool running, cool satisfied, and off. This would help verify each requirement visually before recording.

### What Tools and/or Resources Are You Adding to Your Support Network?

I am adding a more formal verification workflow that includes wiring validation checklists, consistent I2C verification steps such as device detection and address confirmation, and repeatable test scripts/checklists for triggering each state transition, LED condition, and LCD behavior prior to submission.

I will continue using lab guides and rubrics as requirement references and use targeted debug output to confirm runtime behavior.

### What Skills From This Project Will Be Particularly Transferable to Other Projects and/or Coursework?

Transferable skills include:

- Hardware/software integration using GPIO input/output, I2C sensor communication, LCD output, and UART telemetry
- Debugging discipline using a baseline, isolate, test one change, and verify process
- State-machine design for predictable control behavior
- PWM-based LED signaling for active versus satisfied system states
- Validation practices using observable outputs such as LCD/LED behavior and repeatable test sequences

These skills apply directly to future embedded projects and any system that requires reliable integration and troubleshooting.

### How Did You Make This Project Maintainable, Readable, and Adaptable?

I kept the project maintainable by separating responsibilities such as sensor reads, LED updates, LCD updates, UART output, and button handling while driving behavior through a small set of states.

This structure makes it easier to extend the project with new states, different sensors, alternate display formats, or different telemetry intervals without rewriting large sections of code.

## Future Improvements

- Reformat `Thermostat.py` for improved readability
- Add `requirements.txt`
- Add setup instructions for Raspberry Pi configuration
- Add screenshots of the wiring, LCD output, and LED behavior
- Add a short validation checklist for each thermostat state
- Organize files into `src/`, `docs/`, and `media/` folders
