"""
JobRight.ai Scraper — updated with longer timeout and better selectors
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
    return "jr_" + hashlib.md5(url.encode()).hexdigest()[:14]


async def scrape_jobright(role: str, max_jobs: int = 20) -> list[dict]:
    jobs = []
    url = f"https://jobright.ai/jobs/search?keyword={quote(role)}&sortBy=date"

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()
        try:
            # Use longer timeout + domcontentloaded (not networkidle) to avoid timeout
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(5)

            for _ in range(4):
                await page.evaluate("window.scrollBy(0, 600)")
                await asyncio.sleep(1)

            cards = await page.query_selector_all(
                "[class*='job-card'], [class*='JobCard'], article[class*='job'], .job-item, li[class*='job']"
            )
            if not cards:
                cards = await page.query_selector_all("article, li[class*='job']")

            for card in cards[:max_jobs]:
                try:
                    title = company = location = href = ""
                    for sel in ["h2", "h3", "[class*='title']", "[class*='Title']"]:
                        el = await card.query_selector(sel)
                        if el:
                            title = (await el.inner_text()).strip()
                            break
                    for sel in ["[class*='company']", "[class*='Company']"]:
                        el = await card.query_selector(sel)
                        if el:
                            company = (await el.inner_text()).strip()
                            break
                    for sel in ["[class*='location']", "[class*='Location']"]:
                        el = await card.query_selector(sel)
                        if el:
                            location = (await el.inner_text()).strip()
                            break
                    link_el = await card.query_selector("a")
                    if link_el:
                        href = await link_el.get_attribute("href") or ""
                        if href and not href.startswith("http"):
                            href = "https://jobright.ai" + href

                    # Try to get posted date
                    posted_at = ""
                    for sel in ["time", "[class*='date']", "[class*='posted']", "[class*='ago']", "[class*='time']"]:
                        date_el = await card.query_selector(sel)
                        if date_el:
                            dt_attr = await date_el.get_attribute("datetime") or ""
                            dt_text = (await date_el.inner_text()).strip()
                            raw = dt_attr or dt_text
                            if raw:
                                from scrapers.date_utils import scrape_time_text
                                posted_at = scrape_time_text(raw)
                                break

                    if title and href:
                        jobs.append({
                            "id": make_job_id(href), "title": title,
                            "company": company or "Unknown", "location": location,
                            "url": href, "source": "JobRight",
                            "posted_at": posted_at, "job_type": "Full-time", "description": "",
                        })
                except Exception:
                    continue

        except Exception as e:
            print(f"  ⚠️  JobRight scrape error: {e}")
        finally:
            await browser.close()

    print(f"  📋 JobRight [{role}] → {len(jobs)} jobs found")
    return jobs


async def run_jobright_scraper() -> list[dict]:
    all_jobs = []
    seen_ids = set()
    for role in SEARCH["roles"][:2]:
        jobs = await scrape_jobright(role)
        for job in jobs:
            if job["id"] not in seen_ids:
                seen_ids.add(job["id"])
                all_jobs.append(job)
        await asyncio.sleep(3)
    return all_jobs


if __name__ == "__main__":
    jobs = asyncio.run(run_jobright_scraper())
    for j in jobs[:5]:
        print(f"  {j['title']} @ {j['company']} — {j['location']}")
