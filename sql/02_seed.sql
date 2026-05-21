-- 02_seed.sql — Sample data for the library domain
-- Run order: 01_schema.sql → 02_seed.sql → 03_queries.sql
-- Row counts: category=12, book=15, member=12, rental=25 (≥ subject §4.4 minimum of 10/table)
-- Coverage: member#12 zero rentals; open+returned rentals; rentals older than 1 year for query #14
-- SQLite-specific: PRAGMA foreign_keys = ON; (must be ON or FKs are silently ignored)

PRAGMA foreign_keys = ON;

-- Clear in reverse dependency order so re-running is safe.
DELETE FROM rental;
DELETE FROM book;
DELETE FROM member;
DELETE FROM category;

INSERT INTO category (id, name, description) VALUES
  (1,  'Fiction',     'Novels and short stories'),
  (2,  'Non-fiction', 'Essays, journalism, and general non-fiction'),
  (3,  'Science',     'Natural and applied sciences'),
  (4,  'History',     'Historical works and biographies of historical figures'),
  (5,  'Technology',  'Computing, engineering, and technical manuals'),
  (6,  'Biography',   'Life stories of notable people'),
  (7,  'Children',    'Books for young readers'),
  (8,  'Cooking',     'Recipes and culinary guides'),
  (9,  'Travel',      'Guides and travel writing'),
  (10, 'Art',         'Visual arts, design, and aesthetics'),
  (11, 'Philosophy',  'Ethics, logic, and philosophical treatises'),
  (12, 'Reference',   'Dictionaries and encyclopedias');

INSERT INTO book (id, title, author, isbn, published_year, category_id) VALUES
  (1,  'Clean Code',                    'Robert C. Martin',    '978-0-13-235088-4', 2008, 5),
  (2,  'The Pragmatic Programmer',      'Andrew Hunt',         '978-0-201-61622-4', 1999, 5),
  (3,  'A Brief History of Time',       'Stephen Hawking',     '978-0-553-38016-3', 1998, 3),
  (4,  'Sapiens',                       'Yuval Noah Harari',   '978-0-06-231609-7', 2011, 4),
  (5,  'Dune',                          'Frank Herbert',       '978-0-441-17271-9', 1965, 1),
  (6,  '1984',                          'George Orwell',       '978-0-452-28423-4', 1949, 1),
  (7,  'To Kill a Mockingbird',         'Harper Lee',          '978-0-06-112008-4', 1960, 1),
  (8,  'The Selfish Gene',              'Richard Dawkins',     '978-0-19-929115-1', 1976, 3),
  (9,  'Educated',                      'Tara Westover',       '978-0-399-59050-4', 2018, 6),
  (10, 'The Great Gatsby',              'F. Scott Fitzgerald', '978-0-7432-7356-5', 1925, 1),
  (11, 'Harry Potter and the Sorcerer''s Stone', 'J.K. Rowling', '978-0-590-35340-3', 1997, 7),
  (12, 'Salt Fat Acid Heat',            'Samin Nosrat',        '978-1-4767-5383-6', 2017, 8),
  (13, 'Lonely Planet Japan',           'Lonely Planet',       '978-1-78657-021-5', 2019, 9),
  (14, 'Steve Jobs',                    'Walter Isaacson',     '978-1-4516-4853-9', 2011, 6),
  (15, 'The Art of War',                'Sun Tzu',             '978-1-59030-963-7', 2005, 4);

