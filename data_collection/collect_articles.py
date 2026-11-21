
import argparse
import re
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


def clean_text(text):
    # Keep article prose; remove citation markers and embedded external URLs.
    text = re.sub(r"\[(?:\d+(?:\s*[,–-]\s*\d+)*|citation needed|verification needed)\]", "", text, flags=re.I)
    text = re.sub(r"(?:https?://|www\.)[^\s<>]+", "", text)
    return " ".join(text.split())


def fetch_article(page_id, category):
    data = api_request({
        "action": "query",
        "prop": "extracts|info",
        "pageids": str(page_id),
        "redirects": 1,
        "exintro": 1,
        "explaintext": 1,
        "inprop": "url"
    })
    page = data["query"]["pages"][0]
    if "missing" in page:
        return None
    return {
        "doc_id": page["pageid"],
        "title": page["title"],
        "category": category.removeprefix("Category:"),
        "text": page.get("extract", ""),
        "url": page.get("fullurl", "")
    }


def discover_articles(categories):
    queue = deque((category, 0) for category in categories)
    visited_categories = set()
    seen_ids = set()

    while queue and len(visited_categories) < MAX_CATEGORIES:
        category, depth = queue.popleft()
        if category in visited_categories:
            continue
        visited_categories.add(category)
        print(f"Searching {category} (depth {depth})")
        continuation = {}

        while True:
            data = api_request({
                "action": "query",
                "list": "categorymembers",
                "cmtitle": category,
                "cmtype": "page|subcat",
                "cmlimit": 50,
                **continuation
            })
            for member in data["query"]["categorymembers"]:
                if member["ns"] == 0 and member["pageid"] not in seen_ids:
                    seen_ids.add(member["pageid"])
                    yield member["pageid"], category
                elif member["ns"] == 14 and depth < MAX_DEPTH:
                    queue.append((member["title"], depth + 1))
            if "continue" not in data:
                break
            continuation = data["continue"]


def main():
    parser = argparse.ArgumentParser(description="Collect and clean Wikipedia introductions.")
    parser.add_argument("--category", action="append", help="Source category; can be repeated.")
    parser.add_argument("--limit", type=int, default=MAX_ARTICLES, help="Number of valid new articles.")
    parser.add_argument("--append", action="store_true", help="Keep and clean the existing sample first.")
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit must be positive")
    categories = ["Category:" + c.removeprefix("Category:") for c in (args.category or CATEGORIES)]

    articles = []
    seen_ids, seen_urls, seen_titles = set(), set(), set()

    def add_article(article):
        if not article:
            return False
        article["text"] = clean_text(article["text"])
        title_key = article["title"].strip().casefold()
        if not all(article.values()) or article["doc_id"] in seen_ids or article["url"] in seen_urls or title_key in seen_titles:
            return False
        seen_ids.add(article["doc_id"])
        seen_urls.add(article["url"])
        seen_titles.add(title_key)
        articles.append(article)
        return True

    if args.append:
        with output.open(encoding="utf-8") as f:
            existing = json.load(f)
        for article in existing:
            if not clean_text(article["text"]):
                title = article["title"]
                article = fetch_article(article["doc_id"], article["category"])
                print(f"Retried empty introduction: {title} — {'recovered' if article and clean_text(article['text']) else 'still empty/missing'}")
            add_article(article)
        print(f"Kept {len(articles)} of {len(existing)} existing articles after cleaning")

    existing_count = len(articles)
    for page_id, category in discover_articles(categories):
        if page_id in seen_ids:
            continue
        if add_article(fetch_article(page_id, category)):
            added = len(articles) - existing_count
            if added % 20 == 0:
                print(f"Collected {added} valid new articles")
            if added == args.limit:
                break

    added = len(articles) - existing_count
    if added < args.limit:
        # Preserve the existing sample if the requested collection is incomplete.
        raise RuntimeError(f"Only found {added}/{args.limit} valid new articles. Expand categories or depth.")
    with output.open("w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Saved {len(articles)} cleaned articles ({added} new) to {output}")


if __name__ == "__main__":
    main()
