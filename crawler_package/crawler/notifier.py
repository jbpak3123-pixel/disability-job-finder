# ============================================================
# notifier.py — SendGrid 이메일 알림 발송
# ============================================================
import os
from datetime import date
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, To
from config import RECIPIENT_EMAIL


def _dday_label(deadline_str: str | None) -> str:
    if not deadline_str:
        return "마감일 미정"
    try:
        dl = date.fromisoformat(deadline_str)
        d  = (dl - date.today()).days
        if d < 0:
            return "마감"
        return f"D-{d}"
    except Exception:
        return deadline_str


def build_email_html(new_jobs: list[dict]) -> str:
    """신규 공고 이메일 HTML 생성"""
    rows = ""
    for j in new_jobs:
        dday  = _dday_label(j.get("deadline"))
        color = "#D94F3D" if "D-" in dday and int(dday[2:] or 99) <= 3 else \
                "#F4A135" if "D-" in dday and int(dday[2:] or 99) <= 7 else "#2E8B57"
        rows += f"""
        <tr>
          <td style="padding:14px 16px;border-bottom:1px solid #E2E0D8;">
            <div style="font-size:13px;color:#9A9A94;margin-bottom:4px;">
              [{j.get('source','')}] {j.get('region_name','')} ·
              <span style="color:{color};font-weight:700">{dday}</span>
            </div>
            <div style="font-size:16px;font-weight:700;color:#1C1C1A;margin-bottom:4px;">
              {j.get('title','')}
            </div>
            <div style="font-size:14px;color:#5A5A56;margin-bottom:6px;">
              {j.get('company','')} | {j.get('location','')}
            </div>
            <div style="font-size:13px;color:#1A7F6E;margin-bottom:8px;">
              {j.get('salary','')} | 마감: {j.get('deadline','미정')}
            </div>
            <div style="font-size:12px;color:#5A5A56;margin-bottom:10px;">
              📌 {j['reasons'][0] if j.get('reasons') else ''}
            </div>
            <a href="{j.get('url','')}"
               style="display:inline-block;background:#1A7F6E;color:#fff;
                      padding:8px 18px;border-radius:6px;font-size:13px;
                      text-decoration:none;font-weight:700;">
              {'📄 공고 바로보기 ↗' if j.get('post_direct') else '📋 채용 게시판 ↗'}
            </a>
          </td>
        </tr>"""

    return f"""
<!DOCTYPE html>
<html lang="ko">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#FAFAF8;font-family:'Apple SD Gothic Neo',sans-serif;">
  <div style="max-width:600px;margin:0 auto;padding:20px 0;">
    <div style="background:#1A7F6E;padding:24px;border-radius:12px 12px 0 0;">
      <div style="font-size:22px;font-weight:700;color:#fff;">🤝 일자리 알리미</div>
      <div style="font-size:14px;color:rgba(255,255,255,.8);margin-top:4px;">
        신규 장애인 특례 채용공고 {len(new_jobs)}건이 등록되었습니다
      </div>
    </div>
    <table style="width:100%;background:#fff;border-collapse:collapse;">
      {rows}
    </table>
    <div style="background:#fff;padding:16px;border-top:1px solid #E2E0D8;
                border-radius:0 0 12px 12px;text-align:center;">
      <div style="font-size:12px;color:#9A9A94;">
        수신 해지: 이 이메일에 회신하거나 담당자에게 문의하세요<br>
        데이터 출처: 워크넷, KEAD, 강동·광진·송파·하남 구청, 강동·성동 문화재단
      </div>
    </div>
  </div>
</body>
</html>"""


def send_notification(new_jobs: list[dict]) -> bool:
    """신규 공고 이메일 발송"""
    api_key = os.getenv("SENDGRID_API_KEY")
    sender  = os.getenv("SENDER_EMAIL", "noreply@disability-job-finder.com")

    if not api_key:
        print("[알림] SendGrid API 키 없음 — 이메일 발송 건너뜀")
        return False
    if not new_jobs:
        print("[알림] 신규 공고 없음 — 발송 건너뜀")
        return False

    subject = f"[일자리 알리미] 신규 장애인 채용공고 {len(new_jobs)}건"
    html    = build_email_html(new_jobs)

    message = Mail(
        from_email=sender,
        to_emails=RECIPIENT_EMAIL,
        subject=subject,
        html_content=html,
    )

    try:
        sg = SendGridAPIClient(api_key)
        resp = sg.send(message)
        print(f"[알림] 이메일 발송 완료 → {RECIPIENT_EMAIL} (상태: {resp.status_code})")
        return True
    except Exception as e:
        print(f"[알림] 이메일 발송 실패: {e}")
        return False
