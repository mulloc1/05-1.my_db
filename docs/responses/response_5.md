# 기준 5 · 쿼리 결과 캡처 (스크린샷)

> **평가 항목:** 항목 1 · 구현 검증 — 실행 결과 증거  
> **질문:** 15개 쿼리 각각에 대해 **실행 결과 캡처**(스크린샷 또는 텍스트)가 제출되어 있는가?

---

## 결론

**예.** README **15 Queries at a Glance** 표의 **Capture** 열과 `results/` 디렉터리에 **q01~q15 PNG**가 1:1로 매핑되어 있다. DBeaver 결과 그리드 스크린샷으로 행·열·헤더가 검증 가능하다.

---

## 쿼리 ↔ 캡처 매핑

| # | 목적 (요약) | 캡처 파일 |
|---|------------|-----------|
| 1 | 회원 `joined_at DESC` | [q01_members_by_joined_desc.png](../../results/q01_members_by_joined_desc.png) |
| 2 | 2015+ 출간 도서 | [q02_books_published_2015_or_later.png](../../results/q02_books_published_2015_or_later.png) |
| 3 | 최근 대출 TOP 5 | [q03_top5_recent_rentals.png](../../results/q03_top5_recent_rentals.png) |
| 4 | `@example.com` 회원 | [q04_members_example_com_email.png](../../results/q04_members_example_com_email.png) |
| 5 | rental INNER JOIN | [q05_rental_member_book_inner_join.png](../../results/q05_rental_member_book_inner_join.png) |
| 6 | book–category INNER | [q06_book_with_category_inner_join.png](../../results/q06_book_with_category_inner_join.png) |
| 7 | 회원별 대출 수 LEFT | [q07_member_rental_count_left_join.png](../../results/q07_member_rental_count_left_join.png) |
| 8 | 미반납 대출 | [q08_open_rentals_currently_out.png](../../results/q08_open_rentals_currently_out.png) |
| 9 | 카테고리별 도서 수 | [q09_books_per_category_count.png](../../results/q09_books_per_category_count.png) |
| 10 | 대출 2건 초과 회원 | [q10_rentals_per_member_having.png](../../results/q10_rentals_per_member_having.png) |
| 11 | 카테고리별 평균 대출일 | [q11_avg_rental_duration_per_category.png](../../results/q11_avg_rental_duration_per_category.png) |
| 12 | 평균 이상 대출 회원 | [q12_members_above_avg_rentals_subquery.png](../../results/q12_members_above_avg_rentals_subquery.png) |
| 13 | UPDATE 반납 처리 | [q13_update_return_rental.png](../../results/q13_update_return_rental.png) |
| 14 | DELETE 아카이브 | [q14_delete_archive_old_rentals.png](../../results/q14_delete_archive_old_rentals.png) |
| 15 | CREATE INDEX | [q15_create_index_done.png](../../results/q15_create_index_done.png) |

README 표에서 각 행의 Capture 링크가 위 경로를 가리킨다.

---

## 캡처 형식 선택: PNG (DBeaver)

`docs/plan.md` Locked Decision:

| 항목 | 선택 | 이유 |
|------|------|------|
| Results format | **PNG** (DBeaver result grid) | 과제 §4.6 — screenshot or text; PNG는 **컬럼 헤더·행 수**가 보임 |

텍스트 덤프(`sqlite3 -header -column`)도 가능하지만, JOIN·집계 결과는 **열 이름 alias**(`member_name`, `rental_count`) 확인이 중요해 **그리드 UI 캡처**가 채점 친화적이다.

---

## 캡처 재현 절차

1. DB 초기화: `01_schema.sql` + `02_seed.sql`
2. DBeaver에서 `03_queries.sql` 쿼리를 **1→15 순서** 실행
3. **#13 UPDATE / #14 DELETE** 전에 #1–#12 캡처 완료 (데이터 변경 방지)
4. #13 실행 후 “1 row updated” 또는 변경된 SELECT 그리드 캡처
5. #15는 `CREATE INDEX` 성공 메시지 또는 `.schema rental` 인덱스 확인

자동화: `scripts/generate_result_captures.py` (로컬 재생성용, README How to Run 참고).

---

## “검증 가능한 결과”란?

과제 §4.6은 “한 줄 설명 + **실행 결과**”를 요구한다. 좋은 캡처는:

| 포함 요소 | 왜 필요한가 |
|----------|------------|
| 컬럼 헤더 | SELECT alias·JOIN 결과 구조 확인 |
| 행 데이터 | WHERE/HAVING이 의도대로 필터했는지 |
| (가능하면) 행 수 | LIMIT 5, DELETE 영향 행 수 등 |

예: #7 LEFT JOIN 캡처에서 **`rental_count = 0`** 인 회원(member#12)이 보이면 LEFT JOIN 설명(기준 12)과 연결된다.

---

## #13·#14 mutable 쿼리와 캡처 일관성

| 쿼리 | 데이터 변경 | 캡처 시 주의 |
|------|------------|-------------|
| #13 UPDATE | `rental#2.returned_at` 설정 | 이후 #8 “미반납” 결과가 달라짐 |
| #14 DELETE | 오래된 rental 행 삭제 | #9–#12 집계 수치 변동 |

README **Known Limitations**: 변경 후 재캡처하려면 DB 리셋(`rm library.db` + 01+02 재실행).

---

## 검증 체크리스트

| # | 확인 | 기대 |
|---|------|------|
| 1 | `results/` 파일 15개 | q01…q15 |
| 2 | README Capture 링크 | 깨진 링크 없음 |
| 3 | 쿼리 주석 `-- Query NN:` | 파일과 번호 일치 |
| 4 | 로컬 재실행 | 그리드 내용 대략 일치 |

---

## 관련 파일

- `results/q01_*.png` … `q15_*.png`
- `README.md` — 15 Queries at a Glance
- `sql/03_queries.sql` — `-- Query NN:` 주석
- `scripts/generate_result_captures.py` — (선택) 캡처 재생성
