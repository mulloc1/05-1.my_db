# 기준 8 · 컬럼 타입 선택 이유

> **평가 항목:** 항목 2 · 설계 설명 — 데이터 타입  
> **질문:** TEXT, INTEGER, DATE, DATETIME 등 컬럼 타입을 **왜 그렇게 선택했는지** 설명할 수 있는가?

---

## 결론

**예 (본 문서로 보완).** 각 컬럼 타입은 **저장할 값의 성격(숫자 연산 vs 문자열 vs 시점 vs 날짜만)** 과 **SQLite/표준 SQL 호환**을 기준으로 선택했다. 아래는 테이블별 타입 결정표와 대안 비교다.

---

## 타입 선택 원칙 (요약)

| 원칙 | 적용 |
|------|------|
| **의미에 맞는 타입** | 연도는 INTEGER, 이메일은 TEXT |
| **NULL 허용은 “없을 수 있음”** | `returned_at NULL` = 아직 미반납 |
| **NOT NULL은 “없으면 행이 무의미”** | `book.title`, `rental.rented_at` |
| **SQLite 현실** | DATETIME은 TEXT ISO-8601 저장 (`docs/plan.md`) |
| **이식성** | DB 특화 함수는 `-- SQLite-specific:` 주석 |

---

## 테이블별 컬럼 타입 근거

### `category`

| 컬럼 | 타입 | 이유 |
|------|------|------|
| `id` | `INTEGER PRIMARY KEY` | 대리 키, 조인·FK용 정수 |
| `name` | `TEXT NOT NULL UNIQUE` | 가변 길이 문자열; 장르명은 수학 연산 불필요 |
| `description` | `TEXT` (nullable) | 긴 설명, 선택 입력 |

**왜 VARCHAR(n)이 아닌 TEXT?** SQLite는 TEXT/VARCHAR 구분이 느슨하고, 과제 예시가 TEXT. PostgreSQL 이식 시 `VARCHAR(100)` 등으로 제한 가능.

---

### `book`

| 컬럼 | 타입 | 이유 |
|------|------|------|
| `id` | `INTEGER PRIMARY KEY` | PK |
| `title`, `author` | `TEXT NOT NULL` | 가변 길이, 필수 메타 |
| `isbn` | `TEXT UNIQUE` | ISBN은 **하이픈 포함 문자열** — INTEGER로 저장하면 선행 0·포맷 손실 |
| `published_year` | `INTEGER` (nullable) | **연도만** 필요 → `YEAR` 타입 없는 DB에서 INTEGER가 관례; `>= 2015` 비교 (#2) |
| `category_id` | `INTEGER NOT NULL` | FK → `category.id`, 정수 참조 |

**왜 `published_year`를 DATE가 아�na?** “2011년 출간” 수준이면 **연도 정수**가 단순. 정확한 출판일이 필요하면 `DATE`로 확장.

**왜 author를 별도 테이블·INTEGER FK가 아�na?** YAGNI — 과제 4테이블 내에서 저자 문자열로 충분.

---

### `member`

| 컬럼 | 타입 | 이유 |
|------|------|------|
| `id` | `INTEGER PRIMARY KEY` | PK |
| `name` | `TEXT NOT NULL` | 사람 이름 |
| `email` | `TEXT NOT NULL UNIQUE` | 이메일은 문자열; 로그인·연락 **비즈니스 키** (UNIQUE) |
| `phone` | `TEXT` (nullable) | `010-1111-2222` — **숫자 연산 안 함** → TEXT (INTEGER면 하이픈 불가) |
| `joined_at` | `DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP` | **시각** 포함 가입 시점; 정렬 (#1 `ORDER BY joined_at DESC`) |

**SQLite:** `DATETIME`은 내부적으로 TEXT(ISO-8601 `'2024-01-05 14:30:00'`)로 저장. 비교·정렬이 문자열 순서 = 시간 순서가 되도록 형식 통일.

---

### `rental`

| 컬럼 | 타입 | 이유 |
|------|------|------|
| `id` | `INTEGER PRIMARY KEY` | PK |
| `member_id`, `book_id` | `INTEGER NOT NULL` | FK |
| `rented_at` | `DATETIME NOT NULL` | **대출 시각** (시·분 의미) |
| `due_at` | `DATE NOT NULL` | **반납 기한일** — “며칠까지”면 **날짜만** 있으면 됨 |
| `returned_at` | `DATETIME NULL` | 미반납 = NULL; 반납 시 시각 기록 |

**`due_at`은 DATE, `rented_at`은 DATETIME인 이유**

| 컬럼 | 필요 정밀도 | 예 |
|------|------------|-----|
| `rented_at` | 시각 | “2024-03-01 14:30 대출” |
| `due_at` | 일 단위 | “2024-03-15까지” |
| `returned_at` | 시각 | 반납 처리 시각 (#13 `CURRENT_TIMESTAMP`) |

**CHECK 제약:**

```sql
CHECK (due_at >= date(rented_at))
```

반납 기한이 대출일 **당일 이전**이 될 수 없음 — 도메인 규칙을 DB 레벨에서 방어.

---

## 타입별 “잘못된 선택” 예시

| 컬럼 | 잘못된 타입 | 문제 |
|------|------------|------|
| `isbn` | INTEGER | `978-…` 하이픈·선행0 처리 불가 |
| `phone` | INTEGER | 하이픈, 국제번호 `+82` |
| `published_year` | TEXT | `'2011'` vs `2011` — 정렬·범위 비교 혼란 |
| `due_at` | DATETIME only | 불필요한 시각까지 강제 |
| `member_id` | TEXT | FK 정수 PK와 타입 불일치 |

---

## SQLite vs PostgreSQL 이식 메모

| 항목 | SQLite (본 프로젝트) | PostgreSQL 이식 |
|------|---------------------|-----------------|
| 시각 | TEXT ISO-8601 | `TIMESTAMP WITH TIME ZONE` |
| 일수 차이 (#11) | `julianday()` | `(returned_at::date - rented_at::date)` |
| FK pragma | `PRAGMA foreign_keys = ON` | 기본 ON |

`03_queries.sql`에 dialect 차이는 주석으로 표기.

---

## 구두 설명용 스크립트

> “PK·FK는 INTEGER로 통일했고, 이름·제목·ISBN은 TEXT입니다. ISBN과 전화번호는 숫자로 바꾸면 하이픈이 깨져서 TEXT입니다. 출판연도는 연도만 쓰니 INTEGER, 대출 시각은 DATETIME, 반납 **기한**은 날짜만 필요해서 DATE입니다. 아직 안 돌려준 책은 `returned_at`을 NULL로 둡니다.”

---

## 관련 파일

- `sql/01_schema.sql` — 타입 정의
- `docs/plan.md` — Date/time type Locked Decision
- `docs/subject.md` §4.2 — TEXT, INTEGER, DATE/DATETIME 요구
