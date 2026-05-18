"""
Main Orchestrator — scrapes LinkedIn, Indeed, Glassdoor, Dice, Handshake, JobRight
Runs the full pipeline: Scrape → Score → Notify (grouped by platform) → Apply
"""
import asyncio
import time
from datetime import datetime
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from config import SCHEDULER, SEARCH
from data.database import init_db, job_exists, job_exists_by_title_company, save_job, save_job_seen, bulk_save_seen, get_stats
from scrapers.linkedin_scraper  import run_linkedin_scraper
from scrapers.jobright_scraper  import run_jobright_scraper
from scrapers.indeed_scraper    import run_indeed_scraper
from scrapers.glassdoor_scraper import run_glassdoor_scraper
from scrapers.dice_scraper      import run_dice_scraper
from scrapers.handshake_scraper import run_handshake_scraper
from ai_engine.matcher import filter_jobs, preload_common_answers
from notifier.notifications import notify_all
from scrapers.recency_filter import apply_recency_filter
#from apply_bot.auto_apply import run_auto_apply
try:
    from apply_bot.auto_apply import run_auto_apply
except ImportError:
    async def run_auto_apply(jobs):
        print("  ℹ️  Auto-apply module not available in this environment.")


SCRAPERS = [
    ("LinkedIn",  run_linkedin_scraper),
    ("Indeed",    run_indeed_scraper),
    ("Dice",      run_dice_scraper),
    ("Glassdoor", run_glassdoor_scraper),
    ("Handshake", run_handshake_scraper),
    ("JobRight",  run_jobright_scraper),
]


def print_banner():
    print("""
╔══════════════════════════════════════════════════════╗
║  🎯 JOB HUNTER — Multi-Platform Data Engineer Bot   ║
║  Sources: LinkedIn · Indeed · Dice · Glassdoor      ║
║           Handshake · JobRight                      ║
║  Built for: Sri Krishna Sai Kota                    ║
╚══════════════════════════════════════════════════════╝
    """)


async def run_pipeline(auto_apply: bool = True):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*54}")
    print(f"  🔄 Pipeline started: {now}")
    print(f"{'='*54}")

    # ── Step 1: Scrape all platforms ──────────
    print("\n📡 Step 1: Scraping all job platforms...")
    all_scraped = []
    platform_counts = {}

    for name, scraper_fn in SCRAPERS:
        try:
            jobs = await scraper_fn()
            platform_counts[name] = len(jobs)
            all_scraped.extend(jobs)
        except Exception as e:
            print(f"  ⚠️  {name} scraper failed: {e}")
            platform_counts[name] = 0

    print(f"\n  Platform breakdown:")
    for name, count in platform_counts.items():
        bar = "█" * min(count, 30)
        print(f"    {name:<12} {bar} {count}")
    print(f"  Total scraped: {len(all_scraped)} jobs")

    # ── Step 1b: Recency + repost filter ─────
    print("\n🕐 Step 1b: Applying 24-hour freshness filter...")
    all_scraped = apply_recency_filter(all_scraped, strict=True)

    # ── Step 2: Deduplicate ───────────────────
    print("\n🔍 Step 2: Filtering already-seen jobs...")
    new_jobs = [
        j for j in all_scraped
        if not job_exists(j["id"])
        and not job_exists_by_title_company(j["title"], j["company"])
    ]
    skipped  = len(all_scraped) - len(new_jobs)
    print(f"  New: {len(new_jobs)}  |  Already seen: {skipped}")

    if not new_jobs:
        print("  ℹ️  No new jobs this run.")
        return

    # ── Save ALL new jobs as seen immediately ──
    # This ensures even low-scoring jobs are never re-processed next run
    bulk_save_seen(new_jobs)
    print(f"  💾 Saved {len(new_jobs)} jobs to DB (will be skipped in future runs)")

    # ── Step 3: AI Scoring ────────────────────
    print(f"\n🤖 Step 3: AI scoring {len(new_jobs)} new jobs...")
    qualifying_jobs = filter_jobs(new_jobs)
    print(f"  Qualifying (score ≥ {SEARCH['min_match_score']}): {len(qualifying_jobs)}")

    # Show qualifying breakdown by platform
    if qualifying_jobs:
        from collections import Counter
        q_by_platform = Counter(j.get("source") for j in qualifying_jobs)
        print(f"  By platform: {dict(q_by_platform)}")

    # Update qualifying jobs with scores in DB
    for job in qualifying_jobs:
        save_job(job)

    # ── Step 4: Notify ────────────────────────
    print(f"\n🔔 Step 4: Sending email (grouped by platform)...")
    notify_all(qualifying_jobs)

    # ── Step 5: Auto Apply ────────────────────
    if auto_apply:
        apply_candidates = [j for j in qualifying_jobs
                           if j.get("recommendation") == "apply"
                           and j.get("source") == "LinkedIn"]
        print(f"\n🚀 Step 5: Auto-applying to {len(apply_candidates)} LinkedIn jobs...")
        await run_auto_apply(apply_candidates)
    else:
        print("\n⏭️  Step 5: Auto-apply skipped (manual mode)")

    # ── Summary ───────────────────────────────
    stats = get_stats()
    print(f"""
📊 Session Summary:
   • Platforms scraped     : {len([c for c in platform_counts.values() if c > 0])}/{len(SCRAPERS)}
   • Total jobs scraped    : {len(all_scraped)}
   • New jobs found        : {len(new_jobs)}
   • Qualifying (≥score)   : {len(qualifying_jobs)}
   • Total in DB           : {stats['total_jobs']}
   • Applied (all time)    : {stats['applied']}
   • Applied today         : {stats['today_applied']}
   • Q&A answers stored    : {stats['qa_answers']}
    """)


def run_scheduler(auto_apply: bool = True):
    interval = SCHEDULER["check_interval_minutes"] * 60
    print_banner()
    init_db()
    preload_common_answers()
    print(f"⏰ Scheduler started. Running every {SCHEDULER['check_interval_minutes']} minutes.")
    print("   Press Ctrl+C to stop.\n")

    while True:
        try:
            asyncio.run(run_pipeline(auto_apply=auto_apply))
        except KeyboardInterrupt:
            print("\n👋 Scheduler stopped.")
            break
        except Exception as e:
            print(f"\n⚠️  Pipeline error: {e}")

        print(f"\n⏳ Next run in {SCHEDULER['check_interval_minutes']} minutes...")
        time.sleep(interval)


def run_once(auto_apply: bool = False):
    print_banner()
    init_db()
    preload_common_answers()
    asyncio.run(run_pipeline(auto_apply=auto_apply))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Job Hunter Bot")
    parser.add_argument("--once",     action="store_true", help="Run once and exit")
    parser.add_argument("--no-apply", action="store_true", help="No auto-apply")
    parser.add_argument("--schedule", action="store_true", help="Run on schedule")
    args = parser.parse_args()

    auto_apply = not args.no_apply
    if args.once:
        run_once(auto_apply=auto_apply)
    else:
        run_scheduler(auto_apply=auto_apply)