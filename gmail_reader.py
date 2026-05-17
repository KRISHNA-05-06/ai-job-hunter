"""
Gmail Reader — reads job-related emails and classifies them.
Uses IMAP (Gmail App Password) + keyword matching + Groq AI for ambiguous cases.
Writes results to data/email_updates.json for the Chrome extension to read.
"""
import imaplib
import email
import json
import re
import time
import os
from datetime import datetime, timedelta
from email.header import decode_header
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent))

from config import NOTIFICATIONS, AI
from data.database import save_answer, find_answer

# ── Constants ────────────────────────────────────────────────

OUTPUT_FILE = "data/email_updates.json"

# Keywords for fast classification (no API call needed)
KEYWORDS = {
    "submission": [
        "application received", "application submitted", "thank you for applying",
        "thanks for applying", "we received your application", "successfully applied",
        "your application has been", "application confirmation", "applied to",
        "we got your application", "application for", "has been submitted",
    ],
    "interview": [
        "interview", "phone screen", "video call", "zoom call", "teams call",
        "schedule a call", "speak with you", "next steps", "move forward",
        "shortlisted", "selected for", "recruiter would like", "hiring manager",
        "technical screen", "coding challenge", "assessment", "hackerrank",
        "coderpad", "take-home", "onsite", "virtual interview", "calendly",
    ],
    "rejection": [
        "we regret", "not moving forward", "decided to move forward with other",
        "unfortunately", "not selected", "other candidates", "won't be moving",
        "position has been filled", "not a match", "not the right fit",
        "we have decided", "after careful consideration", "no longer considering",
        "application was not successful", "not shortlisted",
    ],
    "offer": [
        "offer letter", "job offer", "pleased to offer", "offer of employment",
        "we are delighted", "we are excited to offer", "compensation package",
        "start date", "welcome to the team", "offer extended",
    ],
    "followup": [
        "checking in", "following up", "status of my application",
        "any update", "wanted to follow up",
    ],
}

# Job platforms that send confirmation emails
PLATFORM_SENDERS = {
    "linkedin":   "LinkedIn",
    "indeed":     "Indeed",
    "glassdoor":  "Glassdoor",
    "dice":       "Dice",
    "handshake":  "Handshake",
    "jobright":   "JobRight",
}


# ── Gmail IMAP Connection ────────────────────────────────────

def connect_gmail():
    """Connect to Gmail via IMAP using App Password."""
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(NOTIFICATIONS["email_sender"], NOTIFICATIONS["email_password"])
        print("  ✅ Gmail connected")
        return mail
    except Exception as e:
        print(f"  ⚠️  Gmail connection failed: {e}")
        return None


def fetch_recent_emails(mail, days_back: int = 3) -> list[dict]:
    """Fetch emails from the last N days."""
    mail.select("INBOX")
    since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")

    # Search for job-related emails
    _, msg_ids = mail.search(None, f'(SINCE "{since_date}")')
    ids = msg_ids[0].split()

    print(f"  📧 Found {len(ids)} emails in last {days_back} days")

    emails = []
    for msg_id in ids[-50:]:  # cap at 50 most recent
        try:
            _, msg_data = mail.fetch(msg_id, "(RFC822)")
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)

            subject = decode_email_str(msg.get("Subject", ""))
            sender  = msg.get("From", "")
            date    = msg.get("Date", "")
            body    = extract_body(msg)

            emails.append({
                "id":      msg_id.decode(),
                "subject": subject,
                "sender":  sender,
                "date":    date,
                "body":    body[:3000],
            })
        except Exception as e:
            continue

    return emails


def decode_email_str(s: str) -> str:
    """Decode email header string."""
    try:
        parts = decode_header(s)
        decoded = []
        for part, enc in parts:
            if isinstance(part, bytes):
                decoded.append(part.decode(enc or "utf-8", errors="replace"))
            else:
                decoded.append(str(part))
        return " ".join(decoded)
    except Exception:
        return str(s)


