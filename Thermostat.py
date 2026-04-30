#!/usr/bin/env python3
"""
Thermostat.py

CS-350 Final Project

This script implements a Raspberry Pi-based thermostat controller that reads
temperature data from an AHT20 sensor, displays system status on a 16x2 LCD,
uses physical buttons for user input, drives heating/cooling LEDs with PWM, and
sends periodic UART telemetry.

Hardware uses BCM numbering:
    AHT20 temp/humidity sensor: I2C bus 1 (SCL=GPIO3, SDA=GPIO2)

    Red LED:      GPIO 18
    Blue LED:     GPIO 23
    Mode button:  GPIO 24  (OFF -> HEAT -> COOL -> OFF)
    Temp Up:      GPIO 12  (set point +1 F)
    Temp Down:    GPIO 25  (set point -1 F)

    16x2 LCD:
        RS -> GPIO 17
        EN -> GPIO 27
        D4 -> GPIO 5
        D5 -> GPIO 6
        D6 -> GPIO 13
        D7 -> GPIO 26

Implemented requirements:
    1. Default set point is 72 F.
    2. Read temperature from the AHT20 sensor over I2C.
    3. Use LEDs to indicate heat/cool status:
        - Fade while actively heating/cooling.
        - Remain solid when the selected mode is satisfied.
    4. Use three buttons:
        - Button 1: toggle OFF / HEAT / COOL.
        - Button 2: increase set point by 1 F.
        - Button 3: decrease set point by 1 F.
    5. LCD output:
        - Line 1: date and current time.
        - Line 2: alternates between current temperature and mode/set point.
    6. UART output:
        - Send comma-delimited telemetry every 30 seconds:
          state, current temperature, set point.
"""

from __future__ import annotations

import math
import time
from contextlib import suppress
from datetime import datetime
from typing import Any

import adafruit_ahtx0
import adafruit_character_lcd.character_lcd as character_lcd
import board
import busio
import digitalio
import RPi.GPIO as GPIO
import serial
from gpiozero import Button


# -----------------------------
# Constants
# -----------------------------

# LED pins (BCM)
RED_LED_PIN = 18
BLUE_LED_PIN = 23

# Button pins (BCM)
MODE_BUTTON_PIN = 24
TEMP_UP_BUTTON_PIN = 12
TEMP_DOWN_BUTTON_PIN = 25

# LCD pin mapping (BCM)
LCD_RS_PIN = 17
LCD_EN_PIN = 27
LCD_D4_PIN = 5
LCD_D5_PIN = 6
LCD_D6_PIN = 13
LCD_D7_PIN = 26
LCD_COLUMNS = 16
LCD_ROWS = 2

# PWM
FADE_FREQUENCY_HZ = 100.0

# UART
UART_PORT = "/dev/serial0"
UART_BAUDRATE = 115200
UART_INTERVAL_SECONDS = 30.0

# Timing
LCD_TOGGLE_INTERVAL_SECONDS = 2.0
MAIN_LOOP_SLEEP_SECONDS = 0.1

# Thermostat modes
OFF = 0
HEAT = 1
COOL = 2

# Default set point
DEFAULT_SETPOINT_F = 72.0


# -----------------------------
# Global state
# -----------------------------

current_mode = OFF
setpoint_f = DEFAULT_SETPOINT_F
show_temp_on_lcd = True


# -----------------------------
# Initialization helpers
# -----------------------------

def init_i2c_and_sensor() -> Any:
    """Initialize the I2C bus and AHT20 temperature/humidity sensor."""
    i2c = busio.I2C(board.SCL, board.SDA)
    return adafruit_ahtx0.AHTx0(i2c)


