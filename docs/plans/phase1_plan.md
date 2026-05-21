# Phase 1 — Schema (`01_schema.sql`)

> Parent plan: [`docs/plan.md`](../plan.md) §6 Phase 1
> Subject reference: [`docs/subject.md`](../subject.md) §2.1, §2.2, §4.2, §4.3

This phase converts the ERD sketch from Phase 0 into an executable `CREATE TABLE` script. After this phase, running `sqlite3 library.db < sql/01_schema.sql` against a fresh DB produces the **four-table, three-1:N** schema locked in `plan.md` §4 — with PKs, FKs, NOT NULL, and UNIQUE constraints in place. No rows yet; that is Phase 2.

---

## 1. Goal

- Author `sql/01_schema.sql` so it creates `category`, `book`, `member`, `rental` in **dependency order** (parents before children).
- Encode every constraint from `plan.md` §4.3: PK on every table, FK with `ON DELETE RESTRICT`, ≥ 1 NOT NULL, ≥ 1 UNIQUE.
- Keep the file **idempotent-friendly** for development: each `CREATE TABLE` is preceded by a `DROP TABLE IF EXISTS` in **reverse** dependency order, so a developer can re-run the script during iteration without dropping the DB file.
- Result: `.schema` in `sqlite3` shows four tables with the expected columns, constraints, and FK declarations.

---

## 2. Scope (In / Out)

**In scope**
- `PRAGMA foreign_keys = ON;` at the top (already present from Phase 0 — verify).
- `DROP TABLE IF EXISTS` block in **reverse** dependency order (`rental`, `book`, `member`, `category`).
- `CREATE TABLE` for each of the four tables with columns, types, PK, FK (`ON DELETE RESTRICT`), NOT NULL, UNIQUE, defaults.
- Inline `-- SQLite-specific:` comments above any non-standard syntax (`AUTOINCREMENT`, `CURRENT_TIMESTAMP` defaults, etc.).
- A short header comment block summarizing run order and FK enforcement note.

