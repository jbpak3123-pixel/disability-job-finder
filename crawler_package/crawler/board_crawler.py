# ============================================================
# board_crawler.py — 기관 게시판 크롤러 (Playwright)
# 강동구청, 광진구청, 송파구청, 하남시청, 강동문화재단, 성동문화재단, KEAD
# ============================================================
import re
import time
import hashlib
from datetime import date
from typing import Optional
from playwright.sync_api import sync_playwright, Page, TimeoutError as PWTimeout
from config import BOARD_SOURCES, DISABILITY_KEYWORDS
from matcher import (get_region_info, get_job_match, calc_score,
                     build_reasons, parse_deadline)


# ── 공통 유틸 ────────────────────────────────────────────────
def is_disability_post(title: str, content: str = "") -> bool:
    """장애인 관련 공고인지 판단"""
    text = title + " " + content
    return any(kw in text for kw in DISABILITY_KEYWORDS)


def make_source_id(source: str, url: str) -> str:
    """URL 기반 고유 ID 생성 (중복 방지)"""
    raw = f"{source}::{url}"
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def build_job(
    source: str, rank: int, title: str, post_title: str,
    url: str, board_url: str, company: str, location: str,
    salary: str, deadline: Optional[date], employment: str,
    writing_dept: str, contact: str, description: str,
    tags: list[str], post_direct: bool = True,
) -> dict:
    """공통 job dict 생성"""
    region_info = get_region_info(location)
    match_info  = get_job_match(title, description)
    score       = calc_score(region_info["rank"], match_info["match_type"], deadline)
    reasons     = build_reasons(match_info["match_type"], match_info["job_type"],
                                location or source, region_info["rank"])
    source_id   = make_source_id(source, url)

    tag_classes = []
    for tag in tags:
        if any(kw in tag for kw in ["사무", "행정", "복지"]):
            tag_classes.append("m")
        elif any(kw in tag for kw in ["바리스타", "카페"]):
            tag_classes.append("mg")
        else:
            tag_classes.append("")

    return {
        "source":        source,
        "source_id":     source_id,
        "title":         title,
        "post_title":    post_title or title,
        "company":       company,
        "location":      location,
        "job_type":      match_info["job_type"],
        "salary":        salary,
        "deadline":      deadline.isoformat() if deadline else None,
        "employment":    employment,
        "writing_dept":  writing_dept,
        "contact_dept":  writing_dept,
        "contact":       contact,
        "qualification": "",
        "description":   description[:500] if description else "",
        "url":           url,
        "board_url":     board_url,
        "post_direct":   post_direct,
        "rank":          region_info["rank"],
        "region_name":   source if region_info["rank"] == 5 else location.split()[0] if location else source,
        "region_class":  region_info["class"],
        "match_type":    match_info["match_type"],
        "match_label":   match_info["match_label"],
        "score":         score,
        "reasons":       reasons,
        "tags":          tags,
        "tag_classes":   tag_classes,
        "posted_at":     date.today().isoformat(),
        "notified":      False,
    }


# ── 광진구청 크롤러 ──────────────────────────────────────────
def crawl_gwangjin(page: Page) -> list[dict]:
    board_url = "https://www.gwangjin.go.kr/portal/bbs/B0000004/list.do?menuNo=200193"
    jobs = []
    try:
        page.goto(board_url, timeout=60000)
        page.wait_for_load_state("networkidle", timeout=60000)

        rows = page.query_selector_all("table tbody tr")
        for row in rows[:30]:
            cells = row.query_selector_all("td")
            if len(cells) < 3:
                continue

            title_el = row.query_selector("a")
            if not title_el:
                continue
            title = title_el.inner_text().strip()

            # 장애인 관련 공고 필터
            if not is_disability_post(title):
                continue

            # 게시글 URL
            href = title_el.get_attribute("href") or ""
            if href.startswith("http"):
                post_url = href
            elif href.startswith("/"):
                post_url = "https://www.gwangjin.go.kr" + href
            else:
                post_url = board_url

            # 작성부서 (마지막 셀 또는 두번째 셀)
            dept = cells[-2].inner_text().strip() if len(cells) >= 2 else ""
            # 마감일
            deadline_text = cells[-1].inner_text().strip() if cells else ""
            deadline = parse_deadline(deadline_text)

            job = build_job(
                source="광진구청", rank=2,
                title=title[:60], post_title=title,
                url=post_url, board_url=board_url,
                company="광진구청", location="서울 광진구",
                salary="", deadline=deadline, employment="",
                writing_dept=dept, contact="02-450-7114",
                description="", tags=["행정보조", "공공기관"],
                post_direct=(post_url != board_url),
            )
            jobs.append(job)
    except PWTimeout:
        print(f"[광진구청] 타임아웃 — 건너뜀")
    except Exception as e:
        print(f"[광진구청] 오류: {e}")
    return jobs


