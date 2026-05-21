# SQL Database Practice Implementation Plan (plan.md)

This document is a phased implementation plan that satisfies both the requirements in `docs/subject.md` and the coding/structure rules in the repository `.cursorrules`. Following the **Minimal-First / YAGNI** principle (.cursorrules §4) and **Lightweight Plans** (.cursorrules §2), we start with the **minimum schema that meets requirements**; bonus tasks (subject §5) are separated into a later phase after the core assignment is done.

---

## 1. Goal Summary

- Deliver a **SQL-only database practice artifact** with no backend framework: schema, seed data, and queries are the entire deliverable (subject §1, §2).
- Design a normalized schema with **at least 4 tables** and **at least 2 1:N relationships**, expressed via `PRIMARY KEY` / `FOREIGN KEY` and integrity constraints (subject §2.1, §4.2, §4.3).
- Ship the assignment as **three executable `.sql` files** — schema creation, sample inserts, and 15 verification queries — runnable from top to bottom in a fresh database (subject §2.2–§2.4, §4.7).
- Insert **at least 10 rows per table** with FK links that reflect realistic usage so aggregate/join queries return non-trivial results (subject §2.3, §4.4).
- Cover the required query categories — basic select, joins (INNER + LEFT), aggregates with `GROUP BY`, at least one subquery, update/delete, and at least one `CREATE INDEX` — in **15 queries total** (subject §2.4, §4.5).
- Document each query with a **one-line purpose** and capture its execution result (screenshot or text) under a single results folder (subject §4.6).
- Keep the SQL portable: prefer **standard SQL**, and call out dialect-specific syntax in a comment on the offending query (subject §4.1).

---

## 2. Locked Decisions

Decisions for items left open in subject ("free", "pick one", etc.) and other choices that are costly to reverse later. Specific column comments, exact row counts beyond the minimum, and result-capture filenames are decided during implementation (.cursorrules §2).

| Item | Decision | Rationale (subject / .cursorrules) |
| ---- | -------- | ---------------------------------- |
| Domain | **Book rental** (library) | Subject §2.1 example; gives natural 1:N fan-out (member→rental, book→rental, category→book) |
| RDBMS | **SQLite** (file-based, single `.db`) | Subject §4.1 lists it; no server, easy to ship; portable across reviewers' machines |
| Client tool | **DBeaver** for screenshots; CLI (`sqlite3`) for script execution | Subject §4.1; DBeaver renders result tables cleanly for captures |
| SQL dialect | **Standard SQL first**; SQLite-specific syntax (`AUTOINCREMENT`, `strftime`) flagged with `-- SQLite-specific` comment | Subject §4.1 portability note |
| Table count | **4 tables**: `category`, `book`, `member`, `rental` | Subject §2.1 minimum; one parent (`category`) + two main entities (`book`, `member`) + one association (`rental`) |
| 1:N relationships | **3 total** (`category` 1:N `book`, `member` 1:N `rental`, `book` 1:N `rental`) | Subject §4.2 requires ≥ 2; one extra so a single delete/update query can demonstrate cascade meaningfully |
| Surrogate keys | **Integer PK** on every table (`id INTEGER PRIMARY KEY`) | Simpler joins; demonstrates PK/FK clearly; avoids composite-key edge cases in beginner scope |
| Natural unique keys | `book.isbn UNIQUE`, `member.email UNIQUE` | Subject §4.3 requires ≥ 1 `UNIQUE`; two satisfies the constraint with a realistic shape |
| NOT NULL columns | `book.title`, `book.author`, `member.name`, `rental.rented_at`, `rental.due_at` (among others) | Subject §4.3 requires ≥ 1; chosen to mirror real-world "this row is meaningless without it" |
| FK behavior | `ON DELETE RESTRICT` on `book.category_id`, `rental.book_id`, `rental.member_id` | Subject §4.3 — FK must block references to non-existent values; RESTRICT is the safest default |
| FK enforcement | `PRAGMA foreign_keys = ON;` at the top of every SQL file | SQLite-specific — FK enforcement is off by default; flagged in a header comment |
| Sample row counts | **10–15 rows per parent table**, **20–30 `rental` rows** | Subject §4.4 minimum; inflated `rental` count keeps aggregates non-trivial |
| Date/time type | `DATE` for due/return dates, `DATETIME` (`TEXT` ISO-8601 under SQLite) for `created_at`/`rented_at` | Standard SQL semantics; matches subject §4.2 type examples |
| Query count | **15 queries exactly** in the core deliverable; bonus queries live in `bonus_plan.md` | Subject §2.4, §4.5 minimum; do not pad core scope |
| Index choice | **One** `CREATE INDEX` on `rental(member_id, rented_at)` | Subject §4.5 — supports "rentals by member, recent first", a query already in the 15 |
| Results format | **PNG screenshots** of DBeaver result grid, named `q01_*.png` … `q15_*.png` | Subject §4.6 — screenshot or text; PNG keeps headers/row counts visible |
| File naming | `01_schema.sql`, `02_seed.sql`, `03_queries.sql` (numeric prefix = execution order) | Subject §4.7 "execution order"; reviewer can run them in sequence without reading the README |
| ERD | **dbdiagram.io** export checked in as `docs/erd.png` | Subject §4.7 optional bonus; cheap visual aid for the README |

