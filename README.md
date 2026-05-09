# Teaching Machine CYD

Port of [TeachingMachinePython](https://github.com/Qazebulon/TeachingMachinePython) to the ESP32 CYD (Cheap Yellow Display). A snake game combined with an adaptive math drill that tracks per-student progress.

Keyboard input is received wirelessly via ESP-NOW from the [ESP32 Keyboard](https://github.com/Qazebulon/ESP_32_Keyboard) project running on a YD-ESP32-S3.

## Hardware

- **CYD:** ESP32-2432S028 (ILI9341 320x240 TFT, DAC speaker on GPIO 26)
- **Keyboard sender:** YD-ESP32-S3 running the ESP32 Keyboard firmware with a USB keyboard attached

No wiring required between the two boards — they communicate over ESP-NOW (WiFi channel 1, unencrypted).

## Prerequisites

Install these Python packages on your PC:

```bash
pip install esptool adafruit-ampy pyserial
```

**Linux only (one-time):** Add yourself to the `dialout` group for serial access, then log out and back in:

```bash
sudo usermod -a -G dialout $USER
```

## Flashing a New CYD

The `flash_cyd.py` script auto-detects the CYD's CH340 serial port. If auto-detection fails, pass the port explicitly with `--port`:

```bash
# Windows (typically COM5)
python flash_cyd.py --port COM5 all

# Linux (typically /dev/ttyUSB0)
python flash_cyd.py --port /dev/ttyUSB0 all
```

### 1. Download MicroPython firmware

```bash
python flash_cyd.py download
```

This saves `micropython-esp32.bin` locally (ESP32_GENERIC v1.24.0).

### 2. Erase and flash firmware

Connect the CYD via USB (the micro-USB port).

```bash
python flash_cyd.py erase
python flash_cyd.py flash
```

Or do both plus upload in one step:

```bash
python flash_cyd.py all
```

### 3. Upload application code

```bash
python flash_cyd.py upload
```

This transfers `boot.py`, `main.py`, and `ili9341.py` to the CYD's flash filesystem via ampy.

To re-upload after editing code (no need to erase/flash again):

```bash
python flash_cyd.py upload
```

### 4. Reset the board

Press the reset button on the CYD. The Teaching Machine title screen should appear.

## Usage

### Startup

1. Power on the CYD and the YD-ESP32-S3 keyboard sender
2. The CYD shows "Teaching Machine — Enter Name:"
3. Type a student name on the USB keyboard (up to 10 characters) and press Enter
4. If the student has played before, their progress is loaded automatically

### Gameplay

The screen is split: snake game on the left (208px), math problem sidebar on the right (112px).

The snake moves automatically. When it eats a berry (or a 30-second timer expires, or it crashes), a math problem appears in the sidebar. Answer correctly to resume playing. Wrong answers show the correct answer — press Delete to continue.

The adaptive engine gives harder problems less often and repeats problems you get wrong. Progress is saved per student.

### Controls

| Action | Keys |
|--------|------|
| Snake direction | Arrow keys or Numpad 2/4/6/8 (Numpad 5 = down) |
| Enter digit | Number row (0-9) or Numpad (0-9) |
| Submit answer | Enter or Numpad Enter |
| Delete last digit | Backspace |
| Acknowledge error | Delete |
| Save and quit | Esc |

Numpad keys serve double duty: they control the snake during gameplay and enter digits during math input.

### Difficulty progression

- **Math level:** Starts at 1. Correct answers reduce a problem's weight (appears less often). Wrong answers reset it to maximum weight. The level rises as easier problems are mastered.
- **Snake speed:** Every 10 berries the snake speeds up and grows faster. Snake difficulty is independent of math level.

## Pairing (Magic Sync)

The Teaching Machine no longer hardcodes a sender MAC. It implements the symmetric magic-pairing protocol from `specs/ESP32_Clone_Control/sanity/PROTOCOL.md` (Clone Control v0, magic header `ECC\x01`):

- Identifies as role `'C'` (CYD), name `teach-machine`.
- Broadcasts a beacon every 2s.
- Pairs automatically with any sender that broadcasts a counterpart-role beacon (role `'M'`, the keyboard host).
- HID frames from a paired peer continue to be raw 8-byte boot-keyboard reports — no migration needed on the host side beyond emitting the magic-sync beacon.

To read the CYD's MAC for diagnostic purposes:

```bash
python flash_cyd.py mac
```

## File Overview

| File | Runs on | Purpose |
|------|---------|---------|
| `main.py` | CYD | Game logic, ESP-NOW receiver, display, sound |
| `ili9341.py` | CYD | ILI9341 display driver (SPI, 320x240 landscape) |
| `boot.py` | CYD | Minimal boot stub |
| `flash_cyd.py` | PC | Firmware download, flash, and code upload utility |

Student progress files are stored on the CYD's flash filesystem as `M1_<NAME>` (e.g., `M1_ALICE`).
