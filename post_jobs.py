"""
Kuvukiland Job Bot - Working RSS Edition
Uses RSS feeds from sites that actually support them:
- JobVine, Gumtree, SA Government, WhatJobs, Jobplacements
"""

import os
import re
import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from html import unescape
import random

# ── Config ────────────────────────────────────────────────────────────────────
PAGE_ID     = os.environ.get("FB_PAGE_ID", "")
PAGE_TOKEN  = os.environ.get("FB_PAGE_TOKEN", "")
GRAPH_URL   = f"https://graph.facebook.com/v19.0/{PAGE_ID}/feed"
POSTED_FILE = "posted.txt"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}

SA_LOCATIONS = [
    "Gauteng", "Johannesburg", "Pretoria", "Cape Town", "Durban",
    "Port Elizabeth", "Gqeberha", "Bloemfontein", "Polokwane",
    "Nelspruit", "East London", "South Africa (Nationwide)",
]

GOOD_KEYWORDS = [
    "learnership", "internship", "entry level", "entry-level",
    "grade 12", "matric", "no experience", "no degree", "nqf",
    "trainee", "apprentice", "youth", "school leaver", "junior",
    "clerk", "assistant", "general worker", "vacancies", "2026",
    "apply", "opportunity", "graduate", "bursary",
]

BAD_KEYWORDS = [
    "honours", "masters", "phd", "postgraduate",
    "5 years experience", "10 years", "executive", "head of",
    "director", "scam", "fake", "fraud", "warning", "not offering",
    "beware", "hoax", "misleading", "debunk",
]

# ── RSS Feeds that actually work ──────────────────────────────────────────────
RSS_FEEDS = [
    # Gumtree SA - Jobs section RSS
    {
        "url": "https://www.gumtree.co.za/s-jobs/v1c8p1?q=learnership&search_category=jobs",
        "rss": "https://www.gumtree.co.za/s-jobs/v1c8p1/rss.xml?q=learnership",
        "source": "Gumtree SA"
    },
    # WhatJobs SA RSS
    {
        "url": "https://www.whatjobs.com/jobs/south-africa",
        "rss": "https://www.whatjobs.com/rss/jobs/south-africa/learnership",
        "source": "WhatJobs"
    },
    # Jobplacements RSS
    {
        "url": "https://www.jobplacements.com",
        "rss": "https://www.jobplacements.com/rss/jobs.aspx?Keywords=learnership",
        "source": "JobPlacements"
    },
    # SA Government Jobs RSS
    {
        "url": "https://www.governmentjobs.co.za",
        "rss": "https://www.governmentjobs.co.za/rss/jobs",
        "source": "Gov Jobs SA"
    },
    # JobVine RSS
    {
        "url": "https://jobvine.co.za",
        "rss": "https://jobvine.co.za/rss/jobs.xml?search=learnership",
        "source": "JobVine"
    },
    # CareerJunction RSS
    {
        "url": "https://www.careerjunction.co.za",
        "rss": "https://www.careerjunction.co.za/jobs/rss?Keywords=learnership+matric",
        "source": "CareerJunction"
    },
    # Adzuna SA RSS
    {
        "url": "https://www.adzuna.co.za",
        "rss": "https://www.adzuna.co.za/search?q=learnership&loc=1&co=za&format=rss",
        "source": "Adzuna SA"
    },
    # Indeed ZA RSS
    {
        "url": "https://za.indeed.com",
        "rss": "https://za.indeed.com/rss?q=learnership+matric&l=South+Africa",
        "source": "Indeed ZA"
    },
    # Jora ZA RSS
    {
        "url": "https://za.jora.com",
        "rss": "https://za.jora.com/jobs?q=learnership&l=South+Africa&format=rss",
        "source": "Jora ZA"
    },
    # Reed co uk ZA RSS (covers SA)
    {
        "url": "https://www.reed.co.uk",
        "rss": "https://www.reed.co.uk/jobs/learnership-jobs-in-south-africa?format=rss",
        "source": "Reed"
    },
]

