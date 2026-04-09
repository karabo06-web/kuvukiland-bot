"""
Kuvukiland Job Bot - RSS Edition
Uses Google News RSS feeds - reliable, no scraping breakage
Posts entry-level jobs & learnerships to Kuvukiland Facebook Page
"""

import os
import re
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
    {
        "url": "https://news.google.com/rss/search?q=learnership+south+africa+2025+OR+2026&hl=en-ZA&gl=ZA&ceid=ZA:en",
        "source": "Google News"
    },
    {
        "url": "https://news.google.com/rss/search?q=learnership+matric+south+africa&hl=en-ZA&gl=ZA&ceid=ZA:en",
        "source": "Google News"
    },
    {
        "url": "https://news.google.com/rss/search?q=entry+level+jobs+south+africa+no+experience&hl=en-ZA&gl=ZA&ceid=ZA:en",
        "source": "Google News"
    },
    {
        "url": "https://news.google.com/rss/search?q=government+vacancies+south+africa+grade+12&hl=en-ZA&gl=ZA&ceid=ZA:en",
        "source": "Google News"
    },
    {
        "url": "https://news.google.com/rss/search?q=SETA+learnership+2025+OR+2026+apply&hl=en-ZA&gl=ZA&ceid=ZA:en",
        "source": "Google News"
    },
    {
        "url": "https://news.google.com/rss/search?q=internship+south+africa+matric+2026&hl=en-ZA&gl=ZA&ceid=ZA:en",
        "source": "Google News"
    },
]

# ── Filters ───────────────────────────────────────────────────────────────────
GOOD_KEYWORDS = [
    "learnership", "internship", "entry level", "entry-level",
    "grade 12", "matric", "no experience", "no degree", "nqf",
    "trainee", "apprentice", "youth", "school leaver", "junior",
    "clerk", "assistant", "general worker", "operator", "vacancies",
    "apply now", "2025", "2026", "south africa", "gauteng",
]

BAD_KEYWORDS = [
    "honours required", "masters required", "phd", "postgraduate",
    "10 years", "8 years", "7 years", "6 years", "5 years experience",
    "executive", "head of department", "chief ", "director",
]

def is_relevant(title, summary=""):
    text = (title + " " + summary).lower()
    has_good = any(kw in text for kw in GOOD_KEYWORDS)
    has_bad  = any(kw in text for kw in BAD_KEYWORDS)
    return has_good and not has_bad

# ── RSS Parser ────────────────────────────────────────────────────────────────
def fetch_rss(feed):
    listings = []
    try:
        r = requests.get(feed["url"], headers=HEADERS, timeout=20)
        root = ET.fromstring(r.content)
        items = root.findall(".//item")
        for item in items[:10]:
            title_el = item.find("title")
            link_el  = item.find("link")
            desc_el  = item.find("description")

            title   = unescape(title_el.text.strip()) if title_el is not None and title_el.text else ""
            link    = link_el.text.strip() if link_el is not None and link_el.text else ""
            summary = unescape(desc_el.text.strip()) if desc_el is not None and desc_el.text else ""

            summary = re.sub(r"<[^>]+>", "", summary)
            title = re.sub(r"\s*-\s*[^-]+$", "", title).strip()

            if title and link and is_relevant(title, summary):
                listings.append({
                    "title": title[:120],
                    "link": link,
                    "source": feed["source"],
                })
    except Exception as e:
        print(f"  RSS error: {e}")
    return listings

# ── Post Builder ──────────────────────────────────────────────────────────────
EMOJIS = ["🌟", "🚀", "💼", "📢", "🎯", "✅", "🔥", "👊", "💪", "🙌"]

def build_post(listings):
    today = datetime.now().strftime("%d %B %Y")
    header = (
        f"📣 YOUTH OPPORTUNITIES — {today}\n"
        f"{'='*38}\n"
        f"✔ Grade 12 / Matric holders\n"
        f"✔ No degree needed\n"
        f"✔ No experience required\n\n"
    )
    body = ""
    for i, job in enumerate(listings[:8], 1):
        emoji = EMOJIS[i % len(EMOJIS)]
        body += f"{emoji} {job['title']}\n"
        body += f"   🔗 {job['link']}\n\n"

    footer = (
        "─"*38 + "\n"
        "💡 Share this post — help a young person!\n"
        "👉 Follow Kuvukiland for daily opportunities\n\n"
        "#Learnership #EntryLevel #Grade12Jobs #YouthEmployment "
        "#SouthAfrica #Matric #NoExperience #KuvukilandJobs "
        "#Internship #GovernmentJobs #SETA"
    )
    return header + body + footer

# ── Facebook Poster ───────────────────────────────────────────────────────────
def post_to_facebook(message):
    if not PAGE_TOKEN:
        print("❌ FB_PAGE_TOKEN not set.")
        return False
    payload = {"message": message, "access_token": PAGE_TOKEN}
    try:
        r = requests.post(GRAPH_URL, data=payload, timeout=20)
        result = r.json()
        if "id" in result:
            print(f"✅ Posted! Post ID: {result['id']}")
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
    print("Fetching opportunities via RSS...\n")

    all_listings = []
    for feed in RSS_FEEDS:
        results = fetch_rss(feed)
        print(f"  Feed: {len(results)} found")
        all_listings.extend(results)
        time.sleep(1.5)

    seen, unique = set(), []
    for j in all_listings:
        key = j["title"][:50].lower()
        if key not in seen:
            seen.add(key)
            unique.append(j)

    print(f"\n✅ Unique relevant listings: {len(unique)}")

    if not unique:
        print("⚠️  No listings found. Posting fallback with direct links.")
        message = (
            f"📣 YOUTH OPPORTUNITIES — {datetime.now().strftime('%d %B %Y')}\n"
            "======================================\n"
            "✔ Grade 12 / Matric | No degree | No experience\n\n"
            "🌟 Check these sites daily for fresh opportunities:\n\n"
            "🔗 SA Youth: https://www.sayouth.mobi\n"
            "🔗 Careers Portal: https://www.careersportal.co.za/learnerships\n"
            "🔗 Indeed SA: https://za.indeed.com/jobs?q=learnership\n"
            "🔗 DPSA Vacancies: https://www.dpsa.gov.za\n"
            "🔗 PNet: https://www.pnet.co.za\n\n"
            "--------------------------------------\n"
            "💡 Share — help a young person find work!\n"
            "#Learnership #Grade12Jobs #YouthEmployment #SouthAfrica"
        )
        post_to_facebook(message)
        return

    post = build_post(unique)
    print("\n📝 Post preview (first 500 chars):\n")
    print(post[:500])
    print("\n📤 Posting to Facebook...")
    post_to_facebook(post)

if __name__ == "__main__":
    main()
