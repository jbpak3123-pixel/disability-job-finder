# ============================================================
# matcher.py — 지역·직종 매칭 로직
# ============================================================
import re
from datetime import date
from config import REGION_PRIORITY, REGION_DEFAULT, JOB_MATCH, SCORE_TABLE


def get_region_info(location: str) -> dict:
    """위치 문자열에서 지역 우선순위 반환"""
    if not location:
        return REGION_DEFAULT
    for region, info in REGION_PRIORITY.items():
        if region in location:
            return info
    return REGION_DEFAULT


def get_job_match(title: str, description: str = "") -> dict:
    """공고 제목·설명에서 직종 매칭 등급 반환"""
    text = (title + " " + (description or "")).lower()

    for grade, info in JOB_MATCH.items():
        if any(kw in text for kw in info["keywords"]):
            match_type = "best" if grade.startswith("best") else \
                         "good" if grade == "good" else "fair"
            return {
                "match_type":  match_type,
                "match_label": info["label"],
                "job_type":    info["type"],
            }

    return {"match_type": "fair", "match_label": "▲ 검토", "job_type": "service"}


def calc_score(region_rank: int, match_type: str, deadline: date | None) -> int:
    """매칭 점수 계산"""
    score = 0

    # 직종 점수
    score += {"best": SCORE_TABLE["job_best"],
              "good": SCORE_TABLE["job_good"],
              "fair": SCORE_TABLE["job_fair"]}.get(match_type, 0)

    # 지역 점수
    region_key = f"region_{region_rank}"
    score += SCORE_TABLE.get(region_key, 0)

    # D-day 보너스
    if deadline:
        days_left = (deadline - date.today()).days
        if 0 <= days_left <= 7:
            score += SCORE_TABLE["dday_7"]

    return score


def build_reasons(match_type: str, job_type: str,
                  region_name: str, rank: int) -> list[str]:
    """매칭 근거 문장 생성"""
    reasons = []

    job_reasons = {
        "office":  "사무보조 경력 — 직접 경력 부합",
        "welfare": "사회복지사 2급 자격 — 필수 요건 충족",
        "cafe":    "바리스타 자격증 보유 — 우대 요건 충족",
        "design":  "디자인지원 경력 — 직접 경력 부합",
        "service": "민원응대 경력 — 이용자 응대 업무 부합",
    }
    reasons.append(job_reasons.get(job_type, "직무 관련 경력 보유"))

    rank_labels = {1: "1순위 지역 — 통근 최우선",
                   2: "2순위 지역 — 이동 무난",
                   3: "3순위 지역 — 이동 가능"}
    if rank <= 3:
        reasons.append(f"{region_name} {rank_labels[rank]}")

    return reasons


def parse_deadline(text: str) -> date | None:
    """텍스트에서 마감일 파싱 (YYYY-MM-DD, YYYY.MM.DD, YYYY년MM월DD일)"""
    if not text:
        return None
    patterns = [
        r"(\d{4})-(\d{2})-(\d{2})",
        r"(\d{4})\.(\d{2})\.(\d{2})",
        r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            try:
                return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except ValueError:
                continue
    return None
