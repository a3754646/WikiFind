"""
BM25 Ranking Algorithm for WikiFind.

Ranks Wikipedia articles based on their relevance to a user's
descriptive query using the Okapi BM25 scoring formula.

Uses the inverted index from index.py for document statistics
and returns ranked document IDs with their BM25 scores.
"""

import math
from typing import Sequence

from index import InvertedIndex


def bm25_rank(
    query_tokens: Sequence[str],
    index: InvertedIndex,
    k1: float = 0.9,
    b: float = 1.0,
    top_k: int = 10,
) -> list[tuple[int, float]]:

    # Validate parameters
    if k1 < 0:
        raise ValueError("k1 must be non-negative")

    if not 0 <= b <= 1:
        raise ValueError("b must be between 0 and 1")

    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    # Get corpus statistics
    N = index.num_docs
    avgdl = index.avg_doc_length

    # Handle empty query or index
    if not query_tokens or N == 0 or avgdl == 0:
        return []

    # Retrieve candidate documents
    candidates = index.retrieve_candidates(query_tokens)

    # Calculate IDF for each unique query term
    idf_scores = {}

    for term in dict.fromkeys(query_tokens):
        df = index.doc_freq(term)

        if df > 0:
            idf_scores[term] = math.log(
                1 + (N - df + 0.5) / (df + 0.5)
            )

    # Calculate BM25 scores
    scores = []

    for candidate in candidates:

        doc_id = candidate.doc_id
        dl = index.doc_length(doc_id)
        score = 0.0

        for term, tf in candidate.matched_terms.items():

            idf = idf_scores[term]

            numerator = tf * (k1 + 1)

            denominator = tf + k1 * (
                1 - b + b * (dl / avgdl)
            )

            score += idf * (numerator / denominator)

        scores.append((doc_id, score))

    # Sort by descending score
    scores.sort(key=lambda x: (-x[1], x[0]))

    # Return top-ranked documents
    return scores[:top_k]
