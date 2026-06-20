# 기준 15 · 미션 회고 — 어려웠던 점과 해결

> **평가 항목:** 항목 4 · 회고  
> **질문:** 미션 수행 중 **가장 어려웠던 부분**과 **해결 방법**을 구체적으로 작성했는가?

---

## 결론

**예 (본 문서로 보완).** README에는 기술적 Known Limitations만 있고 **학습 회고**가 없었다. 아래는 SQLite FK·변경 쿼리 순서·LEFT JOIN 집계·서브쿼리 #12·캡처 재현성 등 **실제로 막혔던 지점**과 해결 과정을 기록한 회고다.

---

## 회고 요약

| 순위 | 어려움 | 해결 |
|------|--------|------|
| 1 | SQLite FK가 기본 OFF | 모든 `.sql` 상단 `PRAGMA foreign_keys = ON` |
| 2 | #13/#14 후 earlier 쿼리 결과 불일치 | 캡처 순서 1–12 → 13–15, DB 리셋 문서화 |
| 3 | #7 `rental_count=0` 회원 | LEFT JOIN + `COUNT(r.id)` (NOT `COUNT(*)`) |
| 4 | #12 “평균” 정의 | `rental GROUP BY member_id` 파생 테이블 AVG |
| 5 | #11 일수 계산 이식성 | `julianday` + Postgres 대안 주석 |

---

## 1. SQLite 외래 키가 “안 먹는” 것처럼 보였던 문제

### 증상

`01_schema.sql`에 FK를 정의했는데, orphan `INSERT`가 **성공**하거나 README 검증이 **실패**했다.

### 원인

SQLite는 **레거시 호환**으로 `PRAGMA foreign_keys` **기본값 OFF**. FK 정의는 있어도 **런타임 검사 비활성**.

### 해결

```sql
-- 모든 SQL 파일 첫 줄 근처
PRAGMA foreign_keys = ON;
```

- `01_schema.sql`, `02_seed.sql`, `03_queries.sql` **공통**
- README **Verifying Constraints** + **Known Limitations**에 명시
- DBeaver 실행 시 **스크립트 전체**가 pragma 포함해 실행되도록 확인

### 배운 점

**스키마 DDL만으로는 무결성이 보장되지 않는다** — RDBMS별 **연결/세션 설정**도 설계·문서화 대상.

---

## 2. UPDATE/DELETE(#13, #14)와 캡처·재실행 충돌

### 증상

#13 실행 후 #8 “미반납 대출” 결과에서 **rental#2가 사라짐**. #14 DELETE 후 집계 쿼리 **행 수 변경**. `results/q08`과 **현재 DB 불일치**.

### 원인

UPDATE/DELETE는 **상태를 바꾸는(mutable)** 연산. SELECT-only 쿼리와 **같은 DB 스�APSHOT**을 공유하지 않음.

### 해결

1. **캡처 순서 고정:** fresh seed → #1–#12 캡처 → #13–#15
2. README **How to Run** Note:

   > Re-run steps 1–2 above to reset.

3. Known Limitations에 #13/#14 **mutate rental** 명시

### 배운 점

운영 DB에서도 **마이그레이션·배치 DELETE** 전후 **리포트 쿼리**가 달라진다. 테스트는 **시드 고정 + 트랜잭션 롤백** 또는 **별도 DB 복제**가 필요.

---

## 3. LEFT JOIN + COUNT에서 “0건 회원”이 1로 나온 문제 (#7)

### 증상

`member#12` (대출 0)의 `rental_count`가 **0이 아니라 1**.

### 원인

```sql
-- 잘못된 패턴
COUNT(*)   -- GROUP BY member 1행 = 1
-- 또는
COUNT(r.*) -- LEFT JOIN 후 NULL row도 세는 방식 혼동
```

### 해결

```sql
COUNT(r.id) AS rental_count  -- r.id NULL이면 0
```

시드에 **의도적으로** member#12 zero rental 추가 (`02_seed.sql` 주석).

### 배운 점

LEFT JOIN 집계는 **“무엇을 세는가”** 가 결과 의미를 결정. #7 캡처로 **0 검증** 가능.

---

## 4. 쿼리 #12 — “평균보다 많이”의 정의 혼란

