"""
Notification System
Sends beautifully formatted HTML email grouped by platform.
Jobs sorted by most recent first, with human-readable posted time.
"""
import smtplib
import json
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone
from collections import defaultdict
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from config import NOTIFICATIONS

# Platform branding
PLATFORM_META = {
    "LinkedIn":  {"color": "#0077B5", "icon": "in", "bg": "#E8F4FD"},
    "Indeed":    {"color": "#2164F3", "icon": "In", "bg": "#EEF2FF"},
    "Glassdoor": {"color": "#0CAA41", "icon": "GD", "bg": "#EDFAF3"},
    "Dice":      {"color": "#EB1C26", "icon": "DC", "bg": "#FEF2F2"},
    "Handshake": {"color": "#E8543A", "icon": "HS", "bg": "#FFF3F0"},
    "JobRight":  {"color": "#7C3AED", "icon": "JR", "bg": "#F5F3FF"},
}


def parse_posted_time(posted_at: str) -> datetime | None:
    """Parse posted_at string into a datetime object."""
    if not posted_at:
        return None
    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(posted_at[:len(fmt)+2].strip("Z"), fmt.strip("Z"))
        except ValueError:
            continue
    return None


def human_time(posted_at: str) -> tuple[str, int]:
    """
    Convert posted_at to a human label like '2 hours ago', '1 day ago'.
    Returns (label, sort_key) where sort_key is minutes ago (lower = more recent).
    """
    dt = parse_posted_time(posted_at)
    if not dt:
        return "Recently posted", 99999

    now = datetime.now()
    # Strip timezone if present
    if dt.tzinfo:
        dt = dt.replace(tzinfo=None)

    diff = now - dt
    minutes = int(diff.total_seconds() / 60)

    if minutes < 0:
        return "Just posted", 0
    elif minutes < 60:
        label = "Just now" if minutes < 2 else f"{minutes}m ago"
        color = "#16a34a"  # green — very fresh
    elif minutes < 1440:  # under 24 hours
        hours = minutes // 60
        label = f"{hours}h ago"
        color = "#16a34a" if hours < 6 else "#d97706"
    elif minutes < 2880:  # under 48 hours
        label = "Yesterday"
        color = "#d97706"  # yellow
    else:
        days = minutes // 1440
        label = f"{days} days ago"
        color = "#dc2626"  # red — older

    return label, minutes


def sort_jobs_by_recency(jobs: list[dict]) -> list[dict]:
    """Sort jobs so most recently posted appear first."""
    def sort_key(job):
        _, minutes = human_time(job.get("posted_at", ""))
        # Secondary sort: match score (higher = better) if same recency
        return (minutes, -job.get("match_score", 0))
    return sorted(jobs, key=sort_key)


def get_recency_badge(posted_at: str) -> str:
    """Return an HTML badge showing how recent the job is."""
    label, minutes = human_time(posted_at)

    if minutes < 60:
        bg = "#dcfce7"; color = "#16a34a"; dot = "🟢"
    elif minutes < 360:  # under 6 hours
        bg = "#dcfce7"; color = "#16a34a"; dot = "🟢"
    elif minutes < 1440:  # under 24 hours
        bg = "#fef3c7"; color = "#d97706"; dot = "🟡"
    elif minutes < 2880:  # under 48 hours
        bg = "#fef3c7"; color = "#d97706"; dot = "🟡"
    else:
        bg = "#fee2e2"; color = "#dc2626"; dot = "🔴"

    return (
        f'<span style="background:{bg};color:{color};padding:2px 8px;'
        f'border-radius:20px;font-size:11px;font-weight:600;white-space:nowrap;">'
        f'{dot} {label}</span>'
    )


