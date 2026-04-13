# main.py -- Teaching Machine CYD
# Port of TeachingMachinePython to ESP32 CYD (320x240 ILI9341)
# Receives keyboard via ESP-NOW from YD-ESP32-S3 (8-byte HID reports)
# Snake game + adaptive math drill with per-student progress

import network
import espnow
import random
import time
from machine import Pin, SPI, PWM
from ili9341 import ILI9341

# ── Hardware Setup ────────────────────────────────────────
backlight = Pin(21, Pin.OUT, value=1)
touch_cs = Pin(33, Pin.OUT, value=1)   # deselect touch
sd_cs = Pin(5, Pin.OUT, value=1)       # deselect SD

spi = SPI(1, baudrate=40_000_000, polarity=0, phase=0,
          sck=Pin(14), mosi=Pin(13), miso=Pin(12))
lcd = ILI9341(spi, cs=15, dc=2)

# RGB LED (active LOW: value(0)=ON)
led_r = Pin(4, Pin.OUT, value=1)
led_g = Pin(16, Pin.OUT, value=1)
led_b = Pin(17, Pin.OUT, value=1)

# ESP-NOW
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
enow = espnow.ESPNow()
enow.active(True)
YD_MAC = b'\x28\x37\x2f\xe6\xd7\x74'   # YD-ESP32-S3 keyboard sender
enow.add_peer(YD_MAC)

# Broadcast discovery beacon so YD Host auto-registers this CYD
BCAST = b'\xff\xff\xff\xff\xff\xff'
enow.add_peer(BCAST)
enow.send(BCAST, b'CYD\x01TeachMachine')
enow.del_peer(BCAST)

# ── Layout Constants ──────────────────────────────────────
TILE = 8
MAP_W = 26                       # tiles (26*8=208px for snake area)
MAP_H = 30                       # tiles (30*8=240px full height)
SB_X = MAP_W * TILE              # sidebar x = 208
SB_W = 320 - SB_X               # sidebar width = 112
MX = SB_X + 12                  # math display x offset

# Snake interior bounds (inside border walls)
SX0, SX1 = 1, MAP_W - 2         # 1..24
SY0, SY1 = 1, MAP_H - 2         # 1..28

# ── Colours (RGB565) ─────────────────────────────────────
BLK = 0x0000; WHT = 0xFFFF; GRN = 0x07E0; DGN = 0x03E0
RED = 0xF800; YEL = 0xFFE0; CYN = 0x07FF; GRY = 0x7BEF
DGY = 0x39E7; MAG = 0xF81F

# ── HID Keycodes ─────────────────────────────────────────
K_ENT = 0x28; K_KENT = 0x58; K_BKSP = 0x2A
K_ESC = 0x29; K_DEL = 0x4C
K_RIGHT = 0x4F; K_LEFT = 0x50; K_DOWN = 0x51; K_UP = 0x52
K_KP2 = 0x5A; K_KP4 = 0x5C; K_KP5 = 0x5D; K_KP6 = 0x5E; K_KP8 = 0x60

# Digit map (number row + numpad)
DKEYS = {
    0x27: 0, 0x1E: 1, 0x1F: 2, 0x20: 3, 0x21: 4,
    0x22: 5, 0x23: 6, 0x24: 7, 0x25: 8, 0x26: 9,
    0x62: 0, 0x59: 1, 0x5A: 2, 0x5B: 3, 0x5C: 4,
    0x5D: 5, 0x5E: 6, 0x5F: 7, 0x60: 8, 0x61: 9,
}

# ── Game States ───────────────────────────────────────────
S_GAME = 0; S_PROB = 1; S_ANS = 2; S_ERR = 3; S_FIX = 4

# ── Math Facts (145: 81 addition + 64 multiplication) ────
# Packed as a single string, 3 chars per problem
_F = (
    "1+12+11+23+11+32+24+11+43+22+3"
    "5+11+54+22+43+36+11+65+22+54+3"
    "3+47+11+76+22+65+33+54+48+11+8"
    "7+22+76+33+65+44+59+11+98+22+8"
    "7+33+76+44+65+59+22+98+33+87+4"
    "4+76+55+69+33+98+44+87+55+76+6"
    "9+44+98+55+87+66+79+55+98+66+8"
    "7+79+66+98+77+89+77+98+89+88+9"
    "9+9"
    "2*23*22*34*22*43*35*22*54*33*4"
    "6*22*67*22*75*33*54*48*22*86*3"
    "3*69*22*95*44*57*33*76*44*68*3"
    "3*85*59*33*97*44*76*55*68*44*8"
    "7*55*76*69*44*98*55*87*66*79*5"
    "5*98*66*87*79*66*98*77*89*77*9"
    "8*89*88*99*9"
)
FACTS = [_F[i:i+3] for i in range(0, 435, 3)]
N_FACTS = 145

