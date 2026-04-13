# main.py -- application entry point
# Runs after boot.py on every reset.

from machine import Pin
import time

# Hold pin references to prevent GC from releasing GPIOs
backlight = Pin(21, Pin.OUT, value=1)  # Display backlight ON

# --- Application code here ---


# Keep-alive loop (required to maintain GPIO state after boot)
while True:
    time.sleep(1)
