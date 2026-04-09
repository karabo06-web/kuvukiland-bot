"""
Kuvukiland Job Bot
Scrapes entry-level learnerships & jobs for Grade 12 / no degree youth in SA
Posts automatically to the Kuvukiland Facebook Page
"""

import os
import re
import json
import time
import random
import requests
from datetime import datetime
from bs4 import BeautifulSoup

# ── Config ────────────────────────────────────────────────────────────────────
PAGE_ID       = os.environ.get("FB_PAGE_ID", "1158789827307547")
PAGE_TOKEN    = os.environ.get("FB_PAGE_TOKEN", "")   # set as GitHub secret
GRAPH_URL     = f"https://graph.facebook.com/v25.0/{PAGE_ID}/feed"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# Keywords that confirm entry-level / no-degree suitability
INCLUDE_KEYWORDS = [
    "learnership", "internship", "entry level", "entry-level",
    "grade 12", "matric", "no experience", "no degree",
    "abet", "nqf level 2", "nqf level 3", "nqf level 4",
    "trainee", "apprentice", "youth", "graduate programme",
    "school leavers", "school leaver",
]

# Keywords that disqualify a listing
EXCLUDE_KEYWORDS = [
    "degree required", "b.tech", "btech", "bsc", "ba ", "b.com",
    "honours", "masters", "phd", "postgraduate",
    "5 years experience", "3 years experience", "2 years experience",
    "minimum 2", "minimum 3", "minimum 5",
]

# ── Scrapers ──────────────────────────────────────────────────────────────────

def scrape_sayouth():
    """SA Youth (sayouth.mobi) — learnerships & entry-level"""
    listings = []
    urls = [
        "https://www.sayouth.mobi/Opportunities/Learnerships",
        "https://www.sayouth.mobi/Opportunities/Internships",
    ]
    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")
            cards = soup.select(".opportunity-card, .card, article")
            for card in cards[:5]:
                title = card.get_text(separator=" ", strip=True)[:120]
                link_tag = card.find("a", href=True)
                link = "https://www.sayouth.mobi" + link_tag["href"] if link_tag else url
                if title:
                    listings.append({"title": title, "link": link, "source": "SA Youth"})
        except Exception as e:
            print(f"SAYouth error: {e}")
    return listings


def scrape_careers24():
    """Careers24 — entry-level matric jobs"""
    listings = []
    url = (
        "https://www.careers24.com/jobs/entry+level+matric/"
        "?applyfilter=1&isAdvancedSearch=1"
    )
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        jobs = soup.select(".job-card, .listing-item, article.job")
        for job in jobs[:6]:
            title_el = job.select_one("h2, h3, .job-title, a")
            link_el  = job.find("a", href=True)
            title = title_el.get_text(strip=True) if title_el else ""
            link  = link_el["href"] if link_el else url
            if not link.startswith("http"):
                link = "https://www.careers24.com" + link
            if title:
                listings.append({"title": title, "link": link, "source": "Careers24"})
    except Exception as e:
        print(f"Careers24 error: {e}")
    return listings


def scrape_pnet():
    """PNet — learnership & entry-level"""
    listings = []
    url = "https://www.pnet.co.za/jobs/learnership-entry-level.html"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        jobs = soup.select("article.job-card, .job-result, .listing")
        for job in jobs[:6]:
            title_el = job.select_one("h2, h3, .title, a")
            link_el  = job.find("a", href=True)
            title = title_el.get_text(strip=True) if title_el else ""
            link  = link_el["href"] if link_el else url
            if not link.startswith("http"):
                link = "https://www.pnet.co.za" + link
            if title:
                listings.append({"title": title, "link": link, "source": "PNet"})
    except Exception as e:
        print(f"PNet error: {e}")
    return listings


def scrape_indeed():
    """Indeed SA — learnerships matric"""
    listings = []
    url = "https://za.indeed.com/jobs?q=learnership+matric&l=South+Africa"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        jobs = soup.select(".job_seen_beacon, .result, .jobsearch-ResultsList li")
        for job in jobs[:6]:
            title_el = job.select_one("h2.jobTitle, h2, h3, a[data-jk]")
            link_el  = job.find("a", href=True)
            title = title_el.get_text(strip=True) if title_el else ""
            link  = "https://za.indeed.com" + link_el["href"] if link_el else url
            if title:
                listings.append({"title": title, "link": link, "source": "Indeed SA"})
    except Exception as e:
        print(f"Indeed error: {e}")
    return listings


