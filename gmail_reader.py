"""
Gmail Reader — reads job-related emails and classifies them.
Strict classification — only real company responses, no marketing emails.
"""
import imaplib
import email
import json
import re
from datetime import datetime, timedelta
from email.header import decode_header
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent))
from config import NOTIFICATIONS, AI

OUTPUT_FILE = "data/email_updates.json"

# ── Senders to ALWAYS ignore (marketing, newsletters, job boards) ────────────
IGNORED_SENDERS = [
    # Job boards — they send job alerts not interview invites
    "linkedin", "indeed", "glassdoor", "dice", "handshake", "jobright",
    "ziprecruiter", "monster", "careerbuilder", "simplyhired",
    "jobs-noreply", "jobalerts", "job-alerts",
    # Marketing / coaching services
    "remotehunter", "remote.co", "jobscan", "resumeworded",
    "careers@", "noreply@", "no-reply@", "donotreply",
    "newsletter", "marketing", "notifications@",
    "alerts@", "updates@", "info@",
    # Email platforms
    "myworkday", "workday", "greenhouse", "lever", "taleo",
    "successfactors", "icims", "jobvite", "smartrecruiters",
]

# ── Subjects that are DEFINITELY not real responses ──────────────────────────
IGNORED_SUBJECT_PATTERNS = [
    # Job alerts from boards
    r"new jobs? (for you|matching|alert)",
    r"\d+ new jobs?",
    r"jobs? you might like",
    r"recommended jobs?",
    r"job alert",
    r"jobs? matching your",
    # Marketing
    r"welcome to",
    r"get started",
    r"your (free|trial|account)",
    r"tips? (for|to)",
    r"how to (get|find|land)",
    r"we.ve been guiding",
    r"success factors",
    r"let.s get you hired",
    r"your (remote|job) search",
    # Newsletter patterns
    r"unsubscribe",
    r"view in browser",
    r"weekly digest",
    r"monthly roundup",
]

# ── STRICT interview keywords — must be PERSONAL and DIRECT ─────────────────
# These phrases indicate a REAL human reached out to YOU specifically
INTERVIEW_PHRASES = [
    "would like to invite you to interview",
    "would like to schedule an interview",
    "we'd like to invite you",
    "we would like to invite you",
    "you have been selected for an interview",
    "you've been selected for",
    "pleased to invite you",
    "advance you to the next round",
    "move you to the next stage",
    "schedule a phone screen with you",
    "schedule a call with you",
    "i'd like to connect with you about",
    "i would like to speak with you",
    "recruiter would like to speak",
    "please schedule your interview",
    "book your interview",
    "interview invitation",
    "invite you to a",
    "calendly.com",  # direct scheduling link = real interview
    "zoom.us/j/",   # direct zoom link = real interview
    "teams.microsoft.com/l/meetup",  # teams meeting = real interview
]

# ── STRICT rejection keywords ────────────────────────────────────────────────
REJECTION_PHRASES = [
    "we will not be moving forward with your application",
    "we will not be moving forward with you",
    "we have decided not to move forward",
    "decided to move forward with other candidates",
    "we regret to inform you",
    "after careful consideration, we have decided",
    "we are unable to offer you",
    "your application has been unsuccessful",
    "we will not be proceeding",
    "we won't be moving forward",
    "not selected for this position",
    "position has been filled",
    "we have moved forward with another candidate",
    "we appreciate your interest but",
    "unfortunately, we will not",
    "unfortunately we won't",
]

# ── STRICT offer keywords ────────────────────────────────────────────────────
OFFER_PHRASES = [
    "pleased to offer you",
    "we are pleased to extend an offer",
    "offer of employment",
    "formal offer",
    "offer letter",
    "we'd like to offer you the position",
    "we would like to offer you",
    "congratulations on your offer",
    "your compensation package",
    "your start date",
    "welcome to the team",
    "offer package",
]

# ── Submission keywords ──────────────────────────────────────────────────────
SUBMISSION_PHRASES = [
    "application received",
    "application submitted",
    "thank you for applying",
    "thanks for applying",
    "we received your application",
    "successfully applied",
    "your application has been submitted",
    "application confirmation",
    "we have received your application",
]

# ── Platform senders (for submission tracking) ───────────────────────────────
PLATFORM_SENDERS = {
    "linkedin": "LinkedIn", "indeed": "Indeed", "glassdoor": "Glassdoor",
    "dice": "Dice", "handshake": "Handshake", "jobright": "JobRight",
}


# ── Gmail Connection ─────────────────────────────────────────────────────────

def connect_gmail():
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(NOTIFICATIONS["email_sender"], NOTIFICATIONS["email_password"])
        print("  ✅ Gmail connected")
        return mail
    except Exception as e:
        print(f"  ⚠️  Gmail connection failed: {e}")
        return None


