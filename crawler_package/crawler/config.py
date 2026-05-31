# ============================================================
# config.py — 지역 우선순위 · 직무 매칭 상수
# ============================================================

# 지역 우선순위 매핑
REGION_PRIORITY = {
    "강동구": {"rank": 1, "class": "r1"},
    "송파구": {"rank": 2, "class": "r2"},
    "광진구": {"rank": 2, "class": "r2"},
    "성동구": {"rank": 3, "class": "r3"},
    "하남시": {"rank": 3, "class": "r3"},
    "강남구": {"rank": 4, "class": "r4"},
    "구리시": {"rank": 4, "class": "r4"},
}
REGION_DEFAULT = {"rank": 5, "class": "r5"}

# 직종 매칭 키워드
JOB_MATCH = {
    "best": {
        "type": "office",
        "label": "★ 최우선 매칭",
        "keywords": ["사무", "행정", "문서", "데이터입력", "경리", "원무", "민원"],
    },
    "best_welfare": {
        "type": "welfare",
        "label": "★ 최우선 매칭",
        "keywords": ["사회복지", "복지관", "복지보조", "사회서비스"],
    },
    "good": {
        "type": "cafe",
        "label": "◆ 우선 매칭",
        "keywords": ["바리스타", "카페", "커피", "음료"],
    },
    "fair_design": {
        "type": "design",
        "label": "▲ 검토",
        "keywords": ["디자인", "그래픽", "편집"],
    },
    "fair_service": {
        "type": "service",
        "label": "▲ 검토",
        "keywords": ["서비스", "안내", "고객", "이용자지원"],
    },
}

# 매칭 점수 공식
SCORE_TABLE = {
    "job_best":    40,
    "job_good":    25,
    "job_fair":    10,
    "region_1":    20,
    "region_2":    15,
    "region_3":    10,
    "region_4":     5,
    "region_5":     0,
    "dday_7":      10,   # 마감 7일 이내 보너스
}

# 알림 수신자
RECIPIENT_EMAIL = "jbpak3123@hanmail.net"

# 수집 대상 기관 게시판
BOARD_SOURCES = [
    {
        "name": "강동구청",
        "rank": 1,
        "url": "https://www.gangdong.go.kr/web/newportal/bbs/b_040",
        "type": "gangdong",
    },
    {
        "name": "광진구청",
        "rank": 2,
        "url": "https://www.gwangjin.go.kr/portal/bbs/B0000004/list.do?menuNo=200193",
        "type": "gwangjin",
    },
    {
        "name": "송파구청",
        "rank": 2,
        "url": "https://www.songpa.go.kr/job/selectBbsNttList.do?bbsNo=94&key=3416",
        "type": "songpa",
    },
    {
        "name": "하남시청",
        "rank": 3,
        "url": "https://www.hanam.go.kr/www/selectGosiList.do?key=172&not_ancmt_se_code=05",
        "type": "hanam",
    },
    {
        "name": "강동문화재단",
        "rank": 1,
        "url": "https://www.gdfac.or.kr/community/ko/notice",
        "type": "gdfac",
    },
    {
        "name": "성동문화재단",
        "rank": 3,
        "url": "https://www.sdfac.or.kr/kor/recruit/main/main.do",
        "type": "sdfac",
    },
    {
        "name": "KEAD",
        "rank": 1,
        "url": "https://www.kead.or.kr/bbs/jobinfo/bbsPage.do?menuId=MENU2201",
        "type": "kead",
    },
]

# 장애인 관련 필터 키워드
DISABILITY_KEYWORDS = [
    "장애인", "장애우", "우선채용", "특례", "장애인 채용",
    "장애인우선", "장애인 우선", "장애인특례"
]
