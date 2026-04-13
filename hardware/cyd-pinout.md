# CYD Pinout Reference — ESP32-2432S028

Board: Sunton ESP32-2432S028 "Cheap Yellow Display"
Chip: ESP32-D0WD-V3 (rev 3.x), dual-core 240 MHz, WiFi + BT
USB-Serial: CH340 (programming/serial only, NOT USB Host)

## Display — ILI9341 2.8" 320x240 TFT (SPI)

| Function | GPIO | Notes |
|----------|------|-------|
| SCK      | 14   | SPI clock |
| MOSI     | 13   | SPI data out |
| MISO     | 12   | SPI data in (also used by touch) |
| CS       | 15   | Display chip select |
| DC       | 2    | Data/Command select |
| Backlight| 21   | Active HIGH. Hold Pin ref in variable to prevent GC |

- MADCTL = 0x28 (MV + BGR) for correct landscape orientation
- SPI bus is shared with touch controller and SD card

## Touch — XPT2046 (SPI, active LOW IRQ)

| Function | GPIO | Notes |
|----------|------|-------|
| CS       | 33   | Touch chip select |
| IRQ      | 36   | Touch interrupt (input only, no pull-up) |

Shares SPI bus (SCK=14, MOSI=13, MISO=12) with display.

## RGB LED (active LOW)

| Color | GPIO | Notes |
|-------|------|-------|
| Red   | 4    | value(0) = ON, value(1) = OFF |
| Green | 16   | value(0) = ON, value(1) = OFF |
| Blue  | 17   | value(0) = ON, value(1) = OFF |

## SD Card (SPI)

| Function | GPIO | Notes |
|----------|------|-------|
| CS       | 5    | SD chip select |

Shares SPI bus with display and touch.

## I2C Header (active pins depend on board revision)

| Function | GPIO | Notes |
|----------|------|-------|
| SDA      | 22   | Active pull-up from 4.7k internal in many revisions |
| SCL      | 27   | |

Check your specific board revision — some use different GPIOs on the header.

## Light Sensor (LDR)

| Function | GPIO | Notes |
|----------|------|-------|
| LDR      | 34   | ADC input only, no pull-up/down |

## Speaker / Audio

| Function | GPIO | Notes |
|----------|------|-------|
| Speaker  | 26   | DAC output, small onboard speaker |

## Boot Button

| Function | GPIO | Notes |
|----------|------|-------|
| BOOT     | 0    | Active LOW, held during reset to enter flash mode |

## Power

- 5V via USB-C (through CH340)
- 3.3V regulated onboard
- Do NOT draw more than ~40mA from 3.3V rail for external peripherals

## Pin Usage Map (quick reference)

```
Used by display:  2, 12, 13, 14, 15, 21
Used by touch:    12, 13, 14, 33, 36
Used by SD card:  5, 12, 13, 14
Used by RGB LED:  4, 16, 17
Used by I2C:      22, 27
Used by LDR:      34
Used by speaker:  26
Used by boot btn: 0
Free / available: 25, 32, 35 (input only)
```

## Project Pin Allocation

<!-- Each project should fill this in to track what's wired where -->

| GPIO | Allocated To | Notes |
|------|-------------|-------|
|      |             |       |
