
import requests
import json
import time
from pathlib import Path
from collections import deque

API_URL = "https://en.wikipedia.org/w/api.php"
output = Path(__file__).with_name("sample_articles.json")

HEADERS = {
    "User-Agent": (
        "WikiFind/0.1 "
        "(https://github.com/a3754646)"
    )
}

# Collection settings
CATEGORIES = [
    "Category:Electronics",
    "Category:Consumer electronics"
]

MAX_ARTICLES = 500
MAX_DEPTH = 1
MAX_CATEGORIES = 60
BATCH_SIZE = 20


def api_request(params):
    params = {
        **params,
        "format": "json",
        "formatversion": 2,
        "maxlag": 5
    }

    for attempt in range(4):
        response = requests.get(
            API_URL,
            params=params,
            headers=HEADERS,
            timeout=30
        )

        if response.status_code in (429, 503):
            time.sleep(2 ** attempt + 1)
            continue

        response.raise_for_status()
        data = response.json()

        if "error" in data:
            if data["error"].get("code") == "maxlag":
                time.sleep(2 ** attempt + 1)
                continue
            raise RuntimeError(data["error"])

        time.sleep(0.3)
        return data

    raise RuntimeError("Wikipedia API retry limit reached")


# STEP 1: Discover articles and subcategories

queue = deque((cat, 0) for cat in CATEGORIES)
visited_categories = set()
article_ids = {}

while queue and len(article_ids) < MAX_ARTICLES:

    category, depth = queue.popleft()

    if category in visited_categories:
        continue

    if len(visited_categories) >= MAX_CATEGORIES:
        break

    visited_categories.add(category)

    print(f"Searching {category} (depth {depth})")

    continuation = {}

    while len(article_ids) < MAX_ARTICLES:

        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": category,
            "cmtype": "page|subcat",
            "cmlimit": 50
        }

        params.update(continuation)
        data = api_request(params)

        for member in data["query"]["categorymembers"]:

            # Normal Wikipedia article
            if member["ns"] == 0:
                page_id = member["pageid"]

                if page_id not in article_ids:
                    article_ids[page_id] = category

            # Wikipedia subcategory
            elif member["ns"] == 14 and depth < MAX_DEPTH:
                subcategory = member["title"]

                if subcategory not in visited_categories:
                    queue.append((subcategory, depth + 1))

            if len(article_ids) >= MAX_ARTICLES:
                break

        if "continue" not in data:
            break

        continuation = data["continue"]

    print(f"Total unique IDs: {len(article_ids)}")


# STEP 2: Retrieve introductory text

collected_articles = []
page_ids = list(article_ids.keys())

for i in range(0, len(page_ids), BATCH_SIZE):

    batch = page_ids[i:i + BATCH_SIZE]

    params = {
        "action": "query",
        "prop": "extracts|info",
        "pageids": "|".join(map(str, batch)),
        "exintro": 1,
        "explaintext": 1,
        "exlimit": BATCH_SIZE,
        "inprop": "url"
    }

    data = api_request(params)

    for page in data["query"]["pages"]:

        if "missing" in page:
            continue

        source_category = article_ids[page["pageid"]]

        collected_articles.append({
            "doc_id": page["pageid"],
            "title": page["title"],
            "category": source_category.replace("Category:", ""),
            "text": page.get("extract", ""),
            "url": page.get("fullurl", "")
        })

    print(f"Retrieved {len(collected_articles)} articles")


# STEP 3: Export raw JSON

with open(output, "w", encoding="utf-8") as f:
    json.dump(
        collected_articles,
        f,
        indent=2,
        ensure_ascii=False
    )

print(f"\nSaved {len(collected_articles)} raw articles")
print(f"Categories searched: {len(visited_categories)}")
print(f"Output: {output}")

if len(collected_articles) < MAX_ARTICLES:
    print("Target not reached. Expand categories or depth.")
