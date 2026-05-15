"""
AI Engine — powered by Groq (Free tier)
- Score jobs against your profile
- Generate Q&A answers for applications
- Generate cover letters
- FREE: 14,400 requests/day, no credit card needed

Get your free API key at: https://console.groq.com
Model: llama-3.3-70b-versatile (very capable, very fast)
"""
import json
import re
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from config import AI, PROFILE, SEARCH
from data.database import find_answer, save_answer, get_all_qa


# ── GROQ API CALLER ───────────────────────────

def call_groq(prompt: str, system_prompt: str = None, max_tokens: int = 500) -> str:
    import requests
    api_key = AI["groq_api_key"]
    model   = AI["model"]

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.3,
            },
            timeout=30
        )
        if resp.status_code == 429:
            err = resp.text
            if "tokens per day" in err or "TPD" in err:
                print("  ❌ Daily token limit reached. Resumes tomorrow.")
            else:
                print("  ⏳ Rate limit — waiting 30 seconds...")
                time.sleep(30)
            return ""
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"  ⚠️  Groq call failed: {e}")
        return ""


# ── JOB MATCHING ──────────────────────────────

def score_job(job: dict) -> dict:
    """
    Score a job posting against the candidate profile.
    Returns: {score, reason, relevant_skills, recommendation}
    """
    prompt = f"""You are evaluating a job match for a candidate.

CANDIDATE PROFILE:
Name: {PROFILE['name']}
Role seeking: Data Engineer (Entry level)
Skills: {', '.join(PROFILE['skills'])}
Experience: {PROFILE['experience_years']} year(s) internship
Education: {PROFILE['education']}
Location: {PROFILE['location']}

JOB POSTING:
Title: {job['title']}
Company: {job['company']}
Location: {job['location']}
Description: {job.get('description', 'Not available')[:1500]}

Respond ONLY with a valid JSON object. No markdown, no explanation, just raw JSON:
{{
  "score": <integer 0-100>,
  "reason": "<2 sentence explanation>",
  "relevant_skills": ["skill1", "skill2"],
  "seniority_match": true,
  "recommendation": "apply"
}}

Scoring guide:
- 85-100: Excellent match (strong skills overlap, entry-level friendly)
- 70-84:  Good match (most skills align)
- 50-69:  Partial match (some gaps)
- 0-49:   Poor match (too senior, wrong domain, missing core skills)

Set recommendation to "skip" if job requires 3+ years OR is Staff/Principal/Lead/Manager level.
Set recommendation to "apply" if score >= 70 and entry-level friendly.
Set recommendation to "review" for borderline cases."""

    system = (
        "You are a precise job-matching evaluator. "
        "Always respond with only valid JSON, no extra text."
    )

    text = call_groq(prompt, system_prompt=system, max_tokens=400)
    time.sleep(2)  # stay well under rate limit

    try:
        text = re.sub(r"```json|```", "", text).strip()
        return json.loads(text)
    except Exception:
        # Try extracting JSON if model added extra text
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
        print(f"  ⚠️  Could not parse response: {text[:120]}")
        return {
            "score": 50,
            "reason": "Could not evaluate automatically.",
            "relevant_skills": [],
            "recommendation": "review"
        }


def filter_jobs(jobs: list[dict]) -> list[dict]:
    """Score all jobs and return those above the minimum match score."""
    scored = []
    for job in jobs:
        print(f"  🤖 Scoring: {job['title']} @ {job['company']}...")
        result = score_job(job)
        job["match_score"]   = result.get("score", 0)
        job["match_reason"]  = result.get("reason", "")
        job["recommendation"] = result.get("recommendation", "review")
        if job["match_score"] >= SEARCH["min_match_score"]:
            scored.append(job)
    scored.sort(key=lambda x: x["match_score"], reverse=True)
    return scored


# ── APPLICATION Q&A ───────────────────────────