# ── 송파구청 크롤러 ──────────────────────────────────────────
def crawl_songpa(page: Page) -> list[dict]:
    board_url = "https://www.songpa.go.kr/job/selectBbsNttList.do?bbsNo=94&key=3416"
    jobs = []
    try:
        page.goto(board_url, timeout=60000)
        page.wait_for_load_state("networkidle", timeout=60000)

        items = page.query_selector_all(".board-list li, table tbody tr")
        for item in items[:30]:
            title_el = item.query_selector("a")
            if not title_el:
                continue
            title = title_el.inner_text().strip()
            if not is_disability_post(title):
                continue

            href = title_el.get_attribute("href") or ""
            if "nttNo=" in href:
                post_url = ("https://www.songpa.go.kr" + href) if href.startswith("/") else href
            else:
                post_url = board_url

            cells = item.query_selector_all("td")
            dept = ""
            deadline_text = ""
            if len(cells) >= 3:
                dept = cells[-2].inner_text().strip()
                deadline_text = cells[-1].inner_text().strip()
            deadline = parse_deadline(deadline_text)

            job = build_job(
                source="송파구청", rank=2,
                title=title[:60], post_title=title,
                url=post_url, board_url=board_url,
                company="송파구청", location="서울 송파구",
                salary="", deadline=deadline, employment="",
                writing_dept=dept or "일자리지원팀",
                contact="02-2147-4913",
                description="", tags=["행정보조", "공공기관"],
                post_direct=(post_url != board_url),
            )
            jobs.append(job)
    except PWTimeout:
        print("[송파구청] 타임아웃 — 건너뜀")
    except Exception as e:
        print(f"[송파구청] 오류: {e}")
    return jobs


# ── 하남시청 크롤러 ──────────────────────────────────────────
def crawl_hanam(page: Page) -> list[dict]:
    board_url = "https://www.hanam.go.kr/www/selectGosiList.do?key=172&not_ancmt_se_code=05"
    jobs = []
    try:
        page.goto(board_url, timeout=60000)
        page.wait_for_load_state("networkidle", timeout=60000)

        rows = page.query_selector_all("table tbody tr")
        for row in rows[:30]:
            title_el = row.query_selector("a")
            if not title_el:
                continue
            title = title_el.inner_text().strip()
            if not is_disability_post(title):
                continue

            href = title_el.get_attribute("href") or ""
            if href.startswith("/"):
                post_url = "https://www.hanam.go.kr" + href
            elif href.startswith("http"):
                post_url = href
            else:
                post_url = board_url

            cells = row.query_selector_all("td")
            dept = cells[-2].inner_text().strip() if len(cells) >= 2 else "총무과"
            deadline_text = cells[-1].inner_text().strip() if cells else ""
            deadline = parse_deadline(deadline_text)

            job = build_job(
                source="하남시청", rank=3,
                title=title[:60], post_title=title,
                url=post_url, board_url=board_url,
                company="하남시청", location="경기 하남시",
                salary="", deadline=deadline, employment="",
                writing_dept=dept, contact="031-790-5114",
                description="", tags=["행정보조", "공공기관"],
                post_direct=(post_url != board_url),
            )
            jobs.append(job)
    except PWTimeout:
        print("[하남시청] 타임아웃 — 건너뜀")
    except Exception as e:
        print(f"[하남시청] 오류: {e}")
    return jobs


