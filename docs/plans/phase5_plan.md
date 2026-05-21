# Phase 5 — README & Subject Mapping

> Parent plan: [`docs/plan.md`](../plan.md) §6 Phase 5
> Subject reference: [`docs/subject.md`](../subject.md) §2.4, §4.6, §4.7

This is the final phase of the core deliverable. After this, a reviewer who has never seen the repo before should be able to **recreate the database, run the 15 queries, and verify the results** by following only the README. Per `.cursorrules` §1, the README is the single source of truth for "what is this and how do I run it"; deep design rationale stays in `docs/plan.md`.

---

## 1. Goal

- Author `README.md` so it stands alone as a reviewer-facing front page.
- Map every subject §2 / §4 requirement to a concrete file or section in the repo (subject §4.7 "submission structure").
- Document the **exact** commands to recreate `library.db` and run each SQL file in order (Phase 0–2 file naming was chosen to make this trivial: `01_… → 02_… → 03_…`).
- Embed the ERD from Phase 0 (`docs/erd.png`) and link to the result captures from Phase 4.
- Result: a freshly-cloned reviewer following only the README produces the same `library.db` and sees the same 15 result rows / captures.

---

## 2. Scope (In / Out)

**In scope**
- `README.md` at the repo root (`05-1.my_db/README.md`).
- Sections: title / intro / ERD / stack / how to run / file layout / 15-query summary / subject mapping table / known limitations.
- Inline links to `docs/plan.md`, `docs/bonus_plan.md`, `sql/`, `results/`.
- A "Subject mapping" table mirroring subject §2.1–§2.4 and §4.1–§4.7, each row pointing at the file/section that fulfills it.

**Out of scope**
- Any change to schema, seed, queries, or captures (Phases 1–4 own them).
- Bonus content — subject §5 belongs in `docs/bonus_plan.md` and a future bonus phase; the README only references it ("See docs/bonus_plan.md for join-vs-subquery comparison etc.").
- CI / GitHub Actions / linting setup — none required by subject.
- A separate CONTRIBUTING.md or LICENSE — this is a learning artifact, not a maintained project.

---

## 3. Tasks

### 3.1 README skeleton
Recommended top-to-bottom order:

```md
# SQL Database Practice — Library Domain

Brief 2–3 sentence intro: what this repo demonstrates (4-table schema with 1:N relationships, 15 core queries, captured results) and which DB it targets (SQLite).

## ERD

![ERD](./docs/erd.png)

(One paragraph naming the four tables and the three 1:N edges — copy the wording from `docs/plan.md` §4.1.)

## Stack

- **DB**: SQLite (file-based; portable; no server required).
- **Client**: DBeaver for capturing result grids; `sqlite3` CLI for scripted runs.
- **Plan / decisions**: see [`docs/plan.md`](./docs/plan.md).

## How to Run

```bash
# 1. (Re)create the DB from scratch.
rm -f library.db
sqlite3 library.db < sql/01_schema.sql
sqlite3 library.db < sql/02_seed.sql

# 2. Run the 15 queries (prints results to stdout in CLI; open in DBeaver to capture).
sqlite3 library.db < sql/03_queries.sql
```

Or open `sql/03_queries.sql` in DBeaver, execute each query in order, and compare to `results/qNN_*.png`.

## File Layout

(short tree mirroring `docs/plan.md` §3 — only the top two levels)

## 15 Queries at a Glance

(table copied from `docs/plan.md` §5 — query number, category, one-line purpose, capture link)

| # | Category | Purpose | Capture |
| - | -------- | ------- | ------- |
| 1 | Basic select | List all members sorted by `joined_at DESC`. | [`results/q01_*.png`](./results/q01_members_by_joined_desc.png) |
| … | …        | …       | …       |
| 15| Index | `CREATE INDEX idx_rental_member_rented`. | [`results/q15_*.png`](./results/q15_create_index_done.png) |

## Subject Mapping

(see §3.2)

## Known Limitations

- FK enforcement requires `PRAGMA foreign_keys = ON;` in SQLite (handled in every SQL file).
- The `julianday(...)` expression in query #11 is SQLite-specific; portable form is commented inline.
- Sample data and rendered emails are placeholders (`@example.com`); no real PII.

## Bonus

See [`docs/bonus_plan.md`](./docs/bonus_plan.md) for join-vs-subquery comparison, integrity experiments, and the mini metrics report.
```

### 3.2 Subject mapping table
Place at the same level as "## Subject Mapping" above. The table is the single most important reviewer-facing artifact in the README because subject §4.7 expects an explicit submission map.

