"""
Notification System
Sends beautifully formatted HTML email grouped by platform.
"""
import smtplib
import json
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from collections import defaultdict
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from config import NOTIFICATIONS

# Platform branding
PLATFORM_META = {
    "LinkedIn":  {"color": "#0077B5", "icon": "in",  "bg": "#E8F4FD"},
    "Indeed":    {"color": "#2164F3", "icon": "In",  "bg": "#EEF2FF"},
    "Glassdoor": {"color": "#0CAA41", "icon": "GD",  "bg": "#EDFAF3"},
    "Dice":      {"color": "#EB1C26", "icon": "DC",  "bg": "#FEF2F2"},
    "Handshake": {"color": "#E8543A", "icon": "HS",  "bg": "#FFF3F0"},
    "JobRight":  {"color": "#7C3AED", "icon": "JR",  "bg": "#F5F3FF"},
}


def build_platform_section(platform: str, jobs: list[dict]) -> str:
    meta = PLATFORM_META.get(platform, {"color": "#475569", "icon": "??", "bg": "#F8FAFC"})
    color = meta["color"]
    bg    = meta["bg"]
    icon  = meta["icon"]

    rows = ""
    for job in jobs:
        score = job.get("match_score", 0)
        if score >= 85:
            score_color = "#16a34a"; score_bg = "#dcfce7"
        elif score >= 70:
            score_color = "#d97706"; score_bg = "#fef3c7"
        else:
            score_color = "#dc2626"; score_bg = "#fee2e2"

        reason = job.get("match_reason", "")
        reason = reason[:90] + "..." if len(reason) > 90 else reason

        rows += f"""
        <tr>
          <td style="padding:12px 16px;border-bottom:1px solid #f1f5f9;vertical-align:top;">
            <a href="{job['url']}" target="_blank"
               style="color:{color};font-weight:600;font-size:14px;text-decoration:none;display:block;margin-bottom:2px;">
              {job['title']}
            </a>
            <span style="color:#64748b;font-size:12px;">
              🏢 {job['company']} &nbsp;·&nbsp; 📍 {job['location'] or 'United States'}
            </span>
          </td>
          <td style="padding:12px 16px;border-bottom:1px solid #f1f5f9;text-align:center;vertical-align:top;white-space:nowrap;">
            <span style="background:{score_bg};color:{score_color};padding:4px 10px;
                         border-radius:20px;font-size:13px;font-weight:700;">
              {score}%
            </span>
          </td>
          <td style="padding:12px 16px;border-bottom:1px solid #f1f5f9;font-size:12px;
                     color:#64748b;vertical-align:top;max-width:240px;">
            {reason}
          </td>
          <td style="padding:12px 16px;border-bottom:1px solid #f1f5f9;text-align:center;vertical-align:top;">
            <a href="{job['url']}" target="_blank"
               style="background:{color};color:white;padding:6px 14px;border-radius:6px;
                      font-size:12px;font-weight:600;text-decoration:none;white-space:nowrap;">
              Apply →
            </a>
          </td>
        </tr>"""

    return f"""
    <div style="margin-bottom:28px;">
      <!-- Platform header -->
      <div style="background:{bg};border-left:4px solid {color};
                  border-radius:8px 8px 0 0;padding:12px 18px;
                  display:flex;align-items:center;">
        <span style="background:{color};color:white;font-size:11px;font-weight:700;
                     padding:4px 8px;border-radius:5px;margin-right:10px;
                     letter-spacing:0.05em;">{icon}</span>
        <span style="font-size:15px;font-weight:700;color:{color};">{platform}</span>
        <span style="margin-left:auto;background:{color};color:white;font-size:11px;
                     font-weight:700;padding:3px 9px;border-radius:12px;">
          {len(jobs)} job{'s' if len(jobs)!=1 else ''}
        </span>
      </div>
      <!-- Jobs table -->
      <table style="width:100%;border-collapse:collapse;background:white;
                    border:1px solid #e2e8f0;border-top:none;border-radius:0 0 8px 8px;
                    overflow:hidden;">
        <thead>
          <tr style="background:#f8fafc;">
            <th style="padding:10px 16px;text-align:left;font-size:11px;
                       color:#94a3b8;font-weight:600;text-transform:uppercase;
                       letter-spacing:0.05em;">Position</th>
            <th style="padding:10px 16px;text-align:center;font-size:11px;
                       color:#94a3b8;font-weight:600;text-transform:uppercase;
                       letter-spacing:0.05em;white-space:nowrap;">Match</th>
            <th style="padding:10px 16px;text-align:left;font-size:11px;
                       color:#94a3b8;font-weight:600;text-transform:uppercase;
                       letter-spacing:0.05em;">Why it fits</th>
            <th style="padding:10px 16px;text-align:center;font-size:11px;
                       color:#94a3b8;font-weight:600;text-transform:uppercase;
                       letter-spacing:0.05em;">Link</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </div>"""


