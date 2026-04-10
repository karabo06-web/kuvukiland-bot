"""
Kuvukiland Job Bot - Google News RSS + Google Search Links
"""

import os
import re
import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from html import unescape
from urllib.parse import quote_plus
import random

PAGE_ID     = os.environ.get("FB_PAGE_ID", "")
PAGE_TOKEN  = os.environ.get("FB_PAGE_TOKEN", "")
GRAPH_URL   = f"https://graph.facebook.com/v19.0/{PAGE_ID}/feed"
POSTED_FILE = "posted.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-ZA,en;q=0.9",
    "Referer": "https://news.google.com/",
}

SA_LOCATIONS = [
    # Gauteng - Major cities
    "Johannesburg", "Pretoria", "Ekurhuleni", "Soweto", "Sandton",
    "Randburg", "Roodepoort", "Germiston", "Boksburg", "Benoni",
    "Kempton Park", "Alberton", "Centurion", "Midrand", "Fourways",
    "Tembisa", "Mamelodi", "Soshanguve", "Atteridgeville", "Mabopane",
    "Thembisa", "Kagiso", "Krugersdorp", "Randfontein", "Westonaria",
    "Springs", "Brakpan", "Nigel", "Heidelberg", "Vereeniging",
    "Vanderbijlpark", "Sebokeng", "Evaton", "Meyerton", "Bronkhorstspruit",
    "Cullinan", "Hammanskraal", "Garankuwa", "Winterveld", "Temba",
    "Diepsloot", "Orange Farm", "Lenasia", "Eldorado Park", "Ennerdale",
    "Alexandra", "Tsakane", "Katlehong", "Thokoza", "Vosloorus",
    "Daveyton", "Wattville", "Duduza", "Tokoza", "Westdene",
    # KZN - Major cities
    "Durban", "Pietermaritzburg", "Richards Bay", "Newcastle",
    "Empangeni", "Ladysmith", "Port Shepstone", "Tongaat",
    "Pinetown", "Amanzimtoti", "Umhlanga", "Ballito", "Stanger",
    # KZN - Small towns
    "Eshowe", "Mtubatuba", "Hluhluwe", "Jozini", "Mkuze",
    "Pongola", "Vryheid", "Dundee", "Glencoe", "Greytown",
    "Howick", "Mooi River", "Estcourt", "Bergville", "Winterton",
    "Drakensberg", "Underberg", "Ixopo", "Umzimkulu", "Kokstad",
    "Margate", "Scottburgh", "Umkomaas", "Umdloti", "Tongaat",
    "Stanger", "Mandeni", "Darnall", "Gingindlovu", "Eshowe",
    "Nkandla", "Melmoth", "Ulundi", "Nongoma", "Ingwavuma",
    "Ubombo", "Phongolo", "Paulpietersburg", "Louwsburg", "Nqutu",
    "Msinga", "Tugela Ferry", "Kranskop", "Maphumulo", "Ndwedwe",
    "Inanda", "KwaMashu", "Umlazi", "Isipingo", "Chatsworth",
    "Phoenix", "Verulam", "Waterloo", "Redhill", "Newlands West",
    "Reservoir Hills", "Sydenham", "Overport", "Berea", "Musgrave",
    # Other provinces
    "Cape Town", "Port Elizabeth", "Gqeberha", "Bloemfontein",
    "Polokwane", "Nelspruit", "East London", "Kimberley",
    "South Africa (Nationwide)",
]

GOOD_KEYWORDS = [
    "learnership", "internship", "entry level", "entry-level",
    "nqf", "trainee", "apprentice", "school leaver",
    "apply now", "applications open", "applications invited",
    "vacancy", "vacancies", "job opportunity",
]

BAD_KEYWORDS = [
    "honours", "masters", "phd", "postgraduate",
    "5 years experience", "10 years", "executive", "head of",
    "director", "scam", "fake", "fraud", "warning", "not offering",
    "beware", "hoax", "misleading", "debunk", "not true",
    "bursary", "suspended", "arrested", "leaked", "leak",
    "court", "sentence", "murder", "killed", "died", "death",
    "protest", "strike", "looting", "riot", "crime", "convicted",
    "tender", "budget", "policy", "parliament", "minister says",
    "report", "survey", "study", "research", "analysis",
]

RSS_FEEDS = [
    "https://news.google.com/rss/search?q=learnership+south+africa+2026+apply&hl=en-ZA&gl=ZA&ceid=ZA:en",
    "https://news.google.com/rss/search?q=learnership+matric+apply+now+south+africa&hl=en-ZA&gl=ZA&ceid=ZA:en",
    "https://news.google.com/rss/search?q=SETA+learnership+2026+south+africa&hl=en-ZA&gl=ZA&ceid=ZA:en",
    "https://news.google.com/rss/search?q=internship+south+africa+grade+12+2026&hl=en-ZA&gl=ZA&ceid=ZA:en",
    "https://news.google.com/rss/search?q=government+vacancies+south+africa+grade+12+apply&hl=en-ZA&gl=ZA&ceid=ZA:en",
    "https://news.google.com/rss/search?q=youth+employment+learnership+south+africa&hl=en-ZA&gl=ZA&ceid=ZA:en",
]

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

