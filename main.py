#!/usr/bin/env python3
"""news-image-20261121 entry: draw the front page of Saturday 21 November 2026.

A newspaper front page summing up the day's world news, drawn entirely by
code with the Python standard library only (no network, no fonts, no image
files). The program builds a 1024x1024 RGB framebuffer, draws masthead,
three stories and a ticker strip with a hand-built 5x7 bitmap font, then
encodes the framebuffer as a PNG with a hand-rolled encoder (zlib + CRC32).

Deterministic: no randomness, no clock, no timestamps anywhere in the PNG,
so two runs write byte-identical files.

Stories (all verified from 21 Nov 2026 coverage):
  1. Russian missiles land in NATO Poland; Tusk calls it a deliberate
     provocation, NATO jets scramble, Kyiv's bridges are hit.
  2. The AI trade crashes: Nasdaq -5.3% in a day, Anthropic's record IPO
     fizzles, Nvidia -14%, $4 trillion wiped off tech in a week.
  3. The UK and EU seal a landmark reset deal in Brussels.

Usage: python3 main.py   (writes $MAKEFUN_OUTPUT_DIR/entry.png,
or /output/entry.png when the variable is unset)
"""

import binascii
import math
import os
import struct
import zlib

W, H = 1024, 1024

# Palette: newsprint cream, ink black, signal red, deep blue, gold.
PAPER = (246, 241, 227)
INK = (17, 17, 17)
RED = (193, 39, 45)
BLUE = (29, 78, 137)
DARKBLUE = (16, 42, 74)
GOLD = (217, 164, 65)
GREY = (120, 116, 104)
LIGHTGREY = (226, 220, 203)
WHITE = (255, 255, 255)
SKY = (178, 205, 226)
LAND = (232, 222, 188)
GREEN = (46, 125, 72)

# ---------------------------------------------------------------- 5x7 font
# Each glyph is 7 rows of 5 bits, '#' = on, '.' = off. Hand-built.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '$': ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    '_': ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    '•': ("00000", "00000", "01100", "01100", "00000", "00000", "00000"),
    '£': ("00110", "01000", "01000", "11110", "01000", "10010", "01100"),
    '€': ("00110", "01001", "10000", "11110", "10000", "01001", "00110"),
}


def text_width(s, scale):
    """Pixel width of string s rendered at the given scale."""
    return len(s) * 6 * scale - scale


