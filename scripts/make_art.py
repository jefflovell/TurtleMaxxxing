"""Draws the project's pixel art with only Python's standard library.

    uv run --directory backend python ../scripts/make_art.py

Writes:
  assets/turtle-i-like-turtles.png  the README banner: the turtle centered over "I like turtles"
  assets/social-preview.png         1280x640 link-preview card (upload it in the repo's
                                    Settings > General > Social preview)
"""

import struct
import zlib
from pathlib import Path

ASSETS = Path(__file__).resolve().parents[1] / "assets"

# The same turtle as assets/turtle.png and the app icon.
TURTLE = [
    "......KKKKKK........",
    "....KKGGgGGgKK......",
    "...KGgGGGGgGGGK.KKK.",
    "..KGGGgGGGGgGGGKSSSK",
    "..KGgGGGgGGGgGGKSWkK",
    ".KGGGGgGGGGgGGGGKSSK",
    "KYYYYYYYYYYYYYYYKSSK",
    "KSKKKKKKKKKKKKKKSSK.",
    ".KKSSK.KSSK.KSSKKK..",
    "...KKK..KK...KKK....",
]

CLEAR = (0, 0, 0, 0)
COLORS = {
    "K": (27, 42, 27, 255),     # outline
    "G": (63, 163, 77, 255),    # shell
    "g": (42, 107, 51, 255),    # shell pattern
    "S": (155, 224, 122, 255),  # skin
    "W": (255, 255, 255, 255),  # eye shine
    "k": (0, 0, 0, 255),        # eye
    "Y": (232, 197, 71, 255),   # shell rim
}
CREAM = (246, 241, 222, 255)

# A small pixel font, 7 pixels tall plus 2 below the line for g, p and y.
# Just the letters the art uses.
FONT = {
    "I": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "a": [".....", ".....", ".###.", "....#", ".####", "#...#", ".####"],
    "c": [".....", ".....", ".###.", "#....", "#....", "#...#", ".###."],
    "e": [".....", ".....", ".###.", "#...#", "#####", "#....", ".###."],
    "f": ["..##.", ".#...", "####.", ".#...", ".#...", ".#...", ".#..."],
    "g": [".....", ".....", ".####", "#...#", "#...#", "#...#", ".####", "....#", ".###."],
    "i": ["..#..", ".....", ".##..", "..#..", "..#..", "..#..", ".###."],
    "k": ["#....", "#....", "#..#.", "#.#..", "##...", "#.#..", "#..#."],
    "l": [".##..", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "n": [".....", ".....", "#.##.", "##..#", "#...#", "#...#", "#...#"],
    "o": [".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."],
    "p": [".....", ".....", "####.", "#...#", "#...#", "#...#", "####.", "#....", "#...."],
    "r": [".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."],
    "s": [".....", ".....", ".####", "#....", ".###.", "....#", "####."],
    "t": ["..#..", "..#..", "#####", "..#..", "..#..", "..#.#", "...#."],
    "u": [".....", ".....", "#...#", "#...#", "#...#", "#..##", ".##.#"],
    "v": [".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "x": [".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"],
    "y": [".....", ".....", "#...#", "#...#", "#...#", "#...#", ".####", "....#", ".###."],
    "-": ["....", "....", "....", ".##.", "....", "....", "...."],
    ".": [".", ".", ".", ".", ".", ".", "#"],
    "·": [".", ".", ".", "#", ".", ".", "."],
    " ": ["...", "...", "...", "...", "...", "...", "..."],
}


class Canvas:
    def __init__(self, width: int, height: int, background=CLEAR):
        self.width, self.height = width, height
        self.px = [[background] * width for _ in range(height)]

    def block(self, x: int, y: int, size: int, color) -> None:
        for yy in range(max(0, y), min(self.height, y + size)):
            row = self.px[yy]
            for xx in range(max(0, x), min(self.width, x + size)):
                row[xx] = color

    def sprite(self, rows: list[str], x: int, y: int, scale: int) -> None:
        for r, line in enumerate(rows):
            for c, ch in enumerate(line):
                if ch in COLORS:
                    self.block(x + c * scale, y + r * scale, scale, COLORS[ch])

    def text(self, text: str, x: int, y: int, scale: int, fill, outline=None) -> None:
        """Pixel text. With an outline, each letter gets a 1-pixel border, so it reads on light and dark."""
        lit = set()
        cx = 0
        for ch in text:
            glyph = FONT[ch]
            for r, line in enumerate(glyph):
                for c, on in enumerate(line):
                    if on == "#":
                        lit.add((cx + c, r))
            cx += len(glyph[0]) + 1
        if outline:
            for gx, gy in lit:
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        self.block(x + (gx + dx) * scale, y + (gy + dy) * scale, scale, outline)
        for gx, gy in lit:
            self.block(x + gx * scale, y + gy * scale, scale, fill)

    def save(self, path: Path) -> None:
        raw = b"".join(b"\x00" + b"".join(bytes(p) for p in row) for row in self.px)

        def chunk(tag: bytes, data: bytes) -> bytes:
            return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))

        png = b"\x89PNG\r\n\x1a\n"
        png += chunk(b"IHDR", struct.pack(">IIBBBBB", self.width, self.height, 8, 6, 0, 0, 0))
        png += chunk(b"IDAT", zlib.compress(raw, 9))
        png += chunk(b"IEND", b"")
        path.write_bytes(png)


