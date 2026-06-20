# 기준 13 · 집계 함수 동작 원리 (결과 기반 설명)

> **평가 항목:** 항목 3 · 핵심 개념 — GROUP BY / 집계  
> **질문:** `COUNT`, `AVG`, `GROUP BY`, `HAVING`을 쓴 쿼리 **결과를 보며 어떻게 동작하는지** 설명할 수 있는가?

---

## 결론

**예 (본 문서로 보완).** 집계 쿼리 #9, #10, #11과 LEFT JOIN 집계 #7, #12가 **행 → 그룹 → 집계값** 파이프라인을 보여 준다. 아래는 각 쿼리를 **실행 결과 관점**에서 단계별로 풀어 쓴 설명이다.

---

## 집계 SQL의 3단계 mental model

```
1. FROM + JOIN + WHERE     → 대상 **행** 필터
2. GROUP BY                → 행을 **그룹(버킷)** 으로 묶음
3. SELECT 집계함수 + HAVING → 그룹당 **한 줄** 요약
```

| 절 | 역할 | 필터 대상 |
|----|------|----------|
| `WHERE` | 그룹 만들 **전** 행 제거 | **행** |
| `HAVING` | 그룹 만든 **후** 그룹 제거 | **그룹** |

---

## #9 · COUNT + GROUP BY — “카테고리별 책 몇 권?”

```sql
SELECT c.name AS category, COUNT(b.id) AS book_count
FROM category c
LEFT JOIN book b ON b.category_id = c.id
GROUP BY c.id, c.name
ORDER BY book_count DESC, c.name ASC;
```

### 동작

1. **JOIN:** 각 category에 속한 book 행들이 붙음 (없으면 b.* NULL)
2. **GROUP BY c.id:** Fiction, Science, … **장르당 하나의 그룹**
3. **COUNT(b.id):** 그룹 안 **book id 개수** (NULL id는 미카운트)

### 결과 해석 (캡처 q09)

| category | book_count | 의미 |
|----------|------------|------|
| Fiction | (다수) | Fiction `category_id`인 book 행 수 |
| (어떤 장르) | 1 | 해당 장르 책 1권 |
| (빈 장르) | **0** | LEFT JOIN — 책 없어도 category 행 유지 |

