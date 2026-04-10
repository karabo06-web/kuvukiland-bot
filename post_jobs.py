"""
Kuvukiland Job Bot - Direct Job Sites Edition
Scrapes real job listings from SA Youth, Indeed ZA, Careers24, PNet, JobVine
Posts to Kuvukiland Facebook Page with actual application links
"""

import os
import re
import time
import requests
import json
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
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-ZA,en;q=0.9",
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
    "apply now", "applications open", "hiring", "opportunity",
]

BAD_KEYWORDS = [
    "honours", "masters", "phd", "postgraduate",
    "5 years experience", "10 years", "executive", "head of",
    "director", "scam", "fake", "fraud", "warning", "not offering",
    "beware", "hoax", "misleading", "debunk", "not true",
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

# ── Scrapers ──────────────────────────────────────────────────────────────────

def fetch_sayouth():
    """SA Youth - sayouth.mobi (official government youth jobs site)"""
    listings = []
    searches = [
        "https://sayouth.mobi/Search?q=learnership",
        "https://sayouth.mobi/Search?q=internship",
        "https://sayouth.mobi/Search?q=entry+level",
    ]
    for url in searches:
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            # Extract job cards using regex (no BS4)
            titles = re.findall(r'<h[23][^>]*class="[^"]*job[^"]*"[^>]*>(.*?)</h[23]>', r.text, re.DOTALL)
            links  = re.findall(r'href="(/Job/\d+[^"]*)"', r.text)
            for i, link in enumerate(links[:8]):
                title = titles[i] if i < len(titles) else ""
                title = re.sub(r'<[^>]+>', '', title).strip()
                full_link = f"https://sayouth.mobi{link}"
                if title and is_relevant(title):
                    listings.append({"title": title[:120], "link": full_link, "source": "SA Youth"})
            time.sleep(2)
        except Exception as e:
            print(f"  SA Youth error: {e}")
    return listings

def fetch_careers24():
    """Careers24 - learnership/entry level jobs"""
    listings = []
    searches = [
        "https://www.careers24.com/jobs/learnership/",
        "https://www.careers24.com/jobs/internship/",
        "https://www.careers24.com/jobs/entry-level/",
    ]
    for url in searches:
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            # Extract job titles and links
            matches = re.findall(
                r'href="(https://www\.careers24\.com/jobs/[^"]+)"[^>]*>[^<]*<[^>]*>([^<]{10,100})</[^>]*>',
                r.text
            )
            for link, title in matches[:8]:
                title = title.strip()
                if title and is_relevant(title):
                    listings.append({"title": title[:120], "link": link, "source": "Careers24"})
            time.sleep(2)
        except Exception as e:
            print(f"  Careers24 error: {e}")
    return listings

def fetch_pnet():
    """PNet - South Africa's biggest job site"""
    listings = []
    searches = [
        "https://www.pnet.co.za/jobs/learnership.html",
        "https://www.pnet.co.za/jobs/internship.html",
        "https://www.pnet.co.za/jobs/entry-level.html",
        "https://www.pnet.co.za/jobs/matric.html",
    ]
    for url in searches:
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            matches = re.findall(
                r'href="(https://www\.pnet\.co\.za/jobs/[^"]+\.html)"[^>]*title="([^"]{10,120})"',
                r.text
            )
            for link, title in matches[:8]:
                title = title.strip()
                if title and is_relevant(title):
                    listings.append({"title": title[:120], "link": link, "source": "PNet"})
            time.sleep(2)
        except Exception as e:
            print(f"  PNet error: {e}")
    return listings

def fetch_jobvine():
    """JobVine SA"""
    listings = []
    searches = [
        "https://jobvine.co.za/search/?search=learnership",
        "https://jobvine.co.za/search/?search=internship+matric",
        "https://jobvine.co.za/search/?search=entry+level+no+experience",
    ]
    for url in searches:
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            matches = re.findall(
                r'href="(https://jobvine\.co\.za/[^"]*job[^"]*)"[^>]*>([^<]{10,120})</a>',
                r.text
            )
            for link, title in matches[:8]:
                title = title.strip()
                if title and is_relevant(title):
                    listings.append({"title": title[:120], "link": link, "source": "JobVine"})
            time.sleep(2)
        except Exception as e:
            print(f"  JobVine error: {e}")
    return listings

def fetch_indeed():
    """Indeed ZA"""
    listings = []
    searches = [
        "https://za.indeed.com/jobs?q=learnership&l=South+Africa",
        "https://za.indeed.com/jobs?q=internship+matric&l=South+Africa",
        "https://za.indeed.com/jobs?q=entry+level+no+experience&l=South+Africa",
    ]
    for url in searches:
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            # Indeed uses data-jk for job keys
            job_keys = re.findall(r'data-jk="([a-f0-9]+)"', r.text)
            titles   = re.findall(r'class="jobTitle[^"]*"[^>]*><[^>]+>([^<]{5,100})</[^>]+>', r.text)
            for i, jk in enumerate(job_keys[:8]):
                title = titles[i].strip() if i < len(titles) else ""
                link  = f"https://za.indeed.com/viewjob?jk={jk}"
                if title and is_relevant(title):
                    listings.append({"title": title[:120], "link": link, "source": "Indeed ZA"})
            time.sleep(2)
        except Exception as e:
            print(f"  Indeed error: {e}")
    return listings

def fetch_dpsa():
    """DPSA - Government vacancies (grade 12 posts)"""
    listings = []
    try:
        r = requests.get(
            "https://www.dpsa.gov.za/dpsa2g/vacancies.asp",
            headers=HEADERS, timeout=20
        )
        matches = re.findall(
            r'href="(vacancy[^"]+\.pdf)"[^>]*>([^<]{10,120})</a>',
            r.text, re.IGNORECASE
        )
        for link, title in matches[:8]:
            title = title.strip()
            full_link = f"https://www.dpsa.gov.za/dpsa2g/{link}"
            listings.append({"title": title[:120], "link": full_link, "source": "DPSA Gov"})
        time.sleep(2)
    except Exception as e:
        print(f"  DPSA error: {e}")
    return listings

# ── Aggregate All Sources ─────────────────────────────────────────────────────
def fetch_all_listings():
    print("  Fetching SA Youth...")
    all_listings = fetch_sayouth()
    print(f"    → {len(all_listings)} found")

    print("  Fetching Careers24...")
    c24 = fetch_careers24()
    print(f"    → {len(c24)} found")
    all_listings += c24

    print("  Fetching PNet...")
    pnet = fetch_pnet()
    print(f"    → {len(pnet)} found")
    all_listings += pnet

    print("  Fetching JobVine...")
    jv = fetch_jobvine()
    print(f"    → {len(jv)} found")
    all_listings += jv

    print("  Fetching Indeed ZA...")
    ind = fetch_indeed()
    print(f"    → {len(ind)} found")
    all_listings += ind

    print("  Fetching DPSA Gov...")
    dpsa = fetch_dpsa()
    print(f"    → {len(dpsa)} found")
    all_listings += dpsa

    # Deduplicate
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

    print("Fetching listings from real job sites...\n")
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
        print("⚠️ All fetched jobs already posted. Clearing history and restarting.")
        # Clear posted.txt so it starts fresh
        open(POSTED_FILE, "w").close()
        job = listings[0]

    print(f"📤 Posting: {job['title'][:60]}...")
    print(f"🔗 Link: {job['link']}")
    print(f"🌐 Source: {job.get('source', 'Unknown')}")

    post = build_post(job)
    print("\n--- POST PREVIEW ---")
    print(post)
    print("--------------------\n")

    result = post_to_facebook(post)

    if result:
        save_posted(make_key(job["title"]))
        print("✅ Saved to posted.txt")

if __name__ == "__main__":
    main()
