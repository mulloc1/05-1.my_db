# SQL Database Practice Bonus Implementation Plan (bonus_plan.md)

This document plans the **bonus tasks** in `docs/subject.md` §5. It assumes the core mission (`docs/plan.md` Phases 0–5) is **done and committed**, and starts a new phase on top of the working schema, seed data, and 15 core queries. Per `.cursorrules` §4 (YAGNI), we keep additions **minimal** and only extend files where the existing responsibility already fits.

Subject §5 lists three optional items:

| Item | Subject text |
| ---- | ------------ |
| **Join vs subquery** | Solve the same requirement both ways and compare |
| **Integrity experiment** | Try input that breaks FK; record why it fails and how to fix |
| **Mini report** | Define "3 core metrics this DB can produce" + final SQL each (e.g. monthly rentals, top 10 books) |

---

## 1. Goal Summary

- Add the three bonus items **without touching** the 15 core queries or the captured results in `results/` — the core grading scope stays frozen.
- Demonstrate a **measurable comparison** between a JOIN-based solution and an equivalent subquery-based solution for the same business question, including row-set equality and `EXPLAIN QUERY PLAN` differences.
- Produce a **short, reproducible integrity log** that records exactly what FK / `NOT NULL` / `UNIQUE` violations the schema rejects, the error message, and how a correct insert would look.
- Define **3 cross-cutting metrics** that the existing schema can already answer (no schema changes), each backed by a single final SQL query that runs end-to-end against the seed data.
- Ship bonus deliverables as **separate files and a separate set of commits** so a reviewer can grade the core scope without reading bonus material (`.cursorrules` §6 Logical Commit Unit).

---

## 2. Locked Decisions

Decisions for items left free by subject §5 (which query to compare, which violation to demonstrate, which metrics to define) and for choices that would be expensive to reverse later.

| Item | Decision | Rationale |
| ---- | -------- | --------- |
| Comparison target query | "Members who have rented more books than the average member" — the same business question as core query #12 | Already a subquery in core; the JOIN-based rewrite is a clean apples-to-apples comparison |
| Comparison artifact | A single `sql/04_join_vs_subquery.sql` file containing **both** queries side by side with a comment block explaining the difference | One file = one logical artifact; reviewer can run it top-to-bottom |
| Equivalence proof | After both queries, run `EXCEPT` both ways to assert empty diff — captured as the comparison's result | Stronger than eyeballing two result grids; standard SQL |
| Plan capture | `EXPLAIN QUERY PLAN` output for each variant pasted into a `-- ` comment block below the queries | Avoids tying the bonus to a specific GUI tool; works with `sqlite3` CLI |
| Integrity experiment file | `sql/05_integrity_experiments.sql` — each scenario is a separate `BEGIN; … ROLLBACK;` block so the file is idempotent | Re-runnable without polluting `library.db`; failures expected and captured |
| Integrity scenarios | **Three** failing inserts: (a) FK violation on `rental.book_id`, (b) `UNIQUE` violation on `member.email`, (c) `NOT NULL` violation on `book.title`. Plus **one** correct insert that fixes scenario (a) | Covers the three constraint types from subject §4.3; one "fix" closes the loop required by §5 |
| Integrity result capture | Plain text log at `results/integrity_log.txt` — copy/paste of `sqlite3` output including the error messages | Subject §4.6 allows text capture; smaller diff than screenshots |
| Metric #1 | **Monthly rental volume** — rentals grouped by `strftime('%Y-%m', rented_at)`, all months descending | Subject §5 example; obvious operational KPI |
| Metric #2 | **Top 10 most-rented books** — `book.title` joined with `COUNT(rental.id)`, ordered desc, `LIMIT 10` | Subject §5 example; tests join + aggregate + sort + limit in one shot |
| Metric #3 | **Active vs lapsed members** — members with ≥ 1 rental in the last 90 days vs. those without, as a two-row breakdown | Adds a non-trivial third metric that uses date arithmetic; not redundant with #1/#2 |
| Metric file | `sql/06_report.sql` — three queries with one-line comment each; "Mini Report" prose lives in the README appendix | Keeps SQL executable; prose in README is for humans |
| Result captures (bonus) | `results/bonus_q01_join.png`, `bonus_q02_subquery.png`, `bonus_q03_except.png`, `bonus_metric01_*.png` … `bonus_metric03_*.png` | Mirrors the core `qNN_*` convention so the file list reads chronologically |
| Schema changes | **None.** All bonus queries run against the existing 4 tables and the existing seed data | YAGNI; bonus is an interpretation exercise, not a schema rewrite |