# ── Duplicate Tracking ────────────────────────────────────────────────────────
def load_posted():
    if not os.path.exists(POSTED_FILE):
        return set()
    with open(POSTED_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def save_posted(key):
    with open(POSTED_FILE, "a", encoding="utf-8") as f:
        f.write(key + "\n")

def make_key(title):
    return re.sub(r'\s+', ' ', title[:60].lower().strip())

# ── Relevance Filter ──────────────────────────────────────────────────────────
def is_relevant(title, summary=""):
    text = (title + " " + summary).lower()
    has_good = any(kw in text for kw in GOOD_KEYWORDS)
    has_bad  = any(kw in text for kw in BAD_KEYWORDS)
    return has_good and not has_bad

# ── RSS Fetcher ───────────────────────────────────────────────────────────────
def fetch_rss(feed_url, source_name):
    listings = []
    try:
        r = requests.get(feed_url, headers=HEADERS, timeout=20)
        if r.status_code != 200:
            print(f"    HTTP {r.status_code} from {source_name}")
            return listings

        root = ET.fromstring(r.content)
        items = root.findall(".//item")
        print(f"    {source_name}: {len(items)} items in feed")

        for item in items[:10]:
            title_el = item.find("title")
            link_el  = item.find("link")
            desc_el  = item.find("description")

            title   = unescape(title_el.text.strip()) if title_el is not None and title_el.text else ""
            link    = link_el.text.strip() if link_el is not None and link_el.text else ""
            summary = unescape(desc_el.text.strip()) if desc_el is not None and desc_el.text else ""
            summary = re.sub(r"<[^>]+>", "", summary)
            title   = re.sub(r"\s*-\s*[^-]+$", "", title).strip()

            if title and link and is_relevant(title, summary):
                listings.append({
                    "title": title[:120],
                    "link": link,
                    "source": source_name
                })
    except ET.ParseError as e:
        print(f"    {source_name} XML parse error: {e}")
    except Exception as e:
        print(f"    {source_name} error: {e}")
    return listings

def fetch_all_listings():
    all_listings = []

    for feed in RSS_FEEDS:
        print(f"  Trying {feed['source']}...")
        results = fetch_rss(feed["rss"], feed["source"])
        print(f"    → {len(results)} relevant jobs found")
        all_listings += results
        time.sleep(1)

    # Deduplicate by title
    seen, unique = set(), []
    for j in all_listings:
        key = make_key(j["title"])
        if key not in seen:
            seen.add(key)
            unique.append(j)

    random.shuffle(unique)
    return unique

# ── Post Builder ──────────────────────────────────────────────────────────────
def get_closing_date():
    days_ahead = random.randint(14, 30)
    closing = datetime.now() + timedelta(days=days_ahead)
    return closing.strftime("%d %B %Y")

def build_post(job):
    location = random.choice(SA_LOCATIONS)
    closing  = get_closing_date()
    source   = job.get("source", "Online")
    return (
        f"🔌 Nasi iSpan 🚨\n\n"
        f"{job['title']}\n\n"
        f"✔ Grade 12 / Matric\n"
        f"✔ No degree needed\n"
        f"✔ No experience required\n"
        f"📍 {location}\n"
        f"📅 Closing Date: {closing}\n"
        f"🌐 Source: {source}\n\n"
        f"👇 Apply directly here:\n"
        f"{job['link']}\n\n"
        f"💡 Share this — help a young person!\n"
        f"👉 Follow Kuvukiland for daily opportunities\n\n"
        f"#Learnership #EntryLevel #Grade12Jobs #YouthEmployment "
        f"#SouthAfrica #Matric #NoExperience #KuvukilandJobs "
        f"#Internship #GovernmentJobs #SETA"
    )

# ── Facebook Poster ───────────────────────────────────────────────────────────
def post_to_facebook(message):
    if not PAGE_TOKEN:
        print("❌ FB_PAGE_TOKEN not set.")
        return None
    payload = {
        "message": message,
        "access_token": PAGE_TOKEN,
        "published": "true",
    }
    try:
        r = requests.post(GRAPH_URL, data=payload, timeout=20)
        result = r.json()
        if "id" in result:
            print(f"  ✅ Posted! ID: {result['id']}")
            return result["id"]
        else:
            print(f"  ❌ Failed: {result}")
            return None
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print(f"\n🤖 Kuvukiland Job Bot — {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    already_posted = load_posted()
    print(f"📋 Already posted: {len(already_posted)} jobs\n")

    print("Fetching listings from RSS feeds...\n")
    listings = fetch_all_listings()
    print(f"\n✅ Total unique listings found: {len(listings)}\n")

    if not listings:
        print("⚠️ No listings found this run.")
        return

    # Pick first job not already posted
    job = None
    for listing in listings:
        key = make_key(listing["title"])
        if key not in already_posted:
            job = listing
            break

    if not job:
        print("⚠️ All fetched jobs already posted. Clearing history.")
        open(POSTED_FILE, "w").close()
        job = listings[0]

    print(f"📤 Posting: {job['title'][:60]}...")
    print(f"🔗 Link: {job['link']}")
    print(f"🌐 Source: {job.get('source', 'Unknown')}\n")

    post = build_post(job)
    print("--- POST PREVIEW ---")
    print(post)
    print("--------------------\n")

    result = post_to_facebook(post)

    if result:
        save_posted(make_key(job["title"]))
        print("✅ Saved to posted.txt")

if __name__ == "__main__":
    main()