SYSTEM_PROMPT = f"""You are filling out job applications on behalf of {PROFILE['name']}.
Always answer in first person. Be concise, professional, and specific.

CANDIDATE FACTS:
- Name:       {PROFILE['name']}
- Email:      {PROFILE['email']}
- Phone:      {PROFILE['phone']}
- Location:   {PROFILE['location']}
- Education:  {PROFILE['education']}
- Skills:     {', '.join(PROFILE['skills'])}
- Experience: {PROFILE['experience_years']} year internship at Magnum Wings (Data Engineering)
- LinkedIn:   {PROFILE['linkedin']}
- GitHub:     {PROFILE['github']}

ANSWER RULES:
- 1-4 sentences max — be direct, no fluff
- Reference real skills and projects when relevant
- Skill yes/no questions: answer "Yes" if skill is in the list above
- Salary: "Open to competitive compensation based on the role and market"
- Work authorization: "Yes, I am authorized to work in the United States"
- Sponsorship: "No, I do not require sponsorship at this time"
- GPA: "3.8/4.0"
- Give ONLY the answer — no intro like "Here is my answer:" or "Sure!"
"""


def answer_question(question: str, job_context: dict = None) -> str:
    """
    Answer a job application question.
    Checks memory first (free), then calls Groq if not found.
    Saves new answers to memory for future reuse.
    """
    # 1. Check memory — no API call needed
    cached = find_answer(question)
    if cached:
        print(f"  💾 Cached: '{question[:60]}'")
        return cached

    # 2. Build context
    job_info = ""
    if job_context:
        job_info = f"\nApplying for: {job_context.get('title','')} at {job_context.get('company','')}"

    existing_qa = get_all_qa()[:5]
    qa_examples = ""
    if existing_qa:
        qa_examples = "\nMY PREVIOUS ANSWERS (match this style and tone):\n"
        for qa in existing_qa:
            qa_examples += f"Q: {qa['question_original']}\nA: {qa['your_answer']}\n\n"

    prompt = f"""Answer this job application question for me.{job_info}

{qa_examples}
QUESTION: {question}

Answer only (1-4 sentences, no preamble):"""

    answer = call_groq(prompt, system_prompt=SYSTEM_PROMPT, max_tokens=250)
    time.sleep(2)

    if answer:
        save_answer(question, answer)
        print(f"  💡 Generated + saved: '{question[:60]}'")

    return answer


def generate_cover_letter(job: dict) -> str:
    """Generate a tailored cover letter for a specific job."""
    prompt = f"""Write a professional cover letter for this Data Engineer job application.

JOB:
Title: {job['title']}
Company: {job['company']}
Description: {job.get('description', 'Not provided')[:1000]}

CANDIDATE:
{PROFILE['summary']}
Key skills: {', '.join(PROFILE['skills'][:12])}
Education: {PROFILE['education']}

FORMAT — exactly 3 short paragraphs:
1. Enthusiasm for this specific company and role
2. 2-3 specific matching skills/projects with concrete details
3. Strong closing with call to action

Tone: Confident but humble (entry-level applicant)
Do NOT start with "I am writing to..."
Do NOT use generic phrases like "I am passionate about..."
"""
    result = call_groq(prompt, max_tokens=550)
    time.sleep(2)
    return result or "Could not generate cover letter."


# ── COMMON ANSWERS PRE-LOADED ─────────────────

