# 기준 2 · 1:N 관계 및 FK 제약

> **평가 항목:** 항목 1 · 구현 검증 — 관계 및 무결성  
> **질문:** `category-book`, `book-rental`, `member-rental` 등 **1:N 관계가 2개 이상** 존재하며, 존재하지 않는 값 참조 시 FK가 차단되는가?

---

## 결론

**예.** 스키마에 **3개의 1:N 관계**가 FK로 구현되어 있고(과제 최소 2개 초과), README **Verifying Constraints** 섹션에서 orphan INSERT가 `FOREIGN KEY constraint failed`로 실패함을 재현할 수 있다.

---

## 1:N 관계 3개 (스키마 매핑)

| # | 부모 (1) | 자식 (N) | FK 컬럼 | ON DELETE |
|---|----------|----------|---------|-----------|
| 1 | `category` | `book` | `book.category_id` | RESTRICT |
| 2 | `member` | `rental` | `rental.member_id` | RESTRICT |
| 3 | `book` | `rental` | `rental.book_id` | RESTRICT |

```
category ──< book ──< rental >── member
   1       N   1       N    N     1
```

`rental`은 **두 부모(`member`, `book`)를 동시에 참조**하는 자식 테이블이다. 하나의 대출 기록은 “누가(member) + 무엇을(book) + 언제(rented_at)”를 묶는 **트랜잭션 행**이다.

---

## FK 정의 (코드)

```26:26:05-1.my_db/sql/01_schema.sql
  FOREIGN KEY (category_id) REFERENCES category(id) ON DELETE RESTRICT
```

```45:46:05-1.my_db/sql/01_schema.sql
  FOREIGN KEY (member_id) REFERENCES member(id) ON DELETE RESTRICT,
  FOREIGN KEY (book_id)   REFERENCES book(id)   ON DELETE RESTRICT,
```

### `ON DELETE RESTRICT`의 의미

부모 행을 삭제하려 할 때 **아직 참조하는 자식이 있으면 삭제를 거부**한다.

- `category` 삭제 시 해당 분류의 `book`이 있으면 → 거부
- `member` 삭제 시 대출 이력(`rental`)이 있으면 → 거부
- `book` 삭제 시 대출 이력이 있으면 → 거부

실무에서 “이력이 있는 회원/도서를 실수로 지우는” 사고를 막는 **안전한 기본값**이다. (과제 범위에서는 CASCADE 대신 RESTRICT를 선택 — `docs/plan.md` Locked Decisions)

---

## FK 무결성 검증 (README 재현)

README **Verifying Constraints**:

```bash
sqlite3 library.db "PRAGMA foreign_keys = ON; \
  INSERT INTO rental (member_id, book_id, rented_at, due_at) \
  VALUES (9999, 9999, '2026-01-01 00:00:00', '2026-01-15');"
```

**기대:** `Error: FOREIGN KEY constraint failed`

- `member_id = 9999` → `member` 테이블에 없음
- `book_id = 9999` → `book` 테이블에 없음

DB가 **고아(orphan) rental 행** 생성을 차단함을 증명한다.

### SQLite 주의: `PRAGMA foreign_keys = ON`

SQLite는 기본적으로 FK 검사가 **꺼져 있다**. 모든 SQL 파일 상단에 다음이 포함된다:

```sql
PRAGMA foreign_keys = ON;
```

이 pragma 없이 INSERT하면 FK 위반이 **조용히 통과**할 수 있어, 실습·채점 모두에서 반드시 켜야 한다.

---

## 1:N이 “관계”를 표현하는 방식

관계형 DB에서 1:N은 **부모 테이블에 N개의 행을 중복 저장하지 않고**, 자식 테이블 FK **한 컬럼**으로 연결한다.

| 잘못된 방식 (비정규화) | 올바른 방식 (1:N) |
|----------------------|-------------------|
| `book` 행마다 `category_name` 문자열 반복 | `book.category_id` → `category.id` |
| `rental`에 `member_name`, `book_title`만 저장 | FK + JOIN으로 이름 조회 |

FK는 “이 rental의 `member_id=3`은 **반드시** `member` 테이블 id=3 행을 가리킨다”는 **참조 무결성(referential integrity)** 계약이다.

---

## 시드 데이터와 FK 순서

`02_seed.sql`은 **부모 → 자식** INSERT 순서를 지킨다:

1. `category` (12행)
2. `book` (`category_id` 참조)
3. `member` (12행)
4. `rental` (`member_id`, `book_id` 참조)

역순 INSERT 시 FK 실패. 이는 “관계가 있는 데이터는 **순서**가 있다”는 DB 기본 원칙을 보여 준다.

---

## 검증 체크리스트

| # | 확인 | 기대 |
|---|------|------|
| 1 | `.schema`에 FK 3개 | `category_id`, `member_id`, `book_id` |
| 2 | orphan rental INSERT | FK failed |
| 3 | 존재하는 FK로 INSERT | 성공 |
| 4 | `PRAGMA foreign_keys` | ON |

---

## 관련 파일

- `sql/01_schema.sql` — FK 정의
- `sql/02_seed.sql` — FK 준수 INSERT 순서
- `README.md` — Verifying Constraints
- `docs/plan.md` §4.1 — 관계 다이어그램