class Canvas:
    """An RGB framebuffer with simple vector drawing primitives."""

    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = color

    def fill_rect(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            row = bytes(color) * (x1 - x0)
            self.px[base:base + (x1 - x0) * 3] = row

    def rect(self, x, y, w, h, color, t=1):
        self.fill_rect(x, y, w, t, color)
        self.fill_rect(x, y + h - t, w, t, color)
        self.fill_rect(x, y, t, h, color)
        self.fill_rect(x + w - t, y, t, h, color)

    def hline(self, x, y, w, color, t=1):
        self.fill_rect(x, y, w, t, color)

    def vline(self, x, y, h, color, t=1):
        self.fill_rect(x, y, t, h, color)

    def line(self, x0, y0, x1, y1, color, t=1):
        """Bresenham line with square brush of thickness t."""
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx - dy
        half = t // 2
        while True:
            self.fill_rect(x0 - half, y0 - half, t, t, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            dx = int((r * r - (yy - cy) ** 2) ** 0.5)
            self.fill_rect(cx - dx, yy, 2 * dx + 1, 1, color)

    def circle(self, cx, cy, r, color, t=1):
        steps = max(24, int(6.28 * r))
        pts = []
        for i in range(steps + 1):
            a = 6.283185307179586 * i / steps
            pts.append((cx + int(r * _cos(a)), cy + int(r * _sin(a))))
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            self.line(x0, y0, x1, y1, color, t)

    def poly(self, pts, color):
        """Fill a polygon with a scanline fill."""
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    x = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
                    xs.append(x)
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                self.fill_rect(int(xs[j]), y, max(1, int(xs[j + 1]) - int(xs[j])), 1, color)

    def text(self, x, y, s, scale, color, align="left"):
        """Draw text; returns the x of the end of the string."""
        if align == "center":
            x -= text_width(s, scale) // 2
        elif align == "right":
            x -= text_width(s, scale)
        cx = x
        for ch in s:
            glyph = FONT.get(ch)
            if glyph is None:
                ch2 = ch.upper()
                glyph = FONT.get(ch2, FONT['?'])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == '1':
                        self.fill_rect(cx + col * scale, y + row * scale,
                                       scale, scale, color)
            cx += 6 * scale
        return cx

    def wrapped(self, x, y, s, scale, color, max_w, line_h=None):
        """Word-wrap text into lines of at most max_w pixels; returns next y."""
        if line_h is None:
            line_h = 9 * scale
        words = s.split(" ")
        lines, cur = [], ""
        for word in words:
            trial = (cur + " " + word).strip()
            if text_width(trial, scale) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        for ln in lines:
            self.text(x, y, ln, scale, color)
            y += line_h
        return y


def _cos(a):
    return math.cos(a)


def _sin(a):
    return math.sin(a)


# ---------------------------------------------------------------- PNG writer
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(cv, path):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.px[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# ---------------------------------------------------------------- layout
M = 28  # page margin


def draw_masthead(cv):
    # Nameplate: THE WORLD TODAY, with TODAY in red.
    title = "THE WORLD TODAY"
    x0 = W // 2 - text_width(title, 9) // 2
    cv.text(x0, 22, title, 9, INK)
    cv.text(x0 + 10 * 6 * 9, 22, "TODAY", 9, RED)
    cv.hline(M, 96, W - 2 * M, INK, 4)
    cv.text(M, 108, "SATURDAY 21 NOVEMBER 2026", 3, INK)
    cv.text(W - M, 108, "ONE DAY - ONE IMAGE", 3, RED, align="right")
    cv.hline(M, 134, W - 2 * M, INK, 2)


def draw_map(cv, x, y, w, h):
    """Stylised map: Poland in the centre, Ukraine to the east, impacts in red."""
    cv.fill_rect(x, y, w, h, SKY)
    # Ukraine (east of Poland).
    cv.poly([(x + 250, y), (x + w, y), (x + w, y + h),
             (x + 262, y + h), (x + 222, y + 240), (x + 242, y + 140)], LIGHTGREY)
    # Poland (simplified outline).
    poland = [(x + 18, y + 34), (x + 62, y + 14), (x + 152, y + 9),
              (x + 212, y + 29), (x + 247, y + 84), (x + 232, y + 154),
              (x + 242, y + 214), (x + 202, y + 274), (x + 142, y + 304),
              (x + 62, y + 289), (x + 22, y + 234), (x + 7, y + 134),
              (x + 12, y + 74)]
    cv.poly(poland, LAND)
    n = len(poland)
    for i in range(n):
        cv.line(poland[i][0], poland[i][1], poland[(i + 1) % n][0],
                poland[(i + 1) % n][1], INK, 3)
    # Missile arcs from the east.
    for (x1, y1, x2, y2) in [(x + 300, y + 150, x + 228, y + 196),
                             (x + 300, y + 210, x + 238, y + 238),
                             (x + 296, y + 260, x + 222, y + 268)]:
        cv.line(x1, y1, x2, y2, RED, 3)
    # Impact sites in south-east Poland.
    for (ix, iy) in [(x + 216, y + 196), (x + 226, y + 238), (x + 210, y + 268)]:
        cv.disc(ix, iy, 8, RED)
        cv.circle(ix, iy, 13, RED, 2)
    # NATO star, top right.
    sx, sy = x + w - 34, y + 30
    cv.disc(sx, sy, 5, GOLD)
    cv.line(sx - 16, sy, sx + 16, sy, GOLD, 3)
    cv.line(sx, sy - 16, sx, sy + 16, GOLD, 3)
    cv.text(sx + 24, sy - 8, "NATO", 2, INK, align="right")
    cv.text(x + 52, y + 120, "POLAND", 2, INK)
    cv.text(x + 252, y + 130, "UKRAINE", 2, INK)
    cv.text(x + 10, y + h - 22, "WEAPONS LAND IN SE POLAND", 2, RED)


def draw_lead(cv):
    x, y, w, h = M, 146, W - 2 * M, 414
    cv.rect(x, y, w, h, INK, 3)
    cv.fill_rect(x + 3, y + 3, w - 6, 46, DARKBLUE)
    cv.text(x + 20, y + 15, "WAR IN EUROPE - NATO", 3, WHITE)
    cv.text(x + 20, y + 58, "MISSILES LAND", 7, INK)
    cv.text(x + 20, y + 112, "IN POLAND", 7, INK)
    cv.text(x + 20, y + 176, "TUSK: 'DELIBERATE PROVOCATION'", 3, RED)
    cv.wrapped(x + 20, y + 206,
               "Two Russian cruise missiles and a jet-powered drone land in "
               "south-east Poland in the biggest attack on Ukraine. NATO jets "
               "scramble; three Kyiv bridges are hit, eight killed.",
               2, INK, 560)
    cv.text(x + 20, y + 296, '"IT DOES NOT LOOK LIKE AN ACCIDENT." - TUSK',
            2, RED)
    draw_map(cv, x + 612, y + 52, 336, 300)
    cv.fill_rect(x + 3, y + h - 43, w - 6, 40, RED)
    cv.text(x + w // 2, y + h - 32,
            "2 MISSILES + 1 DRONE IN POLAND  •  8 KILLED  •  3 KYIV BRIDGES HIT",
            2, WHITE, align="center")


def draw_chart(cv, x, y, w, h):
    """Plunging market line with axes."""
    cv.rect(x, y, w, h, INK, 2)
    cv.fill_rect(x + 2, y + 2, w - 4, h - 4, WHITE)
    cv.line(x + 28, y + 12, x + 28, y + h - 22, INK, 2)
    cv.line(x + 28, y + h - 22, x + w - 12, y + h - 22, INK, 2)
    pts = [(x + 34, y + 18), (x + 110, y + 26), (x + 150, y + 22),
           (x + 210, y + 44), (x + 260, y + 40), (x + 320, y + 62),
           (x + 380, y + 58), (x + 430, y + 70), (x + w - 18, y + h - 30)]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        cv.line(x0, y0, x1, y1, RED, 4)
    for (px, py) in pts:
        cv.disc(px, py, 4, RED)
    cv.text(x + 36, y + 6, "NASDAQ", 2, INK)


def draw_markets(cv):
    x, y, w, h = M, 576, 474, 296
    cv.rect(x, y, w, h, INK, 3)
    cv.text(x + 18, y + 16, "THE AI TRADE UNWINDS - $4TN GONE", 2, RED)
    cv.text(x + 18, y + 40, "AI TRADE", 6, INK)
    cv.text(x + 18, y + 86, "CRASHES", 6, INK)
    draw_chart(cv, x + 18, y + 136, w - 36, 80)
    cv.wrapped(x + 18, y + 224,
               "Anthropic -8.5% to $88.91, barely above its $83 IPO. "
               "Nvidia -14%.",
               2, INK, w - 36)
    cv.fill_rect(x + 3, y + h - 30, w - 6, 27, RED)
    cv.text(x + w // 2, y + h - 23, "NASDAQ -5.3%  •  S&P -3.7%  •  DOW -950",
            2, WHITE, align="center")


def draw_flags(cv, x, y, w, h):
    """Union Jack (left) and EU flag (right), stylised."""
    # Union Jack.
    ux, uw = x, w // 2 - 8
    cv.fill_rect(ux, y, uw, h, BLUE)
    cv.line(ux, y, ux + uw, y + h, WHITE, 16)
    cv.line(ux + uw, y, ux, y + h, WHITE, 16)
    cv.line(ux, y, ux + uw, y + h, RED, 6)
    cv.line(ux + uw, y, ux, y + h, RED, 6)
    cv.fill_rect(ux + uw // 2 - 16, y, 32, h, WHITE)
    cv.fill_rect(ux, y + h // 2 - 16, uw, 32, WHITE)
    cv.fill_rect(ux + uw // 2 - 9, y, 18, h, RED)
    cv.fill_rect(ux, y + h // 2 - 9, uw, 18, RED)
    # EU flag.
    ex = x + w // 2 + 8
    cv.fill_rect(ex, y, uw, h, BLUE)
    cx, cy, r = ex + uw // 2, y + h // 2, 30
    for i in range(12):
        a = 6.283185307179586 * i / 12 - 1.5707963267948966
        cv.disc(cx + int(r * _cos(a)), cy + int(r * _sin(a)), 4, GOLD)


def draw_deal(cv):
    x, y, w, h = M + 494, 576, 474, 296
    cv.rect(x, y, w, h, INK, 3)
    cv.text(x + 18, y + 16, "TEN YEARS AFTER BREXIT", 2, RED)
    cv.text(x + 18, y + 40, "UK-EU SEAL", 5, INK)
    cv.text(x + 18, y + 78, "LANDMARK DEAL", 5, INK)
    draw_flags(cv, x + 18, y + 124, w - 36, 74)
    cv.wrapped(x + 18, y + 210,
               "Food checks end, 100,000 youth visas, emissions trading "
               "linked. Von der Leyen: a turning point.",
               2, INK, w - 36)
    cv.fill_rect(x + 3, y + h - 30, w - 6, 27, GOLD)
    cv.text(x + w // 2, y + h - 23, "WORTH £17BN BY 2040", 2, INK, align="center")


def draw_ticker(cv):
    x, y, w, h = M, 888, W - 2 * M, 56
    cv.fill_rect(x, y, w, h, DARKBLUE)
    cv.text(W // 2, y + 8,
            "ALSO TODAY - EU GIVES UKRAINE €1BN MORE MILITARY AID",
            2, WHITE, align="center")
    cv.text(W // 2, y + 30,
            "U.S. DECLASSIFIES UFO FOOTAGE  •  FRENCH OFFICERS SENTENCED OVER ZEClER BEATING",
            2, WHITE, align="center")


def draw_footer(cv):
    cv.text(W // 2, 962,
            "SATURDAY 21 NOVEMBER 2026 - THE WORLD'S NEWS IN ONE IMAGE",
            2, INK, align="center")


def main():
    cv = Canvas(W, H, PAPER)
    cv.rect(0, 0, W, H, INK, 6)
    draw_masthead(cv)
    draw_lead(cv)
    draw_markets(cv)
    draw_deal(cv)
    draw_ticker(cv)
    draw_footer(cv)
    out = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, "entry.png")
    n = write_png(cv, path)
    print("wrote %s (%d bytes)" % (path, n))


if __name__ == "__main__":
    main()