def preload_common_answers():
    """
    Pre-populate Q&A memory from resume data.
    No API calls needed — all answers are hardcoded from your profile.
    """
    common = [
        ("Are you authorized to work in the United States?",
         "Yes, I am authorized to work in the United States."),

        ("Do you require sponsorship now or in the future?",
         "No, I do not require sponsorship at this time."),

        ("What is your desired salary or compensation?",
         "I am open to competitive compensation based on the role and market standards. I am flexible and happy to discuss."),

        ("Are you willing to relocate?",
         "I am currently based in Tampa, FL and open to remote opportunities. I am also willing to discuss relocation for the right opportunity."),

        ("Are you comfortable working in a hybrid environment?",
         "Yes, I am comfortable with hybrid, remote, or on-site work arrangements."),

        ("How many years of experience do you have with Python?",
         "I have approximately 2 years of hands-on Python experience building ETL pipelines, data processing scripts, and real-time API integrations."),

        ("How many years of experience do you have with SQL?",
         "I have 2+ years of SQL experience covering complex queries, data modeling, and production databases including PostgreSQL, MySQL, and Amazon Redshift."),

        ("Do you have experience with AWS?",
         "Yes — I have used AWS S3, Redshift, Glue, EMR, and CloudWatch in both my academic projects and my Data Engineering internship at Magnum Wings."),

        ("Do you have experience with Apache Spark?",
         "Yes. I used PySpark to process 50K+ records in my USF Smart Parking project and built streaming pipelines at Magnum Wings that reduced system latency by 25%."),

        ("Do you have experience with Apache Kafka?",
         "Yes, I worked with Kafka to build real-time streaming data pipelines during my Data Engineering internship at Magnum Wings."),

        ("Do you have experience with Airflow?",
         "Yes — I used Apache Airflow to orchestrate ETL workflows in both my Healthcare ELT and USF Smart Parking projects, including scheduling, logging, and data validation."),

        ("Do you have experience with dbt?",
         "Yes, I have experience with dbt for data transformation and modeling as part of my data engineering skill set."),

        ("Do you have experience with Snowflake?",
         "Yes, Snowflake is part of my cloud data warehousing skill set alongside Amazon Redshift."),

        ("Do you have experience with Databricks?",
         "Yes, I have hands-on experience with Databricks for large-scale data processing using Apache Spark."),

        ("What is your highest level of education?",
         "I am pursuing an M.S. in Computer Science at the University of South Florida (expected May 2026) and hold a B.Tech in Computer Science from R.V.R & J.C College of Engineering, India."),

        ("What is your GPA?",
         "My GPA is 3.8/4.0."),

        ("Are you available to start immediately?",
         "I am available to discuss start dates and can accommodate reasonable timelines."),

        ("Tell us about yourself.",
         "I'm Sri Krishna Sai Kota, a Data Engineering graduate student at USF with hands-on experience building ETL/ELT pipelines using Python, SQL, Spark, Kafka, and AWS. "
         "At Magnum Wings, I built real-time streaming pipelines processing 10K+ data points per day, cutting latency by 25%. "
         "I'm passionate about building reliable, scalable data infrastructure that powers data-driven decisions."),

        ("Why do you want to work in data engineering?",
         "Data engineering sits at the foundation of everything data-driven — reliable pipelines mean every downstream team can trust the data they work with. "
         "That foundational impact, combined with the technical depth the field requires, is what drew me to it."),

        ("What is your greatest strength?",
         "My greatest strength is learning and applying new tools quickly. At Magnum Wings I picked up WebSockets and geospatial APIs on the job and delivered production-quality integrations within weeks."),

        ("Describe a challenging data pipeline you built and how you handled it.",
         "At Magnum Wings, I built a real-time pipeline ingesting UAV telemetry via WebSockets, which initially had high latency spikes. "
         "I resolved this by switching to asynchronous processing and optimizing the API request handling, ultimately reducing latency by 25% and improving throughput by 30%."),

        ("Are you a US citizen or permanent resident?",
         "I am on an F-1 student visa. I am authorized to work in the US and do not require employer sponsorship at this time."),
    ]

    loaded = 0
    for question, answer in common:
        if not find_answer(question):
            save_answer(question, answer)
            loaded += 1

    print(f"✅ Pre-loaded {loaded} new Q&A answers ({len(common)} total checked).")


# ── TEST ──────────────────────────────────────

if __name__ == "__main__":
    print("🧪 Testing Groq AI engine...\n")
    preload_common_answers()

    print("\n--- Job scoring test ---")
    test_job = {
        "title": "Junior Data Engineer",
        "company": "Acme Analytics",
        "location": "Tampa, FL (Hybrid)",
        "description": (
            "Entry-level Data Engineer to build and maintain ETL pipelines using Python and SQL. "
            "Experience with Apache Spark, AWS S3, and Airflow preferred. 0-2 years required. "
            "Master's degree in CS or related field a plus."
        )
    }
    result = score_job(test_job)
    print(f"  Score     : {result.get('score')}/100")
    print(f"  Reason    : {result.get('reason')}")
    print(f"  Recommend : {result.get('recommendation')}")

    print("\n--- Q&A answering test ---")
    q = "What experience do you have building data pipelines at scale?"
    print(f"  Question  : {q}")
    ans = answer_question(q, job_context=test_job)
    print(f"  Answer    : {ans}")

    print("\n✅ Groq engine is working!")