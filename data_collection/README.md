# WikiFind - Wikipedia Data Collection

## Overview
Collects English Wikipedia introductions about electronics and computer science
using the MediaWiki Action API. This folder handles collection and basic cleaning.

## Data Source
English Wikipedia: https://en.wikipedia.org/w/api.php

## Implementation
1. Discover articles using `categorymembers` and API continuation for pagination.
2. Explore related subcategories up to depth 1 (at most 60 categories).
3. Retrieve plain-text introductions and article URLs, resolving redirects.
4. Clean articles and skip duplicates or empty introductions.
5. Export the cleaned articles to JSON.

## Generate Sample
Run from the repository root:

```sh
python -m pip install requests
python data_collection/collect_articles.py
```

The default command replaces the sample with 500 valid electronics articles.
To keep the existing sample and add 100 valid articles from Computer science:

```sh
python data_collection/collect_articles.py --append --category "Computer science" --limit 100
```

`--limit` counts valid new articles after cleaning and deduplication. Category labels
record the source Wikipedia category, including subcategories. Rerunning the append
command adds another 100 articles if enough new articles are available. If the target
cannot be reached, the script reports an error and leaves the sample file unchanged.

## Output
`data_collection/sample_articles.json`

Each article contains:
- `doc_id`: Wikipedia page ID
- `title`: Article title
- `category`: Source Wikipedia category
- `text`: Cleaned plain-text introductory extract
- `url`: Wikipedia article URL

## Cleaning
- Remove duplicate page IDs, URLs, and titles (case-insensitive).
- Retry empty introductions from Wikipedia, resolving redirects. Drop articles that
  still have no introduction, and deduplicate recovered redirect targets.
- Remove citation markers such as `[1]` and `[citation needed]` from article text.
- Remove embedded external URLs from article text; keep the separate `url` field.
- Normalize whitespace. Keep the original prose, capitalization, and punctuation.

## Current Collection
- Original sample: 500 electronics-related articles.
- Retried all 8 empty introductions: 7 recovered, including 4 duplicate redirect
  targets; 1 remained empty and was removed.
- Retained 495 unique existing articles and added 100 new articles discovered under
  Computer science and its subcategories.
- Final sample: **595 articles**, with all five fields populated and no duplicate
  IDs, URLs, or titles.
- Citation markers were removed from 2 existing articles. The original sample had
  no embedded external URLs in its text.

## Known Limitations
- Only introductions are collected, not full articles.
- Some articles are lists, companies, people, or concepts; relevance is not guaranteed.
- Category labels reflect discovery sources, not a manually curated classification.
- Wikipedia content and category membership may change between runs, so counts and
  article selection can differ when regenerating the sample.