# ── 강동구청 크롤러 ──────────────────────────────────────────
def crawl_gangdong(page: Page) -> list[dict]:
    board_url = "https://www.gangdong.go.kr/web/newportal/bbs/b_040"
    jobs = []
    try:
        page.goto(board_url, timeout=60000)
        page.wait_for_load_state("networkidle", timeout=60000)

        rows = page.query_selector_all("table tbody tr, ul.board-list li")
        for row in rows[:30]:
            title_el = row.query_selector("a")
            if not title_el:
                continue
            title = title_el.inner_text().strip()
            if not is_disability_post(title):
                continue

            href = title_el.get_attribute("href") or ""
            if href.startswith("/"):
                post_url = "https://www.gangdong.go.kr" + href
            elif href.startswith("http"):
                post_url = href
            else:
                post_url = board_url

            cells = row.query_selector_all("td")
            dept = cells[-2].inner_text().strip() if len(cells) >= 2 else "인사혁신과"
            deadline_text = cells[-1].inner_text().strip() if cells else ""
            deadline = parse_deadline(deadline_text)

            job = build_job(
                source="강동구청", rank=1,
                title=title[:60], post_title=title,
                url=post_url, board_url=board_url,
                company="강동구청", location="서울 강동구",
                salary="", deadline=deadline, employment="",
                writing_dept=dept, contact="02-3425-5271",
                description="", tags=["사무보조", "공공기관"],
                post_direct=(post_url != board_url),
            )
            jobs.append(job)
    except PWTimeout:
        print("[강동구청] 타임아웃 — 건너뜀")
    except Exception as e:
        print(f"[강동구청] 오류: {e}")
    return jobs


# ── 강동문화재단 크롤러 ──────────────────────────────────────
def crawl_gdfac(page: Page) -> list[dict]:
    board_url = "https://www.gdfac.or.kr/community/ko/notice"
    jobs = []
    try:
        page.goto(board_url, timeout=60000)
        page.wait_for_load_state("networkidle", timeout=60000)

        items = page.query_selector_all("li a, table tbody tr a")
        seen = set()
        for el in items[:50]:
            title = el.inner_text().strip()
            if not title or title in seen:
                continue
            seen.add(title)
            if not is_disability_post(title):
                continue

            href = el.get_attribute("href") or ""
            if href.startswith("/"):
                post_url = "https://www.gdfac.or.kr" + href
            elif href.startswith("http"):
                post_url = href
            else:
                post_url = board_url

            job = build_job(
                source="강동문화재단", rank=1,
                title=title[:60], post_title=title,
                url=post_url, board_url=board_url,
                company="강동문화재단", location="서울 강동구",
                salary="", deadline=None, employment="",
                writing_dept="경영지원팀", contact="02-6252-0600",
                description="", tags=["행정보조", "문화재단"],
                post_direct=(post_url != board_url),
            )
            jobs.append(job)
    except PWTimeout:
        print("[강동문화재단] 타임아웃 — 건너뜀")
    except Exception as e:
        print(f"[강동문화재단] 오류: {e}")
    return jobs


# ── 성동문화재단 크롤러 ──────────────────────────────────────
def crawl_sdfac(page: Page) -> list[dict]:
    board_url = "https://www.sdfac.or.kr/kor/recruit/main/main.do"
    jobs = []
    try:
        page.goto(board_url, timeout=60000)
        page.wait_for_load_state("networkidle", timeout=60000)

        items = page.query_selector_all("a, .recruit-item, .board-item")
        seen = set()
        for el in items[:50]:
            title = el.inner_text().strip()
            if not title or title in seen or len(title) < 5:
                continue
            seen.add(title)
            if not is_disability_post(title):
                continue

            href = el.get_attribute("href") or ""
            if href.startswith("/"):
                post_url = "https://www.sdfac.or.kr" + href
            elif href.startswith("http"):
                post_url = href
            else:
                post_url = board_url

            job = build_job(
                source="성동문화재단", rank=3,
                title=title[:60], post_title=title,
                url=post_url, board_url=board_url,
                company="성동문화재단", location="서울 성동구",
                salary="", deadline=None, employment="",
                writing_dept="경영지원팀", contact="02-2204-4800",
                description="", tags=["행정보조", "문화재단"],
                post_direct=(post_url != board_url),
            )
            jobs.append(job)
    except PWTimeout:
        print("[성동문화재단] 타임아웃 — 건너뜀")
    except Exception as e:
        print(f"[성동문화재단] 오류: {e}")
    return jobs


