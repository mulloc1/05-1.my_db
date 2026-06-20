#!/usr/bin/env python3
"""Generate docs/erd.png for the library schema."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "erd.png"
FONT_PATH = "/System/Library/Fonts/Helvetica.ttc"

W, H = 900, 540
HEADER_H = 28
ROW_H = 20
PAD_TOP = 36
PAD_BOTTOM = 16


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except OSError:
        return ImageFont.load_default()


def measure_table_height(
    draw: ImageDraw.ImageDraw,
    columns: list[str],
    box_font: ImageFont.ImageFont,
    extra_bottom: int = 0,
) -> int:
    cy = HEADER_H + PAD_TOP
    for col in columns:
        bbox = draw.textbbox((0, 0), col, font=box_font)
        line_h = bbox[3] - bbox[1]
        cy += max(line_h + 6, ROW_H)
    return cy + PAD_BOTTOM + extra_bottom


def draw_table(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    w: int,
    name: str,
    columns: list[str],
    fonts: tuple,
    extra_bottom: int = 0,
) -> int:
    """Draw table; return bottom y coordinate."""
    title_font, box_font = fonts
    h = measure_table_height(draw, columns, box_font, extra_bottom)
    draw.rectangle([x, y, x + w, y + h], fill="white", outline="#333", width=2)
    draw.rectangle([x, y, x + w, y + HEADER_H], fill="#2563eb", outline="#333", width=2)
    draw.text((x + 8, y + 6), name, fill="white", font=title_font)
    cy = y + PAD_TOP
    for col in columns:
        bbox = draw.textbbox((x + 8, cy), col, font=box_font)
        draw.text((x + 8, cy), col, fill="#111", font=box_font)
        line_h = bbox[3] - bbox[1]
        cy += max(line_h + 6, ROW_H)
    return y + h


def draw_arrow(
    draw: ImageDraw.ImageDraw,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    label: str,
    rel_font: ImageFont.ImageFont,
    label_pos: str = "mid",
) -> None:
    draw.line([(x1, y1), (x2, y2)], fill="#555", width=2)
    angle = math.atan2(y2 - y1, x2 - x1)
    ah = 10
    a1 = angle + math.pi * 0.85
    a2 = angle - math.pi * 0.85
    draw.polygon(
        [
            (x2, y2),
            (x2 + ah * math.cos(a1), y2 + ah * math.sin(a1)),
            (x2 + ah * math.cos(a2), y2 + ah * math.sin(a2)),
        ],
        fill="#555",
    )
    lx = (x1 + x2) // 2
    ly = (y1 + y2) // 2
    if label_pos == "above":
        ly -= 14
    elif label_pos == "below":
        ly += 4
    tw = draw.textlength(label, font=rel_font)
    draw.rectangle(
        [lx - tw / 2 - 4, ly - 8, lx + tw / 2 + 4, ly + 10],
        fill="#f8f9fa",
        outline="#ccc",
    )
    draw.text((lx - tw / 2, ly - 6), label, fill="#c2410c", font=rel_font)


def main() -> None:
    img = Image.new("RGB", (W, H), "#f8f9fa")
    draw = ImageDraw.Draw(img)
    title_font = load_font(14)
    box_font = load_font(11)
    rel_font = load_font(10)

    draw.text(
        (20, 12),
        "Library ERD — category ──< book ──< rental >── member",
        fill="#333",
        font=title_font,
    )

    category_cols = [
        "id INTEGER PK",
        "name TEXT UNIQUE NOT NULL",
        "description TEXT",
    ]
    book_cols = [
        "id INTEGER PK",
        "title TEXT NOT NULL",
        "author TEXT NOT NULL",
        "isbn TEXT UNIQUE",
        "published_year INTEGER",
        "category_id FK → category",
    ]
    member_cols = [
        "id INTEGER PK",
        "name TEXT NOT NULL",
        "email TEXT UNIQUE NOT NULL",
        "phone TEXT",
        "joined_at DATETIME NOT NULL",
    ]
    rental_cols = [
        "id INTEGER PK",
        "member_id FK → member",
        "book_id FK → book",
        "rented_at DATETIME NOT NULL",
        "due_at DATE NOT NULL",
        "returned_at DATETIME",
    ]

    cat_bottom = draw_table(draw, 40, 60, 200, "category", category_cols, (title_font, box_font))
    book_bottom = draw_table(
        draw, 340, 60, 220, "book", book_cols, (title_font, box_font), extra_bottom=12
    )
    member_bottom = draw_table(draw, 620, 60, 220, "member", member_cols, (title_font, box_font))

    rental_y = max(book_bottom, member_bottom) + 50
    rental_bottom = draw_table(
        draw, 340, rental_y, 240, "rental", rental_cols, (title_font, box_font)
    )

    draw_arrow(draw, 240, (60 + cat_bottom) // 2, 340, 60 + HEADER_H // 2, "1 : N", rel_font, "above")
    draw_arrow(
        draw,
        450,
        book_bottom,
        450,
        rental_y,
        "1 : N",
        rel_font,
        "right",
    )
    draw_arrow(
        draw,
        620,
        (60 + member_bottom) // 2,
        580,
        rental_y + HEADER_H // 2,
        "1 : N",
        rel_font,
        "below",
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG")
    tmp = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    book_h = measure_table_height(tmp, book_cols, box_font, extra_bottom=12)
    print(f"Saved {OUT} (book table height={book_h}px)")


if __name__ == "__main__":
    main()
