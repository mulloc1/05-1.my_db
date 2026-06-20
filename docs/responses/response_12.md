# 기준 12 · INNER JOIN vs LEFT JOIN 차이

> **평가 항목:** 항목 3 · 핵심 개념 — JOIN  
> **질문:** INNER JOIN과 LEFT JOIN 쿼리가 있을 때, **실행 결과를 기준으로 두 JOIN의 차이**를 설명할 수 있는가?

---

## 결론

**예 (본 문서로 보완).** 본 프로젝트에서 **INNER JOIN**은 #5, #6, #8, **LEFT JOIN**은 #7(및 LEFT가 포함된 #9, #12)에 쓰인다. 핵심 차이: **INNER는 매칭 없으면 행 제거**, **LEFT는 왼쪽(기준) 테이블 행을 전부 유지**하고 매칭 없으면 오른쪽 컬럼이 **NULL**.

---

## JOIN 공통 개념

JOIN은 **두 테이블을 키(FK=PK)로 가로로 붙이는** 연산이다.

```sql
FROM A
[JOIN 종류] B ON A.key = B.key
```

- **왼쪽( FROM 뒤 첫 테이블 )** = 기준(driving) 테이블로 생각하기 쉬움
- **ON** = 연결 조건 (보통 FK = PK)

---

## INNER JOIN — “양쪽 다 있는 것만”

### 대표 쿼리 #5

```sql
SELECT r.id, m.name AS member_name, b.title AS book_title, r.rented_at
FROM rental r
INNER JOIN member m ON m.id = r.member_id
INNER JOIN book   b ON b.id = r.book_id
ORDER BY r.rented_at DESC;
```

**의미:** rental **각 행**에 대해 **반드시** 유효한 member·book이 있어야 결과에 포함.

| rental | member 매칭 | book 매칭 | 결과 |
|--------|------------|----------|------|
| ✅ | ✅ | ✅ | **출력** |
| ✅ | ❌ (FK 위반이면 애초에 없음) | — | — |

시드+FK 전제하에 #5 결과 행 수 ≈ **rental 25행** (각 rental이 member·book과 연결).

**캡처 `q05`:** 모든 행에 `member_name`, `book_title` **NULL 없음**.

### #6 INNER JOIN (category–book)

```sql
FROM book b
INNER JOIN category c ON c.id = b.category_id
```

`category_id NOT NULL` + FK → **모든 book**이 category와 매칭. INNER와 `FROM book`만 써도 행 수 동일.

**INNER가 “빠지는” 경우 (가상):** `category_id`가 NULL인 book이 있다면 #6 결과에서 **제외** — INNER는 **매칭 실패 행 drop**.

---

## LEFT JOIN — “왼쪽은 전부, 오른쪽은 없으면 NULL”

### 대표 쿼리 #7

```sql
SELECT m.id, m.name, COUNT(r.id) AS rental_count
FROM member m
LEFT JOIN rental r ON r.member_id = m.id
GROUP BY m.id, m.name
ORDER BY rental_count DESC, m.name ASC;
```

**의미:** **모든 member**를 기준으로, rental이 **0건**이어도 member 행 **유지**.

| member | rental 매칭 | `r.id` (JOIN 후) | `COUNT(r.id)` |
|--------|------------|------------------|---------------|
| Alice (id=1) | 多건 | 값 있음 | ≥ 1 |
| Jordan (id=12) | **0건** | **NULL** | **0** |

**캡처 `q07`에서 확인할 것:** Jordan Yoon (`id=12`) — **`rental_count = 0`**.

INNER JOIN이었다면:

```sql
FROM member m
INNER JOIN rental r ON r.member_id = m.id
```

Jordan은 **결과에서 사라짐** — “한 번도 안 빌린 회원” 질문에 **답 불가**.

---

## 같은 데이터, JOIN만 바꾼 대조

| 질문 | 적합 JOIN | 이유 |
|------|----------|------|
| “모든 대출 + 이름” (#5) | **INNER** | rental 없는 member는 관심 없음 |
| “전 회원 + 대출 횟수(0 포함)” (#7) | **LEFT** | rental 없는 member **포함** |
| “미반납 대출만” (#8) | INNER + WHERE | rental 중심 |

---

## LEFT JOIN + GROUP BY 동작 (#7)

1. `member` 12행 × LEFT JOIN `rental` → Jordan은 rental NULL 행들과 붙거나 rental 없으면 **member 1행 + r.* NULL**
2. `COUNT(r.id)` — **NULL은 세지 않음** → 0
3. `COUNT(*)`를 쓰면 Jordan도 1로 잘못 집계 — **`COUNT(r.id)`** 가 “대출 건수” 의미

**전문가 포인트:** LEFT JOIN 후 집계할 때 **어떤 컬럼을 COUNT**하느냐가 0 vs 1을 가른다.

---

## #9의 LEFT JOIN (category–book)

```sql
FROM category c
LEFT JOIN book b ON b.category_id = c.id
GROUP BY c.id, c.name
```

**의도:** 책이 **한 권도 없는** category가 있어도 `book_count = 0`으로 표시. INNER만 쓰면 **빈 category**가 목록에서 빠짐.

---

## 다이어그램 (벤 다이어그램)

```
member (LEFT)     rental (RIGHT)

  [Alice]───────────●───●───●   INNER: rental 있는 member만
  [Bob]  ───●───●
  [Jordan] (없음)              LEFT: Jordan도 결과에 ○ (count 0)
```

---

## INNER vs LEFT 요약표

| | INNER JOIN | LEFT [OUTER] JOIN |
|---|-----------|-------------------|
| 매칭 없음 | 행 **제외** | 왼쪽 유지, 오른쪽 **NULL** |
| 행 수 | ≤ 작은 쪽/교집합 | ≥ 왼쪽 행 수 |
| 본 프로젝트 | #5, #6, #8 | #7 (핵심), #9, #12 |
| 전형 질문 | “발생한 이벤트 목록” | “전체 목록 + 이벤트 유무/개수” |

(RIGHT JOIN은 LEFT의 좌우 바꿈 — 실무에선 LEFT로 통일하는 경우 많음.)

---

## 구두 설명용 스크립트

> “#5는 rental 기준 INNER JOIN이라 **대출 기록 있는 것만** 나옵니다. #7은 member 기준 LEFT JOIN이라 **Jordan처럼 대출 0번인 회원도** 나오고 `rental_count`가 0입니다. INNER는 교집합, LEFT는 **왼쪽 전체 + 오른쪽 optional** 이라고 기억하면 됩니다.”

---

## 관련 파일

- `sql/03_queries.sql` — #5 (INNER), #7 (LEFT)
- `results/q05_rental_member_book_inner_join.png`
- `results/q07_member_rental_count_left_join.png`
- `sql/02_seed.sql` — member#12 zero rentals
