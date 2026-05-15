"""
Dice.com Job Scraper — Direct website scraping via Playwright.
No external API needed.
"""
import asyncio
import hashlib
import urllib.parse
from playwright.async_api import async_playwright
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from config import SEARCH


def make_job_id(url: str) -> str:
    return "dc_" + hashlib.md5(url.encode()).hexdigest()[:14]


async def scrape_dice(role: str, max_jobs: int = 25) -> list[dict]:
    """Scrape Dice.com job listings directly via browser."""
    jobs = []
    url = (
        f"https://www.dice.com/jobs?q={urllib.parse.quote(role)}"
        f"&countryCode=US&radius=30&radiusUnit=mi"
        f"&filters.postedDate=ONE"
        f"&filters.employmentType=FULLTIME"
        f"&language=en&eid=S2Q_"
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
            ),
            locale="en-US"
        )
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=35000)
            await asyncio.sleep(5)

            # Scroll to trigger lazy load
            for _ in range(3):
                await page.evaluate("window.scrollBy(0, 700)")
                await asyncio.sleep(1)

            # Try multiple known Dice card selectors
            cards = []
            for selector in [
                "dhi-search-card",
                "[data-cy='search-card']",
                ".search-card",
                "li[class*='search-card']",
            ]:
                cards = await page.query_selector_all(selector)
                if cards:
                    break

            # If still no cards, try getting job links directly
            if not cards:
                links = await page.query_selector_all(
                    "a[href*='/job-detail/'], a.card-title-link"
                )
                for link in links[:max_jobs]:
                    try:
                        title = (await link.inner_text()).strip()
                        href  = await link.get_attribute("href") or ""
                        if href and not href.startswith("http"):
                            href = "https://www.dice.com" + href
                        if title and href:
                            jobs.append({
                                "id":          make_job_id(href),
                                "title":       title,
                                "company":     "See listing",
                                "location":    "United States",
                                "url":         href,
                                "source":      "Dice",
                                "posted_at":   "",
                                "job_type":    "Full-time",
                                "description": "",
                            })
                    except Exception:
                        continue
            else:
                for card in cards[:max_jobs]:
                    try:
                        title_el    = await card.query_selector(
                            "a.card-title-link, h5 a, [data-cy='card-title'], .job-title"
                        )
                        company_el  = await card.query_selector(
                            "[data-cy='search-result-company-name'], .company-name, a[data-cy='company-name']"
                        )
                        location_el = await card.query_selector(
                            "[data-cy='search-result-location'], .location, span[class*='location']"
                        )
                        link_el     = await card.query_selector(
                            "a[href*='job-detail'], a.card-title-link, h5 a"
                        )

                        title    = (await title_el.inner_text()).strip()    if title_el    else ""
                        company  = (await company_el.inner_text()).strip()  if company_el  else "Unknown"
                        location = (await location_el.inner_text()).strip() if location_el else "United States"
                        href     = await link_el.get_attribute("href")      if link_el     else ""

                        if href and not href.startswith("http"):
                            href = "https://www.dice.com" + href

                        if title and href:
                            jobs.append({
                                "id":          make_job_id(href),
                                "title":       title,
                                "company":     company,
                                "location":    location,
                                "url":         href,
                                "source":      "Dice",
                                "posted_at":   "",
                                "job_type":    "Full-time",
                                "description": "",
                            })
                    except Exception:
                        continue

        except Exception as e:
            print(f"  ⚠️  Dice scrape error: {e}")
        finally:
            await browser.close()

    print(f"  📋 Dice [{role}] → {len(jobs)} jobs found")
    return jobs


async def run_dice_scraper() -> list[dict]:
    all_jobs = []
    seen_ids = set()
    for role in SEARCH["roles"][:3]:
        jobs = await scrape_dice(role)
        for job in jobs:
            if job["id"] not in seen_ids:
                seen_ids.add(job["id"])
                all_jobs.append(job)
        await asyncio.sleep(3)
    return all_jobs


if __name__ == "__main__":
    import asyncio
    jobs = asyncio.run(run_dice_scraper())
    print(f"\nTotal: {len(jobs)}")
    for j in jobs[:5]:
        print(f"  {j['title']} @ {j['company']} — {j['location']}")