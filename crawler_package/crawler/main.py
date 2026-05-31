# ============================================================
# main.py — 크롤러 메인 진입점
# 실행: python main.py
# 자동: GitHub Actions (매일 10:00, 16:00 KST)
# ============================================================
import os
import sys
from datetime import date
from supabase import create_client, Client
from board_crawler import crawl_all_boards
from worknet import run as crawl_worknet
from notifier import send_notification


def get_supabase() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        print("[DB] SUPABASE_URL 또는 SUPABASE_KEY 환경변수 없음")
        sys.exit(1)
    return create_client(url, key)


def filter_new_jobs(client: Client, jobs: list[dict]) -> list[dict]:
    """DB에 없는 신규 공고만 반환 (source_id 기준)"""
    if not jobs:
        return []

    # 기존 source_id 목록 조회
    source_ids = [j["source_id"] for j in jobs if j.get("source_id")]
    if not source_ids:
        return jobs

    resp = (client.table("jobs")
                  .select("source_id")
                  .in_("source_id", source_ids)
                  .execute())
    existing = {row["source_id"] for row in (resp.data or [])}

    new_jobs = [j for j in jobs if j.get("source_id") and j["source_id"] not in existing]
    print(f"[DB] 전체 수집 {len(jobs)}건 → 신규 {len(new_jobs)}건 (중복 {len(jobs)-len(new_jobs)}건 제외)")
    return new_jobs


def save_jobs(client: Client, jobs: list[dict]) -> int:
    """신규 공고 Supabase에 저장"""
    if not jobs:
        return 0

    # 마감 지난 공고 제외
    today = date.today()
    valid = []
    for j in jobs:
        if j.get("deadline"):
            try:
                dl = date.fromisoformat(j["deadline"])
                if dl < today:
                    continue
            except Exception:
                pass
        valid.append(j)

    if not valid:
        print("[DB] 저장할 유효 공고 없음")
        return 0

    try:
        resp = client.table("jobs").insert(valid).execute()
        count = len(resp.data or [])
        print(f"[DB] {count}건 저장 완료")
        return count
    except Exception as e:
        print(f"[DB] 저장 오류: {e}")
        return 0


def mark_notified(client: Client, source_ids: list[str]):
    """이메일 발송 완료 표시"""
    if not source_ids:
        return
    try:
        client.table("jobs") \
              .update({"notified": True}) \
              .in_("source_id", source_ids) \
              .execute()
    except Exception as e:
        print(f"[DB] notified 업데이트 오류: {e}")


def main():
    print("=" * 50)
    print(f"장애인 특례 채용공고 수집 시작: {date.today()}")
    print("=" * 50)

    # 1) Supabase 연결
    client = get_supabase()
    print("[DB] Supabase 연결 성공")

    # 2) 기관 게시판 크롤링
    print("\n[크롤링] 기관 게시판 수집 시작...")
    board_jobs = crawl_all_boards()

    # 3) 워크넷 API (키 있을 때만)
    print("\n[크롤링] 워크넷 API 수집 시작...")
    worknet_jobs = crawl_worknet()

    all_jobs = board_jobs + worknet_jobs
    print(f"\n[수집 완료] 총 {len(all_jobs)}건")

    # 4) 신규 공고 필터링
    new_jobs = filter_new_jobs(client, all_jobs)

    # 5) DB 저장
    saved = save_jobs(client, new_jobs)

    # 6) 이메일 알림 발송
    if saved > 0:
        print(f"\n[알림] 신규 {saved}건 이메일 발송...")
        sent = send_notification(new_jobs[:saved])
        if sent:
            source_ids = [j["source_id"] for j in new_jobs[:saved] if j.get("source_id")]
            mark_notified(client, source_ids)
    else:
        print("\n[알림] 신규 공고 없음 — 이메일 발송 생략")

    print(f"\n완료. 저장: {saved}건\n")


if __name__ == "__main__":
    main()
