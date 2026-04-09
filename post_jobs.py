"""
Kuvukiland Job Bot - One Post Per Job
Posts each opportunity as a separate Facebook post
Scheduled to run multiple times per day via GitHub Actions
"""

import os
import re
import json
import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from html import unescape

# ── Config ────────────────────────────────────────────────────────────────────
PAGE_ID    = os.environ.get("FB_PAGE_ID", "1158789827307547")
PAGE_TOKEN = os.environ.get("FB_PAGE_TOKEN", "")
GRAPH_URL  = f"https://graph.facebook.com/v25.0/{PAGE_ID}/feed"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# ── RSS Sources ───────────────────────────────────────────────────────────────
RSS_FEEDS = [
    "https://news.google.com/rss/search?q=learnership+south+africa+2026&hl=en-ZA&gl=ZA&ceid=ZA:en",
    "https://news.google.com/rss/search?q=learnership+matric+south+africa&hl=en-ZA&gl=ZA&ceid=ZA:en",
    "https://news.google.com/rss/search?q=entry+level+jobs+south+africa+no+experience&hl=en-ZA&gl=ZA&ceid=ZA:en",
    "https://news.google.com/rss/search?q=government+vacancies+south+africa+grade+12&hl=en-ZA&gl=ZA&ceid=ZA:en",
    "https://news.google.com/rss/search?q=SETA+learnership+2026+apply&hl=en-ZA&gl=ZA&ceid=ZA:en",
    "https://news.google.com/rss/search?q=internship+south+africa+matric+2026&hl=en-ZA&gl=ZA&ceid=ZA:en",
]

GOOD_KEYWORDS = [
    "learnership", "internship", "entry level", "entry-level",
    "grade 12", "matric", "no experience", "no degree", "nqf",
    "trainee", "apprentice", "youth", "school leaver", "junior",
    "clerk", "assistant", "general worker", "vacancies", "2026",
]

BAD_KEYWORDS = [
    "honours required", "masters", "phd", "postgraduate",
    "5 years experience", "executive", "head of", "director",
]

EMOJIS = ["🌟", "🚀", "💼", "📢", "🎯", "✅", "🔥", "👊", "💪", "🙌",
          "🎉", "📌", "👉", "💡", "🏆", "🌍", "📣", "🤝", "🎓", "💰"]

def is_relevant(title, summary=""):
    text = (title + " " + summary).lower()
    return any(kw in text for kw in GOOD_KEYWORDS) and not any(kw in text for kw in BAD_KEYWORDS)

def fetch_all_listings():
    all_listings = []
    for url in RSS_FEEDS:
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            root = ET.fromstring(r.content)
            for item in root.findall(".//item")[:8]:
                title_el = item.find("title")
                link_el  = item.find("link")
                desc_el  = item.find("description")
                title   = unescape(title_el.text.strip()) if title_el is not None and title_el.text else ""
                link    = link_el.text.strip() if link_el is not None and link_el.text else ""
                summary = unescape(desc_el.text.strip()) if desc_el is not None and desc_el.text else ""
                summary = re.sub(r"<[^>]+>", "", summary)
                title   = re.sub(r"\s*-\s*[^-]+$", "", title).strip()
                if title and link and is_relevant(title, summary):
                    all_listings.append({"title": title[:120], "link": link})
            time.sleep(1)
        except Exception as e:
            print(f"  Feed error: {e}")

    # Deduplicate
    seen, unique = set(), []
    for j in all_listings:
        key = j["title"][:50].lower()
        if key not in seen:
            seen.add(key)
            unique.append(j)
    return unique

def build_single_post(job, index):
    emoji = EMOJIS[index % len(EMOJIS)]
    today = datetime.now().strftime("%d %B %Y")
    return (
        f"{emoji} OPPORTUNITY ALERT — {today}\n"
        f"{'='*38}\n"
        f"✔ Grade 12 / Matric\n"
        f"✔ No degree needed\n"
        f"✔ No experience required\n\n"
        f"📋 {job['title']}\n\n"
        f"🔗 Apply / Read more:\n{job['link']}\n\n"
        f"{'─'*38}\n"
        f"💡 Share this — help a young person!\n"
        f"👉 Follow Kuvukiland for daily opportunities\n\n"
        f"#Learnership #EntryLevel #Grade12Jobs #YouthEmployment "
        f"#SouthAfrica #Matric #NoExperience #KuvukilandJobs"
    )

def post_to_facebook(message):
    if not PAGE_TOKEN:
        print("❌ FB_PAGE_TOKEN not set.")
        return False
    payload = {"message": message, "access_token": PAGE_TOKEN}
    try:
        r = requests.post(GRAPH_URL, data=payload, timeout=20)
        result = r.json()
        if "id" in result:
            print(f"  ✅ Posted! ID: {result['id']}")
            return True
        else:
            print(f"  ❌ Failed: {result}")
            return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    print(f"\n🤖 Kuvukiland Job Bot — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("Fetching listings...\n")

    listings = fetch_all_listings()
    print(f"Found {len(listings)} relevant listings\n")

    if not listings:
        print("⚠️ No listings found this run.")
        return

    # Post only 1 listing per run (GitHub Actions runs every 30 min)
    job = listings[0]
    index = int(datetime.now().strftime("%H")) + int(datetime.now().strftime("%M"))
    post = build_single_post(job, index)
    print(f"📤 Posting: {job['title'][:60]}...")
    post_to_facebook(post)

if __name__ == "__main__":
    main()
