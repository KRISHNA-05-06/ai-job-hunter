# 🎯 Job Hunter — AI-Powered Job Search Automation

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-Scraping-45ba4b?style=for-the-badge&logo=playwright&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-AI_Scoring-F55036?style=for-the-badge)
![Platforms](https://img.shields.io/badge/Platforms-6-0077B5?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**Monitors 6 job platforms every hour, scores jobs with AI, and sends instant email alerts so you never miss a new posting — you apply manually with one click.**

[Features](#-features) • [How It Works](#-how-it-works) • [Setup](#-setup) • [Usage](#-usage)

</div>

---

## 💡 The Problem This Solves

Job hunting is exhausting. Checking LinkedIn, Indeed, Glassdoor, Dice, Handshake, and JobRight manually — multiple times a day — just to catch new postings before they get buried. Most people apply days after a job is posted. **Early applicants get noticed first.**

This bot watches all 6 platforms for you 24/7, scores every new job against your resume using AI, and emails you only the relevant ones — with a direct apply link. You spend 2 minutes applying while the job is still fresh instead of hours searching.

---

## 🚀 Features

- **6 Platforms at Once** — LinkedIn, Indeed, Glassdoor, Dice, Handshake, JobRight
- **AI Match Scoring** — Groq (Llama 3.1) scores each job 0–100 against your skills and resume
- **Instant Email Alerts** — Clean HTML email grouped by platform, with match score and one-click apply link per job
- **Runs Every Hour** — Fully automated on a schedule, even while you sleep
- **No Duplicates** — SQLite database tracks every job seen — you only get notified once per job
- **Zero Account Risk** — Only reads public job listing pages, never logs into any platform
- **Smart Q&A Memory** — Stores answers to common application questions for quick reference when applying
- **100% Free AI** — Groq free tier gives 500K tokens/day, no credit card needed
- **You Stay in Control** — You review every job and apply yourself via the link in the email

---

## 📧 What the Email Looks Like

```
🎯 18 New Data Engineer Jobs — LinkedIn · Indeed · Glassdoor

╔══════════════════════════════════════════════════════════╗
║  LinkedIn  (9 jobs)                                      ║
╠══════════════════════════════════════╦═══════╦══════════╣
║ Jr. Data Engineer                    ║  85%  ║          ║
║ Motorola Solutions · Salt Lake City  ║  🟢   ║ Apply →  ║
╠══════════════════════════════════════╬═══════╬══════════╣
║ Data Engineer                        ║  80%  ║          ║
║ Q2 · Austin, TX                      ║  🟡   ║ Apply →  ║
╚══════════════════════════════════════╩═══════╩══════════╝

╔══════════════════════════════════════════════════════════╗
║  Indeed  (5 jobs)                                        ║
║  ...                                                     ║
╚══════════════════════════════════════════════════════════╝
```

Each job shows: **title, company, location, AI match score, reason it matches, and a direct apply link.**

---

## 🔧 How It Works

```
Every 60 minutes:

  1. SCRAPE   →  Checks LinkedIn, Indeed, Glassdoor, Dice,
                 Handshake, and JobRight for new postings

  2. FILTER   →  Skips jobs already seen (local database)

  3. SCORE    →  Groq AI scores each new job against your
                 resume, skills, and experience (0-100)

  4. EMAIL    →  Sends you an alert with qualifying jobs
                 grouped by platform + one-click apply links

  5. YOU      →  Click the link, review the job, apply in
                 2 minutes while it's still fresh
```

---

## 🛠 Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.10+ |
| Web Scraping | Playwright (Chromium) |
| AI Scoring | Groq API — Llama 3.1 8B Instant (free) |
| Database | SQLite |
| Notifications | Gmail SMTP |
| Scheduling | Python scheduler loop |
| Dashboard | Python CLI |

---

## ⚙️ Setup

### Prerequisites
- Python 3.10+
- Gmail account (with 2-Step Verification enabled)
- Free Groq API key — [console.groq.com](https://console.groq.com)

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/job-hunter.git
cd job-hunter

python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows

pip install -r requirements.txt
playwright install chromium
```

### 2. Add Your Resume

```bash
cp your_resume.pdf data/resume.pdf
```

### 3. Configure

Copy the example config and fill in your details:

```bash
cp config.example.py config.py
```

Open `config.py` and fill in:

```python
PROFILE = {
    "name": "Your Name",
    "email": "your@email.com",
    "skills": ["Python", "SQL", "Spark", "AWS", ...],
    ...
}

AI = {
    "groq_api_key": "gsk_...",   # Free at console.groq.com
    ...
}

NOTIFICATIONS = {
    "email_sender":   "your@gmail.com",
    "email_password": "xxxx xxxx xxxx xxxx",  # Gmail App Password
    "email_recipient": "your@gmail.com",
}

SEARCH = {
    "roles":    ["Data Engineer", "Junior Data Engineer", ...],
    "locations": ["United States"],
    "min_match_score": 65,   # Only email jobs scoring above this
}
```

> **Gmail App Password:** Google Account → Security → 2-Step Verification → App Passwords → Create

### 4. Initialize & Test

```bash
# Set up database
python data/database.py

# Test AI scoring
python ai_engine/matcher.py

# Full dry run — scrape all platforms and send test email
python main.py --once --no-apply
```

---

## 🚀 Usage

```bash
# Run once and exit (good for testing)
python main.py --once --no-apply

# Run on schedule — checks every 60 minutes forever
python main.py --schedule --no-apply

# Open dashboard to manage Q&A answers and view found jobs
python dashboard/cli.py
```

### Windows — One-Click Startup

Create `start_job_hunter.bat` on your Desktop:

```bat
@echo off
cd /d "C:\path\to\job-hunter"
call venv\Scripts\activate
python main.py --schedule --no-apply
pause
```

Double-click every morning. Minimize the window — bot runs in the background.

**Auto-start on Windows login:** Press `Win+R` → type `shell:startup` → copy the `.bat` file there.

---

## 🧠 Q&A Memory

The bot pre-loads answers to common application questions from your resume:
- Work authorization, sponsorship, salary expectations
- Years of experience with Python, SQL, Spark, AWS, Airflow
- Education, availability, strengths, project descriptions

When you're applying manually and hit a question, check the dashboard for a ready answer:

```bash
python dashboard/cli.py → Option 3: View Q&A Memory
```

Add your own answers anytime:
```bash
python dashboard/cli.py → Option 4: Add a new Q&A answer
```

---

## 📁 Project Structure

```
job-hunter/
├── config.py                    # ⭐ Your settings (not committed to Git)
├── config.example.py            # Template — safe to share
├── main.py                      # Main orchestrator + scheduler
├── requirements.txt
├── data/
│   ├── database.py              # SQLite — jobs, Q&A memory
│   └── resume.pdf               # Your resume (add this, not committed)
├── scrapers/
│   ├── linkedin_scraper.py
│   ├── indeed_scraper.py
│   ├── glassdoor_scraper.py
│   ├── dice_scraper.py
│   ├── handshake_scraper.py
│   └── jobright_scraper.py
├── ai_engine/
│   └── matcher.py               # Groq AI scoring + Q&A answering
├── notifier/
│   └── notifications.py         # Email alerts grouped by platform
└── dashboard/
    └── cli.py                   # Interactive CLI dashboard
```

---

## 📊 Real Results

From actual usage:

| Metric | Result |
|---|---|
| Jobs scraped per run | ~120 across 6 platforms |
| Qualifying jobs (≥65% match) | ~20% of total |
| Time to get email after job posts | < 60 minutes |
| Duplicate alerts | 0 (DB prevents them) |
| AI scoring time per job | ~2 seconds |
| Daily AI token usage | Well within free tier |

---

## ⚠️ Notes

- `config.py` is excluded from Git — your API keys stay local
- `data/resume.pdf` is excluded from Git — your resume stays private
- The scraper only reads **public job search pages** — no login to any platform
- You apply to every job **manually** via the link in the email — full control

---

## 🤝 Built With Claude AI

This project was built through a conversational development process with **[Claude AI](https://claude.ai)** by Anthropic — from system design and coding to debugging and deployment.

---

## 📄 License

MIT — free to use, fork, and adapt for your own job search.

---

<div align="center">
  <strong>Built by Sri Krishna Sai Kota</strong><br>
  M.S. Computer Science · University of South Florida<br><br>
  <a href="https://www.linkedin.com/in/srikrishnasai/">LinkedIn</a> •
  <a href="https://github.com/KRISHNA-05-06">GitHub</a>
</div>