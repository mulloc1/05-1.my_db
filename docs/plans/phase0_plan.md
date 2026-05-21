# Phase 0 — Repo Scaffolding & ERD Sketch

> Parent plan: [`docs/plan.md`](../plan.md) §6 Phase 0
> Subject reference: [`docs/subject.md`](../subject.md) §4.1, §4.2, §4.7

This phase lays the **bare-minimum project skeleton** so every later phase has a stable place to drop SQL files and result captures. No tables, no rows, no queries yet — just the directory layout and a visual ERD sketch that locks the schema decisions in `plan.md` §4 before any `CREATE TABLE` is written. Following `.cursorrules` §4 (Minimal-First / YAGNI), nothing more is added here than what is needed to scaffold.

---

## 1. Goal

- Create the static folder layout exactly as locked in `plan.md` §3 (`sql/`, `results/`, `docs/`).
- Draft an **ERD** matching `plan.md` §4.1 (`category ──< book ──< rental >── member`) in dbdiagram.io and export it as `docs/erd.png`.
- Add a `.gitignore` that excludes the SQLite build artifact (`library.db`) so it never leaks into commits.
- Result: `tree 05-1.my_db/` shows the three target folders with placeholder files; the ERD image renders in any markdown viewer.

---

## 2. Scope (In / Out)

**In scope**
- Folder creation: `sql/`, `results/`, `docs/` (the last already exists with `subject.md` / `plan.md` / `bonus_plan.md`).
- Empty placeholder SQL files (`sql/01_schema.sql`, `sql/02_seed.sql`, `sql/03_queries.sql`) so Phase 1–3 only edit existing files.
- `.gitkeep` (or equivalent) inside `results/` so the empty directory is tracked.
- `.gitignore` entry for `library.db` (and `*.db` if you want headroom).
- `docs/erd.png` exported from dbdiagram.io reflecting the four-table model in `plan.md` §4.

**Out of scope**
- Any `CREATE TABLE` statements (Phase 1).
- Any `INSERT` statements (Phase 2).
- Any `SELECT`/`JOIN`/`GROUP BY` queries (Phase 3).
- Result captures (Phase 4).
- README content (Phase 5).

---

## 3. Tasks

### 3.1 Directory tree
Create exactly this structure under `05-1.my_db/` (Phase 0 files are filled with placeholders only; others are empty stubs):

```
05-1.my_db/
├── README.md                 # placeholder — filled in Phase 5
├── docs/
│   ├── subject.md            # already exists
│   ├── plan.md               # already exists
│   ├── bonus_plan.md         # already exists
│   ├── plans/                # this folder of phase plans
│   └── erd.png               # new — ERD export from dbdiagram.io
├── sql/
│   ├── 01_schema.sql         # empty (header comment only)
│   ├── 02_seed.sql           # empty (header comment only)
│   └── 03_queries.sql        # empty (header comment only)
├── results/
│   └── .gitkeep              # tracks the empty folder
└── .gitignore                # ignores library.db, *.db-journal
```

### 3.2 Placeholder SQL files
Each of the three SQL files should be created with **only a header comment** so Phase 1–3 can append content without an extra "create file" step. Use the same header format across the three:

```sql
-- 01_schema.sql — CREATE TABLE statements for the library domain
-- Run order: 01_schema.sql → 02_seed.sql → 03_queries.sql
-- SQLite-specific: PRAGMA foreign_keys = ON;

PRAGMA foreign_keys = ON;
```

- `PRAGMA foreign_keys = ON;` is included in all three files because SQLite's FK enforcement is **off by default** (`plan.md` §8 risk #1). Adding it at the top of every file means a reviewer cannot run any one of them without FK checks active.

### 3.3 ERD sketch
- Open dbdiagram.io and model the four tables from `plan.md` §4.2: `category`, `book`, `member`, `rental`.
- Mark the three 1:N edges per `plan.md` §4.1:
  - `category` 1:N `book`
  - `book` 1:N `rental`
  - `member` 1:N `rental`
- Export as PNG and save to `docs/erd.png`. The exact diagram styling is implementation-time (.cursorrules §2 — not part of the locked plan).
- Embed the path in `README.md` placeholder so Phase 5 only needs to fill the surrounding copy.

### 3.4 `.gitignore`
Add (or create) `.gitignore` with at least these entries:

```
library.db
*.db-journal
.DS_Store
```

- `library.db` is a **build artifact** — Phase 1 + Phase 2 reproduce it deterministically. Ignoring it keeps diffs small and avoids checking in stale binaries.
- `*.db-journal` covers SQLite's transient journal files.

---

## 4. Files Touched

| File | Action |
| ---- | ------ |
| `sql/01_schema.sql` | create (header comment + `PRAGMA foreign_keys = ON;`) |
| `sql/02_seed.sql` | create (same header pattern) |
| `sql/03_queries.sql` | create (same header pattern) |
| `results/.gitkeep` | create (empty) |
| `docs/erd.png` | create (export from dbdiagram.io) |
| `README.md` | create (placeholder — Phase 5 fills it) |
| `.gitignore` | create or update (`library.db`, `*.db-journal`, `.DS_Store`) |

---

## 5. Acceptance Criteria

- [ ] `tree 05-1.my_db/` matches the layout in §3.1 (all directories and placeholder files exist).
- [ ] Each `sql/*.sql` file opens cleanly in DBeaver / `sqlite3` and contains exactly the header + `PRAGMA foreign_keys = ON;` (no other statements).
- [ ] `docs/erd.png` renders four tables (`category`, `book`, `member`, `rental`) and three labeled 1:N relationships.
- [ ] `git status` shows `library.db` is **not** tracked even after running an empty `sqlite3 library.db ".quit"` smoke test.
- [ ] `results/` is tracked via `.gitkeep` so the folder survives a fresh clone.
- [ ] `README.md` exists with at least a title and an `![ERD](./docs/erd.png)` placeholder — full content is Phase 5.

---

## 6. Commit

```
chore: scaffold sql/results folders and add erd sketch
```

One commit covers the whole scaffold per `.cursorrules` §6 Logical Commit Unit.

---

## 7. Risks / Notes

- **`PRAGMA foreign_keys` must be at the top of every SQL file.** It is session-scoped in SQLite; running a file from a fresh `sqlite3` invocation without it silently disables FK checks. The duplicated header is intentional, not a copy-paste smell.
- **ERD drift.** If the schema in Phase 1 diverges from `docs/erd.png`, re-export immediately in the same commit. The ERD is reviewer-facing; a stale image is worse than no image.
- **Do not pre-seed `README.md`.** Keep it a one-line placeholder so Phase 5's diff is meaningful (full intro / run instructions / subject mapping). Avoid the "README written too early then rewritten" anti-pattern.
- Resist the urge to start writing `CREATE TABLE` here. Phase 1 owns that, and mixing scaffold + schema in one commit blurs the rollback boundary.

---

## 8. Definition of Done

- All folders and placeholder files in `plan.md` §3 directory tree exist.
- ERD image accurately reflects the locked schema decisions in `plan.md` §4.
- `.gitignore` keeps the SQLite build artifact out of version control.
- Every later phase can edit existing files instead of creating structure.
