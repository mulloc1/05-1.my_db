# 기준 1 · 스키마 구조 (4개 테이블 + PK)

> **평가 항목:** 항목 1 · 구현 검증 — 테이블 및 PK  
> **질문:** 도서 대출(라이브러리) 도메인에 `category`, `book`, `member`, `rental` 최소 4개 테이블이 존재하며, 각 테이블에 PK가 정의되어 있는가?

---

## 결론

**예.** `sql/01_schema.sql`에 **4개 테이블**이 정의되어 있고, 모든 테이블에 **`INTEGER PRIMARY KEY`** 형태의 대리 키(surrogate key) `id`가 PK로 지정되어 있다. ERD(`docs/erd.png`)와 README의 Subject Mapping에서도 동일한 구조를 명시한다.

---

## 4개 테이블 개요

| 테이블 | PK | 도메인 역할 (한 줄) |
|--------|-----|---------------------|
| `category` | `id` | 도서 분류(장르) 마스터 |
| `book` | `id` | 대출 가능한 도서 카탈로그 |
| `member` | `id` | 도서관 회원 |
| `rental` | `id` | 회원–도서 간 대출 이력(트랜잭션) |

과제 최소 요구(≥ 4 테이블)를 **정확히 4개**로 충족한다. YAGNI 원칙에 따라 불필요한 보조 테이블(예: `author`, `publisher`)은 추가하지 않았다.

---

## PK 정의 (스키마 근거)

```13:17:05-1.my_db/sql/01_schema.sql
CREATE TABLE category (
  id          INTEGER PRIMARY KEY,        -- SQLite: implicit rowid alias
  name        TEXT    NOT NULL UNIQUE,
  description TEXT
);
```

```19:27:05-1.my_db/sql/01_schema.sql
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

```29:36:05-1.my_db/sql/01_schema.sql
CREATE TABLE member (
  id        INTEGER  PRIMARY KEY,
  name      TEXT     NOT NULL,
  email     TEXT     NOT NULL UNIQUE,
  phone     TEXT,
  joined_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

```38:49:05-1.my_db/sql/01_schema.sql
CREATE TABLE rental (
  id          INTEGER  PRIMARY KEY,
  member_id   INTEGER  NOT NULL,
  book_id     INTEGER  NOT NULL,
  rented_at   DATETIME NOT NULL,
  due_at      DATE     NOT NULL,
  returned_at DATETIME NULL,
  FOREIGN KEY (member_id) REFERENCES member(id) ON DELETE RESTRICT,
  FOREIGN KEY (book_id)   REFERENCES book(id)   ON DELETE RESTRICT,
  CHECK (due_at >= date(rented_at))
);
```

---

## PK를 `INTEGER PRIMARY KEY`로 통일한 이유

### 1. 대리 키(Surrogate Key) vs 자연 키(Natural Key)

| 방식 | 예시 | 장점 | 단점 |
|------|------|------|------|
| 자연 키 | `book.isbn`, `member.email` | 비즈니스 의미가 PK에 내장 | 값 변경 시 FK 전파 복잡, 복합키 가능 |
| 대리 키 | `id INTEGER PRIMARY KEY` | 조인 단순, 변경에 강함 | PK만으로는 의미 파악 불가 |

초급 SQL 실습 범위에서는 **모든 테이블에 단일 정수 PK**를 두면 JOIN·FK 학습에 집중할 수 있다. `isbn`, `email`은 **UNIQUE**로 비즈니스 불변식을 따로 표현한다.

### 2. SQLite의 `INTEGER PRIMARY KEY` 특성

SQLite에서 `INTEGER PRIMARY KEY`는 내부 `rowid`와 **별칭(alias)** 이 된다. INSERT 시 `id`를 생략하면 자동 증가한다. 시드 데이터(`02_seed.sql`)에서는 명시적 `id`를 넣어 FK 참조를 예측 가능하게 유지했다.

### 3. FK 연결의 기준점

모든 1:N 관계는 **부모 PK → 자식 FK** 패턴으로 연결된다.

```
category.id  ← book.category_id
member.id    ← rental.member_id
book.id      ← rental.book_id
```

PK가 없으면 “어느 행을 가리키는가”를 DB가 보장할 수 없다. PK는 **행의 유일 식별자**이자 FK 참조의 **앵커**다.

---

## ERD와의 일치

README ERD 섹션:

```
category ──< book ──< rental >── member
   1       N   1       N    N     1
```

- **4개 엔티티** = 4개 테이블
- **3개 1:N 화살표** = 3개 FK (과제 최소 2개 초과)

---

## 검증 방법

```bash
cd 05-1.my_db
sqlite3 library.db ".schema"
```

기대 출력: `CREATE TABLE category|book|member|rental` 각각 `PRIMARY KEY` 포함.

또는:

```bash
sqlite3 library.db "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
# → book, category, member, rental (+ sqlite_sequence if used)
```

---

## 관련 파일

- `sql/01_schema.sql` — CREATE TABLE + PK 정의
- `docs/erd.png` — 시각적 ERD
- `docs/plan.md` §4.2 — 테이블 형태 설계 근거
- `README.md` — ERD · Subject Mapping