def fetch_recent_emails(mail, days_back: int = 7) -> list[dict]:
    mail.select("INBOX")
    since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
    _, msg_ids = mail.search(None, f'(SINCE "{since_date}")')
    ids = msg_ids[0].split()
    print(f"  📧 Found {len(ids)} emails in last {days_back} days")

    emails = []
    for msg_id in ids[-100:]:
        try:
            _, msg_data = mail.fetch(msg_id, "(RFC822)")
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)
            subject = decode_email_str(msg.get("Subject", ""))
            sender  = msg.get("From", "")
            date    = msg.get("Date", "")
            body    = extract_body(msg)
            emails.append({
                "id": msg_id.decode(), "subject": subject,
                "sender": sender, "date": date, "body": body[:3000],
            })
        except Exception:
            continue
    return emails


def decode_email_str(s: str) -> str:
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
                    body += re.sub(r'<[^>]+>', ' ', html)
                except Exception:
                    pass
    else:
        try:
            body = msg.get_payload(decode=True).decode("utf-8", errors="replace")
        except Exception:
            pass
    return " ".join(body.split())[:3000]


# ── Filtering ────────────────────────────────────────────────────────────────

def should_ignore_sender(sender: str) -> bool:
    """Return True if this sender should be completely ignored."""
    sender_lower = sender.lower()
    return any(ig in sender_lower for ig in IGNORED_SENDERS)


def should_ignore_subject(subject: str) -> bool:
    """Return True if this subject matches a marketing/alert pattern."""
    subject_lower = subject.lower()
    return any(re.search(pat, subject_lower) for pat in IGNORED_SUBJECT_PATTERNS)


def is_personal_email(sender: str, body: str) -> bool:
    """
    Check if this looks like a personal email from a real person/company
    vs a bulk automated marketing email.
    """
    # Marketing emails usually have unsubscribe links
    body_lower = body.lower()
    if any(w in body_lower for w in ["unsubscribe", "opt-out", "opt out", "manage preferences", "email preferences"]):
        # Could still be a real ATS email — check for strong interview signals
        if not any(p in body_lower for p in INTERVIEW_PHRASES + OFFER_PHRASES):
            return False

    return True


# ── Classification ────────────────────────────────────────────────────────────

def classify_email_strict(subject: str, body: str, sender: str) -> str | None:
    """
    Strict classification — only return a category if we're very confident.
    Returns None for anything ambiguous → goes to AI.
    """
    text = (subject + " " + body).lower()

    # Check for real interview invitations
    if any(phrase in text for phrase in INTERVIEW_PHRASES):
        return "interview"

    # Check for rejections
    if any(phrase in text for phrase in REJECTION_PHRASES):
        return "rejection"

    # Check for offers
    if any(phrase in text for phrase in OFFER_PHRASES):
        return "offer"

    # Check for submissions (from job boards only)
    if any(phrase in text for phrase in SUBMISSION_PHRASES):
        return "submission"

    return None  # ambiguous


def classify_email_ai(subject: str, body: str, sender: str) -> str:
    """Use Groq AI for ambiguous emails with strict instructions."""
    try:
        import requests
        prompt = f"""You are classifying a job application email. Be VERY strict — only classify as interview/offer/rejection if you are 100% certain it is a DIRECT, PERSONAL response from a hiring company about a specific job application.

From: {sender}
Subject: {subject}
Body (first 600 chars): {body[:600]}

Rules:
- "interview" ONLY if a company directly invites you to interview for a specific role
- "offer" ONLY if a company sends you an actual job offer letter
- "rejection" ONLY if a company explicitly says they will not proceed with your application
- "submission" ONLY if confirming your application was received
- "unrelated" for: job alerts, newsletters, marketing emails, welcome emails, tips/advice, service sign-ups, anything not a direct personal response about YOUR specific application

When in doubt, choose "unrelated".

Respond with ONE word only: interview / offer / rejection / submission / unrelated"""

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
        for cat in ["interview", "offer", "rejection", "submission", "unrelated"]:
            if cat in result:
                return cat
        return "unrelated"
    except Exception as e:
        print(f"  ⚠️  AI classification failed: {e}")
        return "unrelated"


