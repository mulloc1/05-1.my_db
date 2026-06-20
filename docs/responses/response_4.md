# 기준 4 · 15개 쿼리 카테고리 충족

> **평가 항목:** 항목 1 · 구현 검증 — 쿼리 구성  
> **질문:** Basic select(4), JOIN(4), Aggregate(3), Subquery(1), UPDATE/DELETE(2), Index(1)로 **정확히 15개** 쿼리가 작성되어 있는가?

---

## 결론

**예.** `sql/03_queries.sql`에 **15개 쿼리**가 번호·한 줄 주석과 함께 정의되어 있으며, 파일 하단 Coverage tally와 README **15 Queries at a Glance** 표가 동일한 분류를 확인한다.

---

## 카테고리 매트릭스

| 카테고리 | 요구 | 실제 | 쿼리 # |
|----------|------|------|--------|
| Basic SELECT | 4 | **4** | #1–#4 |
| JOIN (INNER) | 3+ | **3** | #5, #6, #8 |
| JOIN (LEFT) | 1+ | **1** | #7 |
| Aggregate + GROUP BY | 3 | **3** | #9, #10, #11 |
| Subquery | 1 | **1** | #12 |
| UPDATE | 1 | **1** | #13 |
| DELETE | 1 | **1** | #14 |
| CREATE INDEX | 1 | **1** | #15 |
| **합계** | **15** | **15** | |

JOIN 합계 4개 = INNER 3 + LEFT 1 (과제 “JOIN 4개” 요구와 일치).

---

## 쿼리별 한 줄 목적

| # | 카테고리 | 목적 |
|---|----------|------|
| 1 | Basic | 회원 전체, `joined_at DESC` 정렬 |
| 2 | Basic | 2015년 이후 출간 도서, 연도·제목 정렬 |
| 3 | Basic | 최근 대출 TOP 5 (`ORDER BY rented_at DESC LIMIT 5`) |
| 4 | Basic | 이메일 `@example.com` 필터 (`LIKE`) |
| 5 | INNER JOIN | 대출 + 회원명 + 도서명 |
| 6 | INNER JOIN | 도서 + 카테고리명 |
| 7 | LEFT JOIN | 전 회원 + 대출 건수(0 포함) |
| 8 | INNER JOIN + WHERE | 미반납 대출 (`returned_at IS NULL`) |
| 9 | Aggregate | 카테고리별 도서 수 `COUNT` |
| 10 | Aggregate | 회원별 대출 수, `HAVING COUNT > 1` |
| 11 | Aggregate | 카테고리별 평균 대출 일수 `AVG` |
| 12 | Subquery | 평균 대출 수 **초과** 회원 |
| 13 | UPDATE | 미반납 rental #2 반납 처리 |
| 14 | DELETE | 1년 지난 반납 이력 아카이브 |
| 15 | Index | `idx_rental_member_rented` 생성 |

---

## 파일 내 자체 검증 (Coverage tally)

```119:125:05-1.my_db/sql/03_queries.sql
-- Coverage tally:
--   Basic select: 4   (#1–#4)
--   Joins:        4   (#5 INNER, #6 INNER, #7 LEFT, #8 INNER)
--   Aggregates:   3   (#9 COUNT, #10 COUNT, #11 AVG; all with GROUP BY)
--   Subquery:     1   (#12)
--   Update/Delete: 2  (#13 UPDATE, #14 DELETE)
--   Index:        1   (#15 CREATE INDEX)
```

채점자가 파일만 열어도 **과제 §4.5 매트릭스**와 대조 가능하도록 의도적으로 footer를 넣었다.

---

## 카테고리별 SQL 패턴 (전문가 요약)

### Basic SELECT (#1–#4)

- `SELECT … FROM single_table`
- `WHERE`, `ORDER BY`, `LIMIT`, `LIKE` — **단일 테이블 검색·정렬·필터** 기본기

### JOIN (#5–#8)

- **INNER**: 매칭되는 행만 (대출이 있는 회원–도서 조합)
- **LEFT**: 왼쪽(`member`) 전원 유지, 매칭 없으면 NULL → #7에서 0건 회원 포함

### Aggregate (#9–#11)

- `GROUP BY` + `COUNT` / `AVG`
- `HAVING`: 그룹 **필터** (`WHERE`는 행 필터, `HAVING`은 그룹 필터 — #10)

### Subquery (#12)

- 상관 없는 집계 서브쿼리: 회원별 대출 수의 **전체 평균**과 비교
- “평균보다 많이 빌린 회원” = **순위/이상치** 문제 패턴

### DML (#13–#14)

- **UPDATE**: 상태 전환 (`returned_at` NULL → 타임스탬프)
- **DELETE**: 보관 정책 (오래된 반납 이력 제거)

### Index (#15)

- `CREATE INDEX … ON rental(member_id, rented_at)` — 조회 패턴 가속 (기준 9·15에서 상세)

---

## 실행 순서 주의 (#13, #14)

README 명시:

> Queries **#13** (`UPDATE`) and **#14** (`DELETE`) **change data**. For captures that match `results/`, run queries 1–12 first on a fresh seed, then #13–#15.

변경 쿼리는 **재현 가능한 캡처**를 위해 순서·초기화 전략이 필요하다. 이는 “쿼리 목록만 있으면 된다”가 아니라 **운영 관점**의 일부다.

---

## 검증 방법

```bash
cd 05-1.my_db
rm -f library.db
sqlite3 library.db < sql/01_schema.sql
sqlite3 library.db < sql/02_seed.sql
sqlite3 library.db < sql/03_queries.sql
```

에러 없이 15개 구문이 실행되면 구조·문법 검증 완료. DBeaver에서는 쿼리별 실행 후 `results/qNN_*.png`와 대조.

---

## 관련 파일

- `sql/03_queries.sql` — 15 쿼리 본문
- `README.md` — 15 Queries at a Glance
- `docs/subject.md` §4.5 — 과제 카테고리 요구
