# ESP32 Board Variants & Limitations

## Standard CYD — ESP32-2432S028

- Chip: ESP32-D0WD-V3 (rev 3.x), dual-core 240 MHz
- USB: CH340 serial chip — **programming and serial monitor only, NOT USB Host**
- WiFi + Bluetooth Classic + BLE
- Cannot act as USB Host (no USB OTG support in hardware)

## ESP32-S3 CYD Variants

- USB OTG support — can act as USB Host (read keyboards, mice, etc.)
- Different firmware flash address (`0x0` instead of `0x1000`)
- Different GPIO assignments — do NOT assume standard CYD pinout applies
- Check your specific S3 board's pinout before wiring

## When You Need USB Host

The standard CYD **cannot** do USB Host. Options:
1. **ESP32-S3 CYD** — has native USB OTG, simplest path
2. **External USB Host controller** (e.g., MAX3421E) — adds complexity, uses SPI
3. **Bluetooth HID** — if the peripheral supports BT, avoid USB entirely

## I2C Header Variation

- Standard pinout: SDA=22, SCL=27
- Some board revisions use different GPIOs on the expansion header
- Always verify with a multimeter or the seller's schematic for your specific revision

## YD-ESP32-S3 (VCC-GND Studio YD-ESP32-23)

- Label: YD-ESP32-23 2022-V1.3
- Chip: ESP32-S3-N8R2 (8MB flash, 2MB PSRAM), dual-core 240 MHz
- Two USB-C ports:
  - **Left** — Native USB OTG (GPIO 19 D-, GPIO 20 D+). USB Host OR Device, not both.
  - **Right** — CH343P serial (flashing/debug only, shows as `USB-Enhanced-SERIAL CH343`). Hardwired as serial — cannot act as HID.
- WiFi 2.4 GHz + BLE (**no Bluetooth Classic**)
- Firmware flash address: `0x0` (S3 standard)
- RGB LED on GPIO 48 (NeoPixel, requires `neopixelWrite()`, not `digitalWrite()`)

### Solder Jumpers (all OPEN by default)

| Jumper | Effect when closed | Risk |
|--------|-------------------|------|
| **USB-OTG** | Bridges VBUS (5V) between both USB-C ports. **Required for USB Host** — without it, devices on the left port get no power. | Never plug both ports into separate PCs simultaneously — two 5V sources on same rail. |
| **IN-OUT** | Bypasses diode, connects USB VBUS to 5Vin pin header. | External power on 5Vin can backfeed to USB. |
| **RGB** | Enables onboard RGB LED on GPIO 48. Some revisions ship pre-bridged with a zero-ohm resistor. | None. |

### Port Identification

| Device Manager shows | Port | Identity |
|---------------------|------|----------|
| `USB-Enhanced-SERIAL CH343 (COMx)` | Right | CH343P serial — flashing + debug |
| `USB Serial Device (COMx)` | Left | Native USB OTG — Host or Device mode |

### Key Gotcha

If a USB device plugged into the left port doesn't power on, the USB-OTG jumper is probably open. Solder-bridge it so 5V flows from the right port through to the left.

### References

- https://github.com/rtek1000/YD-ESP32-23
- https://mischianti.org/vcc-gnd-studio-yd-esp32-s3-devkitc-1-clone-high-resolution-pinout-and-specs/

---

## Adafruit ESP32-S3 Feather

- Chip: ESP32-S3, dual-core 240 MHz Tensilica
- Variants: 8MB Flash / no PSRAM, 4MB Flash / 2MB PSRAM, external antenna (w.FL)
- USB: **Native USB** — can emulate keyboard, mouse, MIDI, disk drive (no CH340 needed)
- WiFi 2.4 GHz + BLE only (**no Bluetooth Classic**)
- Firmware flash address: `0x0` (S3 standard)
- Deep sleep: ~100 uA current draw
- Built-in NeoPixel with GPIO-controlled power (`NEOPIXEL_POWER`)
- STEMMA QT connector for I2C (with GPIO-controlled power via `I2C_POWER`)
- I2C has 5k pull-ups built in (SCL, SDA)
- Most peripherals (PWM, I2S, UART, I2C, SPI) can be mapped to any available pin
- No DAC — cannot do true analog output
- ADC1: A5, D5, D6, D9, D10 | ADC2: A0–A4, D11–D13
- Battery monitor: MAX17048 or LC709203F on I2C (voltage + charge %)
- Red LED on pin 13, boot button on GPIO 0

### Power (Feather)

- **USB-C**: 5V in, regulated to 3.3V (500mA peak, but continuous from 5V risks overheating regulator)
- **LiPo/LiIon battery**: JST jack, 3.7/4.2V, auto-charges when USB connected
- **EN pin**: ground it to disable 3.3V regulator entirely
- **Do NOT connect** alkaline, NiMH, or 7.4V RC batteries to JST — destroys charging circuitry

Reference: https://learn.adafruit.com/adafruit-esp32-s3-feather

---

## Power Constraints (CYD)

- 5V input via USB-C (through CH340)
- 3.3V regulated onboard
- **Do NOT draw more than ~40mA from the 3.3V rail** for external peripherals

---

## Add-On: 5V Charge + Discharge Module (TP4056 replacement)

Adds battery backup to any ESP32 board that lacks built-in LiPo charging (CYD, YD, etc.).

- **Input:** USB-C 5V 1A
- **Output:** 5V (boost converter from single-cell Li-ion/LiPo)
- **Behavior:** Acts as a UPS — USB connected charges battery + powers load simultaneously. USB disconnected, battery powers load at 5V.
- **Battery:** Single-cell 3.7V Li-ion/LiPo (e.g., 18650)
- **Not needed** for boards with built-in charging (e.g., Adafruit Feather)

### Wiring

- Module 5V out → board 5V in (USB or 5V pin, depending on board)
- Battery connects to module's B+/B- pads
- USB-C on the module becomes the new charging port

### Caution

- Do not exceed 1A draw — the boost converter and charge circuit are rated for 1A
- Ensure the board's own USB is not also supplying 5V when powered from the module, or two supplies will conflict (same issue as the YD USB-OTG jumper)