def init_lcd() -> character_lcd.Character_LCD_Mono:
    """Initialize the 16x2 character LCD using the Adafruit library."""
    lcd_rs = digitalio.DigitalInOut(getattr(board, f"D{LCD_RS_PIN}"))
    lcd_en = digitalio.DigitalInOut(getattr(board, f"D{LCD_EN_PIN}"))
    lcd_d4 = digitalio.DigitalInOut(getattr(board, f"D{LCD_D4_PIN}"))
    lcd_d5 = digitalio.DigitalInOut(getattr(board, f"D{LCD_D5_PIN}"))
    lcd_d6 = digitalio.DigitalInOut(getattr(board, f"D{LCD_D6_PIN}"))
    lcd_d7 = digitalio.DigitalInOut(getattr(board, f"D{LCD_D7_PIN}"))

    lcd = character_lcd.Character_LCD_Mono(
        lcd_rs,
        lcd_en,
        lcd_d4,
        lcd_d5,
        lcd_d6,
        lcd_d7,
        LCD_COLUMNS,
        LCD_ROWS,
    )

    lcd.clear()

    # The LCD backlight is hard-wired to +5V/GND in this hardware setup.
    # No backlight_pin was provided, so do not set lcd.backlight here.
    return lcd


def init_gpio_and_buttons() -> tuple[GPIO.PWM, GPIO.PWM, Button, Button, Button]:
    """Initialize GPIO pins, PWM LEDs, and gpiozero button inputs."""
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    GPIO.setup(RED_LED_PIN, GPIO.OUT)
    GPIO.setup(BLUE_LED_PIN, GPIO.OUT)

    red_pwm = GPIO.PWM(RED_LED_PIN, FADE_FREQUENCY_HZ)
    blue_pwm = GPIO.PWM(BLUE_LED_PIN, FADE_FREQUENCY_HZ)

    red_pwm.start(0.0)
    blue_pwm.start(0.0)

    # Hardware uses external 10k pull-ups to 3.3V, so buttons are active-low.
    mode_button = Button(MODE_BUTTON_PIN, pull_up=True, bounce_time=0.1)
    temp_up_button = Button(TEMP_UP_BUTTON_PIN, pull_up=True, bounce_time=0.1)
    temp_down_button = Button(TEMP_DOWN_BUTTON_PIN, pull_up=True, bounce_time=0.1)

    return red_pwm, blue_pwm, mode_button, temp_up_button, temp_down_button


def init_uart() -> serial.Serial:
    """Initialize the UART serial port for telemetry output."""
    return serial.Serial(
        port=UART_PORT,
        baudrate=UART_BAUDRATE,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=1,
    )


# -----------------------------
# Button callbacks
# -----------------------------

def attach_button_callbacks(
    mode_button: Button,
    temp_up_button: Button,
    temp_down_button: Button,
) -> None:
    """Attach input callbacks to the mode, temperature up, and temperature down buttons."""

    def on_mode_pressed() -> None:
        global current_mode

        if current_mode == OFF:
            current_mode = HEAT
        elif current_mode == HEAT:
            current_mode = COOL
        else:
            current_mode = OFF

    def on_temp_up_pressed() -> None:
        global setpoint_f
        setpoint_f += 1.0

    def on_temp_down_pressed() -> None:
        global setpoint_f
        setpoint_f -= 1.0

    mode_button.when_pressed = on_mode_pressed
    temp_up_button.when_pressed = on_temp_up_pressed
    temp_down_button.when_pressed = on_temp_down_pressed


# -----------------------------
# Sensor and temperature helpers
# -----------------------------

def read_temperature_f(sensor: Any) -> float:
    """Read the current temperature from the AHT20 sensor and convert it to Fahrenheit."""
    temp_c = sensor.temperature
    return (temp_c * 9.0 / 5.0) + 32.0


# -----------------------------
# LED and heating/cooling logic
# -----------------------------

def clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    """Clamp a numeric value to the provided minimum and maximum range."""
    return max(minimum, min(maximum, value))


def set_led_duty(
    red_pwm: GPIO.PWM,
    blue_pwm: GPIO.PWM,
    red_level: float,
    blue_level: float,
) -> None:
    """
    Set LED brightness.

    red_level and blue_level use a 0.0 to 1.0 range and are converted to
    0.0 to 100.0 PWM duty cycle values.
    """
    red_pwm.ChangeDutyCycle(clamp(red_level * 100.0))
    blue_pwm.ChangeDutyCycle(clamp(blue_level * 100.0))


