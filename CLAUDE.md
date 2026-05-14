# JobMonster — 자동 채용공고 오케스트레이션 파이프라인

## 프로젝트 개요

핀테크 인턴십 지원을 위한 자동화 시스템. 원티드·사람인에서 채용공고를 수집하고, AI로 스크리닝한 뒤, 기업분석 리포트와 함께 텔레그램으로 발송한다.

## 실행 환경

- **위치**: `job-orchestrator/` 디렉토리
- **브랜치**: `claude/job-posting-orchestration-aE6dY`
- **Python**: 3.12+ 권장
- **OS**: Windows PC 로컬 실행 (인코딩 주의: 모든 파일 I/O는 `encoding="utf-8"` 명시)

### 실행 방법 (Windows)
```
cd fintech-internship-2026\job-orchestrator
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### .env 파일 (job-orchestrator/.env)
```
TELEGRAM_BOT_TOKEN=8856774881:AAFz06DhjHUuA3w75CIJfF5ZuPh3jQaKi58
TELEGRAM_CHAT_ID=8746899014
GEMINI_API_KEY=[본인 키 입력]
SARAMIN_API_KEY=[사람인 API 키 - 신청 중]
WANTED_ACCESS_TOKEN=    # 현재 비어있음 (없어도 동작)
ANTHROPIC_API_KEY=      # 사용 안 함
CRUNCHBASE_API_KEY=     # 사용 안 함
```

---

## 아키텍처

```
main.py  ←→  scheduler.py (APScheduler)
    │
    ├─ 1단계: collectors/wanted.py  + collectors/saramin.py
    ├─ 2단계: screener/jd_screener.py  (Gemini 2.0 Flash Lite → 키워드 폴백)
    ├─ 3단계: enricher/company_enricher.py
    │           ├─ enricher/wanted_company.py  ← Wanted API (작동)
    │           └─ enricher/news_search.py     ← Google News RSS (작동)
    ├─ 4단계: reporters/report_builder.py
    └─ 5단계: reporters/telegram.py
                reporters/company_report.py   (기업분석 리포트)

reporters/telegram_bot.py  ← 양방향 인터페이스 (롱폴링)
db/__init__.py             ← SQLite (jobs, companies, watchlist 테이블)
```

---

## 파일별 상태

### 핵심 파일

| 파일 | 상태 | 설명 |
|------|------|------|
| `main.py` | ✅ 완성 | 5단계 파이프라인 오케스트레이션 |
| `config.py` | ✅ 완성 | 환경변수 로딩, 경로 설정 |
| `scheduler.py` | ✅ 완성 | 원티드 30분/사람인 60분 간격, 위시리스트 매일 9시 |
| `db/__init__.py` | ✅ 완성 | jobs/companies/watchlist 테이블, 캐시 TTL 7일 |

### 수집기

| 파일 | 상태 | 설명 |
|------|------|------|
| `collectors/wanted.py` | ✅ 완성 | 기획·PM/IT·개발 카테고리, 신입/경력/전체 필터 |
| `collectors/saramin.py` | ✅ 완성 | API 키 없으면 비활성화됨 (사람인 신청 중) |

### 스크리닝

| 파일 | 상태 | 설명 |
|------|------|------|
| `screener/jd_screener.py` | ✅ 완성 | Gemini `gemini-2.0-flash-lite` 사용 |

**주의**: Gemini 무료 티어 일일 쿼터 초과 시 circuit breaker 발동 → 키워드 매칭으로 자동 폴백. 다음 날 자정에 자동 리셋.

### Enricher

| 파일 | 상태 | 설명 |
|------|------|------|
| `enricher/company_enricher.py` | ✅ 완성 | wanted_company + news_search 체인 |
| `enricher/wanted_company.py` | ✅ 작동 | Wanted API → 설립연도 추출 완료, 직원수는 API가 미제공 |
| `enricher/news_search.py` | ✅ 완성 | **Google News RSS** 사용 (100건 이상 안정적 반환) |
| `enricher/crunchbase.py` | ⛔ 비활성 | API 키 없음 → 항상 빈값, 체인에서 제거됨 |
| `enricher/jobplanet.py` | ⛔ 비활성 | 403 차단 → 항상 실패, 체인에서 제거됨 |
| `enricher/thevc.py` | ⛔ 비활성 | 404 에러 → 체인에서 제거됨 |

### 리포터

| 파일 | 상태 | 설명 |
|------|------|------|
| `reporters/telegram.py` | ✅ 완성 | 채용공고 알림 발송 |
| `reporters/telegram_bot.py` | ✅ 완성 | 양방향 인터페이스, 키보드 버튼 |
| `reporters/company_report.py` | ✅ 완성 | 기업분석 리포트 HTML 생성 + 발송 |
| `reporters/report_builder.py` | ✅ 완성 | 배치 리포트 빌더 |

---

## 텔레그램 봇 (@jobmonster_bot)

### 키보드 버튼
```
[📊 상태]        [▶️ 즉시실행]
[⏸️ 일시정지]    [▶️ 재개]
[📋 오늘 공고]   [📈 통계]
[⭐ 관심기업 목록] [🔄 수집모드]
```

### 명령어
| 명령어 | 기능 |
|--------|------|
| `/status` | 파이프라인 상태 |
| `/run` | 즉시 실행 |
| `/pause` / `/resume` | 일시정지/재개 |
| `/jobs` | 오늘 공고 + 기업분석 리포트 |
| `/stats` | 수집 통계 |
| `/analyze 기업명` | 특정 기업 즉시 분석 (캐시 무효화 후 재수집) |
| `/watch 기업명` | 관심 기업 등록 |
| `/unwatch 기업명` | 관심 기업 삭제 |
| `/watchlist` | 관심 기업 목록 |
| `/mode entry\|career\|all` | 수집 모드 변경 |

---

## 기업분석 리포트 구조

```
━━━━━━━━━━━━━━━━━━━━
🏢 기업분석 리포트
━━━━━━━━━━━━━━━━━━━━