def text_width(text: str) -> int:
    """Width in font pixels, without an outline."""
    return sum(len(FONT[ch][0]) + 1 for ch in text) - 1


def banner() -> Canvas:
    """The turtle centered over "I like turtles", transparent so it suits GitHub's light and dark themes."""
    words, unit = "I like turtles", 5             # one font pixel = 5x5 screen pixels
    turtle_scale = unit * 2                       # the turtle is drawn at twice the text's pixel size
    text_w = (text_width(words) + 2) * unit       # +2 for the outline on each side
    turtle_w, turtle_h = len(TURTLE[0]) * turtle_scale, len(TURTLE) * turtle_scale
    pad = unit * 2
    width = max(text_w, turtle_w) + pad * 2
    height = pad + turtle_h + unit * 3 + 9 * unit + pad
    canvas = Canvas(width, height)
    canvas.sprite(TURTLE, (width - turtle_w) // 2, pad, turtle_scale)
    canvas.text(words, (width - text_w) // 2 + unit, pad + turtle_h + unit * 4,
                unit, COLORS["G"], outline=COLORS["K"])
    return canvas


def social_card() -> Canvas:
    """1280x640, the size GitHub recommends for link previews."""
    width, height = 1280, 640
    canvas = Canvas(width, height, CREAM)
    title, subtitle, motto = "TurtleMaxxxing", "local-first · private · yours", "I like turtles."
    turtle_scale, title_scale, small = 14, 10, 5
    turtle_h = len(TURTLE) * turtle_scale
    # Lines with g, p or y reach 9 font pixels down; the rest stop at 7.
    block_h = turtle_h + 40 + 9 * title_scale + 24 + 9 * small + 16 + 7 * small
    y = (height - block_h) // 2
    canvas.sprite(TURTLE, (width - len(TURTLE[0]) * turtle_scale) // 2, y, turtle_scale)
    y += turtle_h + 40
    canvas.text(title, (width - text_width(title) * title_scale) // 2, y, title_scale, COLORS["K"])
    y += 9 * title_scale + 24
    canvas.text(subtitle, (width - text_width(subtitle) * small) // 2, y, small, COLORS["g"])
    y += 9 * small + 16
    canvas.text(motto, (width - text_width(motto) * small) // 2, y, small, COLORS["G"])
    return canvas


if __name__ == "__main__":
    banner().save(ASSETS / "turtle-i-like-turtles.png")
    social_card().save(ASSETS / "social-preview.png")
    for name in ("turtle-i-like-turtles.png", "social-preview.png"):
        print(name, (ASSETS / name).stat().st_size, "bytes")