def update_leds_for_state(
    red_pwm: GPIO.PWM,
    blue_pwm: GPIO.PWM,
    mode: int,
    current_temp_f: float,
    active_setpoint_f: float,
    now: float,
) -> None:
    """
    Update heating/cooling LEDs based on thermostat mode and temperature.

    HEAT:
        - temp < set point: red LED fades.
        - temp >= set point: red LED remains solid.

    COOL:
        - temp > set point: blue LED fades.
        - temp <= set point: blue LED remains solid.

    OFF:
        - both LEDs remain off.
    """
    red_level = 0.0
    blue_level = 0.0

    if mode == HEAT:
        if current_temp_f < active_setpoint_f:
            phase = (now % 2.0) / 2.0
            red_level = 0.5 + 0.5 * math.sin(2.0 * math.pi * phase)
        else:
            red_level = 1.0

    elif mode == COOL:
        if current_temp_f > active_setpoint_f:
            phase = (now % 2.0) / 2.0
            blue_level = 0.5 + 0.5 * math.sin(2.0 * math.pi * phase)
        else:
            blue_level = 1.0

    set_led_duty(red_pwm, blue_pwm, red_level, blue_level)


# -----------------------------
# LCD helpers
# -----------------------------

def mode_to_string(mode: int) -> str:
    """Convert the thermostat mode constant to a display string."""
    if mode == OFF:
        return "OFF"

    if mode == HEAT:
        return "HEAT"

    return "COOL"


def format_lcd_line(value: str) -> str:
    """Limit and pad LCD text to exactly 16 characters."""
    return value[:LCD_COLUMNS].ljust(LCD_COLUMNS)


def update_lcd(
    lcd: character_lcd.Character_LCD_Mono,
    current_temp_f: float,
    mode: int,
    active_setpoint_f: float,
    show_temp_line: bool,
) -> None:
    """
    Update LCD output.

    Line 1: date and current time.
    Line 2: alternates between current temperature and mode/set point.
    """
    now = datetime.now()
    line1 = now.strftime("%m/%d %H:%M:%S")

    if show_temp_line:
        line2 = f"Temp: {current_temp_f:5.1f}F"
    else:
        line2 = f"{mode_to_string(mode)} SP:{active_setpoint_f:4.1f}"

    lcd.home()
    lcd.message = f"{format_lcd_line(line1)}\n{format_lcd_line(line2)}"


# -----------------------------
# UART helper
# -----------------------------

def send_uart_status(
    ser: serial.Serial,
    current_temp_f: float,
    mode: int,
    active_setpoint_f: float,
) -> None:
    """
    Send one comma-delimited telemetry record over UART.

    Format:
        state,current_temperature,setpoint
    Example:
        HEAT,70.50,72.00
    """
    state_str = mode_to_string(mode)
    msg = f"{state_str},{current_temp_f:.2f},{active_setpoint_f:.2f}\n"
    ser.write(msg.encode("utf-8"))


# -----------------------------
# Main program
# -----------------------------

def main() -> None:
    """Run the thermostat controller main loop."""
    global current_mode, setpoint_f, show_temp_on_lcd

    print("Initializing thermostat system...")

    sensor = init_i2c_and_sensor()
    lcd = init_lcd()
    red_pwm, blue_pwm, mode_button, temp_up_button, temp_down_button = init_gpio_and_buttons()
    attach_button_callbacks(mode_button, temp_up_button, temp_down_button)
    ser = init_uart()

    last_lcd_toggle_time = time.time()
    last_uart_time = time.time()

    try:
        while True:
            now = time.time()
            current_temp_f = read_temperature_f(sensor)

            update_leds_for_state(
                red_pwm,
                blue_pwm,
                current_mode,
                current_temp_f,
                setpoint_f,
                now,
            )

            if now - last_lcd_toggle_time >= LCD_TOGGLE_INTERVAL_SECONDS:
                show_temp_on_lcd = not show_temp_on_lcd
                last_lcd_toggle_time = now

            update_lcd(
                lcd,
                current_temp_f,
                current_mode,
                setpoint_f,
                show_temp_on_lcd,
            )

            if now - last_uart_time >= UART_INTERVAL_SECONDS:
                send_uart_status(ser, current_temp_f, current_mode, setpoint_f)
                last_uart_time = now

            time.sleep(MAIN_LOOP_SLEEP_SECONDS)

    except KeyboardInterrupt:
        print("\nThermostat stopped by user.")

    finally:
        red_pwm.stop()
        blue_pwm.stop()
        GPIO.cleanup()
        lcd.clear()

        with suppress(Exception):
            ser.close()


if __name__ == "__main__":
    main()