[기업명]
[규모] | 직원 [수] | 설립 [연도]

📊 투자 현황
  투자단계: [Series 정보]
  주요투자사: [투자자]

🤖 AI · 기술 동향
  [AI 관련 뉴스 요약]

📰 최근 핵심 뉴스
  ① [제목] (링크)
     [출처] | [날짜]
  ...최대 5건

💼 채용 포지션  ← 공고가 있을 때만 표시
  [포지션명] ⏰ D-N
  [공고 바로가기 →]
━━━━━━━━━━━━━━━━━━━━
```

---

## 현재 작동 상태 (2026-05-14 기준)

### ✅ 작동하는 것
- 파이프라인 전체 흐름 (수집 → 스크리닝 → enrichment → 텔레그램)
- Wanted API 수집 (access token 불필요, 공개 API)
- Gemini AI 스크리닝 + circuit breaker 폴백
- 텔레그램 양방향 인터페이스 (키보드 + 명령어)
- 기업분석 리포트 발송
- **Google News RSS** 뉴스 수집 (100건+ 안정 반환)
- Wanted API에서 설립연도 추출
- `/analyze` 캐시 무효화 후 재수집
- 위시리스트 기능 (등록/삭제/목록/일 1회 자동분석)
- 오늘 공고 버튼 → 기업분석 리포트 자동 발송

### ⚠️ 미완성/제한 사항
- **직원수**: Wanted API 응답에 `employee_count` 필드 없음 → 항상 "정보 없음"
  - 해결 방향: Wanted 회사 페이지 HTML 스크래핑 (`https://www.wanted.co.kr/company/{id}`) 또는 다른 소스
- **투자단계/투자사**: 현재 수집 소스 없음 → 항상 "정보 없음"
  - 해결 방향: TheVC URL 수정 (`/search` → 올바른 엔드포인트), 또는 Rocketpunch
- **사람인 API**: 신청 중, 승인 후 `.env`의 `SARAMIN_API_KEY` 입력 필요
- **Gemini 쿼터**: 무료 티어 일일 한도 초과 시 키워드 폴백 (다음날 자동 복구)

### 🔧 남은 디버그 코드
`wanted_company.py`에 `logger.info` 출력문이 일부 남아있음. 안정화 후 `logger.debug`로 낮추기 권장.

---

## 다음 세션에서 이어서 할 작업

1. **직원수 수집 개선**
   - `https://www.wanted.co.kr/company/{company_id}` HTML 스크래핑 시도
   - 또는 Rocketpunch (`https://www.rocketpunch.com/@{slug}`) 활용

2. **투자정보 수집**
   - TheVC URL 수정: `https://thevc.kr/` 검색 엔드포인트 재확인 (`/search?s=토스` 등)
   - 또는 Naver 금융 (`https://finance.naver.com/`) 스크래핑

3. **사람인 API 키 입력**
   - 승인 후 `.env`에 `SARAMIN_API_KEY=발급된키` 추가

4. **안정화**
   - debug 로그 정리 (`wanted_company.py`)
   - Gemini 쿼터 모니터링 알림 추가

---

## 주요 트러블슈팅 이력

| 문제 | 원인 | 해결 |
|------|------|------|
| `can't subtract offset-naive and offset-aware datetimes` | `datetime.utcnow()` vs ISO aware | `datetime.now(timezone.utc)` 통일 |
| 텔레그램 `WinError 10060` | Windows urllib 타임아웃 | `send()`를 `httpx.AsyncClient`로 교체 |
| 수집모드 버튼 오작동 | 이모지 포함 텍스트 split 버그 | `text.strip() == "🔄 수집모드"` 직접 비교 |
| 네이버 뉴스 빈 결과 | PC 버전은 JS 동적 로딩 | **Google News RSS**로 전환 |
| Gemini 429 quota | 무료 티어 한도 | Circuit breaker + 키워드 폴백 |
| Wanted API `{}` 반환 | `detail["data"]` 대신 `detail["company"]` | 최상위 키 수정 |
| SyntaxError `*(generator)` | Python 버전 이슈 | 리스트 언패킹 분리 |
| Windows cp949 인코딩 오류 | 기본 인코딩 | 모든 파일 I/O에 `encoding="utf-8"` 추가 |
