#!/usr/bin/env python3
"""
Thermostat.py

CS 350 Final Project 

Hardware (BCM numbering):
  AHT20 temp/humidity sensor on I2C bus 1 (SCL=GPIO3, SDA=GPIO2)
  Red LED       -> GPIO 18
  Blue LED      -> GPIO 23
  Mode button   -> GPIO 24  (OFF -> HEAT -> COOL -> OFF)
  Temp Up       -> GPIO 12  (setpoint +1 F)
  Temp Down     -> GPIO 25  (setpoint -1 F)

  16x2 LCD (character):
    RS -> GPIO 17
    EN -> GPIO 27
    D4 -> GPIO 5
    D5 -> GPIO 6
    D6 -> GPIO 13
    D7 -> GPIO 26

Software requirements implemented:
  1. Default setpoint = 72 F.
  2. Read temperature from AHT20 via I2C.
  3. Use LEDs to indicate heat/cool (fade if actively heating/cooling, solid if satisfied).
  4. Buttons:
       - Button 1 (GPIO 24): toggle OFF / HEAT / COOL.
       - Button 2 (GPIO 12): increase setpoint by 1 F.
       - Button 3 (GPIO 25): decrease setpoint by 1 F.
  5. LCD:
       - Line 1: date and current time.
       - Line 2: alternates between current temperature and mode+setpoint.
  6. UART:
       - Send comma-delimited string every 30 seconds:
           state, current temperature, setpoint.
"""

import time
import math
from datetime import datetime

import board
import busio
import adafruit_ahtx0

import digitalio
import adafruit_character_lcd.character_lcd as character_lcd

import serial

import RPi.GPIO as GPIO
from gpiozero import Button


# -----------------------------
# Constants and global state
# -----------------------------

# LED pins (BCM)
RED_LED_PIN = 18
BLUE_LED_PIN = 23

# Button pins (BCM)
MODE_BUTTON_PIN = 24      # OFF/HEAT/COOL mode button
TEMP_UP_BUTTON_PIN = 12   # increase setpoint
TEMP_DOWN_BUTTON_PIN = 25 # decrease setpoint

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
FADE_FREQUENCY_HZ = 100.0  # LED PWM frequency

# UART
UART_PORT = "/dev/serial0"
UART_BAUDRATE = 115200

# Thermostat modes
OFF = 0
HEAT = 1
COOL = 2

# Default setpoint 
DEFAULT_SETPOINT_F = 72.0

# Global variables for state
current_mode = OFF
setpoint_f = DEFAULT_SETPOINT_F
show_temp_on_lcd = True   # toggles the second line display


# -----------------------------
# Initialization Helpers
# -----------------------------

def init_i2c_and_sensor():
    """Initialize I2C bus and AHT20 temperature sensor."""
    i2c = busio.I2C(board.SCL, board.SDA)
    sensor = adafruit_ahtx0.AHTx0(i2c)
    return sensor


def init_lcd():
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
    # NOTE: backlight is hard-wired to +5V/GND in hardware, so we do NOT
    # call lcd.backlight = True here (no backlight_pin was provided).
    return lcd


def init_gpio_and_buttons():
    """Initialize GPIO, LEDs with PWM, and buttons using gpiozero."""
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    # LEDs as PWM outputs
    GPIO.setup(RED_LED_PIN, GPIO.OUT)
    GPIO.setup(BLUE_LED_PIN, GPIO.OUT)

    red_pwm = GPIO.PWM(RED_LED_PIN, FADE_FREQUENCY_HZ)
    blue_pwm = GPIO.PWM(BLUE_LED_PIN, FADE_FREQUENCY_HZ)

    red_pwm.start(0.0)   # duty cycle 0 = off
    blue_pwm.start(0.0)

    # gpiozero buttons; hardware has external 10k pull-ups to 3.3V (active-low).
    mode_button = Button(MODE_BUTTON_PIN, pull_up=True, bounce_time=0.1)
    temp_up_button = Button(TEMP_UP_BUTTON_PIN, pull_up=True, bounce_time=0.1)
    temp_down_button = Button(TEMP_DOWN_BUTTON_PIN, pull_up=True, bounce_time=0.1)

    return red_pwm, blue_pwm, mode_button, temp_up_button, temp_down_button


def init_uart():
    """Initialize UART serial port for output (Requirement 6)."""
    ser = serial.Serial(
        port=UART_PORT,
        baudrate=UART_BAUDRATE,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=1,
    )
    return ser


# -----------------------------
# Button Callbacks
# -----------------------------