# Movement vectors: right, left, up, down
MOVES = ((1, 0), (-1, 0), (0, -1), (0, 1))

# ── Sound ─────────────────────────────────────────────────
def beep(freq, ms):
    try:
        p = PWM(Pin(26), freq=freq, duty=512)
        time.sleep_ms(ms)
        p.deinit()
    except:
        pass

def snd_berry():
    beep(880, 80)

def snd_ok():
    led_g.value(0)
    beep(660, 80)
    beep(880, 120)
    led_g.value(1)

def snd_err():
    led_r.value(0)
    beep(220, 200)
    led_r.value(1)

def snd_crash():
    beep(440, 80)
    beep(220, 150)

def snd_timer():
    beep(660, 150)

# ── Input ─────────────────────────────────────────────────
_prev = set()

def read_input():
    """Return (new_presses, held_keys, modifier_byte)."""
    global _prev
    host, msg = enow.irecv(10)
    if msg and len(msg) >= 8:
        cur = set(k for k in msg[2:8] if k)
        new = cur - _prev
        _prev = cur
        return new, cur, msg[0]
    return set(), _prev, 0

def hid_char(k):
    """HID keycode -> uppercase letter, or None."""
    if 0x04 <= k <= 0x1D:
        return chr(k - 0x04 + 65)
    return None

# ── Student I/O ──────────────────────────────────────────
def save_stu(name, prob):
    with open("M1_" + name, "w") as f:
        for p in prob:
            f.write("%d\n" % int(p))

def load_stu(name):
    try:
        with open("M1_" + name, "r") as f:
            p = [int(ln) for ln in f if ln.strip()]
        return p if len(p) == N_FACTS else None
    except:
        return None

# ── Drawing Helpers ───────────────────────────────────────
def pad(s, w):
    return s[:w] if len(s) >= w else s + " " * (w - len(s))

def draw_walls():
    for x in range(MAP_W):
        lcd.fill_rect(x * TILE, 0, TILE, TILE, GRY)
        lcd.fill_rect(x * TILE, (MAP_H - 1) * TILE, TILE, TILE, GRY)
    for y in range(1, MAP_H - 1):
        lcd.fill_rect(0, y * TILE, TILE, TILE, GRY)
        lcd.fill_rect((MAP_W - 1) * TILE, y * TILE, TILE, TILE, GRY)

def draw_sidebar():
    lcd.fill_rect(SB_X, 0, SB_W, 240, BLK)
    lcd.fill_rect(SB_X, 0, 2, 240, DGN)

def draw_lv(lv):
    t = "TOP!" if lv >= 141 else "Lv:%d" % lv
    lcd.text(pad(t, 6), SB_X + 6, 4, GRN, BLK, 2)

def draw_name_sb(n):
    lcd.text(pad(n, 13), SB_X + 6, 26, CYN, BLK, 1)

def draw_prob(tn, bn, op, ans):
    lcd.fill_rect(SB_X + 3, 44, SB_W - 3, 108, BLK)
    oc = "+" if op == 1 else "x"
    lcd.text(pad("%2d" % tn, 4), MX, 50, WHT, BLK, 3)
    lcd.text(pad("%s%2d" % (oc, bn), 4), MX, 78, WHT, BLK, 3)
    lcd.fill_rect(MX, 106, 96, 3, GRN)
    draw_ans(ans)

def draw_ans(a):
    lcd.fill_rect(MX, 114, 96, 26, BLK)
    if a == 0:
        lcd.text(pad("  ?", 4), MX, 114, GRN, BLK, 3)
    else:
        lcd.text(pad("%2d" % (a % 100), 4), MX, 114, WHT, BLK, 3)

def draw_err_msg():
    lcd.fill_rect(SB_X + 3, 152, SB_W - 3, 48, BLK)
    lcd.text(pad("ERROR!", 6), SB_X + 6, 156, RED, BLK, 2)
    lcd.text("Press DEL", SB_X + 6, 180, YEL, BLK, 1)