**Out of scope**
- Any `INSERT` statement (Phase 2).
- Any query (Phase 3).
- `CREATE INDEX` (Phase 3, query #15 owns this).
- Views, triggers, generated columns — none are required by subject §4.
- `CHECK` constraints beyond the optional `rental.due_at >= date(rental.rented_at)` noted in `plan.md` §4.3 (add only if portable; document otherwise).

---

## 3. Tasks

### 3.1 File header
Top of `sql/01_schema.sql`:

```sql
-- 01_schema.sql — CREATE TABLE statements for the library domain
-- Run order: 01_schema.sql → 02_seed.sql → 03_queries.sql
-- SQLite-specific: PRAGMA foreign_keys = ON; (FK enforcement is OFF by default in SQLite)

PRAGMA foreign_keys = ON;

-- Drop in reverse dependency order so re-running the script does not break on FKs.
DROP TABLE IF EXISTS rental;
DROP TABLE IF EXISTS book;
DROP TABLE IF EXISTS member;
DROP TABLE IF EXISTS category;
```

### 3.2 `category`
- Parent of `book`. Smallest table, often-static lookup.

```sql
CREATE TABLE category (
  id          INTEGER PRIMARY KEY,        -- SQLite: implicit rowid alias
  name        TEXT    NOT NULL UNIQUE,
  description TEXT
);
```

Constraint mapping (`plan.md` §4.3):
- PK: `id`
- NOT NULL: `name`
- UNIQUE: `name`

### 3.3 `book`
- 1:N child of `category`. Carries the `isbn` UNIQUE business key.

```sql
CREATE TABLE book (
  id             INTEGER PRIMARY KEY,
  title          TEXT    NOT NULL,
  author         TEXT    NOT NULL,
  isbn           TEXT    UNIQUE,
  published_year INTEGER,
  category_id    INTEGER NOT NULL,
  FOREIGN KEY (category_id) REFERENCES category(id) ON DELETE RESTRICT
);
```

Constraint mapping:
- PK: `id`
- NOT NULL: `title`, `author`, `category_id`
- UNIQUE: `isbn`
- FK: `category_id → category(id)` with `ON DELETE RESTRICT` (`plan.md` §2 lock)

### 3.4 `member`
- 1:N child of nothing in this scope; parent of `rental`.

```sql
CREATE TABLE member (
  id        INTEGER  PRIMARY KEY,
  name      TEXT     NOT NULL,
  email     TEXT     NOT NULL UNIQUE,
  phone     TEXT,
  joined_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP   -- SQLite stores as TEXT ISO-8601
);
```

Constraint mapping:
- PK: `id`
- NOT NULL: `name`, `email`, `joined_at`
- UNIQUE: `email`

### 3.5 `rental`
- 1:N child of both `book` and `member`. Drives every interesting query in Phase 3.

```sql
CREATE TABLE rental (
  id          INTEGER  PRIMARY KEY,
  member_id   INTEGER  NOT NULL,
  book_id     INTEGER  NOT NULL,
  rented_at   DATETIME NOT NULL,
  due_at      DATE     NOT NULL,
  returned_at DATETIME NULL,
  FOREIGN KEY (member_id) REFERENCES member(id) ON DELETE RESTRICT,
  FOREIGN KEY (book_id)   REFERENCES book(id)   ON DELETE RESTRICT,
  -- Optional CHECK: only added if dialect-portable for the reviewer's RDBMS.
  CHECK (due_at >= date(rented_at))
);
```

Constraint mapping:
- PK: `id`
- NOT NULL: `member_id`, `book_id`, `rented_at`, `due_at`
- FK: `member_id → member(id)`, `book_id → book(id)`, both `ON DELETE RESTRICT`
- CHECK: `due_at >= date(rented_at)` — defensive; covered by `-- SQLite-specific: date(...)` comment if the reviewer is on a different RDBMS.

### 3.6 Smoke test (manual)
After saving the file, run:

```bash
rm -f library.db
sqlite3 library.db < sql/01_schema.sql
sqlite3 library.db ".schema"
sqlite3 library.db "PRAGMA foreign_key_list(rental);"
```

- `.schema` should print all four tables.
- `PRAGMA foreign_key_list(rental)` must return two rows (one per FK).
- Re-running the same script must succeed (idempotency proven by the `DROP TABLE IF EXISTS` block).

---

## 4. Files Touched

| File | Action |
| ---- | ------ |
| `sql/01_schema.sql` | full implementation: header + `PRAGMA` + drops + 4 `CREATE TABLE`s |
| `library.db` | regenerated locally for smoke testing (not committed — `.gitignore`d in Phase 0) |

No other files change in this phase.

---

## 5. Acceptance Criteria

- [ ] `sqlite3 library.db < sql/01_schema.sql` exits 0 against a fresh DB **and** against an existing DB (idempotency via `DROP TABLE IF EXISTS`).
- [ ] `.schema` lists exactly four tables: `category`, `book`, `member`, `rental`.
- [ ] `PRAGMA foreign_key_list(book);` shows the FK to `category`.
- [ ] `PRAGMA foreign_key_list(rental);` shows two FKs (`member`, `book`), both with `on_delete = "RESTRICT"`.
- [ ] Constraint count by category (counted from the file):
  - PK: 4 (one per table)
  - FK: 3 (`book.category_id`, `rental.member_id`, `rental.book_id`)
  - NOT NULL: ≥ 1 (we have 7+)
  - UNIQUE: ≥ 1 (we have `category.name`, `book.isbn`, `member.email`)
- [ ] Any SQLite-specific line is preceded by a `-- SQLite-specific:` comment per `plan.md` §2 portability lock.
- [ ] No `CREATE INDEX`, no `INSERT`, no `SELECT` appears in this file (those belong to later phases).

---

## 6. Commit

```
feat: add schema with 4 tables and 1:n relationships
```

One commit covers the whole schema per `.cursorrules` §6 Logical Commit Unit. The diff is the entire `01_schema.sql` body.

---

## 7. Risks / Notes

- **FK enforcement off by default in SQLite.** Without `PRAGMA foreign_keys = ON;` the FK declarations are *documentation only*. The header `PRAGMA` is the single most important line in the file — do not drop it during cleanup.
- **`ON DELETE RESTRICT` blocks parent deletion when children exist.** This is the safe default for the assignment; the bonus phase explores `CASCADE` separately. If a reviewer expects parent-delete to silently cascade, point them at `bonus_plan.md`.
- **Type affinity, not strict types, in SQLite.** `INTEGER`, `TEXT`, `DATE`, `DATETIME` are *suggestions* to SQLite. The schema still satisfies subject §4.2 because portable RDBMSes treat them strictly; comment any column where the difference matters (`joined_at` is stored as ISO-8601 TEXT under SQLite — already noted).
- **`AUTOINCREMENT` is intentionally omitted.** `INTEGER PRIMARY KEY` aliases SQLite's `rowid`, which auto-increments without the extra keyword and avoids the extra `sqlite_sequence` table. If portability to MySQL/PostgreSQL is needed, switch to `INTEGER PRIMARY KEY AUTOINCREMENT` (MySQL: `AUTO_INCREMENT`; PostgreSQL: `GENERATED ALWAYS AS IDENTITY`) and comment the swap.
- **`CHECK (due_at >= date(rented_at))` uses SQLite's `date()` function.** PostgreSQL would use `due_at >= rented_at::date`. If you switch RDBMS, update the expression and the comment in the same commit.
- **Drift between schema and seed.** Adding a NOT NULL column later breaks `02_seed.sql`. Treat Phase 1 and Phase 2 as one logical pair: if you have to amend Phase 1 after Phase 2 is written, re-run both from a fresh DB before committing the schema change.

---

## 8. Definition of Done

- `01_schema.sql` runs end-to-end on a fresh SQLite DB and produces the four tables with all constraints declared in `plan.md` §4.
- Every constraint required by subject §4.3 (PK on every table, ≥ 2 FK 1:N, ≥ 1 NOT NULL, ≥ 1 UNIQUE) is satisfied and verifiable via `PRAGMA` introspection.
- `library.db` can be deleted and regenerated from this file alone (Phase 2 will add data on top).
- Phase 2 can start writing `INSERT` statements without changing any line in this file.
