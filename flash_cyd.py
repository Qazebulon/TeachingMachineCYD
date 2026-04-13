"""Flash MicroPython + upload code to CYD for Teaching Machine.

Usage:
  python flash_cyd.py download            -- download MicroPython firmware
  python flash_cyd.py erase               -- erase CYD flash
  python flash_cyd.py flash               -- flash MicroPython firmware
  python flash_cyd.py upload              -- upload boot.py, main.py, ili9341.py via ampy
  python flash_cyd.py mac                 -- read CYD STA MAC address via REPL
  python flash_cyd.py all                 -- erase + flash + upload
  python flash_cyd.py --port /dev/ttyUSB0 upload  -- use a specific serial port
"""
import subprocess
import sys
import os
import platform
import time


def detect_port():
    """Auto-detect the CYD serial port, or return a platform default."""
    try:
        import serial.tools.list_ports
        for p in serial.tools.list_ports.comports():
            # CH340 is the USB-serial chip on the CYD
            if "CH340" in (p.description or "") or "CH340" in (p.manufacturer or ""):
                return p.device
    except ImportError:
        pass
    # Fall back to platform default
    if platform.system() == "Windows":
        return "COM5"
    # Linux: /dev/ttyUSB0 is the most common CH340 path
    if os.path.exists("/dev/ttyUSB0"):
        return "/dev/ttyUSB0"
    return "/dev/ttyUSB0"


PORT = detect_port()
BAUD = 460800
FIRMWARE_URL = "https://micropython.org/resources/firmware/ESP32_GENERIC-20241025-v1.24.0.bin"
FIRMWARE_FILE = os.path.join(os.path.dirname(__file__), "micropython-esp32.bin")
CYD_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FILES = ["boot.py", "main.py", "ili9341.py"]


def run(cmd, timeout=120):
    print("  > %s" % cmd)
    result = subprocess.run(cmd, shell=True, timeout=timeout)
    if result.returncode != 0:
        print("  FAILED (exit %d)" % result.returncode)
        sys.exit(result.returncode)


def download():
    if os.path.exists(FIRMWARE_FILE):
        print("Firmware already downloaded: %s" % FIRMWARE_FILE)
        return
    print("Downloading MicroPython firmware...")
    import urllib.request
    urllib.request.urlretrieve(FIRMWARE_URL, FIRMWARE_FILE)
    print("Saved to %s" % FIRMWARE_FILE)


def erase():
    print("Erasing CYD flash...")
    run("python -m esptool --chip esp32 --port %s --baud %d erase_flash" % (PORT, BAUD))


def flash():
    if not os.path.exists(FIRMWARE_FILE):
        print("Firmware not found. Run 'download' first.")
        sys.exit(1)
    print("Flashing MicroPython to CYD...")
    run("python -m esptool --chip esp32 --port %s --baud %d write_flash 0x1000 %s"
        % (PORT, BAUD, FIRMWARE_FILE))
    print("Waiting for reboot...")
    time.sleep(3)


def upload():
    for fname in UPLOAD_FILES:
        fpath = os.path.join(CYD_DIR, fname)
        if not os.path.exists(fpath):
            print("  SKIP %s (not found)" % fname)
            continue
        print("Uploading %s..." % fname)
        run("python -m ampy.cli --port %s --delay 2 put %s" % (PORT, fpath))
    print("Upload complete. Reset the board.")


def mac():
    """Read CYD STA MAC via serial REPL."""
    import serial
    print("Connecting to %s to read MAC..." % PORT)
    with serial.Serial(PORT, 115200, timeout=2) as ser:
        time.sleep(0.5)
        ser.write(b'\x03\x03')
        time.sleep(0.5)
        ser.read(ser.in_waiting)
        cmd = b"import network; w=network.WLAN(network.STA_IF); w.active(True); print(':'.join('%02x'%b for b in w.config('mac')))\r\n"
        ser.write(cmd)
        time.sleep(2)
        output = ser.read(ser.in_waiting).decode('utf-8', errors='replace')
        for line in output.split('\n'):
            line = line.strip()
            if len(line) == 17 and line.count(':') == 5:
                print("CYD STA MAC: %s" % line)
                return line
        print("Could not read MAC. REPL output:")
        print(output)
        return None


if __name__ == "__main__":
    args = sys.argv[1:]

    # Handle --port flag
    if "--port" in args:
        idx = args.index("--port")
        if idx + 1 >= len(args):
            print("ERROR: --port requires a value (e.g. --port /dev/ttyUSB0)")
            sys.exit(1)
        PORT = args[idx + 1]
        args = args[:idx] + args[idx + 2:]

    if not args:
        print(__doc__)
        sys.exit(1)

    print("Using port: %s" % PORT)
    cmd = args[0]

    if cmd == "download":
        download()
    elif cmd == "erase":
        erase()
    elif cmd == "flash":
        flash()
    elif cmd == "upload":
        upload()
    elif cmd == "mac":
        mac()
    elif cmd == "all":
        download()
        erase()
        flash()
        upload()
    else:
        print("Unknown command: %s" % cmd)
        print(__doc__)
        sys.exit(1)
