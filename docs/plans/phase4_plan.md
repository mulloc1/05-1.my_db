# Phase 4 — Result Captures

> Parent plan: [`docs/plan.md`](../plan.md) §6 Phase 4
> Subject reference: [`docs/subject.md`](../subject.md) §2.4, §4.6

This phase produces the visible evidence that every query in Phase 3 actually returns the expected shape. Per `plan.md` §2 lock: **PNG screenshots** of the DBeaver result grid, one per query, named `q01_<slug>.png` … `q15_<slug>.png` and saved to `results/`. The 1:1 mapping between filename prefix and query number (subject §4.5) is the only structure a reviewer needs to find a capture.

---

## 1. Goal

- Produce **15 result captures** in `results/` matching `sql/03_queries.sql` query-for-query.
- Use a consistent capture format (DBeaver result grid PNG) so headers, row counts, and at least the first ~10 result rows are visible without zooming in.
- For the `UPDATE` (#13) and `DELETE` (#14) queries, capture both the **affected-row message** and a **before/after `SELECT` snapshot** that proves the mutation happened — a single screenshot per query is acceptable if both are visible in the same DBeaver view.
- Result: every reviewer can scroll `results/` and visually verify the answer to each numbered query without opening a SQL client.

---

## 2. Scope (In / Out)

**In scope**
- Re-seeding the DB to a known state (`01_schema.sql` + `02_seed.sql`) before capturing.
- Running queries #1–#15 in order in DBeaver and screenshotting each result grid.
- File naming convention `qNN_<short-slug>.png` (e.g. `q07_left_join_member_rentals.png`).
- One capture per query (#13 and #14 may include before/after in one image — see §3.4).
- A small `results/README.md` (optional) listing each capture's purpose — only added if a reviewer asks; not required by subject.

**Out of scope**
- Re-running queries after each capture and re-screenshotting — capture in one session.
- Capturing intermediate query plans (`EXPLAIN QUERY PLAN`) — that lives in the Phase 3 acceptance check, not as a result file.
- Edited / annotated images (arrows, callouts) — keep raw DBeaver grid output so the deliverable is reproducible.
- Animated GIFs or video — PNG only, per `plan.md` §2 lock.

---

## 3. Tasks

### 3.1 Reset to known state
Before any capture, reset `library.db` so query #13's `UPDATE` and query #14's `DELETE` operate on the same seed every time:

```bash
rm -f library.db
sqlite3 library.db < sql/01_schema.sql
sqlite3 library.db < sql/02_seed.sql
```

Then open `library.db` in DBeaver. **Do not** run any query manually between reset and capture #1, otherwise the screenshots may show row IDs / timestamps that differ from a reviewer's fresh run.

### 3.2 Capture each `SELECT` (queries #1–#12, #15 result preview)

For each query:

1. Highlight the query in `sql/03_queries.sql` (or paste it into a DBeaver SQL editor tab).
2. Press F5 / Execute.
3. Take a screenshot of the **entire result panel** including:
   - The query text or query name at the top (DBeaver shows the executed SQL above the grid).
   - The column headers.
   - At least the first ~10 result rows (or all rows if fewer).
   - The row count indicator in the lower-right corner.
4. Save as `results/qNN_<slug>.png`. Suggested slugs:

| # | Slug |
| - | ---- |
| 01 | `members_by_joined_desc` |
| 02 | `books_published_2015_or_later` |
| 03 | `top5_recent_rentals` |
| 04 | `members_example_com_email` |
| 05 | `rental_member_book_inner_join` |
| 06 | `book_with_category_inner_join` |
| 07 | `member_rental_count_left_join` |
| 08 | `open_rentals_currently_out` |
| 09 | `books_per_category_count` |
| 10 | `rentals_per_member_having` |
| 11 | `avg_rental_duration_per_category` |
| 12 | `members_above_avg_rentals_subquery` |
| 15 | `create_index_done` (the DBeaver "DDL executed" / row-affected message) |

The slug is a guideline — final names are decided during capture (`plan.md` §2 — implementation-time detail).

### 3.3 Capture `CREATE INDEX` (query #15)

Two acceptable formats:

- **Option A** (simpler): screenshot the DBeaver SQL editor showing the `CREATE INDEX` statement and the success message ("Query executed successfully").
- **Option B** (more informative): in addition to Option A, run `PRAGMA index_list('rental');` immediately after and capture the row showing `idx_rental_member_rented` in the index list — proves the index actually exists.

Pick one and stick with it across the assignment. Option B is recommended because it doubles as the "index used" evidence the rubric likes.

### 3.4 Capture `UPDATE` / `DELETE` (queries #13, #14)

Mutating queries do not produce a result grid by themselves. Each capture must include:

1. The DBeaver message line ("Updated rows: N" / "Deleted rows: N").
2. A **verification `SELECT`** run immediately after, proving the row's new state (for #13: `SELECT id, returned_at FROM rental WHERE id = 2;` should now show a non-NULL `returned_at`; for #14: a count comparison or a `SELECT … WHERE rented_at < date('now', '-1 year') AND returned_at IS NOT NULL` returning 0 rows).

A single screenshot showing both panels (executed mutating query + verification SELECT result) satisfies the deliverable. Name them `q13_update_return_rental.png` and `q14_delete_archive_old_rentals.png`.

After capturing #13 and #14, the DB is no longer in the pristine seed state. **Do not** re-capture earlier queries from this DB — if you find a typo, reset per §3.1 and restart.

### 3.5 Cross-check filenames against the query file
Run a quick sanity check:

```bash
ls results/ | sort
```

The output should contain exactly 15 `qNN_*.png` files numbered 01–15 with no gaps, no duplicates, and no extras (subject §4.7 "submission structure"). A simple awk one-liner:

```bash
ls results/ | grep -oE 'q[0-9]{2}' | sort -u | wc -l   # must print 15
```

---

## 4. Files Touched

| File | Action |
| ---- | ------ |
| `results/q01_*.png` … `results/q15_*.png` | create (15 PNG captures) |
| `results/.gitkeep` | delete (only if it was added in Phase 0 and is no longer needed once real files exist) |
| `library.db` | regenerated locally; **not** committed (`.gitignore`d in Phase 0) |

No source code or SQL files change in this phase.

---

## 5. Acceptance Criteria

- [ ] `results/` contains exactly **15** PNG files matching the pattern `qNN_<slug>.png` with numeric prefixes 01 through 15 (no gaps).
- [ ] Each `SELECT` capture (queries #1–#12) shows column headers, at least the first 10 rows (or all rows if fewer), and the DBeaver row-count indicator.
- [ ] Query #7 capture visibly includes the **zero-rental member** (proves LEFT JOIN behavior).
- [ ] Query #8 capture shows only rentals where `returned_at` is empty / NULL in the grid.
- [ ] Query #10 capture shows only members with `rental_count > 1`.
- [ ] Query #12 capture shows at least one member with `rental_count` greater than the average (otherwise the seed is too uniform — fix the seed, not the capture).
- [ ] Query #13 capture shows "Updated rows: 1" **and** a verification SELECT proving `returned_at` is now non-NULL for that rental.
- [ ] Query #14 capture shows "Deleted rows: N" (N ≥ 1) **and** a verification SELECT proving the targeted rows are gone.
- [ ] Query #15 capture shows the `CREATE INDEX` success message and, if Option B is used, `PRAGMA index_list('rental');` listing `idx_rental_member_rented`.
- [ ] Each capture is legible at 100 % zoom (no need to zoom in to read headers or first-row values).

---

## 6. Commit

```
docs: capture execution results for 15 queries
```

One commit for all 15 captures per `.cursorrules` §6 — the "result evidence for the query set" is a single logical change. Avoid splitting per-query commits; the diff is purely additive (PNGs) and reviewers want the whole set at once.

---

## 7. Risks / Notes

- **Capture order matters.** Capturing #13/#14 before #1–#12 mutates the DB and breaks the assumption that all earlier captures share a single seed. Always capture in numeric order; if you have to redo any of #1–#12, reset per §3.1 first.
- **Screenshot reproducibility.** Reviewers may recreate the DB from `01_schema.sql` + `02_seed.sql` and re-run a query expecting to see the same rows. Because Phase 2 hard-codes `id` values and uses deterministic `INSERT` literals, this should hold — the only delta is `member.joined_at` if you used `CURRENT_TIMESTAMP` (don't — Phase 2 uses literal ISO strings for this exact reason).
- **DBeaver "Auto-commit" vs "Manual commit"** affects whether #13 and #14 persist. Leave auto-commit ON during captures so the verification SELECT in the same capture reflects committed state.
- **PNG vs JPG.** PNG is required per `plan.md` §2 lock — JPG compression artifacts make column headers harder to read. Configure your screenshot tool to PNG once and forget it.
- **Stale captures.** If `02_seed.sql` or `03_queries.sql` changes in a later iteration, every affected capture must be regenerated in the same commit. The acceptance check "15 PNGs, numeric prefixes 01–15" catches gaps but not stale content — visual review is the only safety net.
- **File size.** Each capture should be under ~500 KB; if your screenshots are 2 MB+, set DBeaver result panel to a smaller font or crop to the meaningful area before saving.

---

## 8. Definition of Done

- 15 `qNN_*.png` files exist in `results/`, matching `03_queries.sql` query-for-query.
- Every capture is legible, includes the result grid (or mutation message + verification), and was produced from the pristine `01_schema.sql` + `02_seed.sql` seed before #13/#14 ran.
- A reviewer can answer "what does query #N return?" by opening `results/qNN_*.png` alone.
- Phase 5 can write the README's "Results" section by listing files in `results/` without re-running any SQL.
