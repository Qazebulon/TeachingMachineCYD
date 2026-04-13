# Display — ILI9341 on CYD

## Orientation

- Use `MADCTL = 0x28` (MV + BGR flags) for correct landscape orientation (320x240).
- Without this, colors and/or axis mapping will be wrong.

## Backlight (GPIO 21)

- Active HIGH — you must explicitly set it or the screen stays dark.
- **Hold the Pin object in a variable.** If you create a throwaway `Pin(21, Pin.OUT)` without assigning it, MicroPython's garbage collector can release the GPIO and the backlight turns off unpredictably.

```python
# WRONG — GC may collect this
Pin(21, Pin.OUT).value(1)

# RIGHT — reference stays alive
backlight = Pin(21, Pin.OUT)
backlight.value(1)
```

## SPI Bus Sharing

The display, touch controller (XPT2046), and SD card all share one SPI bus (SCK=14, MOSI=13, MISO=12). Manage CS lines carefully:
- Display CS: GPIO 15
- Touch CS: GPIO 33
- SD CS: GPIO 5

Only one device should be selected at a time. De-assert (HIGH) all other CS lines before asserting (LOW) the target device's CS.