# ── KEAD 크롤러 ─────────────────────────────────────────────
def crawl_kead(page: Page) -> list[dict]:
    board_url = "https://www.kead.or.kr/bbs/jobinfo/bbsPage.do?menuId=MENU2201"
    jobs = []
    try:
        page.goto(board_url, timeout=25000)
        page.wait_for_load_state("networkidle", timeout=60000)

        rows = page.query_selector_all("table tbody tr")
        for row in rows[:30]:
            title_el = row.query_selector("a")
            if not title_el:
                continue
            title = title_el.inner_text().strip()
            if not title:
                continue

            href = title_el.get_attribute("href") or ""
            if href.startswith("/"):
                post_url = "https://www.kead.or.kr" + href
            elif "javascript" in href:
                # onclick에서 URL 추출 시도
                onclick = title_el.get_attribute("onclick") or ""
                m = re.search(r"'(/[^']+)'", onclick)
                post_url = ("https://www.kead.or.kr" + m.group(1)) if m else board_url
            else:
                post_url = board_url

            cells = row.query_selector_all("td")
            location_text = cells[2].inner_text().strip() if len(cells) > 2 else ""
            deadline_text = cells[-1].inner_text().strip() if cells else ""
            deadline = parse_deadline(deadline_text)

            # KEAD는 장애인 전용 게시판이므로 필터 없이 수집
            job = build_job(
                source="KEAD", rank=1,
                title=title[:60], post_title=title,
                url=post_url, board_url=board_url,
                company=cells[1].inner_text().strip() if len(cells) > 1 else "",
                location=location_text,
                salary="", deadline=deadline, employment="",
                writing_dept="KEAD 채용담당", contact="1588-1519",
                description="", tags=["장애인특례"],
                post_direct=(post_url != board_url),
            )
            jobs.append(job)
    except PWTimeout:
        print("[KEAD] 타임아웃 — 건너뜀")
    except Exception as e:
        print(f"[KEAD] 오류: {e}")
    return jobs


# ── 통합 실행 ────────────────────────────────────────────────
def crawl_all_boards() -> list[dict]:
    """모든 기관 게시판 크롤링 실행"""
    all_jobs = []

    crawlers = [
        ("강동구청",    crawl_gangdong),
        ("광진구청",    crawl_gwangjin),
        ("송파구청",    crawl_songpa),
        ("하남시청",    crawl_hanam),
        ("강동문화재단", crawl_gdfac),
        ("성동문화재단", crawl_sdfac),
        ("KEAD",       crawl_kead),
    ]

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox",
                  "--disable-dev-shm-usage"],
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="ko-KR",
        )
        page = context.new_page()

        for name, fn in crawlers:
            print(f"\n[{name}] 크롤링 시작...")
            try:
                jobs = fn(page)
                print(f"[{name}] 장애인 공고 {len(jobs)}건 수집")
                all_jobs.extend(jobs)
            except Exception as e:
                print(f"[{name}] 실패: {e}")
            time.sleep(2)  # 서버 부하 방지

        context.close()
        browser.close()

    print(f"\n[전체] 총 {len(all_jobs)}건 수집 완료")
    return all_jobs


if __name__ == "__main__":
    jobs = crawl_all_boards()
    for j in jobs:
        print(f"  [{j['source']}] {j['title'][:40]} | {j['deadline']}")