def scrape_dpsa():
    """DPSA — Department of Public Service & Administration vacancies"""
    listings = []
    url = "https://www.dpsa.gov.za/dpsa2g/vacancies.asp"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        links = soup.select("a[href]")
        for a in links[:8]:
            title = a.get_text(strip=True)
            href  = a["href"]
            if not href.startswith("http"):
                href = "https://www.dpsa.gov.za" + href
            if len(title) > 10:
                listings.append({"title": title, "link": href, "source": "DPSA Gov"})
    except Exception as e:
        print(f"DPSA error: {e}")
    return listings


def scrape_letsema():
    """Letsema Learnerships aggregator"""
    listings = []
    url = "https://www.letsema.co.za/learnerships/"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        posts = soup.select("article, .post, h2.entry-title, h3.entry-title")
        for post in posts[:6]:
            title_el = post.select_one("h2, h3, a")
            link_el  = post.find("a", href=True)
            title = title_el.get_text(strip=True) if title_el else ""
            link  = link_el["href"] if link_el else url
            if title:
                listings.append({"title": title, "link": link, "source": "Letsema"})
    except Exception as e:
        print(f"Letsema error: {e}")
    return listings


# ── Filter ────────────────────────────────────────────────────────────────────

def is_suitable(listing):
    text = (listing.get("title", "") + " " + listing.get("link", "")).lower()
    has_include = any(kw in text for kw in INCLUDE_KEYWORDS)
    has_exclude = any(kw in text for kw in EXCLUDE_KEYWORDS)
    return has_include and not has_exclude


# ── Post builder ──────────────────────────────────────────────────────────────

EMOJIS = ["🌟", "🚀", "💼", "📢", "🎯", "✅", "🔥", "👊", "💪", "🙌"]

def build_post(listings):
    today = datetime.now().strftime("%d %B %Y")
    header = (
        f"📣 YOUTH OPPORTUNITIES — {today}\n"
        f"{'='*38}\n"
        f"For Grade 12 holders | No degree needed | No experience required\n\n"
    )

    body = ""
    for i, job in enumerate(listings[:8], 1):
        emoji = EMOJIS[i % len(EMOJIS)]
        body += f"{emoji} {job['title']}\n"
        body += f"   🔗 {job['link']}\n"
        body += f"   📌 Source: {job['source']}\n\n"

    footer = (
        "─" * 38 + "\n"
        "💡 Share this post — help a young person find work!\n"
        "👉 Follow Kuvukiland for daily opportunities\n"
        "#Learnership #EntryLevel #Grade12Jobs #YouthEmployment "
        "#SouthAfrica #Matric #NoExperience #KuvukilandJobs"
    )

    return header + body + footer


# ── Facebook poster ───────────────────────────────────────────────────────────

def post_to_facebook(message):
    if not PAGE_TOKEN:
        print("❌ FB_PAGE_TOKEN not set. Skipping post.")
        return False
    payload = {
        "message": message,
        "access_token": PAGE_TOKEN,
    }
    try:
        r = requests.post(GRAPH_URL, data=payload, timeout=20)
        result = r.json()
        if "id" in result:
            print(f"✅ Posted successfully! Post ID: {result['id']}")
            return True
        else:
            print(f"❌ Post failed: {result}")
            return False
    except Exception as e:
        print(f"❌ Facebook API error: {e}")
        return False


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"\n🤖 Kuvukiland Job Bot — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("Scraping opportunities...\n")

    all_listings = []
    scrapers = [
        scrape_sayouth,
        scrape_careers24,
        scrape_pnet,
        scrape_indeed,
        scrape_dpsa,
        scrape_letsema,
    ]

    for scraper in scrapers:
        results = scraper()
        print(f"  {scraper.__name__}: {len(results)} found")
        all_listings.extend(results)
        time.sleep(random.uniform(1.5, 3.0))  # polite delay

    # Filter for suitability
    suitable = [j for j in all_listings if is_suitable(j)]

    # Deduplicate by title
    seen = set()
    unique = []
    for j in suitable:
        key = j["title"][:60].lower()
        if key not in seen:
            seen.add(key)
            unique.append(j)

    print(f"\n✅ Suitable listings found: {len(unique)}")

    if not unique:
        print("⚠️  No suitable listings found today. Using fallback message.")
        unique = [{
            "title": "Multiple learnerships & entry-level posts available — check now",
            "link": "https://www.sayouth.mobi",
            "source": "SA Youth"
        }]

    post = build_post(unique)
    print("\n📝 Post preview:\n")
    print(post)
    print("\n📤 Posting to Facebook...\n")
    post_to_facebook(post)


if __name__ == "__main__":
    main()
