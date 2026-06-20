#!/usr/bin/env python3
"""Generate results/qNN_*.png from live sqlite3 execution (DBeaver-style grid)."""

from __future__ import annotations

import sqlite3
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "library.db"
RESULTS = ROOT / "results"
SCHEMA = ROOT / "sql" / "01_schema.sql"
SEED = ROOT / "sql" / "02_seed.sql"

FONT_PATH = "/System/Library/Fonts/Menlo.ttc"
PAD = 12
ROW_H = 22
HEADER_H = 28
TITLE_H = 36
MSG_H = 28
FOOTER_H = 24
MAX_ROWS = 12
MAX_COL_W = 280
MIN_COL_W = 60

CAPTURES = [
    (
        1,
        "members_by_joined_desc",
        "Query 01: List all members sorted by joined_at (most recent first).",
        """SELECT id, name, email, joined_at
FROM member
ORDER BY joined_at DESC;""",
        "select",
    ),
    (
        2,
        "books_published_2015_or_later",
        "Query 02: Books published in or after 2015, ordered by year then title.",
        """SELECT id, title, author, published_year
FROM book
WHERE published_year >= 2015
ORDER BY published_year ASC, title ASC;""",
        "select",
    ),
    (
        3,
        "top5_recent_rentals",
        "Query 03: Top 5 most recently rented books, newest rental first.",
        """SELECT b.id, b.title, b.author, r.rented_at
FROM rental r
INNER JOIN book b ON b.id = r.book_id
ORDER BY r.rented_at DESC
LIMIT 5;""",
        "select",
    ),
    (
        4,
        "members_example_com_email",
        "Query 04: Members whose email ends with @example.com.",
        """SELECT id, name, email
FROM member
WHERE email LIKE '%@example.com';""",
        "select",
    ),
    (
        5,
        "rental_member_book_inner_join",
        "Query 05: Each rental with member name and book title (INNER JOIN).",
        """SELECT r.id, m.name AS member_name, b.title AS book_title, r.rented_at, r.due_at
FROM rental r
INNER JOIN member m ON m.id = r.member_id
INNER JOIN book b ON b.id = r.book_id
ORDER BY r.rented_at DESC;""",
        "select",
    ),
    (
        6,
        "book_with_category_inner_join",
        "Query 06: Each book with its category name (INNER JOIN).",
        """SELECT b.id, b.title, b.author, c.name AS category_name
FROM book b
INNER JOIN category c ON c.id = b.category_id
ORDER BY c.name ASC, b.title ASC;""",
        "select",
    ),
    (
        7,
        "member_rental_count_left_join",
        "Query 07: All members and rental counts, including zero rentals (LEFT JOIN).",
        """SELECT m.id, m.name, COUNT(r.id) AS rental_count
FROM member m
LEFT JOIN rental r ON r.member_id = m.id
GROUP BY m.id, m.name
ORDER BY rental_count DESC, m.name ASC;""",
        "select",
    ),
    (
        8,
        "open_rentals_currently_out",
        "Query 08: Currently open rentals (returned_at IS NULL).",
        """SELECT r.id, m.name AS member_name, b.title AS book_title, r.rented_at, r.due_at
FROM rental r
INNER JOIN member m ON m.id = r.member_id
INNER JOIN book b ON b.id = r.book_id
WHERE r.returned_at IS NULL
ORDER BY r.rented_at DESC;""",
        "select",
    ),
    (
        9,
        "books_per_category_count",
        "Query 09: Number of books per category, sorted descending.",
        """SELECT c.name AS category, COUNT(b.id) AS book_count
FROM category c
LEFT JOIN book b ON b.category_id = c.id
GROUP BY c.id, c.name
ORDER BY book_count DESC, c.name ASC;""",
        "select",
    ),
    (
        10,
        "rentals_per_member_having",
        "Query 10: Rentals per member, only members with more than one rental.",
        """SELECT m.id, m.name, COUNT(r.id) AS rental_count
FROM member m
INNER JOIN rental r ON r.member_id = m.id
GROUP BY m.id, m.name
HAVING COUNT(r.id) > 1
ORDER BY rental_count DESC;""",
        "select",
    ),
    (
        11,
        "avg_rental_duration_per_category",
        "Query 11: Average rental duration in days per category (returned only).",
        """SELECT c.name AS category,
       ROUND(AVG(julianday(r.returned_at) - julianday(r.rented_at)), 1) AS avg_days
FROM rental r
INNER JOIN book b ON b.id = r.book_id
INNER JOIN category c ON c.id = b.category_id
WHERE r.returned_at IS NOT NULL
GROUP BY c.id, c.name
ORDER BY avg_days DESC;""",
        "select",
    ),
    (
        12,
        "members_above_avg_rentals_subquery",
        "Query 12: Members who rented more than the average member (subquery).",
        """SELECT m.id, m.name, COUNT(r.id) AS rental_count
FROM member m
LEFT JOIN rental r ON r.member_id = m.id
GROUP BY m.id, m.name
HAVING COUNT(r.id) > (
  SELECT AVG(per_member.cnt)
  FROM (SELECT COUNT(*) AS cnt FROM rental GROUP BY member_id) AS per_member
)
ORDER BY rental_count DESC;""",
        "select",
    ),
]


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except OSError:
        return ImageFont.load_default()