---

## 3. Directory / File Layout

Follows the recommended structure in subject §4.7. Files are grouped by **execution order**, not by category, so a reviewer can replay the assignment by running them in numeric order (.cursorrules §4 "minimum split").

```
05-1.my_db/
├── README.md                 # intro · ERD · how to run · subject mapping (subject §4.7)
├── docs/
│   ├── subject.md
│   ├── plan.md               # (this document)
│   ├── bonus_plan.md
│   └── erd.png               # (optional) ERD export from dbdiagram.io
├── sql/
│   ├── 01_schema.sql         # CREATE TABLE statements + PRAGMA foreign_keys
│   ├── 02_seed.sql           # INSERT statements (parents → children)
│   └── 03_queries.sql        # 15 numbered queries, each preceded by a one-line comment
├── results/
│   ├── q01_*.png             # one screenshot per query (subject §4.6)
│   ├── …
│   └── q15_*.png
└── library.db                # SQLite database file (regenerated by 01 + 02; can be gitignored)
```

**Split rationale (.cursorrules §4·§5 SRP)**

- Three SQL files = three responsibilities (schema / data / queries). They are never edited together, so colocating them under one folder is enough; no per-table file split until the schema reaches dozens of tables.
- `results/` is flat because the 1:1 mapping between filename prefix (`q07_…`) and query number (subject §4.5) is the only structure a reviewer needs.
- The `.db` file is a build artifact (`01_schema.sql` + `02_seed.sql` reproduce it deterministically). It can be `.gitignore`d once the README documents the regeneration command.

---

## 4. Schema Overview

### 4.1 Entities & Relationships (subject §4.2)

```
category ──< book ──< rental >── member
   1       N   1       N    N     1
```

- `category` 1:N `book` — one category groups many books.
- `book` 1:N `rental` — one book can be rented many times (across copies and over time).
- `member` 1:N `rental` — one member has many rental records.

### 4.2 Table Shapes (subject §4.2 — minimum 4 tables)

| Table | Key columns | Purpose |
| ----- | ----------- | ------- |
| `category` | `id PK`, `name UNIQUE NOT NULL`, `description` | Lookup for book taxonomy; small, mostly-static |
| `book` | `id PK`, `title NOT NULL`, `author NOT NULL`, `isbn UNIQUE`, `published_year`, `category_id FK → category(id)` | Catalog of titles available to rent |
| `member` | `id PK`, `name NOT NULL`, `email UNIQUE NOT NULL`, `phone`, `joined_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP` | Library members |
| `rental` | `id PK`, `member_id FK → member(id)`, `book_id FK → book(id)`, `rented_at DATETIME NOT NULL`, `due_at DATE NOT NULL`, `returned_at DATETIME NULL` | The 1:N junction that drives every interesting query |

`rental.returned_at IS NULL` is the "currently rented" predicate used by several queries — a deliberate design choice that keeps "open rentals" expressible without a separate status column.

### 4.3 Constraints Mapping (subject §4.3)

| Constraint type | Where | Why |
| --------------- | ----- | --- |
| `PRIMARY KEY` | All four tables (`id`) | Subject §4.2 — every table has a PK |
| `FOREIGN KEY` | `book.category_id`, `rental.member_id`, `rental.book_id` | Subject §4.2, §4.3 — establishes 1:N and blocks orphan rows |
| `NOT NULL` | `category.name`, `book.title`, `book.author`, `member.name`, `member.email`, `rental.rented_at`, `rental.due_at` | Subject §4.3 minimum ≥ 1; chosen so a row without them would be meaningless |
| `UNIQUE` | `category.name`, `book.isbn`, `member.email` | Subject §4.3 minimum ≥ 1; reflects real-world business invariants |
| `CHECK` (optional) | `rental.due_at >= rental.rented_at::date` if dialect-portable; otherwise document in comment | Defensive; not required by subject |

---

## 5. Query Plan (subject §4.5 — 15 queries)