| Subject ref | Requirement | Where it lives |
| ----------- | ----------- | -------------- |
| §2.1 | Domain DB design (≥ 4 tables, ≥ 2 1:N relationships) | `sql/01_schema.sql` + `docs/plan.md` §4 + `docs/erd.png` |
| §2.2 | Schema creation script | `sql/01_schema.sql` |
| §2.3 | Sample data insert script (≥ 10 rows/table) | `sql/02_seed.sql` |
| §2.4 | 15 core queries + result captures | `sql/03_queries.sql` + `results/qNN_*.png` |
| §4.1 | DB choice + portability notes | README "Stack" section + inline `-- SQLite-specific:` comments in `sql/*.sql` |
| §4.2 | Schema design (≥ 4 tables, PKs, FKs, 1:N, sensible types/names) | `sql/01_schema.sql` |
| §4.3 | Constraints (≥ 1 NOT NULL, ≥ 1 UNIQUE, FK blocks orphans) | `sql/01_schema.sql` + verification command in README |
| §4.4 | Sample data (≥ 10 rows, parents-before-children, realistic FK links) | `sql/02_seed.sql` |
| §4.5 | 15 queries with coverage matrix (4 basic / 4 joins / 3 aggregates / 1 subquery / 2 update-delete / 1 index) | `sql/03_queries.sql` (footer tally) |
| §4.6 | One-line description per query + verifiable results | inline `-- Query NN:` comments + `results/qNN_*.png` |
| §4.7 | Submission structure (one schema SQL, one seed SQL, one queries SQL, one captures folder, optional ERD) | repo layout matches; ERD at `docs/erd.png` |

Each row's "Where it lives" cell is a hyperlink in the actual README so a reviewer can click through.

### 3.3 Verification commands snippet
Inside "Known Limitations" or in a small "Verifying constraints" subsection, paste the one-line tests that prove the FK + UNIQUE constraints work. This is the lowest-friction way for a reviewer to satisfy subject §4.3 "FK must block bad references":

```bash
# FK enforcement check (should fail with "FOREIGN KEY constraint failed").
sqlite3 library.db "INSERT INTO rental (member_id, book_id, rented_at, due_at) VALUES (9999, 9999, '2026-01-01 00:00:00', '2026-01-15');"

# UNIQUE enforcement check (should fail with "UNIQUE constraint failed").
sqlite3 library.db "INSERT INTO member (name, email, joined_at) VALUES ('Dup', 'alice.kim@example.com', '2026-01-01');"
```

### 3.4 ERD verification
Open `docs/erd.png` and confirm it still shows:

- `category` (left), `book` (center-left), `rental` (center), `member` (right).
- Three labeled 1:N edges as in `plan.md` §4.1.

If Phase 1's schema diverged from the Phase 0 ERD, re-export now — this is the last gate before the deliverable is "done".

---

## 4. Files Touched

| File | Action |
| ---- | ------ |
| `README.md` | full content per §3.1 / §3.2 / §3.3 |
| `docs/erd.png` | regenerate **only if** Phase 1 changed the schema (likely no-op) |

No source code, SQL, or capture changes in this phase.

---

## 5. Acceptance Criteria

- [ ] `README.md` exists at `05-1.my_db/README.md` and renders cleanly in GitHub's markdown preview (no broken links, no missing image).
- [ ] The "How to Run" section is **copy-pasteable** — a reviewer can paste the three commands and produce a working `library.db` from a fresh clone.
- [ ] The "15 Queries at a Glance" table has exactly 15 rows, one per query, each linking to the matching `results/qNN_*.png` (links resolve when clicked from GitHub).
- [ ] The "Subject Mapping" table covers every row in subject §2.1–§2.4 and §4.1–§4.7; each cell links to the file/section that fulfills it.
- [ ] The "Verifying constraints" commands fail as advertised on a freshly-seeded DB (smoke-test before committing).
- [ ] `docs/erd.png` is referenced via `![ERD](./docs/erd.png)` and renders inline.
- [ ] No mention of bonus content beyond a one-line pointer to `docs/bonus_plan.md`.
- [ ] No new placeholder text (no `TODO`, no `Lorem ipsum`, no `your-handle-here`).

---

## 6. Commit

```
docs: add readme with run instructions and subject mapping
```

One commit covers the full README per `.cursorrules` §6. Do **not** bundle README content with schema or query edits.

---

## 7. Risks / Notes

- **Stale README is worse than no README.** If you later iterate on schema, seed, or queries, update the README in the **same** commit as the SQL change — never as a follow-up "docs:" commit that ships hours later.
- **Broken image links** are the most common README failure. Always use **relative** paths (`./docs/erd.png`, `./results/q07_member_rental_count_left_join.png`) — they work in GitHub, in local previews, and in any markdown viewer.
- **Subject mapping drift.** If you renumber a query in `03_queries.sql`, both the "15 Queries at a Glance" table and the corresponding `results/qNN_*.png` filename must update in lockstep. The acceptance check for "links resolve" catches this only if you actually click each link before committing.
- **`sqlite3` CLI vs DBeaver result formatting.** The "How to Run" CLI snippet prints results to stdout; the captures in `results/` are from DBeaver. The README should clarify both paths so a reviewer who prefers either one can verify.
- **Bonus drift.** A reviewer skimming the README must not see hints of bonus content in the core sections — it dilutes the "core is done" signal. Keep the single one-line pointer at the end.
- **Sensitive data.** Confirm no real names, emails, or phone numbers leaked into seed data before committing (everything ends in `@example.com`).

---

## 8. Definition of Done

- README documents intro / ERD / stack / how to run / file layout / 15-query summary / subject mapping / limitations.
- A fresh-clone reviewer following only the README reproduces `library.db` and verifies all 15 queries against the captures.
- Subject §2.1–§2.4 and §4.1–§4.7 each map to a concrete file/section.
- The core assignment (Phases 0–5) is now complete; any further work belongs in `docs/bonus_plan.md` and a future bonus phase.