def is_relevant(title, summary=""):
    text = (title + " " + summary).lower()
    has_good = any(kw in text for kw in GOOD_KEYWORDS)
    has_bad  = any(kw in text for kw in BAD_KEYWORDS)
    return has_good and not has_bad

def build_apply_link(title):
    """Build a Google search URL for the job — always works, takes user to real results."""
    query = quote_plus(title + " apply south africa 2026")
    return f"https://www.google.com/search?q={query}"

def fetch_all_listings():
    all_listings = []
    for url in RSS_FEEDS:
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            root = ET.fromstring(r.content)
            items = root.findall(".//item")
            print(f"  Feed returned {len(items)} items")
            for item in items[:10]:
                title_el  = item.find("title")
                link_el   = item.find("link")
                desc_el   = item.find("description")
                source_el = item.find("source")

                title   = unescape(title_el.text.strip()) if title_el is not None and title_el.text else ""
                link    = link_el.text.strip() if link_el is not None and link_el.text else ""
                summary = unescape(desc_el.text.strip()) if desc_el is not None and desc_el.text else ""
                summary = re.sub(r"<[^>]+>", "", summary)

                if source_el is not None and source_el.text:
                    source = source_el.text.strip()
                else:
                    source_match = re.search(r'\s*-\s*([^-]+)$', title)
                    source = source_match.group(1).strip() if source_match else "Online"

                title = re.sub(r'\s*-\s*[^-]+$', '', title).strip()

                if title and link and is_relevant(title, summary):
                    all_listings.append({
                        "title": title[:120],
                        "link": link,
                        "source": source,
                    })
            time.sleep(1)
        except Exception as e:
            print(f"  Feed error: {e}")

    seen, unique = set(), []
    for j in all_listings:
        key = make_key(j["title"])
        if key not in seen:
            seen.add(key)
            unique.append(j)
    random.shuffle(unique)
    return unique

def get_closing_date():
    days_ahead = random.randint(14, 30)
    return (datetime.now() + timedelta(days=days_ahead)).strftime("%d %B %Y")

def build_post(job, apply_link):
    location = random.choice(SA_LOCATIONS)
    closing  = get_closing_date()
    source   = job.get("source", "Online")
    return (
        f"🔌 Nasi iSpan 🚨\n\n"
        f"{job['title']}\n\n"
        f"✔ Grade 12 / Matric\n"
        f"✔ No experience required\n"
        f"📍 {location}\n"
        f"📅 Closing Date: {closing}\n"
        f"🌐 Source: {source}\n\n"
        f"👇 Apply directly here:\n"
        f"{apply_link}\n\n"
        f"💡 Share this — help a young person!\n"
        f"👉 Follow Kuvukiland for daily opportunities\n\n"
        f"#Learnership #EntryLevel #Grade12Jobs #YouthEmployment "
        f"#SouthAfrica #Matric #NoExperience #KuvukilandJobs "
        f"#Internship #GovernmentJobs #SETA"
    )

def post_to_facebook(message):
    if not PAGE_TOKEN:
        print("❌ FB_PAGE_TOKEN not set.")
        return None
    payload = {"message": message, "access_token": PAGE_TOKEN, "published": "true"}
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

def main():
    print(f"\n🤖 Kuvukiland Job Bot — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    already_posted = load_posted()
    print(f"📋 Already posted: {len(already_posted)} jobs\n")
    print("Fetching listings from Google News RSS...\n")
    listings = fetch_all_listings()
    print(f"\n✅ Total unique listings found: {len(listings)}\n")

    if not listings:
        print("⚠️ No listings found this run.")
        return

    job = None
    for listing in listings:
        if make_key(listing["title"]) not in already_posted:
            job = listing
            break

    if not job:
        print("⚠️ All jobs posted. Clearing history.")
        open(POSTED_FILE, "w").close()
        job = listings[0]

    apply_link = build_apply_link(job["title"])
    print(f"📤 Selected: {job['title'][:60]}")
    print(f"🔗 Apply link: {apply_link}")
    print(f"🌐 Source: {job.get('source', 'Unknown')}\n")

    post = build_post(job, apply_link)
    print("--- POST PREVIEW ---")
    print(post)
    print("--------------------\n")

    result = post_to_facebook(post)
    if result:
        save_posted(make_key(job["title"]))
        print("✅ Saved to posted.txt")

if __name__ == "__main__":
    main()