def attach_button_callbacks(mode_button, temp_up_button, temp_down_button):
    """Attach callbacks to buttons using gpiozero."""

    def on_mode_pressed():
        global current_mode
        if current_mode == OFF:
            current_mode = HEAT
        elif current_mode == HEAT:
            current_mode = COOL
        else:
            current_mode = OFF

    def on_temp_up_pressed():
        global setpoint_f
        setpoint_f += 1.0

    def on_temp_down_pressed():
        global setpoint_f
        setpoint_f -= 1.0

    mode_button.when_pressed = on_mode_pressed
    temp_up_button.when_pressed = on_temp_up_pressed
    temp_down_button.when_pressed = on_temp_down_pressed


# -----------------------------
# Sensor / Temperature Helpers
# -----------------------------

def read_temperature_f(sensor):
    """Read the current temperature from the AHT20 in Fahrenheit."""
    temp_c = sensor.temperature
    temp_f = (temp_c * 9.0 / 5.0) + 32.0
    return temp_f


# -----------------------------
# LED / Heating-Cooling Logic
# -----------------------------

def set_led_duty(red_pwm, blue_pwm, red_level, blue_level):
    """
    Set LED brightness.
    red_level and blue_level are 0.0..1.0; convert to 0..100 duty cycle.
    """
    red_pwm.ChangeDutyCycle(max(0.0, min(100.0, red_level * 100.0)))
    blue_pwm.ChangeDutyCycle(max(0.0, min(100.0, blue_level * 100.0)))


def update_leds_for_state(red_pwm, blue_pwm, mode, current_temp_f, setpoint_f, now):
    """
    Requirement 3:
      A. If heating and temp < setpoint: red LED fades in/out.
      B. If cooling and temp > setpoint: blue LED fades in/out.
      C. If heating and temp >= setpoint: red solid ON.
      D. If cooling and temp <= setpoint: blue solid ON.
      OFF mode: both LEDs OFF.
    """
    red_level = 0.0
    blue_level = 0.0

    if mode == HEAT:
        if current_temp_f < setpoint_f:
            # Fade red LED in and out 
            phase = (now % 2.0) / 2.0
            red_level = 0.5 + 0.5 * math.sin(2.0 * math.pi * phase)
        else:
            # Solid red
            red_level = 1.0
    elif mode == COOL:
        if current_temp_f > setpoint_f:
            # Fade blue LED
            phase = (now % 2.0) / 2.0
            blue_level = 0.5 + 0.5 * math.sin(2.0 * math.pi * phase)
        else:
            # Solid blue
            blue_level = 1.0
    else:
        # OFF mode – both LEDs off
        red_level = 0.0
        blue_level = 0.0

    set_led_duty(red_pwm, blue_pwm, red_level, blue_level)


# -----------------------------
# LCD Helpers
# -----------------------------

def mode_to_string(mode):
    if mode == OFF:
        return "OFF"
    elif mode == HEAT:
        return "HEAT"
    else:
        return "COOL"


def update_lcd(lcd, current_temp_f, mode, setpoint_f, show_temp_line):
    """
    Requirement 5:
      - First line: date + current time.
      - Second line: alternates between current temp and mode+setpoint.
    """
    now = datetime.now()
    # Example: "02/20 19:42:33"
    line1 = now.strftime("%m/%d %H:%M:%S")

    if show_temp_line:
        line2 = f"Temp: {current_temp_f:5.1f}F"
    else:
        state_str = mode_to_string(mode)
        line2 = f"{state_str} SP:{setpoint_f:4.1f}"

    # lines are at most 16 chars
    line1 = line1[:16]
    line2 = line2[:16]

    lcd.home()
    lcd.message = line1 + "\n" + line2


# -----------------------------
# UART Helper
# -----------------------------

def send_uart_status(ser, current_temp_f, mode, setpoint_f):
    """
    Requirement 6:
      - Single comma-delimited string every 30 seconds.
      - Fields: state, current temperature, setpoint.
    Example:
      "HEAT,70.50,72.00\n"
    """
    state_str = mode_to_string(mode)
    msg = f"{state_str},{current_temp_f:.2f},{setpoint_f:.2f}\n"
    ser.write(msg.encode("utf-8"))


# -----------------------------
# Main
# -----------------------------

def main():
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

            # Requirement 2
            current_temp_f = read_temperature_f(sensor)

            # Update LED behavior based on mode & temperature
            update_leds_for_state(red_pwm, blue_pwm, current_mode, current_temp_f, setpoint_f, now)

            # Flip what we show on LCD second line every 2 seconds
            if now - last_lcd_toggle_time >= 2.0:
                show_temp_on_lcd = not show_temp_on_lcd
                last_lcd_toggle_time = now

            update_lcd(lcd, current_temp_f, current_mode, setpoint_f, show_temp_on_lcd)

            # Requirement 6
            if now - last_uart_time >= 30.0:
                send_uart_status(ser, current_temp_f, current_mode, setpoint_f)
                last_uart_time = now

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nThermostat stopped by user.")

    finally:
        # Cleanup
        red_pwm.stop()
        blue_pwm.stop()
        GPIO.cleanup()
        lcd.clear()
        try:
            ser.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()