def clear_msg():
    lcd.fill_rect(SB_X + 3, 152, SB_W - 3, 48, BLK)

def draw_spd(slv):
    lcd.text(pad("Snake:%d" % slv, 13), SB_X + 6, 228, DGY, BLK, 1)

# ── Name Entry Screen ────────────────────────────────────
def get_name():
    lcd.fill(BLK)
    lcd.text("Teaching", 40, 16, GRN, BLK, 3)
    lcd.text("Machine", 52, 48, GRN, BLK, 3)
    lcd.text("CYD Edition", 56, 88, DGN, BLK, 2)
    lcd.text("Enter Name:", 20, 130, CYN, BLK, 2)
    lcd.text("_", 20, 160, WHT, BLK, 3)
    lcd.text("Type + Enter", 60, 220, DGY, BLK, 1)

    global _prev
    _prev = set()
    name = ""

    while True:
        new, held, mod = read_input()
        for k in new:
            if k in (K_ENT, K_KENT) and name:
                return name
            elif k == K_BKSP and name:
                name = name[:-1]
            else:
                c = hid_char(k)
                if c and len(name) < 10:
                    name += c
        if new:
            lcd.fill_rect(20, 160, 280, 26, BLK)
            lcd.text(pad(name + "_", 12), 20, 160, WHT, BLK, 3)

