# 기준 3 · 샘플 데이터 (≥ 10행/테이블)

> **평가 항목:** 항목 1 · 구현 검증 — 시드 데이터  
> **질문:** 각 테이블에 **최소 10행 이상**의 의미 있는 샘플 데이터가 `02_seed.sql`에 들어 있는가?

---

## 결론

**예.** `sql/02_seed.sql` 헤더 주석과 실제 INSERT를 기준으로 **category=12, book=15, member=12, rental=25** 행이 삽입되어 과제 최소(≥10/table)를 **모든 테이블에서 초과** 충족한다.

---

## 행 수 요약

| 테이블 | INSERT 행 수 | 최소 요구 | 상태 |
|--------|-------------|----------|------|
| `category` | **12** | ≥ 10 | ✅ |
| `book` | **15** | ≥ 10 | ✅ |
| `member` | **12** | ≥ 10 | ✅ |
| `rental` | **25** | ≥ 10 | ✅ |

```3:4:05-1.my_db/sql/02_seed.sql
-- Row counts: category=12, book=15, member=12, rental=25 (≥ subject §4.4 minimum of 10/table)
-- Coverage: member#12 zero rentals; open+returned rentals; rentals older than 1 year for query #14
```

---

## “의미 있는” 데이터 설계

단순히 10행을 채우는 것이 아니라, **15개 쿼리가 비어 있지 않은 결과**를 내도록 시나리오를 넣었다.

### category (12행)

Fiction, Science, Technology 등 **실제 도서관 분류**에 가까운 장르. `name UNIQUE`로 중복 분류 방지.

### book (15행)

- `Clean Code`, `1984`, `Sapiens` 등 **다양한 장르·출판연도**
- `published_year` 범위: 1925~2019 → 쿼리 #2 (`>= 2015`) 필터링 가능
- 각 `category_id`가 유효 FK → 쿼리 #6, #9, #11 JOIN·집계 가능

### member (12행)

- `@example.com` 이메일 → 쿼리 #4 `LIKE '%@example.com'`
- **`member#12`는 대출 0건** → 쿼리 #7 LEFT JOIN에서 `rental_count = 0` 검증
- `joined_at` 분포 → 쿼리 #1 `ORDER BY joined_at DESC`

### rental (25행)

| 시나리오 | 목적 (쿼리) |
|----------|------------|
| `returned_at IS NULL` (미반납) | #8 현재 대출 중 |
| `returned_at IS NOT NULL` (반납 완료) | #11 평균 대출 기간 |
| 1년 이상 지난 반납 이력 | #14 DELETE 아카이브 |
| 동일 member 다수 rental | #10 HAVING `> 1` |
| member#12 rental 없음 | #7 zero count |
| 최근 `rented_at` 분포 | #3 TOP 5 |

`rental`만 25행으로 **집계·JOIN·서브쿼리**에 통계적 의미를 부여했다 (`docs/plan.md`: “20–30 rental rows”).

---

## INSERT 순서 (FK 준수)

```sql
INSERT INTO category ...   -- 부모
INSERT INTO book ...       -- category 참조
INSERT INTO member ...     -- 독립 부모
INSERT INTO rental ...     -- member + book 참조
```

재실행 안전을 위해 상단에서 `DELETE FROM` 역의존 순서로 비운 뒤 INSERT한다.

---

## 검증 명령

```bash
cd 05-1.my_db
sqlite3 library.db < sql/01_schema.sql
sqlite3 library.db < sql/02_seed.sql

sqlite3 library.db "
  SELECT 'category' AS tbl, COUNT(*) AS cnt FROM category
  UNION ALL SELECT 'book', COUNT(*) FROM book
  UNION ALL SELECT 'member', COUNT(*) FROM member
  UNION ALL SELECT 'rental', COUNT(*) FROM rental;
"
```

기대:

```
category|12
book|15
member|12
rental|25
```

---

## 왜 10행 이상이 필요한가 (전문가 관점)

| 행 수 | JOIN/집계 학습 |
|-------|----------------|
| 1~2행 | GROUP BY, HAVING, AVG 결과가 자명해 **SQL 동작을 관찰하기 어려움** |
| ≥10행 | 필터·정렬·TOP N·평균 이상 회원(#12) 등 **패턴이 드러남** |

과제는 “데이터가 있어야 쿼리를 **검증**할 수 있다”는 전제다. README Subject Mapping §2.3 → `02_seed.sql`로 매핑되어 있다.

---

## 관련 파일

- `sql/02_seed.sql` — 전체 INSERT
- `README.md` — Subject Mapping §2.3
- `docs/plan.md` § Locked Decisions — 행 수 결정 근거
