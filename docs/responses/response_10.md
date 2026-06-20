# 기준 10 · 데이터베이스 vs 엑셀 — 왜 테이블로 나누는가

> **평가 항목:** 항목 3 · 핵심 개념 — DB와 스프레드시트  
> **질문:** DB가 엑셀과 **무엇이 다른지**, **왜 테이블을 나눠 저장하는지** 비교하며 설명할 수 있는가?

---

## 결론

**예 (본 문서로 보완).** 과제 `subject.md` §1: 차이는 “데이터 양”이 아니라 **관계(relationships)와 규칙(rules)을 표현할 수 있느냐**다. 도서 대출 도메인으로 엑셀 한 시트 vs 4테이블 RDB를 대조한다.

---

## 한 줄 비교

| | Excel (단일 시트) | RDB (4테이블) |
|---|------------------|---------------|
| **강점** | 빠른 입력, 눈으로 보기, 피벗 | **관계·무결성·동시 접근·쿼리** |
| **약점** | 중복·불일치·규칙 약함 | 설계·학습 비용 |
| **연결** | VLOOKUP 수동 | **JOIN + FK 자동 검증** |
| **규칙** | 데이터 유효성(제한적) | **NOT NULL, UNIQUE, FK, CHECK** |

---

## 같은 정보, 두 가지 저장 방식

### A. 엑셀식 “대출 대장” 한 장

| member_name | email | book_title | author | category | rented_at | due_at | returned_at |
|-------------|-------|------------|--------|----------|-----------|--------|-------------|
| Alice | alice@… | Clean Code | R. Martin | Technology | 2024-01-10 | 2024-01-24 | 2024-01-20 |
| Alice | alice@… | Sapiens | Harari | History | 2024-04-02 | … | … |
| Bob | bob@… | Clean Code | R. Martin | Technology | 2024-02-14 | … | … |

### B. RDB 4테이블 (본 프로젝트)

```
member(id, name, email, …)
book(id, title, author, category_id, …)
category(id, name, …)
rental(id, member_id, book_id, rented_at, due_at, returned_at)
```

**보이는 데이터는 비슷해 보이지만**, B는 **같은 사실을 한 번만** 저장하고 FK로 연결한다.

---

## 차이 1: 중복과 불일치 (Redundancy)

| 상황 | 엑셀 | DB |
|------|------|-----|
| Alice 이메일 변경 | Alice가 빌린 **모든 행** 수정 필요 | `member` **1행** UPDATE |
| `Technology` → `Tech` | 해당 **모든 book 행** | `category` **1행** |
| `Clean Code` 저자 오타 | rental마다 author 중복 시 **전 행** | `book` **1행** |

엑셀은 **같은 사실이 여러 셀**에 복사되면 **한 곳만 고치고 빠뜨리는** 불일치가 생긴다. DB **정규화**는 “한 사실, 한 곳(single source of truth)”.

---

## 차이 2: 관계와 JOIN

엑셀에서 “장르별 대출 수”:

- 피벗 테이블 또는 VLOOKUP으로 category 열을 **매 행에 끼워 넣**어야 함

DB (쿼리 #9):

```sql
SELECT c.name, COUNT(b.id)
FROM category c
LEFT JOIN book b ON b.category_id = c.id
GROUP BY c.id, c.name;
```

**JOIN**은 테이블 간 FK를 따라 **런타임에 조합**. 스키마에 관계가 **선언**되어 있어 ORM·리포트·앱이 같은 모델을 공유한다.

---

## 차이 3: 규칙(Integrity) — DB만의 계약

본 프로젝트 예:

| 규칙 | DB | 엑셀 |
|------|-----|------|
| 없는 회원 id로 대출 | `FOREIGN KEY constraint failed` | 셀 아무 숫자나 입력 가능 |
| 이메일 중복 | `UNIQUE constraint failed` | 중복 행 방지 어려움 |
| 반납일 < 대출일 | `CHECK (due_at >= date(rented_at))` | 수식/조건부 서식으로 **흉내** |
| 필수 제목 없는 책 | `NOT NULL on title` | 빈 셀 허용 |

엑셀도 “데이터 유효성”이 있지만, **다중 테이블 FK·트랜잭션** 수준의 보장은 RDB 영역이다.

---

## 차이 4: 규모·동시성·앱 연동

| 요구 | 엑셀 | DB |
|------|------|-----|
| 수십만 rental | 느려짐, 파일 공유 충돌 | 인덱스·서버 DB로 확장 |
| 웹앱 + 모바일 동시 대출 | 부적합 | SQLite→PostgreSQL 등 |
| API에서 “미반납 목록” | 파일 잠금·버전 지옥 | `SELECT … WHERE returned_at IS NULL` |

과제는 SQLite 파일 하나지만, **설계 사고방식**은 프로덕션과 동일하다.

---

## 왜 테이블을 “나눠” 저장하는가 (3문장)

1. **서로 다른 개념**(회원, 책, 대출 이벤트)은 **변경 빈도와 속성**이 다르다 → 한 시트에 넣으면 NULL·중복 폭발.
2. **1:N**은 부모를 한 번 저장하고 자식 FK로 **여러 번 참조** → 저장 공간·일관성.
3. **쿼리**는 필요한 테이블만 JOIN해 **뷰를 조합** — 엑셀은 매번 열을 복제해 피벗.

---

## 도서관 도메인 비유 (구두용)

> “엑셀로 대출 대장을 만들면 Alice 이름이 빌릴 때마다 반복되고, Clean Code 저자도 매번 적습니다. DB는 **회원 명부**, **도서 카탈로그**, **대출 기록**을 서랍장처럼 나누고, 대출 한 줄에 ‘회원 3번이 책 1번’처럼 **번호로 연결**합니다. 잘못된 번호는 DB가 거절합니다.”

---

## subject.md 학습 목표와의 연결

| # | 목표 | 본 프로젝트 증거 |
|---|------|-----------------|
| 1 | DB vs Excel, 테이블 분리 | 4테이블 vs 위 단일 시트 |
| 2 | PK/FK, 1:N | `01_schema.sql` |
| 4 | JOIN으로 한 번에 조회 | #5–#8 |
| 6 | 인덱스 | #15 `rental(member_id, rented_at)` |

---

## 관련 파일

- `docs/subject.md` §1, §3.1
- `docs/plan.md` §1 Goal Summary
- `sql/01_schema.sql` — 정규화된 스키마
- `README.md` — Verifying Constraints (엑셀에 없는 FK)
