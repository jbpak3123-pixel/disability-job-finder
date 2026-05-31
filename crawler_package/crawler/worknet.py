# ============================================================
# worknet.py — 워크넷(고용24) Open API 크롤러
# API 키 승인 후 WORKNET_API_KEY 환경변수 설정 시 활성화
# ============================================================
import os
import requests
from datetime import date
from config import DISABILITY_KEYWORDS
from matcher import (get_region_info, get_job_match, calc_score,
                     build_reasons, parse_deadline)

WORKNET_API_BASE = "https://www.work24.go.kr/wk/a/b/1200/selectEmpSrchList.do"

# 서울·경기 지역 코드 (워크넷 API 파라미터)
TARGET_AREA_CODES = [
    "11",   # 서울 전체
    "41",   # 경기 전체
]


def fetch_worknet_jobs(api_key: str) -> list[dict]:
    """워크넷 Open API로 장애인 채용공고 수집"""
    all_jobs = []

    for area_code in TARGET_AREA_CODES:
        params = {
            "authKey":      api_key,
            "returnType":   "JSON",
            "startPage":    1,
            "display":      100,
            "sr":           "OR",          # 검색 방식
            "disabledYn":   "Y",           # 장애인 구직 가능
            "areaCd":       area_code,
        }

        try:
            resp = requests.get(WORKNET_API_BASE, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            items = (data.get("wantedInfo") or
                     data.get("data") or
                     data.get("jobs") or [])

            for item in items:
                job = _parse_worknet_item(item)
                if job:
                    all_jobs.append(job)

            print(f"[워크넷] 지역코드 {area_code}: {len(items)}건")

        except requests.RequestException as e:
            print(f"[워크넷] API 오류 (지역 {area_code}): {e}")
        except Exception as e:
            print(f"[워크넷] 파싱 오류: {e}")

    return all_jobs


def _parse_worknet_item(item: dict) -> dict | None:
    """워크넷 API 응답 항목 → job dict 변환"""
    title = (item.get("wantedTitle") or
             item.get("title") or "").strip()
    if not title:
        return None

    company  = item.get("company") or item.get("companyName") or ""
    location = item.get("workArea") or item.get("jobLocation") or ""
    salary   = item.get("salaryCondition") or item.get("salary") or ""
    emp_type = item.get("empType") or item.get("employmentType") or ""
    wno      = (item.get("wantedAuthNo") or
                item.get("jobId") or
                item.get("id") or "")

    # 게시글 직접 URL
    if wno:
        post_url  = (f"https://www.work24.go.kr/wk/a/b/1500/"
                     f"empDetailAuthView.do?wantedAuthNo={wno}"
                     f"&infoTypeCd=WORKNET")
        post_direct = True
    else:
        post_url    = "https://www.work24.go.kr/wk/a/b/1200/retriveDtlEmpSrchList.do"
        post_direct = False

    board_url = "https://www.work24.go.kr/wk/a/b/1200/retriveDtlEmpSrchList.do"

    deadline_text = item.get("deadlineDate") or item.get("deadline") or ""
    deadline      = parse_deadline(deadline_text)

    region_info = get_region_info(location)
    match_info  = get_job_match(title)
    score       = calc_score(region_info["rank"], match_info["match_type"], deadline)
    reasons     = build_reasons(match_info["match_type"], match_info["job_type"],
                                location.split()[0] if location else "서울", region_info["rank"])

    return {
        "source":       "워크넷",
        "source_id":    f"worknet_{wno}" if wno else None,
        "title":        title[:60],
        "post_title":   title,
        "company":      company,
        "location":     location,
        "job_type":     match_info["job_type"],
        "salary":       salary,
        "deadline":     deadline.isoformat() if deadline else None,
        "employment":   emp_type,
        "writing_dept": "워크넷 등록",
        "contact_dept": "워크넷 등록",
        "contact":      "1350",
        "qualification":"",
        "description":  "",
        "url":          post_url,
        "board_url":    board_url,
        "post_direct":  post_direct,
        "rank":         region_info["rank"],
        "region_name":  location.split()[0] if location else "서울",
        "region_class": region_info["class"],
        "match_type":   match_info["match_type"],
        "match_label":  match_info["match_label"],
        "score":        score,
        "reasons":      reasons,
        "tags":         [match_info["job_type"]],
        "tag_classes":  ["m" if match_info["match_type"] == "best" else ""],
        "posted_at":    date.today().isoformat(),
        "notified":     False,
    }


def run(api_key: str | None = None) -> list[dict]:
    """워크넷 크롤러 진입점"""
    key = api_key or os.getenv("WORKNET_API_KEY")
    if not key:
        print("[워크넷] API 키 없음 — 승인 후 WORKNET_API_KEY 환경변수 설정 필요")
        return []
    print(f"[워크넷] API 키 확인 — 수집 시작")
    return fetch_worknet_jobs(key)


if __name__ == "__main__":
    jobs = run()
    for j in jobs:
        print(f"  {j['title'][:40]} | {j['location']} | {j['deadline']}")
