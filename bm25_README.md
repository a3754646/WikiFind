# WikiFind — BM25 Ranking

## Overview

BM25 ranks Wikipedia articles by how well their text matches a description of an unknown object. It uses the inverted index in `index.py` to find candidate articles and score them without scanning every article.

## Files

- **`bm25.py` — Ranking logic:** `bm25_rank(query_tokens, index, k1, b, top_k)` retrieves candidate documents, weights query terms by inverse document frequency (IDF), adjusts for term frequency and document length, then returns the highest-ranked `(doc_id, score)` pairs. `k1` controls term-frequency saturation; `b` controls length normalization.
- **`demo_bm25.py` — Interactive demonstration:** Loads the saved index and its tokenizer, accepts natural-language descriptions, and displays the top 10 matching articles with their titles, scores, document IDs, categories, and URLs. Useful for manually checking results and for the teammate integrating `search.py`.
- **`evaluate_bm25.py` — Evaluation and tuning:** Runs 15 predefined queries with known target articles. Reports Hit Rate@1, @5, @10 and MRR@10; `--tune` compares 25 combinations of `k1` and `b`.

## Results

Evaluated **595 Wikipedia articles** using **15 development queries** and the basic tokenizer.

| Metric | Baseline (`k1=1.2, b=0.75`) | Selected (`k1=0.9, b=1.0`) |
|---|---:|---:|
| Hit Rate@1 | 46.67% | 46.67% |
| Hit Rate@5 | 80.00% | 80.00% |
| Hit Rate@10 | 93.33% | **100.00%** |
| MRR@10 | 0.5992 | **0.6046** |

The selected configuration favors finding the correct article within the top 10. `k1=0.5, b=1.0` had a slightly higher MRR (0.6074) but lower top-5/top-10 coverage on these queries.

## Run

From the repository root:

```bash
python index.py build                   # Only if the saved index is missing
python demo_bm25.py                    # Helps with Interactive search
python evaluate_bm25.py               # Helps with Baseline evaluation
python evaluate_bm25.py --tune        # Helps with Parameter comparison
python evaluate_bm25.py --k1 0.9 --b 1.0
```

## Using BM25 in `search.py`

The search component can reuse the existing index and tokenizer, then convert ranked document IDs into article metadata:

```python
from bm25 import bm25_rank
from index import resolve_tokenizer

# `index` is an already loaded InvertedIndex; `query` is the user's text.
tokenize = resolve_tokenizer(index.metadata.get("tokenizer", "basic"))
ranked = bm25_rank(tokenize(query), index, k1=0.9, b=1.0, top_k=10)
results = [
    {"doc_id": doc_id, "score": score, **index.doc_info(doc_id)}
    for doc_id, score in ranked
]
```

## Limitations

BM25 relies on matching words, so synonyms may not match well. The 15 queries were used for tuning, so these results are **development-set results**, not independent test performance. Reevaluate after the team's final preprocessing is integrated.
