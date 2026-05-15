"""
config.example.py — Copy this to config.py and fill in your details.
DO NOT commit config.py to GitHub (it contains your API keys).
"""

PROFILE = {
    "name": "Your Full Name",
    "email": "your@email.com",
    "phone": "123-456-7890",
    "linkedin": "https://www.linkedin.com/in/yourprofile/",
    "github": "https://github.com/yourusername",
    "location": "City, State",
    "resume_path": "data/resume.pdf",
    "skills": [
        "Python", "SQL", "Apache Spark", "Apache Kafka", "Apache Airflow",
        "AWS S3", "AWS Redshift", "AWS Glue", "Databricks", "Snowflake",
        "dbt", "Docker", "PostgreSQL", "ETL", "Data Modeling",
    ],
    "education": "M.S. in Computer Science - Your University (Year)",
    "experience_years": 1,
    "summary": "Your professional summary here.",
}

SEARCH = {
    "roles": [
        "Data Engineer",
        "Junior Data Engineer",
        "Entry Level Data Engineer",
        "ETL Developer",
        "Big Data Engineer",
    ],
    "locations": ["United States"],
    "job_types": ["Full-time"],
    "experience_levels": ["Entry level", "Associate"],
    "min_match_score": 65,
    "auto_apply_min_score": 80,
    "blacklist_companies": [],
    "keywords_required": ["data engineer", "data pipeline", "etl"],
    "keywords_excluded": ["senior", "staff", "principal", "lead", "10+ years"],
}

SCHEDULER = {
    "check_interval_minutes": 60,
    "max_applies_per_day": 0,       # 0 = no auto-apply (recommended)
    "apply_delay_seconds": 45,
}

NOTIFICATIONS = {
    "email_enabled": True,
    "email_sender": "your@gmail.com",
    "email_password": "YOUR_GMAIL_APP_PASSWORD",  # myaccount.google.com/apppasswords
    "email_recipient": "your@gmail.com",
    "telegram_enabled": False,
    "telegram_bot_token": "",
    "telegram_chat_id": "",
}

AI = {
    "groq_api_key": "YOUR_GROQ_API_KEY",    # Free at console.groq.com
    "model": "llama-3.1-8b-instant",
    "match_model": "llama-3.1-8b-instant",
}

DATABASE = {
    "path": "data/jobs.db",
}