> All other free choices follow `docs/plan.md` §2 (SQLite, DBeaver, file naming, etc.). This file does **not** override any decision locked there.

---

## 3. Affected Files (Minimal Footprint)

New files only — the three core SQL files and the 15 captured PNGs are not edited.

| File | Change |
| ---- | ------ |
| `sql/04_join_vs_subquery.sql` *(new)* | Two equivalent queries (JOIN + subquery) for the same question; `EXCEPT` equality check; `EXPLAIN QUERY PLAN` comment block |
| `sql/05_integrity_experiments.sql` *(new)* | Three failing-insert experiments inside `BEGIN; … ROLLBACK;`, plus one successful fix insert |
| `sql/06_report.sql` *(new)* | Three "Mini Report" metric queries with a one-line `--` purpose each |
| `results/bonus_q*.png` / `results/bonus_metric*.png` *(new)* | DBeaver result captures for the bonus queries |
| `results/integrity_log.txt` *(new)* | Plain-text capture of CLI output for the integrity experiments |
| `README.md` | Append a **"Bonus"** section: link to the three new SQL files; embed the "Mini Report" prose with each metric's one-paragraph interpretation |

> No new module / no new schema / no edits to `01_schema.sql`, `02_seed.sql`, `03_queries.sql`. The core grading surface is frozen (`.cursorrules` §6 Logical Commit Unit).

---

## 4. Join vs Subquery (subject §5 item 1)

### 4.1 The business question

"Which members have rented more books than the average member?" — identical to core query #12.

### 4.2 Subquery variant (already in core scope)

```sql
SELECT m.id, m.name, COUNT(r.id) AS rental_count
FROM member m
JOIN rental r ON r.member_id = m.id
GROUP BY m.id, m.name
HAVING COUNT(r.id) > (
  SELECT AVG(per_member) FROM (
    SELECT COUNT(*) AS per_member
    FROM rental
    GROUP BY member_id
  )
);
```

### 4.3 JOIN variant (new in `04_join_vs_subquery.sql`)

Compute the average once into a CTE, then join it against the per-member counts:

```sql
WITH per_member AS (
  SELECT member_id, COUNT(*) AS rental_count
  FROM rental
  GROUP BY member_id
),
avg_count AS (
  SELECT AVG(rental_count) AS avg_rentals FROM per_member
)
SELECT m.id, m.name, p.rental_count
FROM per_member p
JOIN member m ON m.id = p.member_id
CROSS JOIN avg_count a
WHERE p.rental_count > a.avg_rentals;
```

### 4.4 Equivalence proof

```sql
-- Both result sets must be empty (each is a superset of the other → identical sets)
<JOIN variant>
EXCEPT
<SUBQUERY variant>;

<SUBQUERY variant>
EXCEPT
<JOIN variant>;
```

### 4.5 Comparison commentary (in the file's header comment)

- **Readability**: JOIN + CTE reads top-to-bottom and names each intermediate step; the subquery nests the same logic inline.
- **Plan**: paste `EXPLAIN QUERY PLAN` for both. Typical observation: SQLite materializes the inner aggregate either way; the JOIN variant may surface a `SCAN CONSTANT ROW` for the CTE, while the subquery uses a `CORRELATED SCALAR SUBQUERY`. Document whichever plan the local SQLite shows — do not invent numbers.
- **Reuse**: the JOIN/CTE form is easier to extend (add a second threshold, another grouping column); the subquery form is shorter when nothing downstream needs the average value.

### 4.6 Captures

- `bonus_q01_join.png` — result of the JOIN variant.
- `bonus_q02_subquery.png` — result of the subquery variant (same rows; capture independently to prove parity visually).
- `bonus_q03_except.png` — two empty result grids from the two `EXCEPT` runs.

---

## 5. Integrity Experiment (subject §5 item 2)

### 5.1 Scenarios in `05_integrity_experiments.sql`

Each scenario is wrapped in `BEGIN; … ROLLBACK;` so the file leaves `library.db` untouched:

| # | Insert | Constraint violated | Expected error fragment (SQLite) |
| - | ------ | ------------------- | -------------------------------- |
| A | `INSERT INTO rental(member_id, book_id, rented_at, due_at) VALUES (1, 99999, ...);` | `FOREIGN KEY (book_id)` | `FOREIGN KEY constraint failed` |
| B | Insert a `member` row whose `email` matches an existing seeded member | `UNIQUE (member.email)` | `UNIQUE constraint failed: member.email` |
| C | `INSERT INTO book(author, isbn) VALUES ('X', '...');` — `title` omitted | `NOT NULL (book.title)` | `NOT NULL constraint failed: book.title` |

### 5.2 Fix demonstration

After scenario A's ROLLBACK, perform the "correct" version:

1. Insert a new `book` row first so the FK target exists.
2. Re-issue the `rental` insert using the new `book.id`.
3. Wrap both in `BEGIN; … COMMIT;` (or `ROLLBACK;` to keep the DB pristine — note the choice in the file header).

### 5.3 Result capture

Run via CLI and capture stdout/stderr to `results/integrity_log.txt`:

```bash
sqlite3 library.db < sql/05_integrity_experiments.sql 2>&1 | tee results/integrity_log.txt
```

The log must show three "constraint failed" lines and one successful insert (or a clean ROLLBACK for the fix scenario if we choose not to persist it). The README links to this file as the integrity proof.

---

## 6. Mini Report (subject §5 item 3)

### 6.1 Three metrics

| # | Metric | One-line definition |
| - | ------ | ------------------- |
| 1 | **Monthly rental volume** | Count of `rental` rows grouped by `strftime('%Y-%m', rented_at)` |
| 2 | **Top 10 most-rented books** | `book.title` joined with `COUNT(rental.id)`, ordered desc, `LIMIT 10` |
| 3 | **Active members (last 90 days)** | Members with at least one rental whose `rented_at >= date('now', '-90 days')`, alongside the inactive count |

### 6.2 Final SQL (lives in `sql/06_report.sql`)

Each query is preceded by a one-line `--` purpose comment, identical in convention to `03_queries.sql`. Shapes (finalized during implementation):

```sql
-- Metric 1: monthly rental volume (most recent months first)
SELECT strftime('%Y-%m', rented_at) AS year_month, COUNT(*) AS rentals
FROM rental
GROUP BY year_month
ORDER BY year_month DESC;

-- Metric 2: top 10 most-rented books
SELECT b.id, b.title, COUNT(r.id) AS rental_count
FROM book b
JOIN rental r ON r.book_id = b.id
GROUP BY b.id, b.title
ORDER BY rental_count DESC
LIMIT 10;

-- Metric 3: active vs lapsed members (last 90 days)
SELECT
  CASE WHEN last_rental >= date('now', '-90 days') THEN 'active' ELSE 'lapsed' END AS status,
  COUNT(*) AS member_count
FROM (
  SELECT m.id, MAX(r.rented_at) AS last_rental
  FROM member m
  LEFT JOIN rental r ON r.member_id = m.id
  GROUP BY m.id
)
GROUP BY status;
```

### 6.3 Report prose (in `README.md` appendix)

For each metric, one short paragraph covering:

- **What** the number measures.
- **Why** the library would care.
- **How** to read the captured result grid (`results/bonus_metric0N_*.png`).

Keep each paragraph ≤ 4 sentences; the SQL file is the source of truth, the prose is for orientation.

---

## 7. Phased Plan

Each phase = **one logical change = one commit** (`.cursorrules` §6). Conventional Commits prefix.

### Phase B0 — Branch off & docs

- Branch off (e.g. `bonus`) from the deployed core commit.
- Add this file as `docs/bonus_plan.md`.
- Commit: `docs: plan bonus tasks (join-vs-subquery, integrity, mini report)`

### Phase B1 — Join vs subquery

- Add `sql/04_join_vs_subquery.sql` with both variants, the `EXCEPT` checks, and the plan comment block.
- Capture `bonus_q01_join.png`, `bonus_q02_subquery.png`, `bonus_q03_except.png`.
- Commit: `feat: compare join and subquery solutions for the same query`

### Phase B2 — Integrity experiments

- Add `sql/05_integrity_experiments.sql` with three failing inserts and one fix.
- Run via CLI, redirect to `results/integrity_log.txt`.
- Commit: `feat: record fk, unique, and not-null violation experiments`