def extract_body(msg) -> str:
    """Extract plain text body from email."""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            if ct == "text/plain":
                try:
                    body += part.get_payload(decode=True).decode("utf-8", errors="replace")
                except Exception:
                    pass
            elif ct == "text/html" and not body:
                try:
                    html = part.get_payload(decode=True).decode("utf-8", errors="replace")
                    # Strip HTML tags
                    body += re.sub(r'<[^>]+>', ' ', html)
                except Exception:
                    pass
    else:
        try:
            body = msg.get_payload(decode=True).decode("utf-8", errors="replace")
        except Exception:
            pass
    return " ".join(body.split())[:3000]


# ── Classification ───────────────────────────────────────────

def classify_email_keywords(subject: str, body: str) -> str | None:
    """
    Fast keyword-based classification.
    Returns category or None if ambiguous.
    """
    text = (subject + " " + body).lower()

    # Check each category
    for category, keywords in KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return category

    return None  # ambiguous — needs AI


def classify_email_ai(subject: str, body: str, sender: str) -> str:
    """Use Groq AI for ambiguous emails."""
    try:
        import requests
        prompt = f"""Classify this email related to a job application. 
        
From: {sender}
Subject: {subject}
Body (first 500 chars): {body[:500]}

Respond with ONLY one word from these options:
- submission (application confirmation)
- interview (interview invitation or scheduling)
- rejection (rejected or not moving forward)
- offer (job offer)
- followup (status update or follow-up)
- unrelated (not job related)

One word only:"""

        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {AI['groq_api_key']}",
                "Content-Type": "application/json",
            },
            json={
                "model": AI["model"],
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 10,
                "temperature": 0,
            },
            timeout=15
        )
        result = resp.json()["choices"][0]["message"]["content"].strip().lower()
        # Clean up
        for cat in ["submission","interview","rejection","offer","followup","unrelated"]:
            if cat in result:
                return cat
        return "unrelated"
    except Exception as e:
        print(f"  ⚠️  AI classification failed: {e}")
        return "unrelated"


def extract_company_from_email(subject: str, body: str, sender: str) -> str:
    """Extract company name from email."""
    # From sender domain
    domain_match = re.search(r'@([\w.-]+)', sender)
    if domain_match:
        domain = domain_match.group(1)
        # Skip common email providers
        skip = ['gmail','yahoo','outlook','hotmail','linkedin','indeed','glassdoor',
                'dice','handshake','jobright','notifications','mail','noreply','no-reply']
        parts = domain.replace('.com','').replace('.io','').replace('.co','').split('.')
        for part in parts:
            if part not in skip and len(part) > 2:
                return part.capitalize()

    # From subject line patterns like "Your application at Company"
    patterns = [
        r'at ([\w\s]+?) (?:is|has|was)',
        r'from ([\w\s]+?) (?:team|recruiting|hr)',
        r'([\w\s]+?) (?:hiring|recruiting|talent)',
    ]
    for pat in patterns:
        m = re.search(pat, subject, re.IGNORECASE)
        if m:
            return m.group(1).strip()

    return "Unknown Company"


def extract_job_title(subject: str, body: str) -> str:
    """Extract job title from email."""
    patterns = [
        r'(?:position|role|job|opportunity)[:\s]+([^\n,\.]+)',
        r'(?:applied for|application for)[:\s]+([^\n,\.]+)',
        r'(?:re:|regarding)[:\s]+([^\n,\.]+)',
        r'Data Engineer[^\n,\.]*',
        r'Junior[^\n,\.]*Engineer[^\n,\.]*',
    ]
    text = subject + " " + body[:500]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            result = m.group(1).strip() if m.lastindex else m.group(0).strip()
            if len(result) < 60:
                return result
    return "Data Engineer Role"


