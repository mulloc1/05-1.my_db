# Phase 2 — Seed Data (`02_seed.sql`)

> Parent plan: [`docs/plan.md`](../plan.md) §6 Phase 2
> Subject reference: [`docs/subject.md`](../subject.md) §2.3, §4.4

This phase populates the four tables from Phase 1 with realistic data so the Phase 3 queries return non-trivial results. Following `plan.md` §2's row-count lock: **10–15 rows** per parent table (`category`, `book`, `member`) and **20–30** `rental` rows. Parents are inserted before children (subject §4.4); FK values reference real parent IDs; the rental set deliberately mixes returned and open rentals so query #8 / #11 / #13 in Phase 3 have non-empty results.

---

## 1. Goal

- Author `sql/02_seed.sql` so that, after running `01_schema.sql` then `02_seed.sql` against a fresh DB, every table has at least 10 rows with realistic FK linkage.
- Order inserts as `category → book → member → rental` so the FK enforcement enabled in Phase 1 never blocks an insert.
- Cover the **business-state matrix** the Phase 3 queries need:
  - At least one category with **no books** (so query #9 has a "0 books" row if you also `LEFT JOIN`; safe to skip if all categories are used).
  - At least one member with **zero rentals** (so query #7's LEFT JOIN demonstrates a zero count).
  - A mix of **returned** (`returned_at IS NOT NULL`) and **open** rentals (`returned_at IS NULL`) so queries #8 and #11 both work.
  - At least one rental older than the cutoff used by query #14's DELETE (e.g. > 1 year ago).

---

## 2. Scope (In / Out)

**In scope**
- `PRAGMA foreign_keys = ON;` repeated at the top (per `plan.md` §8 risk #1).
- `DELETE FROM` block in **reverse** dependency order so re-running the seed against an already-populated DB is safe and idempotent.
- `INSERT INTO category VALUES ...` (10–15 rows).
- `INSERT INTO book VALUES ...` (10–15 rows) referencing real `category.id` values.
- `INSERT INTO member VALUES ...` (10–15 rows) with realistic emails (UNIQUE).
- `INSERT INTO rental VALUES ...` (20–30 rows) referencing real `book.id` / `member.id`.
- Header comment summarizing row counts and the business-state coverage above.

**Out of scope**
- Any schema change (Phase 1 owns it).
- Any `SELECT` / aggregate (Phase 3).
- Any `CREATE INDEX` (Phase 3 query #15).
- Auto-generation via scripts — the seed is hand-written so it stays reviewable as a SQL artifact. (If row counts grow past ~50 per table, revisit; not in scope here.)
- Real PII — emails and phone numbers must be obviously fake (`@example.com`, `010-0000-XXXX`).

---

## 3. Tasks

### 3.1 File header
Top of `sql/02_seed.sql`:

```sql
-- 02_seed.sql — Sample data for the library domain
-- Run order: 01_schema.sql → 02_seed.sql → 03_queries.sql
-- Row counts: category=12, book=15, member=12, rental=25 (≥ subject §4.4 minimum of 10/table)
-- SQLite-specific: PRAGMA foreign_keys = ON; (must be ON or FKs are silently ignored)

PRAGMA foreign_keys = ON;

-- Clear in reverse dependency order so re-running is safe.
DELETE FROM rental;
DELETE FROM book;
DELETE FROM member;
DELETE FROM category;
```

Exact counts in the header comment are confirmed during implementation; pick numbers that match the actual file.

### 3.2 `category` inserts
- 10–15 rows. Use stable, recognizable category names so Phase 3 query results are easy to eyeball.
- Suggested labels: `Fiction`, `Non-fiction`, `Science`, `History`, `Technology`, `Biography`, `Children`, `Cooking`, `Travel`, `Art`, `Philosophy`, `Reference`.
- Pattern:

```sql
INSERT INTO category (id, name, description) VALUES
  (1,  'Fiction',     'Novels and short stories'),
  (2,  'Non-fiction', 'Essays, journalism, and general non-fiction'),
  (3,  'Science',     'Natural and applied sciences'),
  -- … remaining rows …
  (12, 'Reference',   'Dictionaries and encyclopedias');
```

- Hard-coding `id` values keeps FK references in later inserts deterministic and reviewable.

### 3.3 `book` inserts
- 10–15 rows. Each book has a real `category_id` from §3.2 (test FK by intent, not accident).
- `isbn` must be UNIQUE — use plausible 13-digit strings (`'978-0-13-468599-1'` etc.); two books may share `category_id`, none may share `isbn`.
- Spread books across at least **5** distinct categories so query #9 (books per category) returns interesting variation.
- Pattern:

```sql
INSERT INTO book (id, title, author, isbn, published_year, category_id) VALUES
  (1,  'Clean Code',           'Robert C. Martin',  '978-0-13-235088-4', 2008, 5),
  (2,  'The Pragmatic Programmer', 'Andrew Hunt',   '978-0-201-61622-4', 1999, 5),
  (3,  'A Brief History of Time', 'Stephen Hawking','978-0-553-38016-3', 1998, 3),
  -- … remaining rows …
  (15, 'The Art of War',        'Sun Tzu',           '978-1-59030-963-7', 2005, 4);
```

### 3.4 `member` inserts
- 10–15 rows. `email` is UNIQUE; use `firstname.lastname@example.com` style so the LIKE query #4 has a guaranteed hit.
- Vary `joined_at` over the last 2–3 years so query #1 (sort by `joined_at DESC`) shows visible ordering. Use ISO-8601 strings — SQLite stores `DATETIME` as TEXT.
- Include **at least one member with no rentals** (i.e. their `id` never appears in `rental.member_id`) so query #7's LEFT JOIN demonstrates a zero-rental row.

```sql
INSERT INTO member (id, name, email, phone, joined_at) VALUES
  (1,  'Alice Kim',     'alice.kim@example.com',     '010-1111-2222', '2023-04-12 10:00:00'),
  (2,  'Bob Lee',       'bob.lee@example.com',       '010-2222-3333', '2024-01-05 14:30:00'),
  -- … remaining rows …
  (12, 'Lucas Ko',      'lucas.ko@example.com',      NULL,            '2026-05-01 09:15:00');  -- no rentals
```

### 3.5 `rental` inserts
- 20–30 rows. This is the table that makes aggregates non-trivial. Cover **all** of:
  - Several members with **2+ rentals** (so query #10's `HAVING COUNT(*) > 1` is non-empty).
  - At least one member with rentals across **multiple categories** (drives variation in query #11).
  - **Open rentals** (`returned_at IS NULL`) for queries #8 and #13.
  - **Returned rentals** with realistic `returned_at >= rented_at` for query #11's `AVG` duration.
  - At least one rental older than ~1 year so query #14's archival DELETE removes at least one row.
- `rented_at`, `due_at`, `returned_at` are date/datetime literals; keep `due_at >= date(rented_at)` to satisfy the optional CHECK in Phase 1.
- Pattern:

```sql
INSERT INTO rental (id, member_id, book_id, rented_at, due_at, returned_at) VALUES
  (1,  1, 1,  '2025-12-01 11:00:00', '2025-12-15', '2025-12-10 17:30:00'),  -- returned
  (2,  1, 3,  '2026-02-04 09:30:00', '2026-02-18', NULL),                    -- open
  (3,  2, 1,  '2026-03-01 13:45:00', '2026-03-15', '2026-03-13 10:00:00'),
  -- … remaining rows …
  (25, 7, 9,  '2024-08-10 16:00:00', '2024-08-24', '2024-08-22 12:00:00');   -- > 1 year old, archivable by #14
```

### 3.6 Smoke test (manual)
After saving, run from a clean DB:

```bash
rm -f library.db
sqlite3 library.db < sql/01_schema.sql
sqlite3 library.db < sql/02_seed.sql
sqlite3 library.db <<'SQL'
SELECT 'category' AS t, COUNT(*) FROM category
UNION ALL SELECT 'book',    COUNT(*) FROM book
UNION ALL SELECT 'member',  COUNT(*) FROM member
UNION ALL SELECT 'rental',  COUNT(*) FROM rental;
SQL
```

- Each table must report `COUNT(*) >= 10` (`rental >= 20`).
- A second run of `02_seed.sql` against the same DB must succeed (proven by the `DELETE FROM` block).
- A deliberate FK violation smoke test (e.g. `INSERT INTO rental (member_id, book_id, rented_at, due_at) VALUES (999, 999, '2026-01-01', '2026-01-15');`) must fail — proving FK enforcement is live.

---

## 4. Files Touched

| File | Action |
| ---- | ------ |
| `sql/02_seed.sql` | full implementation: header + `PRAGMA` + clears + 4 `INSERT INTO ... VALUES` blocks |
| `library.db` | regenerated locally for smoke testing (not committed) |

No other files change in this phase.

---

## 5. Acceptance Criteria

- [ ] `sqlite3 library.db < sql/02_seed.sql` exits 0 against a freshly-schema'd DB **and** against an already-seeded DB (idempotency via `DELETE FROM`).
- [ ] Row counts: `category ≥ 10`, `book ≥ 10`, `member ≥ 10`, `rental ≥ 20` (verified by the smoke test in §3.6).
- [ ] At least one member has zero rentals (verify via `SELECT m.id, m.name, COUNT(r.id) FROM member m LEFT JOIN rental r ON r.member_id = m.id GROUP BY m.id HAVING COUNT(r.id) = 0;`).
- [ ] At least one rental has `returned_at IS NULL` and at least one has `returned_at IS NOT NULL`.
- [ ] At least one rental row is older than `date('now', '-1 year')` so query #14's DELETE has something to delete in Phase 3.
- [ ] FK violation test (`INSERT INTO rental` with non-existent `member_id`) fails with a foreign-key error — proves FK enforcement (subject §4.3).
- [ ] UNIQUE violation test (re-insert a duplicate `book.isbn` or `member.email`) fails with a UNIQUE error.
- [ ] No PII; all emails end with `@example.com`; phone numbers are obviously placeholder.

---

## 6. Commit

```
feat: add sample data for all tables
```

One commit covers the full seed per `.cursorrules` §6 Logical Commit Unit. Keep schema and seed as separate commits; do not amend Phase 1.

---

## 7. Risks / Notes

- **Insert order matters.** SQLite with `foreign_keys = ON` rejects an INSERT that references a non-existent parent. Always seed `category → book → member → rental`. If you reorder for readability, FK errors will surface immediately during the smoke test.
- **Hard-coded `id` values are intentional.** They keep FK references reviewable in the SQL file and make queries' captured results stable across re-seeds. If you switch to letting SQLite auto-assign, you also have to switch every FK reference to a subquery — a much bigger diff.
- **Idempotent re-seed via `DELETE FROM`.** Using `DELETE FROM` (vs. `DROP TABLE`) preserves the schema and lets the `DELETE FROM` itself be FK-checked — which is the closer simulation to "real" production resets.
- **`DELETE FROM` does not reset SQLite's rowid counter.** Because we hard-code `id` values in the INSERTs, this does not matter; if you later switch to auto-id, add `DELETE FROM sqlite_sequence WHERE name IN ('category','book','member','rental');` to keep IDs starting at 1.
- **Member with zero rentals must remain unreferenced after every edit.** Easy to forget when you add a rental later — guard with the acceptance check above.
- **Seed drift with schema.** If Phase 1 adds a column with `NOT NULL` later, this file breaks. Treat the pair as one logical change; re-run both from a fresh DB before committing any schema edit.

---

## 8. Definition of Done

- All four tables have ≥ 10 rows (`rental ≥ 20`) of realistic, FK-valid data.
- Open/returned rental mix, zero-rental member, and ≥ 1-year-old rental all present (manually verified).
- FK and UNIQUE enforcement is reproducible from a one-liner failure test (subject §4.3 "FK must block bad references" deliverable proven).
- `01_schema.sql` + `02_seed.sql` together produce the same `library.db` every time.
- Phase 3 can start writing queries against a known, stable data set.
