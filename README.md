# 🎯 Job Hunter — AI-Powered Job Search Automation

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-Scraping-45ba4b?style=for-the-badge&logo=playwright&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-AI_Scoring-F55036?style=for-the-badge)
![Platforms](https://img.shields.io/badge/Platforms-6-0077B5?style=for-the-badge)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-Automated-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**Monitors 6 job platforms, scores jobs with AI, sends instant email alerts with recency badges — runs automatically 5 times a day on GitHub Actions, even when your laptop is off.**

[Features](#-features) • [How It Works](#-how-it-works) • [Setup](#-setup) • [Usage](#-usage) • [GitHub Actions](#-github-actions-runs-without-your-laptop)

</div>

---

## 💡 The Problem This Solves

Job hunting is exhausting. Checking LinkedIn, Indeed, Glassdoor, Dice, Handshake, and JobRight manually — multiple times a day — just to catch new postings before they get buried. Most people apply days after a job is posted. **Early applicants always get noticed first.**

This bot watches all 6 platforms for you 24/7, scores every new job against your resume using AI, shows you exactly how recent each posting is, and emails you only the relevant ones — with a direct apply link. You spend 2 minutes applying while the job is still fresh instead of hours searching.

---

## 🚀 Features

- **6 Platforms at Once** — LinkedIn, Indeed, Glassdoor, Dice, Handshake, JobRight
- **AI Match Scoring** — Groq (Llama 3.1) scores each job 0–100 against your skills and resume
- **Recency Badges** — Every job shows exactly when it was posted: 🟢 2h ago · 🟡 Yesterday · 🔴 3 days ago
- **Sorted Newest First** — Most recently posted jobs always appear at the top of your email
- **Runs 5x Daily on GitHub Actions** — Fully automated, runs even when your laptop is completely off
- **Instant Email Alerts** — Clean HTML email grouped by platform with match scores and one-click apply links
- **No Duplicates** — SQLite database tracks every job seen — you only ever get notified once per job
- **Zero Account Risk** — Only reads public job listing pages, never logs into any platform
- **Smart Q&A Memory** — Stores answers to common application questions for quick reference when applying
- **100% Free** — Groq free tier (500K tokens/day) + GitHub Actions free tier (2,000 min/month)
- **You Stay in Control** — You review every job and apply yourself via the link in the email

---

## 📧 What the Email Looks Like

```
🎯 18 New Data Engineer Jobs — LinkedIn · Indeed · Glassdoor
May 16, 2026 at 9:00 AM

Posted time legend:
🟢 Under 6 hours  ·  🟡 6–48 hours  ·  🔴 Older than 2 days

╔══════════════════════════════════════════════════════════════╗
║  LinkedIn  (9 jobs)                                          ║
╠══════════════════════════╦═══════╦════════════════╦════════╣
║ Jr. Data Engineer         ║  85%  ║ Strong match   ║        ║
║ Motorola Solutions        ║  🟢   ║ on Spark, AWS  ║ Apply →║
║ 🟢 Just now               ║       ║                ║        ║
╠══════════════════════════╬═══════╬════════════════╬════════╣
║ Data Engineer             ║  80%  ║ ETL pipeline   ║        ║
║ Q2 · Austin, TX           ║  🟡   ║ skills align   ║ Apply →║
║ 🟡 3h ago                 ║       ║                ║        ║
╚══════════════════════════╩═══════╩════════════════╩════════╝

╔══════════════════════════════════════════════════════════════╗
║  Indeed  (5 jobs)                                            ║
║  ...                                                         ║
╚══════════════════════════════════════════════════════════════╝
```

---

## 🔧 How It Works

```
5 times every day (GitHub Actions — no laptop needed):

  1. SCRAPE   →  Checks LinkedIn, Indeed, Glassdoor, Dice,
                 Handshake, and JobRight for new postings

  2. FILTER   →  Skips jobs already seen (persistent database)

  3. SCORE    →  Groq AI scores each new job against your
                 resume, skills, and experience (0-100)

  4. SORT     →  Orders jobs by most recently posted first
                 with color-coded recency badges

  5. EMAIL    →  Sends alert grouped by platform with
                 match scores + one-click apply links

  6. YOU      →  Click the link, apply in 2 minutes
                 while the job is still fresh
```

---

## ☁️ GitHub Actions — Runs Without Your Laptop

The bot runs automatically on GitHub's servers **5 times every day**, even when your laptop is completely off:

```
6:00 AM  EDT  →  Fresh overnight postings
9:00 AM  EDT  →  Peak morning posting time
12:00 PM EDT  →  Midday check
3:00 PM  EDT  →  Afternoon check
6:00 PM  EDT  →  Evening check
```

**Completely free:**
- GitHub Actions free tier: 2,000 minutes/month
- Each run takes ~5–8 minutes
- 5 runs/day × 8 min × 30 days = 1,200 minutes — well within limit

You can also trigger a manual run anytime from the GitHub Actions tab.

---

## 🛠 Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.10+ |
| Web Scraping | Playwright (Chromium) |
| AI Scoring | Groq API — Llama 3.1 8B Instant (free) |
| Database | SQLite (persisted via GitHub Actions cache) |
| Notifications | Gmail SMTP |
| Scheduling | GitHub Actions cron |
| Dashboard | Python CLI |

---

## ⚙️ Setup

### Prerequisites
- Python 3.10+
- Gmail account (with 2-Step Verification enabled)
- Free Groq API key — [console.groq.com](https://console.groq.com)
- GitHub account

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/ai-job-hunter.git
cd ai-job-hunter

python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows

pip install -r requirements.txt
playwright install chromium
```

### 2. Configure locally

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
    "groq_api_key": "gsk_...",        # Free at console.groq.com
    "model": "llama-3.1-8b-instant",
}

NOTIFICATIONS = {
    "email_sender":    "your@gmail.com",
    "email_password":  "xxxx xxxx xxxx xxxx",  # Gmail App Password
    "email_recipient": "your@gmail.com",
}

SEARCH = {
    "roles":             ["Data Engineer", "Junior Data Engineer", ...],
    "locations":         ["United States"],
    "min_match_score":   65,
}
```

> **Gmail App Password:** Google Account → Security → 2-Step Verification → App Passwords → Create

### 3. Initialize & Test Locally

```bash
python data/database.py           # Set up database
python ai_engine/matcher.py       # Test AI scoring
python main.py --once --no-apply  # Full dry run
```

---

## ☁️ Deploy to GitHub Actions (Run 24/7 for Free)

### Step 1 — Add secrets to your GitHub repo

Go to: **GitHub repo → Settings → Secrets and variables → Actions → New repository secret**

Add these 4 secrets:

| Secret Name | Value |
|---|---|
| `GROQ_API_KEY` | Your Groq API key (`gsk_...`) |
| `EMAIL_SENDER` | Your Gmail address |
| `EMAIL_PASSWORD` | Your Gmail App Password |
| `EMAIL_RECIPIENT` | Where to send alerts (your email) |

### Step 2 — Push your code

```bash
git add .
git commit -m "Deploy Job Hunter Bot"
git push
```

### Step 3 — Trigger a test run

GitHub → Actions tab → **Job Hunter Bot** → **Run workflow** → **Run workflow**

Watch the logs — green checkmark means it worked and you'll get an email! ✅

---

## 🚀 Local Usage

```bash
# Run once — scrape all platforms and send email (no applying)
python main.py --once --no-apply

# Run on schedule locally — every 60 minutes
python main.py --schedule --no-apply

# Open dashboard — manage Q&A answers, view found jobs
python dashboard/cli.py
```

### Windows — One-Click Local Startup

Create `run_once_job_hunter.bat`:

```bat
@echo off
cd /d "C:\path\to\ai-job-hunter"
call venv\Scripts\activate
python main.py --once --no-apply
pause
```

---

## 🧠 Q&A Memory

Pre-loaded answers from your resume for common questions:
- Work authorization, sponsorship, salary expectations
- Years of experience with Python, SQL, Spark, AWS, Airflow, Kafka
- Education, availability, project descriptions

Add your own via the dashboard:
```bash
python dashboard/cli.py → Option 4: Add a new Q&A answer
```

---

## 📁 Project Structure

```
ai-job-hunter/
├── .github/
│   └── workflows/
│       └── job_hunter.yml       # GitHub Actions automation
├── config.py                    # ⭐ Your settings (not on GitHub)
├── config.example.py            # Template — safe to share
├── main.py                      # Main orchestrator + scheduler
├── requirements.txt
├── data/
│   ├── database.py              # SQLite — jobs, Q&A memory
│   └── resume.pdf               # Your resume (not on GitHub)
├── scrapers/
│   ├── date_utils.py            # Shared recency parsing
│   ├── linkedin_scraper.py
│   ├── indeed_scraper.py
│   ├── glassdoor_scraper.py
│   ├── dice_scraper.py
│   ├── handshake_scraper.py
│   └── jobright_scraper.py
├── ai_engine/
│   └── matcher.py               # Groq AI scoring + Q&A
├── notifier/
│   └── notifications.py         # Email alerts grouped by platform
└── dashboard/
    └── cli.py                   # Interactive CLI dashboard
```

---

## 📊 Real Results

| Metric | Result |
|---|---|
| Jobs scraped per run | ~120 across 6 platforms |
| Qualifying jobs (≥65% match) | ~15–20% of total |
| Email delivery after job posts | < 60 minutes |
| Duplicate alerts | 0 (DB prevents them) |
| Runs per day (GitHub Actions) | 5 automatic + unlimited manual |
| Monthly GitHub Actions cost | $0 (free tier) |
| Monthly AI cost | $0 (Groq free tier) |

---

## ⚠️ Notes

- `config.py` is excluded from Git — your API keys stay local and in GitHub Secrets
- `data/resume.pdf` is excluded from Git — your resume stays private
- The scraper only reads **public job search pages** — no login to any platform
- You apply to every job **manually** via the link in the email — full control
- Database is persisted between GitHub Actions runs via cache

---

## 🤝 Built With Claude AI

This project was built entirely through a conversational development process with **[Claude AI](https://claude.ai)** by Anthropic — from system design and coding to debugging, deployment, and GitHub Actions automation.

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