INSERT INTO member (id, name, email, phone, joined_at) VALUES
  (1,  'Alice Kim',    'alice.kim@example.com',    '010-1111-2222', '2023-04-12 10:00:00'),
  (2,  'Bob Lee',      'bob.lee@example.com',      '010-2222-3333', '2024-01-05 14:30:00'),
  (3,  'Carol Park',   'carol.park@example.com',   '010-3333-4444', '2024-06-18 09:00:00'),
  (4,  'David Choi',   'david.choi@example.com',   '010-4444-5555', '2023-11-22 16:45:00'),
  (5,  'Emma Jung',    'emma.jung@example.com',      '010-5555-6666', '2025-02-14 11:20:00'),
  (6,  'Frank Yoon',   'frank.yoon@example.com',     '010-6666-7777', '2024-09-03 08:30:00'),
  (7,  'Grace Han',    'grace.han@example.com',      '010-7777-8888', '2023-07-30 13:00:00'),
  (8,  'Henry Lim',    'henry.lim@example.com',      '010-8888-9999', '2024-12-01 15:15:00'),
  (9,  'Irene Shin',   'irene.shin@example.com',     '010-9999-0000', '2025-08-19 10:45:00'),
  (10, 'Jack Min',     'jack.min@example.com',       '010-0000-1111', '2024-03-25 12:00:00'),
  (11, 'Kate Oh',      'kate.oh@example.com',        '010-1010-2020', '2025-01-10 17:30:00'),
  (12, 'Lucas Ko',     'lucas.ko@example.com',       NULL,            '2026-05-01 09:15:00');

INSERT INTO rental (id, member_id, book_id, rented_at, due_at, returned_at) VALUES
  (1,  1,  1,  '2025-12-01 11:00:00', '2025-12-15', '2025-12-10 17:30:00'),
  (2,  1,  3,  '2026-02-04 09:30:00', '2026-02-18', NULL),
  (3,  2,  1,  '2026-03-01 13:45:00', '2026-03-15', '2026-03-13 10:00:00'),
  (4,  2,  2,  '2025-11-10 10:00:00', '2025-11-24', '2025-11-20 14:00:00'),
  (5,  3,  5,  '2026-01-15 08:00:00', '2026-01-29', NULL),
  (6,  4,  8,  '2025-10-05 14:20:00', '2025-10-19', '2025-10-14 11:00:00'),
  (7,  5,  4,  '2026-04-01 16:00:00', '2026-04-15', NULL),
  (8,  5,  10, '2025-08-20 09:00:00', '2025-09-03', '2025-08-28 18:00:00'),
  (9,  6,  11, '2026-03-10 11:30:00', '2026-03-24', NULL),
  (10, 7,  1,  '2025-06-01 10:00:00', '2025-06-15', '2025-06-12 15:00:00'),
  (11, 7,  3,  '2025-07-01 12:00:00', '2025-07-15', '2025-07-10 09:30:00'),
  (12, 7,  9,  '2026-02-20 14:00:00', '2026-03-06', NULL),
  (13, 7,  12, '2025-09-01 08:30:00', '2025-09-15', '2025-09-12 16:00:00'),
  (14, 8,  6,  '2025-12-20 13:00:00', '2026-01-03', '2025-12-28 10:00:00'),
  (15, 9,  2,  '2026-03-05 15:45:00', '2026-03-19', NULL),
  (16, 10, 7,  '2025-04-10 09:00:00', '2025-04-24', '2025-04-18 17:00:00'),
  (17, 11, 13, '2026-01-20 11:00:00', '2026-02-03', '2026-01-28 14:30:00'),
  (18, 1,  5,  '2025-07-15 10:30:00', '2025-07-29', '2025-07-22 12:00:00'),
  (19, 3,  14, '2025-11-01 14:00:00', '2025-11-15', '2025-11-08 09:00:00'),
  (20, 4,  15, '2026-02-10 16:30:00', '2026-02-24', NULL),
  (21, 8,  4,  '2025-05-05 11:00:00', '2025-05-19', '2025-05-14 13:00:00'),
  (22, 2,  6,  '2024-12-01 10:00:00', '2024-12-15', '2024-12-10 15:00:00'),
  (23, 10, 1,  '2024-06-15 09:00:00', '2024-06-29', '2024-06-25 11:00:00'),
  (24, 6,  8,  '2024-03-01 08:00:00', '2024-03-15', '2024-03-10 14:00:00'),
  (25, 7,  9,  '2024-08-10 16:00:00', '2024-08-24', '2024-08-22 12:00:00');
