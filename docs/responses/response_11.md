# 기준 11 · PK와 FK의 역할 — 데이터 연결 방식

> **평가 항목:** 항목 3 · 핵심 개념 — PK/FK  
> **질문:** 본인 스키마 기준으로 **PK와 FK의 역할을 구분**하고, **데이터가 어떻게 연결되는지** 설명할 수 있는가?

---

## 결론

**예 (본 문서로 보완).** PK는 각 테이블에서 **행을 유일하게 식별**하고, FK는 자식 테이블에서 **부모 행을 가리키는 참조**다. 도서관 스키마에서는 모든 PK가 `id INTEGER`이고, FK 3개가 **category→book→rental←member** 그래프를 완성한다.

---

## PK vs FK 한눈에

| | PRIMARY KEY (PK) | FOREIGN KEY (FK) |
|---|------------------|------------------|
| **위치** | 보통 **자기 테이블** | **자식 테이블** 컬럼 |
| **역할** | “이 행은 **나**” | “이 값은 **저 테이블의 어떤 행**” |
| **개수/행** | 테이블당 **1개(또는 복합)** | 여러 FK 가능 |
| **NULL** | NOT NULL (PK) | NOT NULL이면 반드시 부모 존재 |
| **본 프로젝트** | `id` on 4 tables | `category_id`, `member_id`, `book_id` |

**비유:** PK = 주민등록번호(본인), FK = “소속 부서 코드”(다른 명부를 가리킴).

---

## PK의 역할 (테이블별)

| 테이블 | PK | 식별하는 것 |
|--------|-----|------------|
| `category` | `id=5` | “Technology” **그 분류 하나** |
| `book` | `id=1` | “Clean Code” **카탈로그 항목 하나** |
| `member` | `id=1` | “Alice Kim” **회원 한 명** |
| `rental` | `id=2` | **한 번의 대출 이벤트** (2024-04-02 Alice가 Sapiens) |

PK 없으면:

- JOIN `ON b.category_id = c.id`에서 **`c.id`가 모호**
- FK `REFERENCES category(id)`의 **대상**이 없음

---

## FK의 역할 (연결 그래프)

```
category.id ──────► book.category_id
member.id   ──────► rental.member_id
book.id     ──────► rental.book_id
```

### `book.category_id` → `category.id`

- **의미:** 이 책은 **어느 분류에 속하는가**
- **예:** `Clean Code`.category_id = **5** → `category` where id=5 = Technology
- **1:N:** category 5 하나에 book 여러 개

### `rental.member_id` → `member.id`

- **의미:** 이 대출은 **누가** 했는가
- **예:** rental#10.member_id = **1** → Alice

### `rental.book_id` → `book.id`

- **의미:** 이 대출은 **어떤 책**에 대한 것인가
- **예:** rental#10.book_id = **4** → Sapiens

**rental 한 행** = `(member_id, book_id, rented_at, …)` = FK 두 개로 **두 부모와 동시 연결**.

---

## 데이터 연결의 실제 흐름 (쿼리 #5)

**질문:** “각 대출에 회원 이름과 책 제목을 붙여라.”

```sql
SELECT r.id, m.name AS member_name, b.title AS book_title, r.rented_at
FROM rental r
INNER JOIN member m ON m.id = r.member_id   -- FK: rental → member
INNER JOIN book   b ON b.id = r.book_id     -- FK: rental → book
ORDER BY r.rented_at DESC;
```

**연결 단계 (논리):**

```
1. rental 행 r (PK r.id)
2. r.member_id == m.id  → member 행 m에서 name 획득
3. r.book_id   == b.id  → book 행 b에서 title 획득
4. 결과: (대출id, Alice, Clean Code, 2024-…)
```

FK는 **저장된 정수**지만, JOIN으로 **사람이 읽는 문자열**을 **조합**한다. rental에 `member_name`을 중복 저장하지 않는 이유다.

---

## PK/FK와 UNIQUE의 역할 분담

| 키 종류 | 컬럼 | 역할 |
|---------|------|------|
| PK | `member.id` | 내부 조인용 **안정 식별자** |
| UNIQUE | `member.email` | **비즈니스** 중복 방지 |
| FK | `rental.member_id` | PK `member.id` **참조** |

이메일이 바뀌어도 `id`는 유지 → **과거 rental FK 깨지지 않음**. PK를 email(자연키)로 쓰면 이메일 변경 시 **모든 rental FK 업데이트** 필요.

---

## FK가 “연결을 강제”하는 증명

README 검증:

```bash
INSERT INTO rental (member_id, book_id, rented_at, due_at)
VALUES (9999, 9999, '2026-01-01', '2026-01-15');
-- FOREIGN KEY constraint failed
```

**연결 규칙:** rental은 **반드시** 존재하는 member와 book에만 매달릴 수 있다. PK만 있고 FK 없으면 **아무 정수나** 넣을 수 있어 **의미 없는 연결**이 된다.

---

## ON DELETE RESTRICT와 “연결 유지”

부모 삭제 시:

```sql
DELETE FROM member WHERE id = 1;  -- Alice, rental 있음
-- RESTRICT → 실패 (rental이 member_id=1 참조)
```

**의도:** 이력(`rental`)이 있는 회원을 **실수로 삭제**하지 못하게. 연결 **무결성** = 고아 rental 방지.

---

## ERD 화살표 읽기

```
category ──< book ──< rental >── member
```

- `──<` : FK가 **오른쪽(자식)** 에 있음 (book.category_id, rental.book_id)
- `>──` : FK가 **왼쪽(rental)** 에 있음 (rental.member_id)

---

## 구두 설명용 스크립트

> “네 테이블 모두 PK `id`로 **한 행을 가리킵니다**. book은 category를 `category_id` FK로, rental은 member와 book을 각각 FK로 **연결**합니다. 대출 목록에 이름을 안 넣고 JOIN하는 이유는 FK가 **이미 누구·무엇**을 가리키기 때문이고, 없는 id는 INSERT 단계에서 막힙니다.”

---

## 관련 파일

- `sql/01_schema.sql` — PK/FK 정의
- `README.md` — Verifying Constraints
- `sql/03_queries.sql` — #5 JOIN 연결 예
- `docs/subject.md` §3.2 — PK/FK 학습 목표