def detect_platform(sender: str, body: str) -> str:
    """Detect which platform sent the email."""
    text = (sender + " " + body[:200]).lower()
    for key, name in PLATFORM_SENDERS.items():
        if key in text:
            return name
    return "Direct"


# ── Main Processing ──────────────────────────────────────────

def process_emails() -> dict:
    """
    Main function: connect, fetch, classify, and return structured results.
    Returns dict with submissions, interviews, rejections, offers.
    """
    print("\n📧 Processing Gmail...")

    mail = connect_gmail()
    if not mail:
        return load_existing_data()

    try:
        raw_emails = fetch_recent_emails(mail, days_back=7)
    finally:
        try:
            mail.logout()
        except Exception:
            pass

    # Load existing data to merge with
    existing = load_existing_data()
    existing_ids = {e["email_id"] for e in existing.get("all_updates", [])}

    new_updates = []
    stats = {"submission": 0, "interview": 0, "rejection": 0, "offer": 0, "unrelated": 0}

    for em in raw_emails:
        if em["id"] in existing_ids:
            continue  # already processed

        subject = em["subject"]
        body    = em["body"]
        sender  = em["sender"]

        # Skip clearly unrelated emails fast
        text_lower = (subject + body[:200]).lower()
        job_signals = ["apply", "application", "interview", "position", "job", "role",
                       "recruit", "hiring", "career", "offer", "engineer", "talent"]
        if not any(sig in text_lower for sig in job_signals):
            continue

        # Classify
        category = classify_email_keywords(subject, body)
        if category is None:
            category = classify_email_ai(subject, body, sender)

        if category == "unrelated":
            continue

        stats[category] = stats.get(category, 0) + 1

        company   = extract_company_from_email(subject, body, sender)
        job_title = extract_job_title(subject, body)
        platform  = detect_platform(sender, body)

        update = {
            "email_id":     em["id"],
            "category":     category,
            "company":      company,
            "job_title":    job_title,
            "platform":     platform,
            "subject":      subject,
            "sender":       sender,
            "date":         em["date"],
            "body_preview": body[:300],
            "processed_at": datetime.now().isoformat(),
        }

        new_updates.append(update)
        print(f"  {category_emoji(category)} [{category.upper()}] {company} — {job_title[:40]}")

    # Merge with existing
    all_updates = new_updates + existing.get("all_updates", [])

    # Build categorized views
    result = {
        "last_updated": datetime.now().isoformat(),
        "stats": {
            "total_emails_processed": len(all_updates),
            "new_this_run": len(new_updates),
        },
        "all_updates": all_updates,
        "heard_back": [u for u in all_updates if u["category"] in ["interview","offer","rejection"]],
        "submissions": [u for u in all_updates if u["category"] == "submission"],
        "interviews":  [u for u in all_updates if u["category"] == "interview"],
        "offers":      [u for u in all_updates if u["category"] == "offer"],
        "rejections":  [u for u in all_updates if u["category"] == "rejection"],
    }

    # Save to file
    Path(OUTPUT_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\n  📊 Email summary: {len(new_updates)} new — "
          f"interviews:{stats.get('interview',0)} "
          f"rejections:{stats.get('rejection',0)} "
          f"offers:{stats.get('offer',0)}")

    return result


def load_existing_data() -> dict:
    """Load previously processed email data."""
    try:
        if Path(OUTPUT_FILE).exists():
            with open(OUTPUT_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return {"all_updates": [], "heard_back": [], "submissions": [],
            "interviews": [], "offers": [], "rejections": []}


def category_emoji(cat: str) -> str:
    return {"submission":"📨","interview":"📞","rejection":"❌","offer":"🎉","followup":"💬"}.get(cat,"📧")


if __name__ == "__main__":
    result = process_emails()
    print(f"\n✅ Done. Total tracked: {len(result['all_updates'])} emails")
    print(f"   Heard back from: {len(result['heard_back'])} companies")