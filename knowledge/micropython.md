# MicroPython on ESP32 CYD

## Firmware Flashing

- **ESP32 (standard CYD):** flash address is `0x1000`
- **ESP32-S3 (S3 CYD variant):** flash address is `0x0`
- Using the wrong address silently fails or produces boot loops.

## Boot Sequence

1. `boot.py` runs first (use for WiFi, early config)
2. `main.py` runs second (main application logic)
3. **`main.py` must end with a `while True` loop** — otherwise the script exits and GPIO/display state is lost (pins reset, backlight goes dark).

## File Transfer (ampy)

- Command: `python -m ampy.cli --port <COM_PORT> --delay 2`
- The `--delay 2` flag is critical on Windows — without it, serial timeouts are common due to CH340 USB-serial timing.
- ampy does not support directories natively; transfer files one at a time.

## Garbage Collection Gotchas

- MicroPython aggressively garbage-collects unreferenced objects.
- Any hardware Pin, SPI, or I2C object must be held in a named variable for its entire lifetime.
- This applies to backlight pins, CS pins, bus objects — anything you need to persist.

## I2C

- `SoftI2C` is more reliable than hardware I2C on many ESP32 boards.
- If I2C peripherals are intermittent, try switching from `I2C` to `SoftI2C`.

## Common Pitfalls

| Symptom | Likely Cause |
|---------|-------------|
| Screen goes dark randomly | Backlight Pin got garbage-collected |
| ampy times out on Windows | Missing `--delay 2` flag |
| Board boot loops after flash | Wrong firmware address (0x1000 vs 0x0) |
| GPIO state lost after main.py | Missing `while True` loop at end |
| I2C sensor intermittent | Try SoftI2C instead of hardware I2C |