def truncate(text: str, max_px: int, font: ImageFont.ImageFont, draw: ImageDraw.ImageDraw) -> str:
    s = str(text) if text is not None else ""
    if draw.textlength(s, font=font) <= max_px:
        return s
    while s and draw.textlength(s + "…", font=font) > max_px:
        s = s[:-1]
    return (s + "…") if s else "…"


def reset_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA.read_text())
    conn.executescript(SEED.read_text())
    conn.commit()


def run_select(conn: sqlite3.Connection, sql: str) -> tuple[list[str], list[tuple]]:
    cur = conn.execute(sql)
    cols = [d[0] for d in cur.description] if cur.description else []
    rows = cur.fetchall()
    return cols, rows


def col_widths(
    cols: list[str],
    rows: list[tuple],
    font: ImageFont.ImageFont,
    data_font: ImageFont.ImageFont,
    draw: ImageDraw.ImageDraw,
) -> list[int]:
    widths = []
    for i, col in enumerate(cols):
        w = int(draw.textlength(col, font=font)) + 16
        for row in rows[:MAX_ROWS]:
            cell = truncate(str(row[i]), MAX_COL_W, data_font, draw)
            w = max(w, int(draw.textlength(cell, font=data_font)) + 16)
        widths.append(min(max(w, MIN_COL_W), MAX_COL_W))
    return widths


def render_select(
    title: str,
    sql: str,
    cols: list[str],
    rows: list[tuple],
    out_path: Path,
) -> None:
    title_font = load_font(11)
    sql_font = load_font(9)
    header_font = load_font(10)
    data_font = load_font(10)
    footer_font = load_font(9)

    tmp = Image.new("RGB", (1, 1))
    draw_tmp = ImageDraw.Draw(tmp)

    display_rows = rows[:MAX_ROWS]
    widths = col_widths(cols, rows, header_font, data_font, draw_tmp)
    table_w = sum(widths)
    img_w = max(table_w + PAD * 2, 720)

    sql_lines = textwrap.wrap(sql.strip(), width=95)
    sql_block_h = len(sql_lines) * 14 + 8
    body_h = HEADER_H + ROW_H * len(display_rows) + FOOTER_H
    img_h = TITLE_H + sql_block_h + body_h + PAD * 2

    img = Image.new("RGB", (img_w, img_h), "#f4f6f8")
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, img_w, TITLE_H], fill="#2b579a")
    draw.text((PAD, 10), title, fill="white", font=title_font)

    y = TITLE_H + 6
    for line in sql_lines:
        draw.text((PAD, y), line, fill="#333", font=sql_font)
        y += 14
    y += 4

    x0 = PAD
    for i, col in enumerate(cols):
        draw.rectangle([x0, y, x0 + widths[i], y + HEADER_H], fill="#d6e4f5", outline="#aab")
        draw.text(
            (x0 + 8, y + 6),
            truncate(col, widths[i] - 12, header_font, draw),
            fill="#111",
            font=header_font,
        )
        x0 += widths[i]

    y += HEADER_H
    for ri, row in enumerate(display_rows):
        x0 = PAD
        bg = "#fff" if ri % 2 == 0 else "#f9fafb"
        for i, val in enumerate(row):
            draw.rectangle([x0, y, x0 + widths[i], y + ROW_H], fill=bg, outline="#dde")
            cell = truncate(str(val), widths[i] - 12, data_font, draw)
            draw.text((x0 + 8, y + 5), cell, fill="#111", font=data_font)
            x0 += widths[i]
        y += ROW_H

    shown = len(display_rows)
    total = len(rows)
    footer = f"Rows: {shown} shown" + (f" of {total}" if total > shown else f" (total {total})")
    draw.text((PAD, y + 4), footer, fill="#555", font=footer_font)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG", optimize=True)


