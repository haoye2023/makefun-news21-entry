#!/usr/bin/env python3
"""The World in a Day - Saturday 21 November 2026.

Entry for the make.fun bounty "Sum up 21 November's world news in one
image" (news-image-20261121). Pure Python standard library, no network.
Draws a newspaper front page carrying 30 stories from Saturday
21 November 2026: a numbers strip, three lead stories with
program-drawn illustrations, twelve short reports and a 15-item
"Also on Saturday" list, plus a date-check line. Writes a
deterministic 1024x1024 entry.png (two runs are byte-identical).

Run:  MAKEFUN_OUTPUT_DIR=/tmp/out python3 main.py
"""

import os
import struct
import zlib

W = 1024
H = 1024

PAPER = (247, 242, 228)
INK = (25, 25, 36)
RED = (179, 53, 43)
BLUE = (29, 78, 137)
GRAY = (107, 107, 107)
NIGHT = (24, 34, 74)
WHITE = (245, 245, 245)
GOLD = (214, 164, 32)


def png_bytes(w, h, pixels):
    """pixels: bytearray of w*h*3 RGB bytes. Returns PNG file bytes."""
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw += pixels[y * stride:(y + 1) * stride]

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bytes(bg) * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def rect(self, x, y, rw, rh, color):
        for yy in range(y, y + rh):
            if 0 <= yy < self.h:
                base = yy * self.w
                for xx in range(x, x + rw):
                    if 0 <= xx < self.w:
                        i = (base + xx) * 3
                        self.px[i:i + 3] = bytes(color)

    def frame(self, x, y, rw, rh, color, t=2):
        self.rect(x, y, rw, t, color)
        self.rect(x, y + rh - t, rw, t, color)
        self.rect(x, y, t, rh, color)
        self.rect(x + rw - t, y, t, rh, color)

    def line(self, x0, y0, x1, y1, color, t=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            for ox in range(t):
                for oy in range(t):
                    self.set(x0 + ox, y0 + oy, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, color)


# ---------------------------------------------------------------- fonts
# 5x7 dot-matrix font, one string per glyph, rows joined by "/".
FONT5 = {
    "A": ".###./#...#/#...#/#####/#...#/#...#/#...#",
    "B": "####./#...#/#...#/####./#...#/#...#/####.",
    "C": ".####/#..../#..../#..../#..../#..../.####",
    "D": "####./#...#/#...#/#...#/#...#/#...#/####.",
    "E": "#####/#..../#..../####./#..../#..../#####",
    "F": "#####/#..../#..../####./#..../#..../#....",
    "G": ".####/#..../#..../#.###/#...#/#...#/.###.",
    "H": "#...#/#...#/#...#/#####/#...#/#...#/#...#",
    "I": "#####/..#../..#../..#../..#../..#../#####",
    "J": "..###/...#./...#./...#./...#./#..#./.##..",
    "K": "#...#/#..#./#.#../##.../#.#../#..#./#...#",
    "L": "#..../#..../#..../#..../#..../#..../#####",
    "M": "#...#/##.##/#.#.#/#.#.#/#...#/#...#/#...#",
    "N": "#...#/##..#/#.#.#/#..##/#...#/#...#/#...#",
    "O": ".###./#...#/#...#/#...#/#...#/#...#/.###.",
    "P": "####./#...#/#...#/####./#..../#..../#....",
    "Q": ".###./#...#/#...#/#...#/#.#.#/#..#./.##.#",
    "R": "####./#...#/#...#/####./#.#../#..#./#...#",
    "S": ".####/#..../#..../.###./....#/....#/####.",
    "T": "#####/..#../..#../..#../..#../..#../..#..",
    "U": "#...#/#...#/#...#/#...#/#...#/#...#/.###.",
    "V": "#...#/#...#/#...#/#...#/#...#/.#.#./..#..",
    "W": "#...#/#...#/#...#/#.#.#/#.#.#/##.##/#...#",
    "X": "#...#/.#.#./..#../..#../..#../.#.#./#...#",
    "Y": "#...#/#...#/.#.#./..#../..#../..#../..#..",
    "Z": "#####/....#/...#./..#../.#.../#..../#####",
    "0": ".###./#...#/#..##/#.#.#/##..#/#...#/.###.",
    "1": "..#../.##../..#../..#../..#../..#../#####",
    "2": ".###./#...#/....#/..##./.#.../#..../#####",
    "3": ".###./#...#/....#/..##./....#/#...#/.###.",
    "4": "...#./..##./.#.#./#..#./#####/...#./...#.",
    "5": "#####/#..../####./....#/....#/#...#/.###.",
    "6": ".###./#..../#..../####./#...#/#...#/.###.",
    "7": "#####/....#/..#../..#../..#../..#../..#..",
    "8": ".###./#...#/#...#/.###./#...#/#...#/.###.",
    "9": ".###./#...#/#...#/.####/....#/....#/.###.",
    " ": "...../...../...../...../...../...../.....",
    ".": "...../...../...../...../...../...../..#..",
    ",": "...../...../...../...../...../..#../.#...",
    "'": "..#../..#../.#.../...../...../...../.....",
    ":": "...../..#../..#../...../..#../..#../.....",
    ";": "...../..#../..#../...../..#../..#../.#...",
    "-": "...../...../...../#####/...../...../.....",
    "+": "...../..#../..#../.###./..#../..#../.....",
    "$": "..#../.####/#.#../.###./..#.#/####./..#..",
    "%": "##..#/##.#./....#/...#./..#../.#.../#.##.",
    "/": "....#/....#/..#../..#../.#.../#..../#....",
    "(": "...##/..#../.#.../.#.../.#.../..#../...##",
    ")": "##.../..#../...#./...#./...#./..#../##...",
    "!": "..#../..#../..#../..#../..#../...../..#..",
    "?": ".###./#...#/....#/..##./..#../...../..#..",
    "&": ".##../#..#./#.#../.#.../#.#.#/#..#./.##.#",
    '"': ".#.#./.#.#./...../...../...../...../.....",
    "_": "...../...../...../...../...../...../#####",
}
FONT5 = {k: tuple(v.split("/")) for k, v in FONT5.items()}

# 3x5 micro font for the ALSO list (drawn at scale 2).
FONT3 = {
    "A": ("###", "#.#", "###", "#.#", "#.#"),
    "B": ("##.", "#.#", "##.", "#.#", "##."),
    "C": (".##", "#..", "#..", "#..", ".##"),
    "D": ("##.", "#.#", "#.#", "#.#", "##."),
    "E": ("###", "#..", "##.", "#..", "###"),
    "F": ("###", "#..", "##.", "#..", "#.."),
    "G": ("###", "#..", "#.#", "#.#", "###"),
    "H": ("#.#", "#.#", "###", "#.#", "#.#"),
    "I": ("###", ".#.", ".#.", ".#.", "###"),
    "J": ("..#", "..#", "..#", "#.#", ".#."),
    "K": ("#.#", "#.#", "##.", "#.#", "#.#"),
    "L": ("#..", "#..", "#..", "#..", "###"),
    "M": ("#.#", "###", "###", "#.#", "#.#"),
    "N": ("#.#", "###", "###", "#.#", "#.#"),
    "O": ("###", "#.#", "#.#", "#.#", "###"),
    "P": ("###", "#.#", "###", "#..", "#.."),
    "Q": ("###", "#.#", "#.#", "###", "..#"),
    "R": ("###", "#.#", "##.", "#.#", "#.#"),
    "S": (".##", "#..", ".#.", "..#", "##."),
    "T": ("###", ".#.", ".#.", ".#.", ".#."),
    "U": ("#.#", "#.#", "#.#", "#.#", "###"),
    "V": ("#.#", "#.#", "#.#", "#.#", ".#."),
    "W": ("#.#", "#.#", "###", "###", "#.#"),
    "X": ("#.#", "#.#", ".#.", "#.#", "#.#"),
    "Y": ("#.#", "#.#", ".#.", ".#.", ".#."),
    "Z": ("###", "..#", ".#.", "#..", "###"),
    "0": ("###", "#.#", "#.#", "#.#", "###"),
    "1": (".#.", "##.", ".#.", ".#.", "###"),
    "2": ("##.", "..#", ".#.", "#..", "###"),
    "3": ("##.", "..#", ".#.", "..#", "##."),
    "4": ("#.#", "#.#", "###", "..#", "..#"),
    "5": ("###", "#..", "##.", "..#", "##."),
    "6": (".##", "#..", "##.", "#.#", ".#."),
    "7": ("###", "..#", ".#.", ".#.", ".#."),
    "8": (".#.", "#.#", ".#.", "#.#", ".#."),
    "9": (".#.", "#.#", ".##", "..#", "##."),
    " ": ("...", "...", "...", "...", "..."),
    ".": ("...", "...", "...", "...", ".#."),
    ",": ("...", "...", "...", ".#.", ".#."),
    "'": (".#.", ".#.", "...", "...", "..."),
    ":": ("...", ".#.", "...", ".#.", "..."),
    ";": ("...", ".#.", "...", ".#.", ".#."),
    "-": ("...", "...", "###", "...", "..."),
    "+": ("...", ".#.", "###", ".#.", "..."),
    "$": (".#.", "###", "##.", ".##", "##."),
    "%": ("#.#", "..#", ".#.", "#..", "#.#"),
    "/": ("..#", "..#", ".#.", "#..", "#.."),
    "(": ("..#", ".#.", ".#.", ".#.", "..#"),
    ")": ("#..", ".#.", ".#.", ".#.", "#.."),
    "!": (".#.", ".#.", ".#.", "...", ".#."),
    "?": ("##.", "..#", ".#.", "...", ".#."),
    "&": (".#.", "#.#", ".#.", "#.#", ".##"),
    '"': ("#.#", "#.#", "...", "...", "..."),
}


# ---------------------------------------------------------------- text
def draw_text(cv, x, y, s, scale, color, font=FONT5, cw=5, ch=7, gap=1):
    """Draw string s (uppercased) with top-left at (x, y). Returns width."""
    s = s.upper()
    step = (cw + gap) * scale
    cx = x
    for char in s:
        glyph = font.get(char, font[" "])
        for ry, row in enumerate(glyph):
            for rx, cell in enumerate(row):
                if cell == "#":
                    cv.rect(cx + rx * scale, y + ry * scale, scale, scale,
                            color)
        cx += step
    return step * len(s) - gap * scale if s else 0


def text_w(s, scale, font=FONT5, cw=5, gap=1):
    if not s:
        return 0
    return (cw + gap) * scale * len(s) - gap * scale


def draw_centered(cv, y, s, scale, color, font=FONT5, cw=5, ch=7, gap=1):
    w = text_w(s, scale, font, cw, gap)
    draw_text(cv, (W - w) // 2, y, s, scale, color, font, cw, ch, gap)
    return w


def wrap(s, max_chars):
    """Greedy word wrap to lines of at most max_chars characters."""
    lines = []
    cur = ""
    for word in s.upper().split():
        if len(word) > max_chars:  # hard-split very long words
            if cur:
                lines.append(cur)
                cur = ""
            while len(word) > max_chars:
                lines.append(word[:max_chars])
                word = word[max_chars:]
            cur = word
            continue
        trial = word if not cur else cur + " " + word
        if len(trial) <= max_chars:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(cv, x, y, s, scale, color, max_chars, leading, font=FONT5,
                 cw=5, ch=7):
    lines = wrap(s, max_chars)
    for i, ln in enumerate(lines):
        draw_text(cv, x, y + i * leading, ln, scale, color, font, cw, ch)
    return len(lines)


# ---------------------------------------------------------------- data
STRIP = [
    ("110+", "MISSILES FIRED AT UKRAINE"),
    ("2", "MISSILES DOWN IN POLAND"),
    ("-3.7%", "S&P 500 IN CORRECTION"),
    ("-5.3%", "NASDAQ ERASES 2026 GAIN"),
    ("$7.25BN", "BAYER ROUNDUP DEAL"),
    ("-69%", "DENGUE IN BRAZIL TRIAL"),
]

LEADS = [
    {
        "tag": "WARSAW, POLAND - WAR",
        "head": "Russian missiles come down inside Poland",
        "body": ("Two Russian missiles and a suspected drone fell in Poland "
                 "during a huge overnight barrage on Ukraine. PM Tusk calls "
                 "it a deliberate provocation; NATO's Rutte calls it a "
                 "grave violation."),
        "src": "(AP - Zark News)",
        "art": "poland",
    },
    {
        "tag": "ANTALYA - CLIMATE",
        "head": "COP31 runs into overtime over fossil fuels",
        "body": ("Delegates reject two draft deals; the second angers "
                 "countries by dropping any mention of a fossil-fuel "
                 "phase-out. A third text is drafted overnight."),
        "src": "(Zark News - One Turn)",
        "art": "cop",
    },
    {
        "tag": "NEW YORK - MARKETS",
        "head": "AI sell-off pushes Wall Street into correction",
        "body": ("The S&P 500 falls 3.7% and the Nasdaq 5.3%, erasing its "
                 "2026 gains, as the AI trade stumbles after Anthropic's "
                 "debut; Nvidia drops about 14%."),
        "src": "(AP - Argus)",
        "art": "chart",
    },
]

SHORTS = [
    ("KRYVYI RIH",
     "Russian missile hits Zelensky's hometown centre: 2 killed, 60 "
     "wounded; 117 of 148 drones downed.", "(One Turn)"),
    ("GUASAVE, MEXICO",
     "Mexico captures FBI most-wanted cartel boss 'El Chapo Isidro'; "
     "violence follows in Sinaloa.", "(PBS - One Turn)"),
    ("WASHINGTON",
     "Trump defends Shenzhen summit, calls China's nuclear buildup "
     "'hot and heavy'.", "(Morning Brief)"),
    ("GULF OF FINLAND",
     "Russian cargo ship hit by drones catches fire on its way to "
     "Kaliningrad.", "(Agencies)"),
    ("HORMUZ",
     "Two oil tankers hit mines near the Strait of Hormuz and burst "
     "into flames.", "(Reports)"),
    ("TBILISI",
     "Suspected gas blast partly collapses an apartment block: six "
     "killed, including a child.", "(World News)"),
    ("SEOUL",
     "Supreme Court overturns ex-PM Han's 15-year martial-law sentence; "
     "retrial ordered.", "(World News)"),
    ("SAN SALVADOR",
     "Bukele registers to run for a third term; election set for "
     "28 February 2027.", "(World News)"),
    ("ST. LOUIS",
     "Judge approves Bayer's $7.25bn Roundup settlement over cancer "
     "claims.", "(Zark News)"),
    ("WASHINGTON",
     "FBI crime database suffers a suspected breach; Trump calls it "
     "'not good'.", "(Reports)"),
    ("GENEVA",
     "UN talks agree to keep working on rules for AI weapons, the "
     "'killer robots' pact.", "(Japan Times)"),
    ("SPACE",
     "BepiColombo arrives at Mercury after its long cruise from Earth.",
     "(Headlines)"),
]

ALSO = [
    "Ukraine says 400+ drones fired overnight",
    "Berlin hosts Coalition of the Willing talks",
    "Trump weighs new strikes on Iran",
    "Appeals court lets US end TPS for 600,000 Venezuelans",
    "Court: $1.7tn spending bill passed unconstitutionally",
    "Honda and Toyota recall 1.6m cars over airbags",
    "Bitcoin bounces 9% to retake $60,000",
    "Dengue falls 69% in Brazil mosquito trial",
    "700,000 displaced in southern Ethiopia",
    "Salvadoran troops fight gangs in Haiti",
    "Turkey court seizes opposition Sozcu TV",
    "Bangladesh vows Rohingya compensation push",
    "Anthropic researcher: Claude solves maths riddle",
    "$22.5m train heist staggers investigators",
    "Japan wary of regular big-three summits",
]

DATE_CHECK = ("DATE CHECK - Every story on this page was first reported "
              "on Saturday 21 November 2026. Friday's and Sunday's news "
              "was left out on purpose.")
FOOTER = ("Sources named beside each story - One page, one day - "
          "Drawn entirely by program (Python standard library)")


# ---------------------------------------------------------------- art
def art_poland(cv, x, y, w, h):
    """Night sky, missile trails coming down, bursts over a town."""
    cv.rect(x, y, w, h, NIGHT)
    for sx, sy in ((30, 16), (90, 10), (210, 14), (268, 22), (150, 26)):
        cv.set(x + sx, y + sy, WHITE)
        cv.set(x + sx + 2, y + sy + 1, WHITE)
    cv.circle(x + w - 42, y + 22, 9, WHITE)  # moon
    # missile trails (descending diagonals) with warheads
    cv.line(x + 40, y + 6, x + 96, y + 58, RED, 2)
    cv.line(x + 120, y + 2, x + 176, y + 54, RED, 2)
    cv.line(x + 250, y + 8, x + 206, y + 56, RED, 2)
    for bx, by in ((100, 62), (180, 58), (202, 60)):
        cv.circle(x + bx, y + by, 4, GOLD)
        cv.line(x + bx - 9, y + by, x + bx + 9, y + by, GOLD, 1)
        cv.line(x + bx, y + by - 9, x + bx, y + by + 9, GOLD, 1)
    # town silhouette
    cv.rect(x, y + h - 22, w, 22, INK)
    for bx, bw, bh in ((8, 26, 14), (44, 18, 20), (120, 30, 12),
                       (196, 22, 18), (252, 34, 13)):
        cv.rect(x + bx, y + h - 22 - bh, bw, bh, INK)
    for wx, wy in ((16, h - 30), (52, h - 36), (206, h - 33), (266, h - 28)):
        cv.rect(x + wx, y + wy, 3, 3, GOLD)


def art_cop(cv, x, y, w, h):
    """A globe under a rising sun, with a thermometer climbing."""
    cv.rect(x, y, w, h, (222, 233, 240))
    cv.circle(x + 66, y + 58, 34, BLUE)          # globe
    cv.circle(x + 54, y + 46, 10, (90, 160, 90))  # land blobs
    cv.circle(x + 80, y + 68, 12, (90, 160, 90))
    cv.circle(x + 70, y + 82, 7, (90, 160, 90))
    cv.circle(x + w - 52, y + 30, 16, GOLD)       # sun
    for dx, dy in ((-24, 0), (24, 0), (0, -24), (0, 24), (-17, -17),
                   (17, -17), (-17, 17), (17, 17)):
        cv.line(x + w - 52 + dx, y + 30 + dy, x + w - 52 + dx * 2 // 3,
                y + 30 + dy * 2 // 3, GOLD, 2)
    # thermometer
    tx = x + w // 2 + 16
    cv.rect(tx, y + 18, 8, 62, INK)
    cv.rect(tx + 2, y + 24, 4, 40, RED)
    cv.circle(tx + 4, y + 86, 9, RED)
    cv.rect(x, y + h - 10, w, 10, (90, 160, 90))  # ground


def art_chart(cv, x, y, w, h):
    """Falling market chart: grid, red plunge line, dropping bars."""
    cv.rect(x, y, w, h, (250, 248, 242))
    for gx in range(30, w, 34):
        cv.line(x + gx, y + 8, x + gx, y + h - 8, (210, 208, 198), 1)
    for gy in range(12, h, 20):
        cv.line(x + 8, y + gy, x + w - 8, y + gy, (210, 208, 198), 1)
    pts = [(10, 26), (58, 20), (104, 34), (150, 30), (196, 52),
           (238, 66), (282, 88)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        cv.line(x + ax, y + ay, x + bx, y + by, RED, 3)
    for bx, bh in ((36, 18), (96, 26), (156, 40), (216, 56), (268, 74)):
        cv.rect(x + bx, y + h - 10 - bh, 22, bh, RED)
    cv.line(x + 8, y + h - 10, x + w - 8, y + h - 10, INK, 2)


ART = {"poland": art_poland, "cop": art_cop, "chart": art_chart}


# ---------------------------------------------------------------- page
M = 28            # page margin
IW = W - 2 * M    # inner width = 968


def rule(cv, y, color=INK, t=2):
    cv.rect(M, y, IW, t, color)


def draw_front_page():
    cv = Canvas(W, H, PAPER)

    # masthead
    rule(cv, 22)
    rule(cv, 27, t=1)
    draw_centered(cv, 38, "30 STORIES - 6 REGIONS - EVERY ONE DATED "
                          "SATURDAY 21 NOVEMBER 2026", 2, INK)
    rule(cv, 62, t=1)
    rule(cv, 66)
    draw_centered(cv, 80, "THE WORLD IN A DAY", 8, INK)
    draw_centered(cv, 148, "SATURDAY 21 NOVEMBER 2026 - One day of "
                           "world news on a single page", 2, INK)
    rule(cv, 172, t=1)
    rule(cv, 176)

    # numbers strip
    y = 188
    cell = IW // 6
    for i, (big, label) in enumerate(STRIP):
        cx = M + i * cell
        bw = text_w(big, 3)
        draw_text(cv, cx + (cell - bw) // 2, y, big, 3,
                  RED if i % 2 == 0 else INK)
        lines = wrap(label, 24)
        for j, ln in enumerate(lines[:2]):
            lw = text_w(ln, 1)
            draw_text(cv, cx + (cell - lw) // 2, y + 30 + j * 10, ln, 1,
                      INK)
        if i:
            cv.rect(cx - 1, y + 2, 1, 44, GRAY)
    rule(cv, y + 54)

    # lead stories
    y = 262
    col = (IW - 32) // 3
    for i, lead in enumerate(LEADS):
        cx = M + i * (col + 16)
        ART[lead["art"]](cv, cx, y, col, 110)
        cv.frame(cx, y, col, 110, INK, 2)
        ty = y + 118
        draw_text(cv, cx, ty, lead["tag"], 2, RED)
        n = draw_wrapped(cv, cx, ty + 20, lead["head"], 2, INK,
                         col // 12, 17)
        by = ty + 20 + n * 17 + 4
        nb = draw_wrapped(cv, cx, by, lead["body"], 1, INK, col // 6, 10)
        draw_text(cv, cx, by + nb * 10 + 3, lead["src"], 1, GRAY)
    rule(cv, 566)

    # short reports, 4 columns x 3 rows
    y = 580
    scol = (IW - 48) // 4
    rowh = 58
    for idx, (loc, text, src) in enumerate(SHORTS):
        cx = M + (idx % 4) * (scol + 16)
        cy = y + (idx // 4) * rowh
        draw_text(cv, cx, cy, loc, 1, RED)
        n = draw_wrapped(cv, cx, cy + 10, text, 1, INK, scol // 6, 9)
        draw_text(cv, cx, cy + 10 + n * 9 + 2, src, 1, GRAY)
    rule(cv, y + 3 * rowh + 4)

    # also on saturday
    y = y + 3 * rowh + 16
    draw_text(cv, M, y, "ALSO ON SATURDAY 21 NOVEMBER", 2, RED)
    y += 22
    half = (len(ALSO) + 1) // 2
    colw = (IW - 24) // 2
    for j, colitems in enumerate((ALSO[:half], ALSO[half:])):
        cx = M + j * (colw + 24)
        for k, item in enumerate(colitems):
            iy = y + k * 17
            cv.rect(cx, iy + 3, 5, 5, RED)
            draw_text(cv, cx + 12, iy, item, 2, INK, FONT3, 3, 5)
    y += half * 17 + 10

    # date check box
    cv.frame(M, y, IW, 48, RED, 2)
    lines = wrap(DATE_CHECK, 76)
    for i, ln in enumerate(lines[:2]):
        lw = text_w(ln, 2)
        draw_text(cv, (W - lw) // 2, y + 8 + i * 16, ln, 2, RED)
    y += 62

    draw_centered(cv, y, FOOTER, 1, GRAY)
    rule(cv, y + 16, t=1)
    rule(cv, y + 20)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    cv = draw_front_page()
    data = png_bytes(W, H, cv.px)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes)" % (path, len(data)))


if __name__ == "__main__":
    main()
