from machine import Pin
import framebuf
import time

# ILI9341 commands
_SWRESET = 0x01
_SLPOUT  = 0x11
_DISPON  = 0x29
_CASET   = 0x2A
_PASET   = 0x2B
_RAMWR   = 0x2C
_MADCTL  = 0x36
_COLMOD  = 0x3A


class ILI9341:
    def __init__(self, spi, cs, dc, rst=None, bl=None, width=320, height=240):
        self.spi = spi
        self.cs  = Pin(cs,  Pin.OUT, value=1)
        self.dc  = Pin(dc,  Pin.OUT, value=0)
        self.rst = Pin(rst, Pin.OUT, value=1) if rst is not None else None
        self.w   = width
        self.h   = height

        if bl is not None:
            Pin(bl, Pin.OUT).value(1)

        self._init()

    def _cmd(self, cmd):
        self.dc.value(0)
        self.cs.value(0)
        self.spi.write(bytes([cmd]))
        self.cs.value(1)

    def _dat(self, data):
        self.dc.value(1)
        self.cs.value(0)
        self.spi.write(data if isinstance(data, (bytes, bytearray)) else bytes([data]))
        self.cs.value(1)

    def _init(self):
        if self.rst:
            self.rst.value(0); time.sleep_ms(50)
            self.rst.value(1); time.sleep_ms(50)
        self._cmd(_SWRESET); time.sleep_ms(150)
        self._cmd(_SLPOUT);  time.sleep_ms(150)
        self._cmd(_COLMOD);  self._dat(0x55)   # 16-bit colour
        self._cmd(_MADCTL);  self._dat(0x28)   # landscape (MV+BGR)
        self._cmd(_DISPON);  time.sleep_ms(100)

    def _window(self, x0, y0, x1, y1):
        self._cmd(_CASET)
        self._dat(bytes([x0 >> 8, x0 & 0xFF, x1 >> 8, x1 & 0xFF]))
        self._cmd(_PASET)
        self._dat(bytes([y0 >> 8, y0 & 0xFF, y1 >> 8, y1 & 0xFF]))
        self._cmd(_RAMWR)

    def fill(self, colour):
        self._window(0, 0, self.w - 1, self.h - 1)
        hi, lo = colour >> 8, colour & 0xFF
        chunk = bytes([hi, lo] * 64)
        self.dc.value(1); self.cs.value(0)
        for _ in range(self.w * self.h // 64):
            self.spi.write(chunk)
        self.cs.value(1)

    def fill_rect(self, x, y, w, h, colour):
        """Fill a rectangle with a solid colour."""
        if w <= 0 or h <= 0:
            return
        self._window(x, y, x + w - 1, y + h - 1)
        hi, lo = colour >> 8, colour & 0xFF
        total = w * h
        csz = min(total, 128)
        chunk = bytes([hi, lo] * csz)
        self.dc.value(1); self.cs.value(0)
        full = total // csz
        rem = total % csz
        for _ in range(full):
            self.spi.write(chunk)
        if rem:
            self.spi.write(bytes([hi, lo] * rem))
        self.cs.value(1)

    def text(self, string, x, y, fg, bg=0x0000, scale=1):
        """Draw text using the built-in 8x8 font, scaled by `scale`."""
        cw, ch = 8 * len(string), 8
        # Render to small framebuf
        buf = bytearray(cw * ch * 2)
        fb  = framebuf.FrameBuffer(buf, cw, ch, framebuf.RGB565)
        fb.fill(bg); fb.text(string, 0, 0, fg)

        sw, sh = cw * scale, ch * scale
        out = bytearray(sw * sh * 2)
        for py in range(ch):
            for px in range(cw):
                off  = (py * cw + px) * 2
                b0, b1 = buf[off], buf[off + 1]
                for dy in range(scale):
                    row = (py * scale + dy) * sw
                    for dx in range(scale):
                        o2 = (row + px * scale + dx) * 2
                        out[o2] = b0; out[o2 + 1] = b1

        self._window(x, y, x + sw - 1, y + sh - 1)
        self.dc.value(1); self.cs.value(0)
        self.spi.write(out)
        self.cs.value(1)