def extract_company_from_email(subject: str, body: str, sender: str) -> str:
    """Extract company name — skip generic senders."""
    # Try sender domain first
    domain_match = re.search(r'@([\w.-]+)', sender)
    if domain_match:
        domain = domain_match.group(1)
        skip = ['gmail','yahoo','outlook','hotmail','linkedin','indeed','glassdoor',
                'dice','handshake','jobright','notifications','mail','noreply',
                'no-reply','workday','greenhouse','lever','icims','remotehunter']
        parts = domain.replace('.com','').replace('.io','').replace('.co','').split('.')
        for part in parts:
            if part not in skip and len(part) > 2:
                return part.capitalize()

    # From subject patterns
    patterns = [
        r'(?:from|at|with) ([\w\s]+?) (?:team|recruiting|hr|talent)',
        r'([\w\s]+?) (?:is moving forward|would like to)',
        r'your (?:application|interview) (?:with|at) ([\w\s]+)',
    ]
    text = subject + " " + body[:300]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            result = m.group(1).strip()
            if 3 < len(result) < 40:
                return result

    return "Unknown Company"


def extract_job_title(subject: str, body: str) -> str:
    """Extract job title."""
    patterns = [
        r'(?:position|role|job|opportunity)[:\s]+([^\n,\.]{5,50})',
        r'(?:applied for|application for)[:\s]+([^\n,\.]{5,50})',
        r'Data Engineer[^\n,\.]{0,30}',
        r'Junior[^\n,\.]{0,20}Engineer[^\n,\.]{0,20}',
        r'ETL[^\n,\.]{0,20}',
    ]
    text = subject + " " + body[:500]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            result = (m.group(1) if m.lastindex else m.group(0)).strip()
            if len(result) < 80:
                return result
    return "Data Engineer Role"


def detect_platform(sender: str, body: str) -> str:
    text = (sender + " " + body[:200]).lower()
    for key, name in PLATFORM_SENDERS.items():
        if key in text:
            return name
    return "Direct"


# ── Main ─────────────────────────────────────────────────────────────────────

def process_emails() -> dict:
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

    existing     = load_existing_data()
    existing_ids = {e["email_id"] for e in existing.get("all_updates", [])}
    new_updates  = []
    stats        = {"submission": 0, "interview": 0, "rejection": 0, "offer": 0, "skipped": 0}

    for em in raw_emails:
        if em["id"] in existing_ids:
            continue

        subject = em["subject"]
        body    = em["body"]
        sender  = em["sender"]

        # ── Gate 1: Skip ignored senders immediately ──
        if should_ignore_sender(sender):
            stats["skipped"] += 1
            continue

        # ── Gate 2: Skip marketing subject patterns ───
        if should_ignore_subject(subject):
            stats["skipped"] += 1
            continue

        # ── Gate 3: Skip bulk marketing emails ───────
        if not is_personal_email(sender, body):
            stats["skipped"] += 1
            continue

        # ── Gate 4: Must have some job-related signal ─
        text_lower = (subject + body[:300]).lower()
        job_signals = ["application", "position", "role", "engineer",
                       "interview", "offer", "recruiter", "hiring"]
        if not any(sig in text_lower for sig in job_signals):
            stats["skipped"] += 1
            continue

        # ── Classify ──────────────────────────────────
        category = classify_email_strict(subject, body, sender)
        if category is None:
            category = classify_email_ai(subject, body, sender)

        if category == "unrelated":
            stats["skipped"] += 1
            continue

        stats[category] = stats.get(category, 0) + 1
        company  = extract_company_from_email(subject, body, sender)
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
        print(f"  {cat_emoji(category)} [{category.upper()}] {company} — {job_title[:40]}")

    # Merge with existing (keep existing, add new)
    all_updates = new_updates + existing.get("all_updates", [])

    result = {
        "last_updated": datetime.now().isoformat(),
        "stats": {"total": len(all_updates), "new_this_run": len(new_updates)},
        "all_updates": all_updates,
        "heard_back":  [u for u in all_updates if u["category"] in ["interview","offer","rejection"]],
        "submissions": [u for u in all_updates if u["category"] == "submission"],
        "interviews":  [u for u in all_updates if u["category"] == "interview"],
        "offers":      [u for u in all_updates if u["category"] == "offer"],
        "rejections":  [u for u in all_updates if u["category"] == "rejection"],
    }

    Path(OUTPUT_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\n  📊 Email results: {len(new_updates)} classified, {stats['skipped']} skipped")
    print(f"     interviews:{stats.get('interview',0)} "
          f"rejections:{stats.get('rejection',0)} "
          f"offers:{stats.get('offer',0)} "
          f"submissions:{stats.get('submission',0)}")
    return result


def load_existing_data() -> dict:
    try:
        if Path(OUTPUT_FILE).exists():
            with open(OUTPUT_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return {"all_updates": [], "heard_back": [], "submissions": [],
            "interviews": [], "offers": [], "rejections": []}


def cat_emoji(cat: str) -> str:
    return {"submission":"📨","interview":"📞","rejection":"❌","offer":"🎉"}.get(cat,"📧")


if __name__ == "__main__":
    result = process_emails()
    print(f"\n✅ Done. Heard back from: {len(result['heard_back'])} companies")