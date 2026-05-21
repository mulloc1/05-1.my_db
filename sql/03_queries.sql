-- 03_queries.sql — 15 core SQL queries for the library domain
-- Run order: 01_schema.sql → 02_seed.sql → 03_queries.sql
-- Categories (subject §4.5):
--   Basic select: 4   Joins (INNER): 3   Joins (LEFT): 1
--   Aggregates:  3   Subquery: 1        Update/Delete: 2   Index: 1
-- SQLite-specific syntax (date('now', ...), julianday(...)) is commented per-query.

PRAGMA foreign_keys = ON;

-- Query 01: List all members sorted by joined_at (most recent first).
SELECT id, name, email, joined_at
FROM member
ORDER BY joined_at DESC;

-- Query 02: Books published in or after 2015, ordered by year then title.
SELECT id, title, author, published_year
FROM book
WHERE published_year >= 2015
ORDER BY published_year ASC, title ASC;

-- Query 03: Top 5 most recently rented books, newest rental first.
SELECT b.id, b.title, b.author, r.rented_at
FROM rental r
INNER JOIN book b ON b.id = r.book_id
ORDER BY r.rented_at DESC
LIMIT 5;

-- Query 04: Members whose email ends with @example.com.
SELECT id, name, email
FROM member
WHERE email LIKE '%@example.com';

-- Query 05: Each rental shown with member name and book title (INNER JOIN, no orphans).
SELECT r.id, m.name AS member_name, b.title AS book_title, r.rented_at, r.due_at
FROM rental r
INNER JOIN member m ON m.id = r.member_id
INNER JOIN book   b ON b.id = r.book_id
ORDER BY r.rented_at DESC;

-- Query 06: Each book with its category name (excludes uncategorized).
SELECT b.id, b.title, b.author, c.name AS category_name
FROM book b
INNER JOIN category c ON c.id = b.category_id
ORDER BY c.name ASC, b.title ASC;

-- Query 07: All members and their rental counts, including members with zero rentals.
SELECT m.id, m.name, COUNT(r.id) AS rental_count
FROM member m
LEFT JOIN rental r ON r.member_id = m.id
GROUP BY m.id, m.name
ORDER BY rental_count DESC, m.name ASC;

-- Query 08: Currently open rentals (returned_at IS NULL) with member and book info.
SELECT r.id, m.name AS member_name, b.title AS book_title, r.rented_at, r.due_at
FROM rental r
INNER JOIN member m ON m.id = r.member_id
INNER JOIN book   b ON b.id = r.book_id
WHERE r.returned_at IS NULL
ORDER BY r.rented_at DESC;

-- Query 09: Number of books per category, sorted descending.
SELECT c.name AS category, COUNT(b.id) AS book_count
FROM category c
LEFT JOIN book b ON b.category_id = c.id
GROUP BY c.id, c.name
ORDER BY book_count DESC, c.name ASC;

-- Query 10: Rentals per member, only members with more than one rental.
SELECT m.id, m.name, COUNT(r.id) AS rental_count
FROM member m
INNER JOIN rental r ON r.member_id = m.id
GROUP BY m.id, m.name
HAVING COUNT(r.id) > 1
ORDER BY rental_count DESC;

-- Query 11: Average rental duration in days per category (returned rentals only).
-- SQLite-specific: julianday() for day diff; Postgres: (returned_at::date - rented_at::date)
SELECT c.name AS category,
       ROUND(AVG(julianday(r.returned_at) - julianday(r.rented_at)), 1) AS avg_days
FROM rental r
INNER JOIN book b ON b.id = r.book_id
INNER JOIN category c ON c.id = b.category_id
WHERE r.returned_at IS NOT NULL
GROUP BY c.id, c.name
ORDER BY avg_days DESC;

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

-- Query 13: Mark a specific open rental as returned (returned_at = current timestamp).
-- SQLite-specific: CURRENT_TIMESTAMP stored as TEXT ISO-8601
UPDATE rental
SET returned_at = CURRENT_TIMESTAMP
WHERE id = 2 AND returned_at IS NULL;

-- Query 14: Archive rentals older than one year that have been returned (DELETE).
-- SQLite-specific: date('now', '-1 year'); Postgres: rented_at < CURRENT_DATE - INTERVAL '1 year'
DELETE FROM rental
WHERE returned_at IS NOT NULL
  AND rented_at < date('now', '-1 year');

-- Query 15: Index on rental(member_id, rented_at) — accelerates queries #7 and #10
--          (group/aggregate on member_id) and #3 (ORDER BY rented_at DESC LIMIT 5).
--          Composite order (member_id, rented_at) supports equality on member_id
--          and range/sort on rented_at without an extra single-column index.
CREATE INDEX IF NOT EXISTS idx_rental_member_rented
  ON rental(member_id, rented_at);

-- Coverage tally:
--   Basic select: 4   (#1–#4)
--   Joins:        4   (#5 INNER, #6 INNER, #7 LEFT, #8 INNER)
--   Aggregates:   3   (#9 COUNT, #10 COUNT, #11 AVG; all with GROUP BY)
--   Subquery:     1   (#12)
--   Update/Delete: 2  (#13 UPDATE, #14 DELETE)
--   Index:        1   (#15 CREATE INDEX)
