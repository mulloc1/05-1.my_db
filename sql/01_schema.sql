-- 01_schema.sql — CREATE TABLE statements for the library domain
-- Run order: 01_schema.sql → 02_seed.sql → 03_queries.sql
-- SQLite-specific: PRAGMA foreign_keys = ON; (FK enforcement is OFF by default in SQLite)

PRAGMA foreign_keys = ON;

-- Drop in reverse dependency order so re-running the script does not break on FKs.
DROP TABLE IF EXISTS rental;
DROP TABLE IF EXISTS book;
DROP TABLE IF EXISTS member;
DROP TABLE IF EXISTS category;

CREATE TABLE category (
  id          INTEGER PRIMARY KEY,        -- SQLite: implicit rowid alias
  name        TEXT    NOT NULL UNIQUE,
  description TEXT
);

CREATE TABLE book (
  id             INTEGER PRIMARY KEY,
  title          TEXT    NOT NULL,
  author         TEXT    NOT NULL,
  isbn           TEXT    UNIQUE,
  published_year INTEGER,
  category_id    INTEGER NOT NULL,
  FOREIGN KEY (category_id) REFERENCES category(id) ON DELETE RESTRICT
);

CREATE TABLE member (
  id        INTEGER  PRIMARY KEY,
  name      TEXT     NOT NULL,
  email     TEXT     NOT NULL UNIQUE,
  phone     TEXT,
  -- SQLite-specific: CURRENT_TIMESTAMP default; joined_at stored as TEXT ISO-8601
  joined_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE rental (
  id          INTEGER  PRIMARY KEY,
  member_id   INTEGER  NOT NULL,
  book_id     INTEGER  NOT NULL,
  rented_at   DATETIME NOT NULL,
  due_at      DATE     NOT NULL,
  returned_at DATETIME NULL,
  FOREIGN KEY (member_id) REFERENCES member(id) ON DELETE RESTRICT,
  FOREIGN KEY (book_id)   REFERENCES book(id)   ON DELETE RESTRICT,
  -- SQLite-specific: date() for CHECK; PostgreSQL would use due_at >= rented_at::date
  CHECK (due_at >= date(rented_at))
);