def build_platform_section(platform: str, jobs: list[dict]) -> str:
    meta  = PLATFORM_META.get(platform, {"color": "#475569", "icon": "??", "bg": "#F8FAFC"})
    color = meta["color"]
    bg    = meta["bg"]
    icon  = meta["icon"]

    # Sort jobs by recency within each platform
    jobs = sort_jobs_by_recency(jobs)

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
        reason = reason[:85] + "..." if len(reason) > 85 else reason

        recency_badge = get_recency_badge(job.get("posted_at", ""))

        rows += f"""
        <tr>
          <td style="padding:12px 16px;border-bottom:1px solid #f1f5f9;vertical-align:top;">
            <a href="{job['url']}" target="_blank"
               style="color:{color};font-weight:600;font-size:14px;
                      text-decoration:none;display:block;margin-bottom:3px;">
              {job['title']}
            </a>
            <span style="color:#64748b;font-size:12px;">
              🏢 {job['company']} &nbsp;·&nbsp; 📍 {job.get('location') or 'United States'}
            </span><br>
            <span style="margin-top:4px;display:inline-block;">{recency_badge}</span>
          </td>
          <td style="padding:12px 16px;border-bottom:1px solid #f1f5f9;
                     text-align:center;vertical-align:top;white-space:nowrap;">
            <span style="background:{score_bg};color:{score_color};padding:4px 10px;
                         border-radius:20px;font-size:13px;font-weight:700;">
              {score}%
            </span>
          </td>
          <td style="padding:12px 16px;border-bottom:1px solid #f1f5f9;font-size:12px;
                     color:#64748b;vertical-align:top;max-width:220px;">
            {reason}
          </td>
          <td style="padding:12px 16px;border-bottom:1px solid #f1f5f9;
                     text-align:center;vertical-align:top;">
            <a href="{job['url']}" target="_blank"
               style="background:{color};color:white;padding:6px 14px;border-radius:6px;
                      font-size:12px;font-weight:600;text-decoration:none;white-space:nowrap;">
              Apply →
            </a>
          </td>
        </tr>"""

    return f"""
    <div style="margin-bottom:28px;">
      <div style="background:{bg};border-left:4px solid {color};
                  border-radius:8px 8px 0 0;padding:12px 18px;
                  display:flex;align-items:center;">
        <span style="background:{color};color:white;font-size:11px;font-weight:700;
                     padding:4px 8px;border-radius:5px;margin-right:10px;
                     letter-spacing:0.05em;">{icon}</span>
        <span style="font-size:15px;font-weight:700;color:{color};">{platform}</span>
        <span style="margin-left:auto;background:{color};color:white;font-size:11px;
                     font-weight:700;padding:3px 9px;border-radius:12px;">
          {len(jobs)} job{'s' if len(jobs) != 1 else ''}
        </span>
      </div>
      <table style="width:100%;border-collapse:collapse;background:white;
                    border:1px solid #e2e8f0;border-top:none;
                    border-radius:0 0 8px 8px;overflow:hidden;">
        <thead>
          <tr style="background:#f8fafc;">
            <th style="padding:10px 16px;text-align:left;font-size:11px;
                       color:#94a3b8;font-weight:600;text-transform:uppercase;
                       letter-spacing:0.05em;">Position · When Posted</th>
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

    # Sort ALL jobs by recency first (for the overall summary)
    all_sorted = sort_jobs_by_recency(jobs)

    # Group by platform (preserving recency order within each)
    by_platform = defaultdict(list)
    for job in all_sorted:
        by_platform[job.get("source", "LinkedIn")].append(job)

    # Sort platforms by most recent job posted
    def platform_freshness(item):
        platform_jobs = item[1]
        _, minutes = human_time(platform_jobs[0].get("posted_at", ""))
        return minutes

    sorted_platforms = sorted(by_platform.items(), key=platform_freshness)

    # Build sections
    sections = "".join(
        build_platform_section(platform, platform_jobs)
        for platform, platform_jobs in sorted_platforms
    )

    # Platform pills
    pills = ""
    for platform, platform_jobs in sorted_platforms:
        meta = PLATFORM_META.get(platform, {"color": "#475569", "bg": "#F8FAFC"})
        pills += f"""
        <span style="display:inline-block;background:{meta['bg']};color:{meta['color']};
                     border:1px solid {meta['color']}33;padding:4px 12px;
                     border-radius:20px;font-size:12px;font-weight:600;margin:3px;">
          {platform}: {len(platform_jobs)}
        </span>"""

    # Freshness legend
    legend = """
    <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;
                padding:10px 16px;margin-bottom:20px;font-size:12px;color:#64748b;">
      <strong style="color:#475569;">Posted time legend:</strong> &nbsp;
      <span style="color:#16a34a;">🟢 Under 6 hours</span> &nbsp;·&nbsp;
      <span style="color:#d97706;">🟡 6–48 hours</span> &nbsp;·&nbsp;
      <span style="color:#dc2626;">🔴 Older than 2 days</span>
      &nbsp;·&nbsp; Jobs sorted newest first within each platform.
    </div>"""

    html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f1f5f9;
             font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;">
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
      <div>{pills}</div>
    </div>

    {legend}

    {sections}

    <!-- Footer -->
    <div style="text-align:center;padding:16px;color:#94a3b8;font-size:11px;">
      Job Hunter Bot · Sorted by most recent first · Built for Sri Krishna Sai Kota<br>
      <span style="color:#cbd5e1;">Apply while the job is fresh — early applicants get noticed first</span>
    </div>

  </div>
</body>
</html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🎯 {len(jobs)} New Data Engineer Jobs — {', '.join(p for p, _ in sorted_platforms)}"
    msg["From"]    = cfg["email_sender"]
    msg["To"]      = cfg["email_recipient"]
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(cfg["email_sender"], cfg["email_password"])
            server.sendmail(cfg["email_sender"], cfg["email_recipient"], msg.as_string())
        summary = ", ".join(f"{p}:{len(j)}" for p, j in sorted_platforms)
        print(f"  ✉️  Email sent: {len(jobs)} jobs [{summary}] → {cfg['email_recipient']}")
    except Exception as e:
        print(f"  ⚠️  Email error: {e}")


def send_telegram_alert(jobs: list[dict]):
    if not NOTIFICATIONS["telegram_enabled"] or not jobs:
        return

    token   = NOTIFICATIONS["telegram_bot_token"]
    chat_id = NOTIFICATIONS["telegram_chat_id"]

    by_platform = defaultdict(list)
    for job in sort_jobs_by_recency(jobs):
        by_platform[job.get("source", "LinkedIn")].append(job)

    text = f"🎯 *{len(jobs)} New Data Engineer Jobs!*\n\n"
    for platform, pjobs in by_platform.items():
        text += f"*{platform}* ({len(pjobs)})\n"
        for job in pjobs[:4]:
            label, _ = human_time(job.get("posted_at", ""))
            score_emoji = "🟢" if job["match_score"] >= 85 else "🟡" if job["match_score"] >= 70 else "🔴"
            text += (
                f"{score_emoji} [{job['title']}]({job['url']})\n"
                f"   🏢 {job['company']} · {job['match_score']}% · ⏰ {label}\n"
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


def notify_all(jobs: list[dict]):
    if not jobs:
        print("  ℹ️  No new qualifying jobs to notify about.")
        return
    send_email_alert(jobs)
    send_telegram_alert(jobs)