### 증상

- 전체 member(0건 포함) 평균 vs rental 있는 member만 평균 — **HAVING 결과 다름**
- 서브쿼리 위치: SELECT vs HAVING

### 해결 과정

1. 요구를 **“회원별 rental cnt의 AVG보다 큰 member”** 로 문장화
2. **안쪽:** `SELECT COUNT(*) … GROUP BY member_id` → `AVG(cnt)`
3. **바깥:** `LEFT JOIN` + `HAVING COUNT(r.id) > (subquery)`
4. `docs/plan.md` / `-- Query 12:` 주석과 README 표 설명 정렬

### 배운 점

복잡 SQL은 **자연어 요구 → 중간 결과 테이블 그림 → SQL** 순이 오류를 줄인다 (기준 14와 동일).

---

## 5. #11 `julianday`와 SQLite 종속

### 증상

“평균 대출 **일수**”를 `(returned_at - rented_at)`로 어떻게?

### 해결

```sql
ROUND(AVG(julianday(r.returned_at) - julianday(r.rented_at)), 1)
```

- `-- SQLite-specific:` 주석
- Postgres: `(returned_at::date - rented_at::date)` 주석 병기
- `WHERE returned_at IS NOT NULL` — 미반납 제외

### 배운 점

과제 §4.1 **표준 SQL 우선, dialect는 주석** — 이식성과 동작을 **동시에** 만족.

---

## 6. 시드 데이터와 쿼리 요구사항 맞추기

### 증상

#14 “1년 이상 지난 **반납** rental DELETE” — 초기 seed에 해당 행 **없음** → DELETE 0 rows.

### 해결

`02_seed.sql` 헤더:

> rentals older than 1 year for query #14

- `rented_at < date('now', '-1 year')` AND `returned_at IS NOT NULL` 행 **의도적 삽입**
- member#12 zero rental, open rentals for #8 등 **쿼리별 시나리오** 주석

### 배운 점

DB 과제는 **스키마 + 데이터 + 쿼리** 삼각형 — seed가 **테스트 케이스** 역할.

---

## 7. ERD·문서 vs 구두 설명 gap (평가 6–15)

### 증상

구현(Pass 1–5)은 충족했으나, **왜 4테이블인지·JOIN 차이·회고**가 README에 없어 설명 항목 Fail.

### 해결 (본 responses 시리즈)

- `docs/responses/response_6.md` … `response_15.md` — **구두·서면 설명** 보강
- (선택) README에 “Design Rationale” 섹션 링크 추가

### 배운 점

**동작하는 SQL ≠ 설명 가능한 설계** — subject §3 Learning Objectives는 **말로 풀기**까지 포함.

---

## 잘 됐던 점 (짧게)

| 항목 | 이유 |
|------|------|
| 3파일 분리 (01/02/03) | 채점·재실행 순서 명확 |
| `qNN_` 캡처 명명 | 쿼리 번호 1:1 |
| Coverage tally in SQL footer | #4 자체 검증 |
| RESTRICT FK | 실수 DELETE 방지, Verifying Constraints 스토리 |

---

## 다음에 다시 한다면

1. README 초안에 **Design Rationale** (기준 6–11 요약) 포함
2. #12 평균 정의를 **한 문장** README에 고정
3. `sqlite3` **테스트 스크립트**로 FK 실패·#7 zero count 자동 assert (보너스)
4. PostgreSQL Docker로 **동일 schema 이식** 실험 (`bonus_plan.md`)

---

## 구두 회고 30초

> “가장 헷갈린 건 SQLite FK pragma와 #13 UPDATE 뒤 캡처가 어긋난 거였습니다. pragma를 파일마다 넣고, 캡처는 1–12 먼저 찍은 뒤 DB를 리셋하는 순서로 정리했습니다. LEFT JOIN에서 COUNT 컬럼 고르는 것과 #12 서브쿼리 평균 정의도 연습이 됐습니다.”

---

## 관련 파일

- `README.md` — Known Limitations, How to Run
- `docs/plan.md` — Locked Decisions
- `sql/02_seed.sql` — 시나리오 주석
- `docs/responses/response_6.md` … `response_14.md` — 개념 보강