Each query is preceded by a **one-line comment** in `03_queries.sql` stating what it verifies (subject §4.6). The grid below shows the **shape** of the 15; exact column lists and `WHERE` predicates are finalized during implementation.

| # | Category | Purpose (one-line description) |
| - | -------- | ------------------------------ |
| 1 | Basic select | List all members sorted by `joined_at DESC` (most recent first) |
| 2 | Basic select | Books published in or after 2015, ordered by year then title (`WHERE` + `ORDER BY`) |
| 3 | Basic select | Top 5 most recently rented books (`ORDER BY rented_at DESC LIMIT 5`) |
| 4 | Basic select | Members whose email ends with `@example.com` (`LIKE`) |
| 5 | INNER JOIN | Each rental shown with member name and book title |
| 6 | INNER JOIN | Books with their category name (excludes uncategorized) |
| 7 | LEFT JOIN | All members and their rental counts — including members with zero rentals |
| 8 | INNER JOIN + filter | Currently open rentals (`returned_at IS NULL`) with member and book info |
| 9 | Aggregate (`COUNT` + `GROUP BY`) | Number of books per category, sorted descending |
| 10 | Aggregate (`COUNT` + `GROUP BY`) | Rentals per member, only members with > 1 rental |
| 11 | Aggregate (`AVG` + `GROUP BY`) | Average rental duration in days per category (uses returned rentals only) |
| 12 | Subquery | Members who have rented more books than the average member |
| 13 | UPDATE | Mark a specific open rental as returned (`returned_at = CURRENT_TIMESTAMP`) |
| 14 | DELETE | Remove rental records older than a cutoff date for archival (with `WHERE`) |
| 15 | `CREATE INDEX` | Index on `rental(member_id, rented_at)` — accelerates queries #7 and #10; one-line comment justifies it |

**Coverage check against subject §4.5 minimums**

| Category | Minimum | Plan |
| -------- | ------- | ---- |
| Basic select | 4+ | #1–#4 (with `WHERE`/`ORDER BY`/`LIMIT`/`LIKE`) |
| Joins | 4+ (≥ 2 INNER, ≥ 1 LEFT) | #5, #6, #8 INNER; #7 LEFT; total 4 |
| Aggregate | 3+ (≥ 2 of `COUNT`/`SUM`/`AVG` + `GROUP BY`) | #9 `COUNT`, #10 `COUNT`, #11 `AVG` |
| Subquery | 1+ | #12 |
| Update/Delete | 2+ | #13, #14 |
| Index | 1+ with one-line rationale | #15 |

---

## 6. Phased Implementation Plan

Each phase = **one logical change = one commit** (.cursorrules §6 Logical Commit Unit), with Conventional Commits prefixes. (.cursorrules §2 "coarse steps: 3–7")

### Phase 0 — Repo scaffolding & ERD sketch

- Create `sql/` and `results/` folders; commit empty placeholders if needed (`.gitkeep`).
- Sketch ERD in dbdiagram.io; export as `docs/erd.png`.
- Commit: `chore: scaffold sql/results folders and add erd sketch`

### Phase 1 — Schema (`01_schema.sql`)

- Write `CREATE TABLE` for `category`, `book`, `member`, `rental` in dependency order.
- Add PK, FK, `NOT NULL`, `UNIQUE` per §4.3; include `PRAGMA foreign_keys = ON;` header.
- Smoke-test by running against a fresh `library.db` and confirming `.schema` output.
- Commit: `feat: add schema with 4 tables and 1:n relationships`

### Phase 2 — Seed data (`02_seed.sql`)

- Insert 10–15 rows per parent table (`category`, `book`, `member`) and 20–30 `rental` rows.
- Parents inserted before children (subject §4.4); FK values reference real parent IDs.
- Mix returned and open rentals so query #8 / #11 / #13 have non-empty results.
- Commit: `feat: add sample data for all tables`

### Phase 3 — Queries (`03_queries.sql`)

- Implement queries #1–#15 from §5, each with a one-line comment above it.
- Verify each returns a sensible row set against the seed data.
- Commit: `feat: add 15 core sql queries`

### Phase 4 — Result captures

- Run each query in DBeaver; screenshot the result grid; save as `results/qNN_<slug>.png`.
- Commit: `docs: capture execution results for 15 queries`

### Phase 5 — README & subject mapping

- `README.md`: intro, ERD image, how to recreate the DB (`sqlite3 library.db < sql/01_schema.sql ; sqlite3 library.db < sql/02_seed.sql`), how to view results, subject §2/§4 mapping table.
- Commit: `docs: add readme with run instructions and subject mapping`

