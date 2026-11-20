
# WikiFind - Wikipedia Data Collection

## Overview
Collects Wikipedia articles about electronics using
the MediaWiki Action API.

## Data Source
English Wikipedia
https://en.wikipedia.org/w/api.php

## Implementation
1. Discover articles using categorymembers.
2. Explore related subcategories up to depth 1.
3. Use API continuation for pagination.
4. Retrieve introductory plain text and URLs.
5. Export collected articles to JSON.

## How to Run
From the repository root:

pip install -r requirements.txt
python data_collection/collect_articles.py

## Output
data_collection/sample_articles.json

Each article contains:
- doc_id: Wikipedia page ID
- title: Article title
- category: Source Wikipedia category
- text: Plain-text introductory extract
- url: Wikipedia URL

## Current Collection
- Target: 500 raw articles
- Topic: Electronics and related subcategories
- 500 unique article IDs collected

## Known Limitations
- Some articles have empty descriptions.
- Some articles are lists, companies, or concepts.
- Article relevance is not guaranteed.
- Wikipedia content may change between runs.
- 500 raw articles does not guarantee 500 valid articles.

## Handoff
Raw dataset is passed to the cleaning and
validation teammate.

Text normalization, filtering, and validation
are handled separately.
