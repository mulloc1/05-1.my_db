# 기준 14 · 가장 복잡한 쿼리 — 단계별 풀이

> **평가 항목:** 항목 3 · 핵심 개념 — 쿼리 분해  
> **질문:** 15개 중 **가장 복잡한 쿼리**를 고르고, **단계별로 어떻게 풀었는지** 설명할 수 있는가?

---

## 결론

**예 (본 문서로 보완).** 본 프로젝트에서 **가장 복잡한 쿼리**는 **#12 (서브쿼리 + LEFT JOIN + GROUP BY + HAVING)** 로 판단한다. #11(다중 JOIN + AVG + SQLite 함수)이 그다음이다. 아래는 #12를 **요구사항 → 설계 → SQL 조각 → 결과 검증** 순으로 분해한 풀이다.

---

## 왜 #12가 “가장 복잡”한가

| 복잡도 요인 | #12 | 다른 쿼리 비교 |
|------------|-----|---------------|
| JOIN 종류 | LEFT JOIN | #5–#6 INNER만 |
| 집계 | GROUP BY + COUNT | #9–#10 단일 레벨 |
| 필터 | **HAVING + 서브쿼리** | #10 HAVING만 |
| 서브쿼리 | **중첩 + 파생 테이블** | #12만 |
| 개념 | “전체 평균” **동적 임계값** | #10은 상수 `> 1` |

```87:98:05-1.my_db/sql/03_queries.sql
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
```

---

## Step 0 · 요구사항을 한국어로

> **“평균보다 많이 책을 빌린 회원”** 을 찾아라.

부분 요구:

1. **회원별** 대출 **건수** 계산
2. **전 회원(또는 대출 있는 회원)** 의 그 건수들의 **평균** 계산
3. 자신의 건수 > 그 평균인 회원만 출력
4. 0건 회원은 “평균보다 많다”가 성립하기 어려움 — LEFT JOIN으로 포함하되 HAVING에서 탈락

---

## Step 1 · 안쪽부터 — “회원별 대출 수” 목록

```sql
SELECT COUNT(*) AS cnt
FROM rental
GROUP BY member_id;
```

**결과 형태 (개념):**

| member_id | cnt |
|-----------|-----|
| 1 | 5 |
| 2 | 3 |
| … | … |

**rental이 없는 member**는 이 서브쿼리에 **행 없음** — “대출한 회원”만 cnt 보유.

---

## Step 2 · 그 목록의 평균 — “평균 회원 대출 수”

```sql
SELECT AVG(per_member.cnt)
FROM (
  SELECT COUNT(*) AS cnt FROM rental GROUP BY member_id
) AS per_member;
```

**의미:**

- `per_member` = **파생 테이블**(inline view) — “회원당 1행, cnt 컬럼”
- `AVG(cnt)` = **대출 경험이 있는 회원들**의 대출 건수 평균

**주의 (설계 선택):**

- Jordan(0건)은 **평균 계산에 포함 안 됨** (rental GROUP BY에 없음)
- “전체 가입자 평균”을 원하면 `member LEFT JOIN rental`로 cnt=0 포함한 뒤 AVG — **문제 정의가 달라짐**

과제 #12는 **“rental GROUP BY member_id의 AVG”** — README/주석과 일치.

---

## Step 3 · 바깥 — 회원별 COUNT와 HAVING 비교

```sql
SELECT m.id, m.name, COUNT(r.id) AS rental_count
FROM member m
LEFT JOIN rental r ON r.member_id = m.id
GROUP BY m.id, m.name
HAVING COUNT(r.id) > ( Step 2 서브쿼리 )
```

**동작:**

1. LEFT JOIN → member 12명 각각 그룹
2. `COUNT(r.id)` = 해당 회원 대출 건수 (Jordan = 0)
3. HAVING: `rental_count > (평균)` 인 그룹만

**Jordan:** 0 > avg → **false** → 제외  
**Alice:** 5 > avg → avg가 5 미만이면 **포함**

---

## Step 4 · ORDER BY

```sql
ORDER BY rental_count DESC;
```

“평균 이상” 회원을 **많이 빌린 순**으로 — 리포트 가독성.

---

## 실행 계획 (논리 흐름 다이어그램)

```
rental
   │
   ├─► [서브쿼리 A] GROUP BY member_id → cnt
   │         │
   │         └─► AVG(cnt) = threshold
   │
member ──LEFT JOIN──► rental
   │
   └─► GROUP BY member → COUNT(r.id) = rental_count
              │
              └─► HAVING rental_count > threshold
                        │
                        └─► 결과 집합 (q12 캡처)
```

---

## 풀이 과정에서 고려한 대안

### 대안 1: #10처럼 상수 `HAVING > 1`

- 단순하지만 **“평균”** 요구 미충족

### 대안 2: 윈도우 함수 (SQLite 3.25+)

```sql
-- 개념 (보너스; 과제는 서브쿼리 1개 요구)
AVG(COUNT(...)) OVER () 
```

과제 §4.5 **Subquery: 1** → **스칼라 서브쿼리 + 파생 테이블** 선택.

### 대안 3: INNER JOIN만

- 0건 회원 제외 — 문제에 “member who rented more than…”이면 INNER도 가능하나, **LEFT + HAVING**이 #7과 패턴 통일.

---

## 결과 검증 (캡처 q12)

1. **모든 출력 행:** `rental_count > (수동 계산한 avg)`  
2. **Jordan 없음** (0건)  
3. **#10 결과**와 교차: #10은 `>1`, #12는 **동적 threshold** — #12 ⊆ “다회 이용자”일 수 있으나 avg에 따라 다름

**수동 검증 스니펫:**

```bash
sqlite3 library.db "
  SELECT AVG(cnt) FROM (
    SELECT COUNT(*) AS cnt FROM rental GROUP BY member_id
  );
"
# 나온 값을 기억하고 #12 결과의 rental_count와 비교
```

---

## #11을 두 번째로 복잡한 이유 (짧게)

- rental → book → category **2-hop JOIN**
- `WHERE returned_at IS NOT NULL` + **AVG** + `julianday` dialect
- “카테고리별” 그룹 — book을 거쳐 category 부여

풀이 순서: 반납만 필터 → JOIN으로 장르 붙이기 → GROUP BY category → AVG(일수).

---

## 구두 설명용 1분 스크립트

> “가장 어려운 건 #12입니다. 먼저 rental을 member_id로 묶어 **회원별 대출 수**를 만들고, 그 숫자들의 **평균**을 구합니다. 바깥에서는 모든 member에 LEFT JOIN으로 대출 수를 세고, **HAVING**으로 자기 count가 그 평균보다 큰 사람만 남깁니다. 안쪽 서브쿼리가 **기준선**, 바깥 GROUP BY가 **회원별 점수**입니다.”

---

## 관련 파일

- `sql/03_queries.sql` — Query #12
- `results/q12_members_above_avg_rentals_subquery.png`
- `docs/bonus_plan.md` — (선택) join vs subquery 비교