### Phase B3 — Mini report

- Add `sql/06_report.sql` with the three metric queries.
- Capture `bonus_metric01_*.png` … `bonus_metric03_*.png`.
- Commit: `feat: add three core db metrics for mini report`

### Phase B4 — README sync

- Append a **"Bonus"** section to `README.md`: list the three new SQL files, embed the mini-report prose for the three metrics, and link to `results/integrity_log.txt`.
- Commit: `docs: document bonus deliverables (join vs subquery, integrity, metrics)`

---

## 8. Verification Strategy

Same posture as `plan.md` §7 (manual checklist; SQL execution is deterministic). New checks layered on top of the core checklist:

- [ ] **Join vs subquery**: both variants in `sql/04_join_vs_subquery.sql` return the same row set; both `EXCEPT` queries return zero rows.
- [ ] **Plans captured**: the file's comment block contains `EXPLAIN QUERY PLAN` output for both variants and one sentence comparing them.
- [ ] **Integrity log**: `results/integrity_log.txt` contains the three expected error fragments verbatim; the file is reproducible by re-running the command in §5.3.
- [ ] **DB untouched**: after running `05_integrity_experiments.sql`, `SELECT COUNT(*)` on each table matches the post-seed counts (proves `BEGIN; … ROLLBACK;` semantics).
- [ ] **Mini report runs**: `sqlite3 library.db < sql/06_report.sql` returns three result sets without errors.
- [ ] **Metric 1** has at least two distinct months in its output (seed data should span ≥ 2 months — adjust seed if not).
- [ ] **Metric 2** returns at most 10 rows; `LIMIT 10` is honored even when there are more candidates.
- [ ] **Metric 3** returns exactly two rows (`active`, `lapsed`) or one row if all members fall in one bucket — both are acceptable; the README prose notes which case the seed produced.
- [ ] **README**: the "Bonus" section enumerates the three deliverables, links each SQL file, and embeds the three-paragraph mini report.
- [ ] **Regressions**: every checklist item from `plan.md` §7 still passes (core scope untouched).

---

## 9. Risks / Open Points

| Risk | Mitigation |
| ---- | ---------- |
| Plan output differs across SQLite versions | Capture the locally observed `EXPLAIN QUERY PLAN` text; do not assert a specific operator name in the prose |
| `BEGIN; … ROLLBACK;` not honored if `PRAGMA foreign_keys` is off | Re-state `PRAGMA foreign_keys = ON;` at the top of `05_integrity_experiments.sql` |
| Seed data has < 90-day spread → Metric 3 only shows one status | Document the observed case in README; optionally extend seed `rented_at` range when bonus starts (still no schema change) |
| Top-10 metric returns < 10 rows on a small seed | Acceptable; the `LIMIT` clause is what's being demonstrated, not the row count |
| Bonus screenshots drift from core convention | Filename prefix `bonus_qNN` / `bonus_metricNN` makes them obviously distinct in `results/` |
| Reviewer runs bonus SQL before core seed | README "Bonus" section spells out the required execution order (`01` → `02` → `03` → bonus `04`/`05`/`06`) |
| Schema creep ("just one more column for the metric") | Hard rule: **no edits to `01_schema.sql`** in this phase; metrics that need new columns are out of scope |

---

## 10. Definition of Done

- `sql/04_join_vs_subquery.sql` contains both variants, two `EXCEPT` equivalence checks, and an `EXPLAIN QUERY PLAN` comparison comment; both result captures land in `results/`.
- `sql/05_integrity_experiments.sql` provokes one FK, one UNIQUE, and one NOT NULL violation inside `BEGIN; … ROLLBACK;` blocks; `results/integrity_log.txt` captures the three errors plus the corrective insert.
- `sql/06_report.sql` defines the three Mini Report metrics with one-line purpose comments; each metric has a `results/bonus_metric0N_*.png` capture.
- `README.md` has a "Bonus" section that lists the three deliverables, embeds the three-paragraph mini-report, and links every new artifact.
- No edits to `01_schema.sql`, `02_seed.sql`, `03_queries.sql`, or any `results/qNN_*.png` from the core scope.
- Every core checklist item from `plan.md` §9 still passes against the same `library.db`.
