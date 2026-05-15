"""
Handshake Job Scraper
Scrapes Handshake public job listings — great for new grads/entry level.
Uses Playwright since Handshake requires JS rendering.
"""
import asyncio
import hashlib
from urllib.parse import quote
from playwright.async_api import async_playwright
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from config import SEARCH


def make_job_id(url: str) -> str:
    return "hs_" + hashlib.md5(url.encode()).hexdigest()[:14]


async def scrape_handshake(role: str, max_jobs: int = 20) -> list[dict]:
    """
    Scrape Handshake public job search.
    Handshake is specifically for students/new grads — great match for your profile.
    """
    jobs = []
    url = (
        f"https://app.joinhandshake.com/stu/postings"
        f"?sort=RELEVANCE&query={quote(role)}"
        f"&job_type%5B%5D=full_time"
    )

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(5)

            # Scroll to load content
            for _ in range(3):
                await page.evaluate("window.scrollBy(0, 600)")
                await asyncio.sleep(1)

            cards = await page.query_selector_all(
                "[data-hook='posting-card'], .posting-card, article[class*='posting']"
            )

            for card in cards[:max_jobs]:
                try:
                    title_el    = await card.query_selector("h3, h2, [data-hook='posting-name']")
                    company_el  = await card.query_selector("[data-hook='employer-name'], .employer-name")
                    location_el = await card.query_selector("[data-hook='posting-location'], .location")
                    link_el     = await card.query_selector("a")
                    date_el     = await card.query_selector(
                        "[data-hook='posting-date'], time, [class*='date'], [class*='posted'], [class*='ago']"
                    )

                    title    = (await title_el.inner_text()).strip()    if title_el    else ""
                    company  = (await company_el.inner_text()).strip()  if company_el  else ""
                    location = (await location_el.inner_text()).strip() if location_el else ""
                    href     = await link_el.get_attribute("href")      if link_el     else ""

                    posted_at = ""
                    if date_el:
                        dt_attr = await date_el.get_attribute("datetime") or ""
                        dt_text = (await date_el.inner_text()).strip()
                        raw = dt_attr or dt_text
                        from scrapers.date_utils import scrape_time_text
                        posted_at = scrape_time_text(raw)

                    if href and not href.startswith("http"):
                        href = "https://app.joinhandshake.com" + href

                    if title and href:
                        jobs.append({
                            "id":        make_job_id(href),
                            "title":     title,
                            "company":   company or "Unknown",
                            "location":  location,
                            "url":       href,
                            "source":    "Handshake",
                            "posted_at": posted_at,
                            "job_type":  "Full-time",
                            "description": "",
                        })
                except Exception:
                    continue

        except Exception as e:
            print(f"  ⚠️  Handshake scrape error: {e}")
        finally:
            await browser.close()

    print(f"  📋 Handshake [{role}] → {len(jobs)} jobs found")
    return jobs


async def run_handshake_scraper() -> list[dict]:
    all_jobs = []
    seen_ids = set()
    for role in SEARCH["roles"][:2]:
        jobs = await scrape_handshake(role)
        for job in jobs:
            if job["id"] not in seen_ids:
                seen_ids.add(job["id"])
                all_jobs.append(job)
        await asyncio.sleep(3)
    return all_jobs


if __name__ == "__main__":
    jobs = asyncio.run(run_handshake_scraper())
    for j in jobs[:5]:
        print(f"  {j['title']} @ {j['company']} — {j['location']}")
