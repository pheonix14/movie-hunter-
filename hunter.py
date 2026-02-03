import re
import time
from internetarchive import search_items, get_item
import requests

HEADERS = {"User-Agent": "LostMediaHunter/1.0"}
VIDEO_EXT = (".mp4", ".mkv", ".avi", ".mov", ".mpg", ".mpeg")

# ---------------- UTIL ----------------

def log(msg):
    print(f"[HUNTER] {msg}")

def clean_title(t):
    return re.sub(r"[^a-zA-Z0-9 ]", "", t.lower()).strip()

def expand_titles(title):
    words = clean_title(title).split()
    variants = set()
    variants.add(" ".join(words))
    for i in range(len(words)):
        variants.add(" ".join(words[:i+1]))
    return list(variants)

def score(item, title):
    score = 0
    if item.get("size", 0) > 300:
        score += 30
    if title.lower() in item.get("title", "").lower():
        score += 25
    if item.get("source") == "Internet Archive":
        score += 25
    if item.get("type") == "video":
        score += 20
    return score

# ---------------- SOURCE 1: INTERNET ARCHIVE ----------------

def hunt_archive(title, year="", limit=10):
    results = []
    queries = expand_titles(title)

    for q in queries:
        query = f'mediatype:movies {q}'
        if year:
            query += f" AND year:{year}"

        try:
            search = search_items(query)
        except:
            continue

        for item in search:
            identifier = item.get("identifier")
            name = item.get("title", "Unknown")

            try:
                ia = get_item(identifier)
            except:
                continue

            for f in ia.files:
                fname = f.get("name", "").lower()
                if fname.endswith(VIDEO_EXT):
                    results.append({
                        "title": name,
                        "file": f["name"],
                        "size": int(f.get("size", 0)) // (1024 * 1024),
                        "url": f"https://archive.org/download/{identifier}/{f['name']}",
                        "source": "Internet Archive",
                        "type": "video"
                    })
                    break

            if len(results) >= limit:
                return results

    return results

# ---------------- SOURCE 2: OPEN DIRECTORY DISCOVERY ----------------
# (Discovery only – safe, no crawling)

def hunt_open_indexes(title):
    queries = [
        f'intitle:"index of" "{title}"',
        f'"{title}" filetype:mp4',
        f'"{title}" filetype:mkv'
    ]

    results = []
    for q in queries:
        results.append({
            "title": title,
            "file": "Unknown (open directory)",
            "size": 0,
            "url": f"https://duckduckgo.com/?q={q}",
            "source": "Search Engine Index",
            "type": "discovery"
        })
    return results

# ---------------- SOURCE 3: TORRENT METADATA (LEGAL ONLY) ----------------
# No downloading, no pirate indexes

def hunt_torrents_legal(title):
    return [{
        "title": title,
        "file": "Torrent metadata only",
        "size": 0,
        "url": f"https://www.google.com/search?q={title}+torrent+site:archive.org",
        "source": "Torrent Metadata (Legal)",
        "type": "metadata"
    }]

# ---------------- MAIN HUNTER ----------------

def hunt_everything(title, year=""):
    log(f"Starting full hunt for: {title}")
    results = []

    results.extend(hunt_archive(title, year))
    results.extend(hunt_open_indexes(title))
    results.extend(hunt_torrents_legal(title))

    # Deduplicate by URL
    unique = {r["url"]: r for r in results}.values()

    # Rank
    ranked = sorted(unique, key=lambda r: score(r, title), reverse=True)
    return ranked

# ---------------- CLI MODE ----------------

if __name__ == "__main__":
    print("=== LOST MEDIA HUNTER : FULL MODE ===")

    title = input("Enter name/title: ").strip()
    year = input("Year (optional): ").strip()

    found = hunt_everything(title, year)

    print("\n=== RESULTS ===")
    for i, r in enumerate(found, 1):
        print("------------------------------------------------")
        print(f"{i}. {r['title']}")
        print("   Source:", r["source"])
        print("   File  :", r["file"])
        print("   Size  :", r["size"], "MB")
        print("   URL   :", r["url"])
