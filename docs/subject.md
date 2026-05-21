# SQL Database Practice Mission

---

## 1. Mission Overview

The difference between Excel and a DB is not “how much data you have.” It is whether you can express **relationships** between tables. Without that, JOINs and ORMs stay confusing. Nail it here and the rest gets easier. You will complete the flow from **table design** to solving requirements in **one SQL shot**.

A database stores service data safely with **relationships and rules**, not as files or spreadsheets. **SQL** is the most direct language for practical needs: query, search, sort, and aggregate.

In this mission you design domain tables (PK/FK, constraints), insert data (INSERT), and extract what you need (SELECT/JOIN/GROUP BY)—**without a backend framework**. It builds the foundation for **1:N**, **PK/FK**, **integrity**, and **join thinking** needed later with JPA/ORM.

---

## 2. Final Deliverable

Complete a **SQL-based database practice deliverable** meeting all four items below (**no backend framework**).

### 2.1 Domain Database Design

| Item | Requirement |
|------|-------------|
| **Topic** | Free choice (book rental, movie ratings, café orders, travel plans, class management, etc.) |
| **Tables** | At least **4** |
| **Relationships** | At least **2** **1:N** relationships |

### 2.2 Schema Creation Script

- Define schema with `CREATE TABLE`, including **PK/FK and constraints**
- Submit as **one** `.sql` file in **execution order**

### 2.3 Sample Data Insert Script

- Meaningful `INSERT` statements
- **At least 10 rows per table**

### 2.4 15 Core Queries + Execution Result Captures

- **15 queries** covering select, join, aggregate, subquery, update, delete
- **Screenshot or text** of each query’s result

---

## 3. Learning Objectives

After completing this assignment, learners should be able to explain the following on their own.

1. How a DB differs from Excel and why data is split into tables.
2. How **PK/FK** and **1:N** connect data in words.
3. When to use **SELECT / INSERT / UPDATE / DELETE**.
4. How **JOIN** and **GROUP BY** pull related data in one go.
5. A feel for solving search, sort, aggregate, and ranking needs with SQL.
6. Basic understanding of **why indexes matter** and which columns to index.

---

## 4. Functional Requirements

You must satisfy **all** of the following.

### 4.1 DB Environment

| Item | Requirement |
|------|-------------|
| **DB** | Runnable locally: pick **one** of SQLite, MySQL, PostgreSQL, H2 |
| **Tool** | Run SQL via DBeaver, TablePlus, DataGrip, CLI, etc. |

**DB selection notes**

| DB | Notes |
|----|-------|
| SQLite | Easy setup, file-based, no server (good for beginners) |
| MySQL | Widely used in production, needs a server |
| PostgreSQL | Strong standard SQL and advanced features |
| H2 | Java environments, in-memory mode |

- Prefer **standard SQL** when dialects differ. If using DB-specific syntax, note it in a **comment** on that query.

### 4.2 Data Model (Schema) Design

| Item | Requirement |
|------|-------------|
| **Tables** | At least **4** |
| **PK** | Each table has a PK |
| **FK & 1:N** | At least **2** FKs forming 1:N |
| **Types** | TEXT/VARCHAR, INTEGER, DATE/DATETIME, etc. as appropriate |
| **Names** | e.g. `member`, `rental`, `created_at` so roles are clear |

**Topic examples**: book rental, movie ratings, café orders, online shop, class management, etc.

### 4.3 Constraints

| Constraint | Requirement |
|------------|-------------|
| **NOT NULL** | At least **1** column |
| **UNIQUE** | At least **1** column |
| **FK** | Must block references to non-existent values |

### 4.4 Sample Data

- **At least 10 rows per table**
- FK links must reflect **real relationships**
- **Parent rows** must exist before child INSERTs

### 4.5 15 Core SQL Queries

Categories below; **15 total minimum**.

| Category | Minimum |
|----------|---------|
| Basic select | 4+ (`WHERE`, `ORDER BY`, `LIMIT` included) |
| Joins | 4+ (**2+ INNER JOIN**, **1+ LEFT JOIN**) |
| **Aggregate** | 3+ (**2+ types** among `COUNT`/`SUM`/`AVG` + `GROUP BY`) |
| Subquery | 1+ |
| Update/Delete | 2+ (`UPDATE`, `DELETE`) |
| Index | **1+** `CREATE INDEX` + **one line** on why it was added |

### 4.6 Result Documentation

- Each query’s result must be verifiable
- **One-line** description per query: what it checks
- Results: screenshot or text

### 4.7 Submission Structure

| File/Folder |
|-------------|
| One schema creation SQL |
| One sample INSERT SQL |
| One SQL file with 15 queries |
| One folder of execution captures |
| **(Optional)** ERD image (draw.io, dbdiagram.io, etc.) |

---

## 5. Bonus

| Item | Content |
|------|---------|
| **Join vs subquery** | Solve the same requirement both ways and compare |
| **Integrity experiment** | Try input that breaks FK; record why it fails and how to fix |
| **Mini report** | Define “3 core metrics this DB can produce” + final SQL each (e.g. monthly rentals, top 10 books) |