def send_email_alert(jobs: list[dict]):
    if not NOTIFICATIONS["email_enabled"] or not jobs:
        return

    cfg = NOTIFICATIONS
    now = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    # Group jobs by platform
    by_platform = defaultdict(list)
    for job in jobs:
        by_platform[job.get("source", "LinkedIn")].append(job)

    # Sort platforms by job count descending
    sorted_platforms = sorted(by_platform.items(), key=lambda x: len(x[1]), reverse=True)

    # Build platform sections
    sections = ""
    for platform, platform_jobs in sorted_platforms:
        sections += build_platform_section(platform, platform_jobs)

    # Platform summary pills
    pills = ""
    for platform, platform_jobs in sorted_platforms:
        meta = PLATFORM_META.get(platform, {"color": "#475569", "bg": "#F8FAFC"})
        pills += f"""
        <span style="display:inline-block;background:{meta['bg']};color:{meta['color']};
                     border:1px solid {meta['color']}33;padding:4px 12px;
                     border-radius:20px;font-size:12px;font-weight:600;margin:3px;">
          {platform}: {len(platform_jobs)}
        </span>"""

    html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;">
  <div style="max-width:780px;margin:24px auto;padding:0 16px;">

    <!-- Header -->
    <div style="background:linear-gradient(135deg,#0f172a 0%,#1e3a5f 100%);
                border-radius:12px;padding:28px 32px;margin-bottom:20px;">
      <div style="color:#94a3b8;font-size:12px;text-transform:uppercase;
                  letter-spacing:0.1em;margin-bottom:6px;">Job Hunter Alert</div>
      <h1 style="color:white;margin:0 0 6px;font-size:24px;font-weight:700;">
        🎯 {len(jobs)} New Data Engineer Jobs
      </h1>
      <div style="color:#94a3b8;font-size:13px;margin-bottom:16px;">{now}</div>
      <!-- Platform summary -->
      <div>{pills}</div>
    </div>

    <!-- Job sections grouped by platform -->
    {sections}

    <!-- Footer -->
    <div style="text-align:center;padding:16px;color:#94a3b8;font-size:11px;">
      Job Hunter Bot · Running every 60 minutes · Built for Sri Krishna Sai Kota<br>
      <span style="color:#cbd5e1;">Apply while the job is fresh — early applicants get noticed first</span>
    </div>

  </div>
</body>
</html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🎯 {len(jobs)} New Data Engineer Jobs — {', '.join(by_platform.keys())}"
    msg["From"]    = cfg["email_sender"]
    msg["To"]      = cfg["email_recipient"]
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(cfg["email_sender"], cfg["email_password"])
            server.sendmail(cfg["email_sender"], cfg["email_recipient"], msg.as_string())
        summary = ", ".join(f"{p}:{len(j)}" for p, j in sorted_platforms)
        print(f"  ✉️  Email sent: {len(jobs)} jobs [{summary}] to {cfg['email_recipient']}")
    except Exception as e:
        print(f"  ⚠️  Email error: {e}")


def send_telegram_alert(jobs: list[dict]):
    if not NOTIFICATIONS["telegram_enabled"] or not jobs:
        return

    token   = NOTIFICATIONS["telegram_bot_token"]
    chat_id = NOTIFICATIONS["telegram_chat_id"]

    by_platform = defaultdict(list)
    for job in jobs:
        by_platform[job.get("source", "LinkedIn")].append(job)

    text = f"🎯 *{len(jobs)} New Data Engineer Jobs!*\n\n"
    for platform, pjobs in by_platform.items():
        text += f"*{platform}* ({len(pjobs)})\n"
        for job in pjobs[:5]:
            score_emoji = "🟢" if job["match_score"] >= 85 else "🟡" if job["match_score"] >= 70 else "🔴"
            text += (
                f"{score_emoji} [{job['title']}]({job['url']})\n"
                f"   🏢 {job['company']} · {job['match_score']}%\n"
            )
        text += "\n"

    url  = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps({
        "chat_id": chat_id, "text": text[:4000],
        "parse_mode": "Markdown", "disable_web_page_preview": True
    }).encode()

    try:
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
        print(f"  📱 Telegram sent: {len(jobs)} jobs")
    except Exception as e:
        print(f"  ⚠️  Telegram error: {e}")


def send_apply_notification(job: dict, success: bool):
    if not NOTIFICATIONS["telegram_enabled"]:
        return
    status = "✅ Applied" if success else "❌ Failed"
    msg = f"{status}: {job['title']} @ {job['company']}\n{job['url']}"
    token   = NOTIFICATIONS["telegram_bot_token"]
    chat_id = NOTIFICATIONS["telegram_chat_id"]
    url  = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps({"chat_id": chat_id, "text": msg}).encode()
    try:
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
    except Exception:
        pass


def notify_all(jobs: list[dict]):
    if not jobs:
        print("  ℹ️  No new qualifying jobs to notify about.")
        return
    send_email_alert(jobs)
    send_telegram_alert(jobs)