def render_mutation(
    title: str,
    sql: str,
    message: str,
    verify_title: str,
    verify_sql: str,
    cols: list[str],
    rows: list[tuple],
    out_path: Path,
) -> None:
    title_font = load_font(11)
    sql_font = load_font(9)
    msg_font = load_font(10)
    header_font = load_font(10)
    data_font = load_font(10)
    footer_font = load_font(9)

    tmp = Image.new("RGB", (1, 1))
    draw_tmp = ImageDraw.Draw(tmp)
    widths = col_widths(cols, rows, header_font, data_font, draw_tmp)
    table_w = sum(widths)
    img_w = max(table_w + PAD * 2, 720)

    sql_lines = textwrap.wrap(sql.strip(), width=95)
    verify_lines = textwrap.wrap(verify_sql.strip(), width=95)
    block_h = (len(sql_lines) + len(verify_lines)) * 14 + MSG_H + 16
    body_h = HEADER_H + ROW_H * max(len(rows), 1) + FOOTER_H
    img_h = TITLE_H + block_h + body_h + PAD * 2

    img = Image.new("RGB", (img_w, img_h), "#f4f6f8")
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, img_w, TITLE_H], fill="#2b579a")
    draw.text((PAD, 10), title, fill="white", font=title_font)

    y = TITLE_H + 6
    for line in sql_lines:
        draw.text((PAD, y), line, fill="#333", font=sql_font)
        y += 14
    y += 4
    draw.rectangle([PAD, y, img_w - PAD, y + MSG_H], fill="#e8f5e9", outline="#81c784")
    draw.text((PAD + 8, y + 6), message, fill="#1b5e20", font=msg_font)
    y += MSG_H + 8
    draw.text((PAD, y), verify_title, fill="#444", font=sql_font)
    y += 14
    for line in verify_lines:
        draw.text((PAD, y), line, fill="#333", font=sql_font)
        y += 14
    y += 4

    x0 = PAD
    for i, col in enumerate(cols):
        draw.rectangle([x0, y, x0 + widths[i], y + HEADER_H], fill="#d6e4f5", outline="#aab")
        draw.text((x0 + 8, y + 6), col, fill="#111", font=header_font)
        x0 += widths[i]
    y += HEADER_H
    for ri, row in enumerate(rows):
        x0 = PAD
        bg = "#fff" if ri % 2 == 0 else "#f9fafb"
        for i, val in enumerate(row):
            draw.rectangle([x0, y, x0 + widths[i], y + ROW_H], fill=bg, outline="#dde")
            draw.text((x0 + 8, y + 5), truncate(str(val), widths[i] - 12, data_font, draw), fill="#111", font=data_font)
            x0 += widths[i]
        y += ROW_H
    draw.text((PAD, y + 4), f"Rows: {len(rows)}", fill="#555", font=footer_font)
    img.save(out_path, "PNG", optimize=True)