# ── Main Game ─────────────────────────────────────────────
def run():
    name = get_name()

    # Load or create student
    prob = load_stu(name)
    if prob is None:
        prob = [16384] * N_FACTS

    # Snake state
    blocks = [[12, 15], [11, 15]]
    dirn = 0                         # 0=right 1=left 2=up 3=down
    berry = [6, 6]
    speed = 250                      # ms per move
    tick = 0
    gtime = 0                        # ms since last problem (game timer)
    bcount = 0                       # berries eaten this snake-level
    seg_add = 1                      # segments added per berry
    slevel = 1                       # snake speed level
    top_lv = 4                       # top math level achieved

    # Problem state
    tn = bn = 1; op = 1; ok_a = 2; ans = 0; sel = 0
    state = S_PROB

    def place_berry():
        for _ in range(200):
            bx = random.randint(SX0, SX1)
            by = random.randint(SY0, SY1)
            hit = False
            for b in blocks:
                if b[0] == bx and b[1] == by:
                    hit = True
                    break
            if not hit:
                berry[0] = bx; berry[1] = by
                return

    def reset_snake():
        nonlocal dirn, tick
        blocks.clear()
        blocks.append([12, 15]); blocks.append([11, 15])
        dirn = 0; tick = 0
        place_berry()
        # Redraw play area
        lcd.fill_rect(TILE, TILE, (MAP_W - 2) * TILE, (MAP_H - 2) * TILE, BLK)
        for i, b in enumerate(blocks):
            lcd.fill_rect(b[0] * TILE, b[1] * TILE, TILE, TILE, GRN if i == 0 else DGN)
        lcd.fill_rect(berry[0] * TILE + 1, berry[1] * TILE + 1, TILE - 2, TILE - 2, RED)

    # Initial screen
    lcd.fill(BLK)
    draw_walls()
    draw_sidebar()
    draw_name_sb(name)
    draw_spd(slevel)
    reset_snake()

    last_t = time.ticks_ms()
    global _prev
    _prev = set()

    while True:
        now = time.ticks_ms()
        dt = time.ticks_diff(now, last_t)
        last_t = now

        new, held, mod = read_input()

        # ── GAME ──────────────────────────────────────
        if state == S_GAME:
            # Direction from held keys
            if K_RIGHT in held or K_KP6 in held:
                if dirn != 1: dirn = 0
            elif K_LEFT in held or K_KP4 in held:
                if dirn != 0: dirn = 1
            elif K_UP in held or K_KP8 in held:
                if dirn != 3: dirn = 2
            elif K_DOWN in held or K_KP2 in held or K_KP5 in held:
                if dirn != 2: dirn = 3

            # Esc = save & quit to name screen
            if K_ESC in new:
                save_stu(name, prob)
                lcd.fill(BLK)
                lcd.text("Saved!", 88, 108, GRN, BLK, 3)
                time.sleep_ms(1000)
                return

            tick += dt
            gtime += dt

            if tick >= speed:
                tick -= speed

                dx, dy = MOVES[dirn]
                nx = blocks[0][0] + dx
                ny = blocks[0][1] + dy

                # Wall collision
                if nx < SX0 or nx > SX1 or ny < SY0 or ny > SY1:
                    snd_crash()
                    reset_snake()
                    state = S_PROB
                    continue

                # Body collision
                body_hit = False
                for i in range(1, len(blocks)):
                    if blocks[i][0] == nx and blocks[i][1] == ny:
                        body_hit = True
                        break
                if body_hit:
                    snd_crash()
                    reset_snake()
                    state = S_PROB
                    continue

                # Move: shift segments, set new head
                old_tail = [blocks[-1][0], blocks[-1][1]]
                for i in range(len(blocks) - 1, 0, -1):
                    blocks[i][0] = blocks[i - 1][0]
                    blocks[i][1] = blocks[i - 1][1]
                blocks[0] = [nx, ny]

                ate = (nx == berry[0] and ny == berry[1])

                if ate:
                    snd_berry()
                    for _ in range(seg_add):
                        blocks.append([old_tail[0], old_tail[1]])
                    bcount += 1
                    if bcount >= 10:
                        bcount = 0
                        speed = max(100, speed - 25)
                        slevel += 1
                        seg_add = min(64, seg_add * 2)
                        draw_spd(slevel)
                    place_berry()
                    lcd.fill_rect(berry[0] * TILE + 1, berry[1] * TILE + 1,
                                  TILE - 2, TILE - 2, RED)
                    state = S_PROB
                else:
                    # Erase old tail
                    lcd.fill_rect(old_tail[0] * TILE, old_tail[1] * TILE,
                                  TILE, TILE, BLK)

                # Redraw old head as body, draw new head
                if len(blocks) > 1:
                    lcd.fill_rect(blocks[1][0] * TILE, blocks[1][1] * TILE,
                                  TILE, TILE, DGN)
                lcd.fill_rect(nx * TILE, ny * TILE, TILE, TILE, GRN)

                if ate:
                    continue

            # Timer forces a problem
            if gtime > 30000:
                snd_timer()
                state = S_PROB

        # ── PROBLEM SELECT ────────────────────────────
        elif state == S_PROB:
            # Calculate adaptive math level
            mx = 65536
            s = n = 0
            while s <= mx and n < N_FACTS:
                s += prob[n]
                n += 1
            level = n
            if level > top_lv:
                top_lv = level
            if mx > s:
                mx = s

            # Weighted random problem selection
            s = n = 0
            r = random.randint(0, mx)
            while s <= r and n < N_FACTS:
                s += prob[n]
                n += 1
            sel = n - 1

            # Parse problem
            w = FACTS[sel]
            tn = ord(w[0]) - 48
            bn = ord(w[2]) - 48
            if w[1] == "+":
                op = 1; ok_a = tn + bn
            else:
                op = 2; ok_a = tn * bn
            ans = 0

            draw_lv(level - 4)
            draw_prob(tn, bn, op, ans)
            clear_msg()
            state = S_ANS

        # ── ANSWER INPUT ──────────────────────────────
        elif state == S_ANS:
            for k in new:
                if k in (K_ENT, K_KENT):
                    if ans == ok_a:
                        snd_ok()
                        prob[sel] = prob[sel] // 16 + 1
                        gtime = 0
                        # Catch-up: more problems if below top level
                        if level < top_lv:
                            state = S_PROB
                        else:
                            state = S_GAME
                    else:
                        snd_err()
                        prob[sel] = 16384
                        state = S_ERR
                elif k == K_BKSP:
                    ans = ans // 10
                    draw_ans(ans)
                elif k in DKEYS:
                    ans = ans * 10 + DKEYS[k]
                    if ans > 99:
                        ans = ans % 100
                    draw_ans(ans)

        # ── ERROR (show briefly, then fix) ────────────
        elif state == S_ERR:
            ans = ok_a
            draw_ans(ans)
            draw_err_msg()
            state = S_FIX

        # ── FIX (wait for DEL key) ───────────────────
        elif state == S_FIX:
            if K_DEL in new:
                clear_msg()
                state = S_PROB

# ── Entry Point ───────────────────────────────────────────
while True:
    run()
