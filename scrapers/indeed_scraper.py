"""
Indeed Job Scraper
Scrapes Indeed using Playwright. No login needed.
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
    return "in_" + hashlib.md5(url.encode()).hexdigest()[:14]


def build_indeed_url(role: str, location: str) -> str:
    return (
        f"https://www.indeed.com/jobs?q={quote(role)}"
        f"&l={quote(location)}&sort=date&fromage=1"
    )


async def scrape_indeed(role: str, location: str, max_jobs: int = 25) -> list[dict]:
    jobs = []
    url = build_indeed_url(role, location)

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
            await asyncio.sleep(3)

            cards = await page.query_selector_all("div.job_seen_beacon, div.cardOutline, .result")

            for card in cards[:max_jobs]:
                try:
                    title_el  = await card.query_selector("h2.jobTitle span, h2 a span")
                    company_el = await card.query_selector("[data-testid='company-name'], .companyName")
                    location_el = await card.query_selector("[data-testid='text-location'], .companyLocation")
                    link_el   = await card.query_selector("h2 a, a.jcs-JobTitle")

                    title    = (await title_el.inner_text()).strip()   if title_el   else ""
                    company  = (await company_el.inner_text()).strip() if company_el else ""
                    location = (await location_el.inner_text()).strip() if location_el else ""
                    href     = await link_el.get_attribute("href")     if link_el    else ""

                    if href and not href.startswith("http"):
                        href = "https://www.indeed.com" + href

                    if title and href:
                        jobs.append({
                            "id":       make_job_id(href),
                            "title":    title,
                            "company":  company or "Unknown",
                            "location": location,
                            "url":      href,
                            "source":   "Indeed",
                            "posted_at": "",
                            "job_type": "Full-time",
                            "description": "",
                        })
                except Exception:
                    continue

        except Exception as e:
            print(f"  ⚠️  Indeed scrape error: {e}")
        finally:
            await browser.close()

    print(f"  📋 Indeed [{role}] → {len(jobs)} jobs found")
    return jobs


async def run_indeed_scraper() -> list[dict]:
    all_jobs = []
    seen_ids = set()
    for role in SEARCH["roles"][:2]:
        for location in SEARCH["locations"][:1]:
            jobs = await scrape_indeed(role, location)
            for job in jobs:
                if job["id"] not in seen_ids:
                    seen_ids.add(job["id"])
                    all_jobs.append(job)
            await asyncio.sleep(3)
    return all_jobs


if __name__ == "__main__":
    jobs = asyncio.run(run_indeed_scraper())
    for j in jobs[:5]:
        print(f"  {j['title']} @ {j['company']} — {j['location']}")