**왜 `COUNT(*)`가 아닌 `COUNT(b.id)`?** 빈 category에서 `COUNT(*)`는 1(그룹 행 1개), `COUNT(b.id)`는 **0** — “책 권수” 의미에 맞음 (#7과 동일 패턴).

---

## #10 · HAVING — “2번 초과 빌린 회원만”

```sql
SELECT m.id, m.name, COUNT(r.id) AS rental_count
FROM member m
INNER JOIN rental r ON r.member_id = m.id
GROUP BY m.id, m.name
HAVING COUNT(r.id) > 1
ORDER BY rental_count DESC;
```

### 동작

1. **INNER JOIN:** rental **있는** member만 (Jordan 제외)
2. **GROUP BY member:** Alice의 rental 5건 → **한 그룹**
3. **COUNT(r.id):** 그룹 내 rental 행 수
4. **HAVING > 1:** rental_count가 1 이하인 **그룹 탈락**

### WHERE vs HAVING (만약 실수)

```sql
-- 잘못된 예 (개념 비교)
WHERE COUNT(r.id) > 1   -- ❌ SQL: WHERE에 집계 불가
HAVING COUNT(r.id) > 1  -- ✅ 그룹 필터
```

### 결과 해석 (캡처 q10)

- 출력된 **각 행** = “2회 이상 대출한 회원 1명”
- `rental_count` 열 = 그 회원의 **총 대출 건수**
- 목록에 **없는** 회원 = 0~1건 빌린 사람

---

## #11 · AVG — “장르별 평균 대출 일수”

```sql
SELECT c.name AS category,
       ROUND(AVG(julianday(r.returned_at) - julianday(r.rented_at)), 1) AS avg_days
FROM rental r
INNER JOIN book b ON b.id = r.book_id
INNER JOIN category c ON c.id = b.category_id
WHERE r.returned_at IS NOT NULL
GROUP BY c.id, c.name
ORDER BY avg_days DESC;
```

### 동작

1. **WHERE returned_at IS NOT NULL:** **미반납 제외** — 기간 계산 불가 행 제거 (행 필터)
2. **JOIN:** rental → book → category (각 rental에 장르 부여)
3. **그룹:** Fiction rental들, Science rental들, …
4. **AVG(일수):** 그룹 내 `(returned - rented)` 일수의 **산술 평균**
5. **ROUND(..., 1):** 소수 첫째 자리

### 결과 해석 (캡처 q11)

| category | avg_days | 의미 |
|----------|----------|------|
| (높은 값) | 예: 14.2 | 그 장르 책들의 **반납까지 평균 14.2일** |
| (낮은 값) | 예: 5.0 | 빨리 돌려준 패턴 (시드 데이터에 따라) |

**주의:** 카테고리에 **반납된 rental 1건**만 있으면 AVG = 그 1건의 일수. 카테고리에 **반납 0건**이면 GROUP BY 후 **행 자체가 없음** (INNER rental 경로).

**SQLite:** `julianday()` — Postgres는 날짜 뺄셈으로 이식 (`03_queries.sql` 주석).

---

## #7 · LEFT JOIN + COUNT (집계 맥락)

```sql
SELECT m.id, m.name, COUNT(r.id) AS rental_count
FROM member m
LEFT JOIN rental r ON r.member_id = m.id
GROUP BY m.id, m.name
```

- **그룹:** member 1명 = 1그룹
- Jordan: JOIN 후 r.id 전부 NULL → **COUNT(r.id)=0**
- Alice: r.id 여러 개 → **COUNT = 대출 건수**

#10과 비교: #7은 **전 회원**, #10은 **HAVING으로 다회 대출자만**.

---

## #12 · 서브쿼리 + HAVING (집계 확장)

```sql
HAVING COUNT(r.id) > (
  SELECT AVG(per_member.cnt)
  FROM (SELECT COUNT(*) AS cnt FROM rental GROUP BY member_id) AS per_member
)
```

**내부:** 회원별 대출 수 `cnt` 목록 → **그 평균** (예: 25 rental / 11명 with rental ≈ … 시드에 따름)

**외부:** `COUNT(r.id) > (그 평균)` 인 member만 — **상위 이용자** 필터.

집계 **결과**를 다시 **임계값**으로 쓰는 패턴.

---

## 집계 함수 치트시트

| 함수 | 입력 | 출력 (그룹당) |
|------|------|--------------|
| `COUNT(col)` | col NOT NULL 행 수 | 정수 |
| `COUNT(*)` | 그룹 행 수 (JOIN cartesian 주의) | 정수 |
| `AVG(expr)` | expr 평균 | 실수 (NULL 무시) |
| `SUM` | (본 과제 미사용) | 합 |
| `MIN`/`MAX` | (본 과제 미사용) | 최소/최대 |

**NULL 규칙:** 집계 함수는 **NULL 입력을 무시** (COUNT(*) 제외).

---

## 구두 설명용 스크립트

> “#9는 장르별로 book을 묶어 **COUNT**합니다. LEFT JOIN이라 책 0권 장르도 0으로 나옵니다. #10은 회원별 대출 수를 세고 **HAVING**으로 2번 넘는 사람만 남깁니다. #11은 **반납된 것만** WHERE로 걸러 **AVG**로 장르별 평균 대출 일수를 냅니다. WHERE는 행을, HAVING은 **묶인 그룹**을 자릅니다.”

---

## 관련 파일

- `sql/03_queries.sql` — #7, #9, #10, #11, #12
- `results/q09_*.png` … `q12_*.png`
- `sql/02_seed.sql` — 집계가 0/다수가 되도록 설계
