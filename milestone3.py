#!/usr/bin/env python3

import RPi.GPIO as GPIO
import time

# --------------------------
# Pin definitions (BCM mode)
# --------------------------
# LCD
LCD_RS = 17
LCD_E  = 27
LCD_D4 = 5
LCD_D5 = 6
LCD_D6 = 13
LCD_D7 = 26

# LEDs
LED_RED  = 18   # dots
LED_BLUE = 23   # dashes

# Button
BUTTON   = 24   # external pull-up (10k to 3V3), active LOW

# --------------------------
# LCD constants
# --------------------------
LCD_WIDTH = 16
LCD_CHR   = True
LCD_CMD   = False

LCD_LINE_1 = 0x80
LCD_LINE_2 = 0xC0

E_PULSE = 0.0005
E_DELAY = 0.0005

# --------------------------
# Morse timing (seconds)
# --------------------------
DOT_TIME          = 0.5
DASH_TIME         = 1.5
INTRA_SYMBOL_GAP  = 0.25   # between dot/dash in same letter
LETTER_GAP        = 0.75
WORD_GAP          = 3.0

# --------------------------
# Morse code map
# --------------------------
MORSE = {
    'A': '.-',    'B': '-...',  'C': '-.-.',  'D': '-..',
    'E': '.',     'F': '..-.',  'G': '--.',   'H': '....',
    'I': '..',    'J': '.---',  'K': '-.-',   'L': '.-..',
    'M': '--',    'N': '-.',    'O': '---',   'P': '.--.',
    'Q': '--.-',  'R': '.-.',   'S': '...',   'T': '-',
    'U': '..-',   'V': '...-',  'W': '.--',   'X': '-..-',
    'Y': '-.--',  'Z': '--..',
    '0': '-----', '1': '.----', '2': '..---', '3': '...--',
    '4': '....-', '5': '.....', '6': '-....', '7': '--...',
    '8': '---..', '9': '----.',
}

# Messages to transmit (edit these if you want)
MESSAGES = [
    "SOS",
    "HELLO",
    "CS 350"
]

# --------------------------
# GPIO / LCD helpers
# --------------------------
def gpio_setup():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    # LCD
    GPIO.setup(LCD_E,  GPIO.OUT)
    GPIO.setup(LCD_RS, GPIO.OUT)
    GPIO.setup(LCD_D4, GPIO.OUT)
    GPIO.setup(LCD_D5, GPIO.OUT)
    GPIO.setup(LCD_D6, GPIO.OUT)
    GPIO.setup(LCD_D7, GPIO.OUT)

    # LEDs
    GPIO.setup(LED_RED,  GPIO.OUT)
    GPIO.setup(LED_BLUE, GPIO.OUT)
    GPIO.output(LED_RED,  False)
    GPIO.output(LED_BLUE, False)

    # Button – external pull-up via 10k to 3V3
    GPIO.setup(BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_OFF)

def lcd_toggle_enable():
    time.sleep(E_DELAY)
    GPIO.output(LCD_E, True)
    time.sleep(E_PULSE)
    GPIO.output(LCD_E, False)
    time.sleep(E_DELAY)

def lcd_byte(bits, mode):
    GPIO.output(LCD_RS, mode)

    # High nibble
    GPIO.output(LCD_D4, bool(bits & 0x10))
    GPIO.output(LCD_D5, bool(bits & 0x20))
    GPIO.output(LCD_D6, bool(bits & 0x40))
    GPIO.output(LCD_D7, bool(bits & 0x80))
    lcd_toggle_enable()

    # Low nibble
    GPIO.output(LCD_D4, bool(bits & 0x01))
    GPIO.output(LCD_D5, bool(bits & 0x02))
    GPIO.output(LCD_D6, bool(bits & 0x04))
    GPIO.output(LCD_D7, bool(bits & 0x08))
    lcd_toggle_enable()

def lcd_init():
    lcd_byte(0x33, LCD_CMD)
    lcd_byte(0x32, LCD_CMD)
    lcd_byte(0x28, LCD_CMD)  # 2 lines, 5x7 matrix
    lcd_byte(0x0C, LCD_CMD)  # display on, cursor off
    lcd_byte(0x06, LCD_CMD)  # entry mode
    lcd_byte(0x01, LCD_CMD)  # clear
    time.sleep(0.003)

def lcd_string(message, line):
    message = str(message).ljust(LCD_WIDTH)
    lcd_byte(line, LCD_CMD)
    for char in message[:LCD_WIDTH]:
        lcd_byte(ord(char), LCD_CHR)

def set_leds(red_on, blue_on):
    GPIO.output(LED_RED,  red_on)
    GPIO.output(LED_BLUE, blue_on)

# --------------------------
# Button helpers (polling)
# --------------------------
def button_pressed_once():
    """Return True once per press+release (active LOW)."""
    if GPIO.input(BUTTON) == GPIO.LOW:
        # debounce: still low after short delay?
        time.sleep(0.02)
        if GPIO.input(BUTTON) == GPIO.LOW:
            # wait until released so we only count once
            while GPIO.input(BUTTON) == GPIO.LOW:
                time.sleep(0.01)
            return True
    return False

def wait_with_button(duration, msg_index):
    """Wait 'duration' seconds, watching for button presses."""
    end_time = time.time() + duration
    while time.time() < end_time:
        if button_pressed_once():
            msg_index = (msg_index + 1) % len(MESSAGES)
        time.sleep(0.01)
    return msg_index

# --------------------------
# Morse / LED behaviors
# --------------------------
def dot(msg_index):
    set_leds(True, False)
    msg_index = wait_with_button(DOT_TIME, msg_index)
    set_leds(False, False)
    return msg_index

def dash(msg_index):
    set_leds(False, True)
    msg_index = wait_with_button(DASH_TIME, msg_index)
    set_leds(False, False)
    return msg_index

def send_letter(letter, msg_index):
    pattern = MORSE.get(letter.upper())
    if not pattern:
        return msg_index

    lcd_string(f"Letter: {letter}", LCD_LINE_2)

    first_symbol = True
    for symbol in pattern:
        if not first_symbol:
            msg_index = wait_with_button(INTRA_SYMBOL_GAP, msg_index)
        first_symbol = False

        if symbol == '.':
            msg_index = dot(msg_index)
        elif symbol == '-':
            msg_index = dash(msg_index)

    msg_index = wait_with_button(LETTER_GAP, msg_index)
    return msg_index

def send_word(word, msg_index):
    for ch in word:
        msg_index = send_letter(ch, msg_index)
    msg_index = wait_with_button(WORD_GAP, msg_index)
    return msg_index

# --------------------------
# Main
# --------------------------
def main():
    gpio_setup()
    lcd_init()

    lcd_string("Milestone 3", LCD_LINE_1)
    lcd_string("Morse + Button", LCD_LINE_2)
    time.sleep(2)

    msg_index = 0

    try:
        while True:
            msg = MESSAGES[msg_index]
            lcd_string(f"Msg:{msg[:13]}", LCD_LINE_1)
            lcd_string(" ", LCD_LINE_2)

            words = msg.split()
            for w in words:
                msg_index = send_word(w, msg_index)
            # now loop repeats; if you pressed the button at any time
            # during the message, msg_index will now be updated,
            # and the *next* message will be different.
    except KeyboardInterrupt:
        pass
    finally:
        try:
            lcd_byte(0x01, LCD_CMD)
        except Exception:
            pass
        set_leds(False, False)
        GPIO.cleanup()

if __name__ == "__main__":
    main()