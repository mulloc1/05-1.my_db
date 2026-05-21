# Phase 3 — 15 Core SQL Queries (`03_queries.sql`)

> Parent plan: [`docs/plan.md`](../plan.md) §6 Phase 3
> Subject reference: [`docs/subject.md`](../subject.md) §2.4, §4.5, §4.6

This phase produces the assignment's single biggest artifact: **15 SQL queries** covering basic select, joins (INNER + LEFT), aggregates with `GROUP BY`, ≥ 1 subquery, ≥ 2 update/delete, and ≥ 1 `CREATE INDEX`. Each query carries a **one-line `--` comment** describing what it verifies (subject §4.6) and is numbered (`-- Query 01: …`) so the matching `results/qNN_*.png` capture in Phase 4 is mechanical to locate.

---

## 1. Goal

- Write 15 queries in `sql/03_queries.sql` matching the grid in `plan.md` §5 — exact column lists and `WHERE` predicates finalized during implementation.
- Every query is preceded by `-- Query NN: <one-line purpose>` (subject §4.6).
- Every query returns a non-empty result against the Phase 2 seed (except where the question's semantics allow empty, e.g. #14 once the cutoff is past).
- The category coverage matrix in `plan.md` §5 "Coverage check" is satisfied (4+ basic / 4+ joins with 2+ INNER & 1+ LEFT / 3+ aggregates with 2+ kinds + GROUP BY / 1+ subquery / 2+ update-delete / 1+ index).
- The index in query #15 is justified in its leading comment and **observably used** by at least one earlier query (verified with `EXPLAIN QUERY PLAN` per the acceptance check).

---

## 2. Scope (In / Out)

**In scope**
- `PRAGMA foreign_keys = ON;` header (same pattern as Phase 1 / 2).
- 15 numbered queries with one-line purpose comments, in the order of `plan.md` §5.
- One `CREATE INDEX` in query #15 with a rationale comment.
- Inline `-- SQLite-specific:` comments above any non-portable expression (`julianday(...)`, `date('now', '-1 year')`, etc.).
- A short footer comment listing the category-coverage tally as a self-check.

**Out of scope**
- Schema or seed changes (Phases 1 / 2 own them).
- Result captures — those are filenames in `results/` and live in Phase 4.
- Bonus comparisons (subject §5, `bonus_plan.md` — joins vs subqueries, integrity experiments).
- Views, CTEs beyond what subqueries naturally need. Use a CTE (`WITH …`) for query #12 only if it materially clarifies the subquery; otherwise keep the bare correlated/uncorrelated subquery form.

---

## 3. Tasks

### 3.1 File header

```sql
-- 03_queries.sql — 15 core SQL queries for the library domain
-- Run order: 01_schema.sql → 02_seed.sql → 03_queries.sql
-- Categories (subject §4.5):
--   Basic select: 4   Joins (INNER): 3   Joins (LEFT): 1
--   Aggregates:  3   Subquery: 1        Update/Delete: 2   Index: 1
-- SQLite-specific syntax (date('now', ...), julianday(...)) is commented per-query.

PRAGMA foreign_keys = ON;
```

The categories tally in the header should match the actual file at commit time — update it in lockstep with any edit.

### 3.2 Queries 1–4: Basic select (subject §4.5 — 4+)

Each query has the shape:

```sql
-- Query 01: List all members sorted by joined_at (most recent first).
SELECT id, name, email, joined_at
FROM member
ORDER BY joined_at DESC;
```

| # | Purpose (one-line) | Required clauses |
| - | ------------------ | ---------------- |
| 1 | List all members sorted by `joined_at DESC`. | `ORDER BY` |
| 2 | Books published in or after 2015, ordered by year then title. | `WHERE`, `ORDER BY` |
| 3 | Top 5 most recently rented books, newest first. | `ORDER BY rented_at DESC`, `LIMIT 5` |
| 4 | Members whose email ends with `@example.com`. | `WHERE … LIKE '%@example.com'` |

Every query selects an **explicit column list** — no `SELECT *` (subject §4.6 "verifiable result").

### 3.3 Queries 5–8: Joins (subject §4.5 — 4+, with 2+ INNER and 1+ LEFT)

```sql
-- Query 05: Each rental shown with member name and book title (INNER JOIN, no orphans).
SELECT r.id, m.name AS member_name, b.title AS book_title, r.rented_at, r.due_at
FROM rental r
INNER JOIN member m ON m.id = r.member_id
INNER JOIN book   b ON b.id = r.book_id
ORDER BY r.rented_at DESC;
```

| # | Purpose | Join type |
| - | ------- | --------- |
| 5 | Each rental with member name + book title. | INNER (× 2) |
| 6 | Each book with its category name (excludes uncategorized, though all books are categorized per schema). | INNER |
| 7 | All members + their rental counts, including members with zero rentals. | **LEFT JOIN** + `COUNT(r.id)` + `GROUP BY m.id` |
| 8 | Currently open rentals (`returned_at IS NULL`) with member and book info. | INNER (× 2) + `WHERE returned_at IS NULL` |

Query 7 is the canonical "LEFT JOIN demonstrates zero-count rows" example — the zero-rental member seeded in Phase 2 makes the result observable.

### 3.4 Queries 9–11: Aggregates (subject §4.5 — 3+, with 2+ of `COUNT`/`SUM`/`AVG` + `GROUP BY`)

```sql
-- Query 09: Number of books per category, sorted descending.
SELECT c.name AS category, COUNT(b.id) AS book_count
FROM category c
LEFT JOIN book b ON b.category_id = c.id
GROUP BY c.id, c.name
ORDER BY book_count DESC, c.name ASC;
```

| # | Purpose | Aggregate function(s) |
| - | ------- | --------------------- |
| 9 | Books per category, descending. | `COUNT(b.id)` + `GROUP BY` |
| 10 | Rentals per member, only members with > 1 rental. | `COUNT(*)` + `GROUP BY` + `HAVING COUNT(*) > 1` |
| 11 | Average rental duration in days per category (returned rentals only). | `AVG(julianday(returned_at) - julianday(rented_at))` + `GROUP BY` |

Query 11 uses SQLite's `julianday(...)` — add `-- SQLite-specific: julianday()` and a portable alternative comment (`-- Postgres: (returned_at::date - rented_at::date)`).

### 3.5 Query 12: Subquery (subject §4.5 — 1+)

```sql
-- Query 12: Members who have rented more books than the average member.
SELECT m.id, m.name, COUNT(r.id) AS rental_count
FROM member m
LEFT JOIN rental r ON r.member_id = m.id
GROUP BY m.id, m.name
HAVING COUNT(r.id) > (
  SELECT AVG(per_member.cnt)
  FROM (
    SELECT COUNT(*) AS cnt FROM rental GROUP BY member_id
  ) AS per_member
)
ORDER BY rental_count DESC;
```

- Uses an uncorrelated subquery for the average; the outer query is a `HAVING` filter. This shape demonstrates both **aggregate inside subquery** and **subquery inside aggregate filter**, which is the most common interview-shaped variant.

### 3.6 Queries 13–14: Update / Delete (subject §4.5 — 2+)

```sql
-- Query 13: Mark a specific open rental as returned (returned_at = current timestamp).
UPDATE rental
SET returned_at = CURRENT_TIMESTAMP    -- SQLite-specific: stored as TEXT ISO-8601
WHERE id = 2 AND returned_at IS NULL;
```

```sql
-- Query 14: Archive rentals older than one year that have been returned (DELETE).
DELETE FROM rental
WHERE returned_at IS NOT NULL
  AND rented_at < date('now', '-1 year');  -- SQLite-specific: date('now', '-1 year')
```

- Both queries always include a `WHERE` clause — the safety check from `plan.md` §2 implicit "no full-table UPDATE/DELETE".
- Phase 4 captures the result *before* and *after* (or just the affected-row count); decide format in Phase 4.

### 3.7 Query 15: Index (subject §4.5 — 1+ with one-line rationale)

```sql
-- Query 15: Index on rental(member_id, rented_at) — accelerates queries #7 and #10
--          (group/aggregate on member_id) and #3 (ORDER BY rented_at DESC LIMIT 5).
--          Composite order (member_id, rented_at) supports both equality on member_id
--          and range/sort on rented_at without an extra single-column index.
CREATE INDEX IF NOT EXISTS idx_rental_member_rented
  ON rental(member_id, rented_at);
```

- `IF NOT EXISTS` keeps the script idempotent — re-running `03_queries.sql` does not fail on the second run.
- The rationale comment is **two lines max** and explains the **column order** choice (`plan.md` §8 risk #6 — "index might not actually be used").

### 3.8 Footer self-check

```sql
-- Coverage tally:
--   Basic select: 4   (#1–#4)
--   Joins:        4   (#5 INNER, #6 INNER, #7 LEFT, #8 INNER)
--   Aggregates:   3   (#9 COUNT, #10 COUNT, #11 AVG; all with GROUP BY)
--   Subquery:     1   (#12)
--   Update/Delete: 2  (#13 UPDATE, #14 DELETE)
--   Index:        1   (#15 CREATE INDEX)
```

---

## 4. Files Touched

| File | Action |
| ---- | ------ |
| `sql/03_queries.sql` | full implementation: header + `PRAGMA` + 15 queries + footer tally |
| `library.db` | smoke-tested locally only (not committed) |

No other files change in this phase.

---

## 5. Acceptance Criteria

- [ ] `sqlite3 library.db < sql/03_queries.sql` exits 0 (no errors) against a freshly-seeded DB.
- [ ] **15 queries exactly**, numbered 1–15, each preceded by `-- Query NN: <one-line purpose>`.
- [ ] Coverage matrix (counted from the file) matches the footer tally in §3.8.
- [ ] Each `SELECT` query returns ≥ 1 row against the Phase 2 seed; the `UPDATE`/`DELETE` queries report an affected-row count ≥ 1 on the first run.
- [ ] `EXPLAIN QUERY PLAN SELECT … FROM rental WHERE member_id = 1 ORDER BY rented_at DESC LIMIT 5;` shows `USING INDEX idx_rental_member_rented` after query #15 runs. If the optimizer ignores the index, update the rationale comment in #15 with the observed plan (`plan.md` §8 risk #6).
- [ ] No `SELECT *` in any query (explicit column lists everywhere).
- [ ] Every `UPDATE` and `DELETE` has a `WHERE` clause (no accidental full-table writes).
- [ ] `IF NOT EXISTS` is present on the `CREATE INDEX` so re-running the file is safe.
- [ ] Every SQLite-specific expression carries an inline `-- SQLite-specific:` comment, ideally with a portable alternative in the same comment (subject §4.1).

---

## 6. Commit

```
feat: add 15 core sql queries
```

One commit covers the whole `03_queries.sql` body per `.cursorrules` §6. Result captures are a separate commit in Phase 4 — do **not** include `.png` files in this diff.

---

## 7. Risks / Notes

- **Index #15 might not be used by the optimizer.** SQLite chooses based on row counts and statistics; with our small seed, a full scan may be cheaper. Two fixes: (a) re-run `ANALYZE;` after the index is created so the planner sees fresh stats, or (b) document the observed plan in the #15 comment. The acceptance criterion accepts either path (`plan.md` §8 risk #6).
- **Query order is part of the deliverable.** Reviewers map `results/qNN_*.png` to query #NN by file order. Renumbering queries mid-phase requires renaming captures in Phase 4 — avoid it once Phase 4 starts.
- **`AVG(julianday(...) - julianday(...))` returns days as a float.** That is correct and intentional; cast to `INTEGER` only if a reviewer asks for whole-day output.
- **Query #11 must filter to returned rentals only.** `WHERE returned_at IS NOT NULL` is non-optional — averaging across `NULL`s either errors or skews the result depending on dialect.
- **`UPDATE` / `DELETE` mutate state.** After Phase 3 runs, `library.db` no longer matches the pristine Phase 2 seed. That is fine for the assignment because the captures in Phase 4 are taken in a known order; re-running Phase 2 restores the seed before re-capturing.
- **Dialect drift.** If a reviewer runs the file under MySQL or PostgreSQL, queries with `julianday`, `date('now', ...)`, and `CURRENT_TIMESTAMP` semantics may differ. The inline comments are the contract for what to translate; the file is not silently portable.

---

## 8. Definition of Done

- 15 queries cover all six required categories at or above subject §4.5 minimums.
- Each query has a one-line purpose comment and returns a sensible result against the Phase 2 seed.
- The new index is observable in at least one query's plan (or its absence is justified in the rationale comment).
- The file is idempotent (`CREATE INDEX IF NOT EXISTS`) and dialect-aware (inline `-- SQLite-specific:` notes).
- Phase 4 can capture results query-by-query without re-editing the SQL.
