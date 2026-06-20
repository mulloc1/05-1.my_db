# 기준 9 · 인덱스 컬럼 선택 이유

> **평가 항목:** 항목 2 · 설계 설명 — 인덱스  
> **질문:** `rental(member_id, rented_at)` 인덱스를 만든 이유, **왜 그 컬럼 조합**인지 설명할 수 있는가?

---

## 결론

**예 (본 문서로 보완).** 쿼리 #15는 `CREATE INDEX idx_rental_member_rented ON rental(member_id, rented_at)`를 정의한다. 이 **복합 인덱스**는 본 프로젝트 15개 쿼리 중 **회원별 rental 집계·필터**와 **최근 대출 시간순 조회** 패턴을 가속하기 위한 선택이다.

---

## 인덱스가 해결하는 문제

테이블이 커지면 DB는 조건·JOIN·정렬에 맞는 행을 찾기 위해 **Full Table Scan**(모든 행 읽기)을 할 수 있다. **인덱스**는 특정 컬럼(들) 값을 **정렬된 별도 구조(B-tree)** 로 유지해, “어디부터 읽을지” 빠르게 찾게 한다.

과제 §3 학습 목표 6: *“어떤 컬럼에 인덱스를 두는지”* — **실제 쿼리 WHERE/JOIN/GROUP BY/ORDER BY** 와 맞춰야 의미 있다.

---

## 선택한 인덱스

```116:117:05-1.my_db/sql/03_queries.sql
CREATE INDEX IF NOT EXISTS idx_rental_member_rented
  ON rental(member_id, rented_at);
```

| 속성 | 값 |
|------|-----|
| 테이블 | `rental` (행 수가 가장 많고, 쿼리 빈도 높음) |
| 컬럼 순서 | **`member_id` 먼저**, **`rented_at` 둘째** |
| 유형 | **복합(composite) 인덱스** |

`03_queries.sql` 주석:

> accelerates queries #7 and #10 (group/aggregate on member_id) and #3 (ORDER BY rented_at DESC LIMIT 5)

---

## 왜 `member_id`인가?

### 도메인

대출 테이블에서 **회원별** 질문이 많다:

- “이 회원은 몇 번 빌렸나?” (#7, #10)
- “평균보다 많이 빌린 회원?” (#12 — rental을 member_id로 GROUP)

### SQL 패턴

```sql
FROM member m
LEFT JOIN rental r ON r.member_id = m.id   -- #7
GROUP BY m.id

FROM member m
INNER JOIN rental r ON r.member_id = m.id  -- #10
GROUP BY m.id
HAVING COUNT(r.id) > 1
```

JOIN 조건 **`r.member_id = m.id`** 는 `rental.member_id`로 rental 행을 **좁히는(narrowing)** 연산이다. `member_id`에 인덱스가 있으면 “member X의 rental만” 빠르게 찾는다.

**단일 컬럼 인덱스 `(member_id)`** 만으로도 #7, #10에 상당 부분 도움.

---

## 왜 `rented_at`을 두 번째 컬럼에 넣었나?

### 복합 인덱스 왼쪽 접두(prefix) 규칙

B-tree 복합 인덱스 `(A, B)`는 대략:

- `WHERE A = ?` ✅
- `WHERE A = ? AND B > ?` / `ORDER BY B` ✅ (같은 A 안에서)
- `WHERE B = ?` **만** ❌ (A 없으면 인덱스 활용 제한)

### 쿼리 #3 패턴

```sql
FROM rental r
INNER JOIN book b ON b.id = r.book_id
ORDER BY r.rented_at DESC
LIMIT 5;
```

전역 “최근 5건”이므로 **`member_id` 필터 없음** — 이 경우 `(member_id, rented_at)` 인덱스만으로는 `rented_at` 단독 정렬에 **완벽하지 않을 수 있다**. (SQLite 옵티마이저는 테이블 크기에 따라 풀스캔 선택 가능)

**솔직한 설계 서술:**

| 쿼리 | 인덱스 기여 |
|------|------------|
| #7, #10, #12 (member_id 그룹) | **`member_id` 접두** — 주요 이득 |
| #3 (전체 rented_at 정렬) | rental 25행 규모에선 체감 미미; **대규모 시 `(rented_at DESC)` 단독 인덱스** 추가 검토 |
| #8 (미반납 + 정렬) | `returned_at IS NULL` — 별도 partial index 후보 (보너스) |

과제는 **인덱스 1개**만 요구하므로, **가장 많이 쓰이는 FK + 시간** 조합 `(member_id, rented_at)` 을 Locked Decision으로 선택 (`docs/plan.md`: “rentals by member, recent first”).

### 회원별 “최근 대출” (확장 시나리오)

```sql
WHERE member_id = 3
ORDER BY rented_at DESC
LIMIT 1;
```

이 패턴에는 `(member_id, rented_at)` **복합 인덱스가 이상적** — member_id로 구간 좁힌 뒤 rented_at 순 정렬.

---

## 왜 `book_id` 인덱스는 #15가 아닌가?

| 후보 | 자주 쓰이는 쿼리 |
|------|-----------------|
| `member_id` | #5, #7, #8, #10, #12 |
| `book_id` | #3, #5, #8, #11 |

둘 다 JOIN에 쓰이지만, **GROUP BY member_id** 질문(#7, #10, #12)이 과제 학습 목표(회원 행동 집계)와 더 맞아 **`member_id` 우선**. `book_id` 인덱스는 보너스(`bonus_plan.md`) 후보.

---

## 인덱스 트레이드오프

| 장점 | 단점 |
|------|------|
| SELECT/JOIN 가속 | INSERT/UPDATE/DELETE 시 인덱스도 갱신 → **쓰기 약간 느림** |
| 디스크 추가 사용 | 너무 많은 인덱스 → 옵티마이저 혼란 |

`rental`은 **INSERT/UPDATE 빈번**(대출·반납)이므로 과제 범위에선 **1개만** — YAGNI.

---

## 검증 (#15 캡처)

```bash
sqlite3 library.db ".indexes rental"
# idx_rental_member_rented

sqlite3 library.db "EXPLAIN QUERY PLAN
  SELECT member_id, COUNT(*) FROM rental GROUP BY member_id;"
```

실행 계획에 `USING INDEX` / `COVERING INDEX` 등이 보이면 인덱스 사용 힌트 (SQLite 버전·통계에 따라 다름).

---

## 구두 설명용 스크립트

> “rental은 데이터가 많아지는 테이블이라 인덱스를 하나 달았습니다. **member_id**는 회원별 대출 JOIN·GROUP BY에 계속 나오고, **rented_at**은 같은 회원 안에서 최근 대출 순으로 볼 때 복합 인덱스 두 번째 컬럼으로 의미가 있습니다. 과제 쿼리 #7, #10과 회원 중심 집계에 맞춘 선택입니다.”

---

## 관련 파일

- `sql/03_queries.sql` — Query #15 + 주석
- `docs/plan.md` — Index choice Locked Decision
- `results/q15_create_index_done.png` — 실행 캡처
- `docs/subject.md` §3.6 — 인덱스 학습 목표