### Phase 6 (Optional) — Bonus (subject §5)

- Only after core passes, in separate commits (.cursorrules §4 YAGNI).
- See `docs/bonus_plan.md` for join-vs-subquery comparison, integrity experiments, and the mini report.

---

## 7. Verification Strategy

This assignment has no automated test suite; use a **manual verification checklist** for acceptance (.cursorrules §6 Testing Determinism — SQL execution is deterministic given fixed seed data, but reviewer-driven so kept manual).

Checklist:

- [ ] `sqlite3 library.db < sql/01_schema.sql` runs cleanly; `.schema` shows 4 tables with PK/FK/NOT NULL/UNIQUE as designed.
- [ ] `sqlite3 library.db < sql/02_seed.sql` runs cleanly; `SELECT COUNT(*)` shows ≥ 10 rows per table.
- [ ] FK enforcement: inserting a `rental` with a non-existent `book_id` fails with a foreign-key error (proves §4.3 — FK must block bad references).
- [ ] `UNIQUE` enforcement: inserting a duplicate `book.isbn` or `member.email` fails.
- [ ] Each of the 15 queries in `03_queries.sql` runs without error and returns at least one row (except where the question's semantics allow empty, e.g. #14 after the cutoff).
- [ ] Coverage matrix (subject §4.5): 4+ basic, 4+ joins (2+ INNER, 1+ LEFT), 3+ aggregates (2+ kinds + `GROUP BY`), 1+ subquery, 2+ update/delete, 1+ `CREATE INDEX` — counted from `03_queries.sql`.
- [ ] Every query in `03_queries.sql` has a one-line `--` comment above it stating what it checks.
- [ ] `results/` contains 15 capture files with matching `qNN` prefixes; each is readable (column headers + row count visible).
- [ ] `EXPLAIN QUERY PLAN` on query #7 or #10 shows the new index from query #15 being used (or document why the optimizer chose otherwise).
- [ ] README documents the recreation steps and the subject mapping; running the steps from a clean checkout reproduces the same DB.

---

## 8. Risks / Deferred Decisions

| Item | Risk | Mitigation |
| ---- | ---- | ---------- |
| SQLite FK enforcement off by default | Reviewer runs scripts and FK checks silently pass on bad data | `PRAGMA foreign_keys = ON;` as the first non-comment line in every SQL file; called out in README |
| Dialect drift if reviewer uses MySQL/PostgreSQL | `AUTOINCREMENT` / `strftime` would fail | Mark dialect-specific lines with `-- SQLite-specific:` and prefer standard SQL where possible (subject §4.1) |
| Date arithmetic in query #11 | SQLite uses `julianday(...)`, PostgreSQL uses `-` between dates | Comment shows both forms; SQLite form is the one executed |
| Seed data drift between schema and inserts | Adding a NOT NULL column later breaks `02_seed.sql` | Treat the two as one logical change; if schema changes, re-run both from a fresh DB before committing |
| Result captures going stale after schema edits | Screenshots no longer match the current queries | Regenerate `results/` whenever `03_queries.sql` changes; the file count check in §7 catches drift |
| Index #15 not actually used | Optimizer ignores the new index | Either tweak the index columns to match the query's filter/sort, or document the observed plan in the comment (.cursorrules §1 — explain optimization choices) |
| Bonus vs plan drift | Later bonus choices may diverge from §2 | Update §2 table when starting bonus; note plan changes in commit message |

---

## 9. Definition of Done

- All four deliverables in subject §2 are met (schema design / schema SQL / seed SQL / 15 queries with captures).
- `01_schema.sql`, `02_seed.sql`, `03_queries.sql` exist under `sql/`, run in numeric order against a fresh SQLite DB, and produce the same `library.db` every time.
- Schema has **4 tables**, **3 1:N relationships**, PK on every table, FK with `ON DELETE RESTRICT`, ≥ 1 `NOT NULL` and ≥ 1 `UNIQUE` per subject §4.3.
- Each table has **≥ 10 rows** with realistic FK linkage; FK and UNIQUE violations are reproducible from the verification checklist (subject §4.4).
- `03_queries.sql` covers all six query categories at or above the subject §4.5 minimums; every query has a one-line purpose comment.
- One `CREATE INDEX` exists with a one-line comment explaining the column choice (subject §4.5 final row).
- `results/` contains a result capture per query, matched by `qNN` prefix (subject §4.6).
- `README.md` includes intro, ERD, recreation steps, and subject §2/§4 mapping (subject §4.7).
- All six learning objectives in subject §3 can be explained from this plan §3–§5 and the implementation.