def render_index(
    title: str,
    create_sql: str,
    create_msg: str,
    pragma_cols: list[str],
    pragma_rows: list[tuple],
    out_path: Path,
) -> None:
    title_font = load_font(11)
    sql_font = load_font(9)
    msg_font = load_font(10)
    header_font = load_font(10)
    data_font = load_font(10)

    tmp = Image.new("RGB", (1, 1))
    draw_tmp = ImageDraw.Draw(tmp)
    widths = col_widths(pragma_cols, pragma_rows, header_font, data_font, draw_tmp)
    img_w = max(sum(widths) + PAD * 2, 720)
    img_h = TITLE_H + 120 + HEADER_H + ROW_H * len(pragma_rows) + PAD * 2

    img = Image.new("RGB", (img_w, img_h), "#f4f6f8")
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, img_w, TITLE_H], fill="#2b579a")
    draw.text((PAD, 10), title, fill="white", font=title_font)

    y = TITLE_H + 8
    for line in textwrap.wrap(create_sql.strip(), width=95):
        draw.text((PAD, y), line, fill="#333", font=sql_font)
        y += 14
    y += 6
    draw.rectangle([PAD, y, img_w - PAD, y + MSG_H], fill="#e8f5e9", outline="#81c784")
    draw.text((PAD + 8, y + 6), create_msg, fill="#1b5e20", font=msg_font)
    y += MSG_H + 12
    draw.text((PAD, y), "PRAGMA index_list('rental');", fill="#333", font=sql_font)
    y += 18

    x0 = PAD
    for i, col in enumerate(pragma_cols):
        draw.rectangle([x0, y, x0 + widths[i], y + HEADER_H], fill="#d6e4f5", outline="#aab")
        draw.text((x0 + 8, y + 6), col, fill="#111", font=header_font)
        x0 += widths[i]
    y += HEADER_H
    for ri, row in enumerate(pragma_rows):
        x0 = PAD
        bg = "#fff" if ri % 2 == 0 else "#f9fafb"
        for i, val in enumerate(row):
            draw.rectangle([x0, y, x0 + widths[i], y + ROW_H], fill=bg, outline="#dde")
            draw.text((x0 + 8, y + 5), str(val), fill="#111", font=data_font)
            x0 += widths[i]
        y += ROW_H
    img.save(out_path, "PNG", optimize=True)


def main() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    reset_db(conn)

    for num, slug, title, sql, _kind in CAPTURES:
        cols, rows = run_select(conn, sql)
        out = RESULTS / f"q{num:02d}_{slug}.png"
        render_select(title, sql, cols, rows, out)
        print(f"Wrote {out.name} ({len(rows)} rows)")

    # Query 13
    q13_sql = """UPDATE rental
SET returned_at = CURRENT_TIMESTAMP
WHERE id = 2 AND returned_at IS NULL;"""
    cur = conn.execute(q13_sql)
    conn.commit()
    msg13 = f"Updated rows: {cur.rowcount}"
    v13_sql = "SELECT id, returned_at FROM rental WHERE id = 2;"
    cols, rows = run_select(conn, v13_sql)
    render_mutation(
        "Query 13: Mark open rental #2 as returned (UPDATE).",
        q13_sql,
        msg13,
        "Verification:",
        v13_sql,
        cols,
        rows,
        RESULTS / "q13_update_return_rental.png",
    )
    print("Wrote q13_update_return_rental.png")

    # Query 14
    count_before = conn.execute(
        "SELECT COUNT(*) FROM rental WHERE returned_at IS NOT NULL "
        "AND rented_at < date('now', '-1 year')"
    ).fetchone()[0]
    q14_sql = """DELETE FROM rental
WHERE returned_at IS NOT NULL
  AND rented_at < date('now', '-1 year');"""
    cur = conn.execute(q14_sql)
    conn.commit()
    msg14 = f"Deleted rows: {cur.rowcount} (eligible before delete: {count_before})"
    v14_sql = (
        "SELECT COUNT(*) AS remaining_old_returned FROM rental "
        "WHERE returned_at IS NOT NULL AND rented_at < date('now', '-1 year');"
    )
    cols, rows = run_select(conn, v14_sql)
    render_mutation(
        "Query 14: Archive returned rentals older than one year (DELETE).",
        q14_sql,
        msg14,
        "Verification:",
        v14_sql,
        cols,
        rows,
        RESULTS / "q14_delete_archive_old_rentals.png",
    )
    print("Wrote q14_delete_archive_old_rentals.png")

    # Query 15
    q15_sql = """CREATE INDEX IF NOT EXISTS idx_rental_member_rented
  ON rental(member_id, rented_at);"""
    conn.execute(q15_sql)
    conn.commit()
    pragma_cols = ["seq", "name", "unique", "origin", "partial"]
    pragma_rows = conn.execute("PRAGMA index_list('rental')").fetchall()
    render_index(
        "Query 15: CREATE INDEX on rental(member_id, rented_at).",
        q15_sql,
        "Query executed successfully.",
        pragma_cols,
        pragma_rows,
        RESULTS / "q15_create_index_done.png",
    )
    print("Wrote q15_create_index_done.png")

    conn.close()
    if (ROOT / "results" / ".gitkeep").exists():
        (ROOT / "results" / ".gitkeep").unlink()


if __name__ == "__main__":
    main()
