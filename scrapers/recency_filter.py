"""
Recency Filter — strictly filters jobs to only those posted in the last 24 hours.
Also filters out reposted jobs using title+company deduplication.
"""
from datetime import datetime, timedelta
from scrapers.date_utils import scrape_time_text


def is_within_24_hours(posted_at: str) -> bool:
    """Return True if job was posted within the last 24 hours."""
    if not posted_at:
        # No date info — be lenient, include it (better to show than miss)
        return True

    try:
        # Normalize to datetime
        iso = scrape_time_text(posted_at)
        dt  = datetime.strptime(iso[:19], "%Y-%m-%dT%H:%M:%S")
        cutoff = datetime.now() - timedelta(hours=24)
        return dt >= cutoff
    except Exception:
        return True  # Parse error — include to be safe


def deduplicate_by_title_company(jobs: list[dict]) -> list[dict]:
    """
    Remove reposted duplicates — same title + company = same job.
    Keeps the most recently posted one.
    """
    seen = {}
    for job in jobs:
        key = (
            job["title"].lower().strip(),
            job["company"].lower().strip(),
        )
        if key not in seen:
            seen[key] = job
        else:
            # Keep whichever was posted more recently
            existing_posted = seen[key].get("posted_at", "")
            new_posted      = job.get("posted_at", "")
            if new_posted and new_posted > existing_posted:
                seen[key] = job

    return list(seen.values())


def apply_recency_filter(jobs: list[dict], strict: bool = True) -> list[dict]:
    """
    Apply all freshness filters:
    1. Remove jobs older than 24 hours (if strict=True)
    2. Remove reposted duplicates (same title+company)
    3. Sort by most recent first
    """
    original_count = len(jobs)

    # Step 1 — 24-hour filter
    if strict:
        fresh = [j for j in jobs if is_within_24_hours(j.get("posted_at", ""))]
        removed_old = original_count - len(fresh)
        if removed_old > 0:
            print(f"  🕐 Removed {removed_old} jobs older than 24 hours")
    else:
        fresh = jobs

    # Step 2 — Remove reposted duplicates across platforms
    deduped = deduplicate_by_title_company(fresh)
    removed_dupes = len(fresh) - len(deduped)
    if removed_dupes > 0:
        print(f"  🔁 Removed {removed_dupes} reposted duplicates (same title+company)")

    # Step 3 — Sort newest first
    def sort_key(job):
        try:
            iso = scrape_time_text(job.get("posted_at", ""))
            return datetime.strptime(iso[:19], "%Y-%m-%dT%H:%M:%S")
        except Exception:
            return datetime.min
    deduped.sort(key=sort_key, reverse=True)

    print(f"  ✅ After freshness filter: {len(deduped)} jobs (from {original_count})")
    return deduped