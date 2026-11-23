# Inverted index and candidate retrieval for WikiFind.
# In: articles from data_collection, tokenized by preprocessing (text -> list of tokens).
# Out: retrieve_candidates(query_tokens) returns Candidates for bm25.py, which also reads
# num_docs, avg_doc_length, doc_freq, term_freq, doc_length. Use one tokenizer for both.

# Usage:
#     python index.py build
#     python index.py query "cooking device with horizontal rods"

from __future__ import annotations

import argparse
import gzip
import importlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Callable, Iterable, Mapping, Sequence
from wikifind.preprocessing import tokenize as preprocess_tokenize

Tokenizer = Callable[[str], "list[str]"]

INDEX_FORMAT_VERSION = 1
DEFAULT_ARTICLES = Path(__file__).with_name("data_collection") / "sample_articles.json"
DEFAULT_INDEX = Path(__file__).with_name("wikifind_index.json.gz")

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_BASIC_TOKENIZER_NAME = "basic"
DEFAULT_TOKENIZER = "wikifind.preprocessing:tokenize"


def basic_tokenize(text: str) -> list[str]:
    # Lowercase and split into letters and digits (Temporary until the preprocessing tokenizer is ready.)
    return _TOKEN_RE.findall(text.lower())


# A retrieved document and the query terms it matched (term -> count).
@dataclass(frozen=True)
class Candidate:
    doc_id: int
    matched_terms: Mapping[str, int]
    score: float


# Maps term -> {doc_id: term count}, and stores document lengths
class InvertedIndex:
    def __init__(self) -> None:
        self._postings: dict[str, dict[int, int]] = {}
        self._doc_lengths: dict[int, int] = {}
        self._doc_info: dict[int, dict[str, str]] = {}
        self._total_length = 0
        self.metadata: dict[str, object] = {}

    # Building

    def add_document(
        self,
        doc_id: int,
        tokens: Iterable[str],
        info: Mapping[str, str] | None = None,
    ) -> None:
        # Add one document. info is extra data like title and url
        if doc_id in self._doc_lengths:
            raise ValueError(f"doc_id {doc_id} is already indexed")

        length = 0
        term_counts: dict[str, int] = {}
        for token in tokens:
            term_counts[token] = term_counts.get(token, 0) + 1
            length += 1

        for term, count in term_counts.items():
            self._postings.setdefault(term, {})[doc_id] = count
        self._doc_lengths[doc_id] = length
        self._doc_info[doc_id] = dict(info or {})
        self._total_length += length

    # Corpus stats (for BM25)

    @property
    def num_docs(self) -> int:
        return len(self._doc_lengths)

    @property
    def avg_doc_length(self) -> float:
        return self._total_length / self.num_docs if self.num_docs else 0.0

    @property
    def vocabulary_size(self) -> int:
        return len(self._postings)

    def doc_ids(self) -> list[int]:
        return sorted(self._doc_lengths)

    def doc_length(self, doc_id: int) -> int:
        return self._doc_lengths[doc_id]

    def doc_info(self, doc_id: int) -> Mapping[str, str]:
        return MappingProxyType(self._doc_info[doc_id])

    def doc_freq(self, term: str) -> int:
        return len(self._postings.get(term, ()))

    def term_freq(self, term: str, doc_id: int) -> int:
        return self._postings.get(term, {}).get(doc_id, 0)

    def postings(self, term: str) -> Mapping[int, int]:
        return MappingProxyType(self._postings.get(term, {}))

    def __contains__(self, term: object) -> bool:
        return term in self._postings

    def __len__(self) -> int:
        return self.num_docs

    # Candidate retrieval

    def retrieve_candidates(
        self,
        query_tokens: Sequence[str],
        min_match: int = 1,
        min_fraction: float = 0.0,
        max_candidates: int | None = None,
    ) -> list[Candidate]:
        # Find documents that share terms with the query, best first.
        if min_match < 1:
            raise ValueError("min_match must be at least 1")
        if not 0.0 <= min_fraction <= 1.0:
            raise ValueError("min_fraction must be between 0 and 1")
        if max_candidates is not None and max_candidates < 1:
            raise ValueError("max_candidates must be at least 1")

        terms = list(dict.fromkeys(query_tokens))
        if not terms:
            return []
        required = max(min_match, math.ceil(min_fraction * len(terms)))

        matched: dict[int, dict[str, int]] = {}
        scores: dict[int, float] = {}
        for term in terms:
            posting = self._postings.get(term)
            if not posting:
                continue
            weight = self._idf(len(posting))
            for doc_id, tf in posting.items():
                matched.setdefault(doc_id, {})[term] = tf
                scores[doc_id] = scores.get(doc_id, 0.0) + weight

        candidates = [
            Candidate(doc_id, MappingProxyType(terms_found), scores[doc_id])
            for doc_id, terms_found in matched.items()
            if len(terms_found) >= required
        ]
        candidates.sort(key=lambda c: (-c.score, c.doc_id))
        return candidates[:max_candidates] if max_candidates else candidates

    def _idf(self, doc_freq: int) -> float:
        return math.log(1.0 + self.num_docs / doc_freq)

    # Saving and loading

    def save(self, path: str | Path) -> None:
        # Save the index to a gzipped JSON file.
        payload = {
            "version": INDEX_FORMAT_VERSION,
            "metadata": self.metadata,
            "doc_lengths": {str(d): n for d, n in sorted(self._doc_lengths.items())},
            "doc_info": {str(d): i for d, i in sorted(self._doc_info.items())},
            "postings": {
                term: sorted(posting.items())
                for term, posting in sorted(self._postings.items())
            },
        }
        with gzip.open(path, "wt", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)

    @classmethod
    def load(cls, path: str | Path) -> "InvertedIndex":
        # Load an index saved with save().
        with gzip.open(path, "rt", encoding="utf-8") as f:
            payload = json.load(f)
        if payload.get("version") != INDEX_FORMAT_VERSION:
            raise ValueError(
                f"Unsupported index version {payload.get('version')!r}; "
                f"expected {INDEX_FORMAT_VERSION}. Rebuild the index."
            )
        index = cls()
        index.metadata = payload.get("metadata", {})
        index._doc_lengths = {int(d): n for d, n in payload["doc_lengths"].items()}
        index._doc_info = {int(d): i for d, i in payload["doc_info"].items()}
        index._total_length = sum(index._doc_lengths.values())
        index._postings = {
            term: {int(doc_id): tf for doc_id, tf in posting}
            for term, posting in payload["postings"].items()
        }
        return index


# Helper functions


def load_articles(path: str | Path = DEFAULT_ARTICLES) -> list[dict]:
    # Load the articles from the data collection JSON file.
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_index(
    articles: Iterable[Mapping],
    tokenize: Tokenizer = preprocess_tokenize, #changed from basic_tokenize
    include_title: bool = False,
) -> InvertedIndex:
    # Build an index from a list of articles.
    index = InvertedIndex()
    index.metadata = {
        "tokenizer": _tokenizer_name(tokenize),
        "include_title": include_title,
    }
    for article in articles:
        text = article["text"]
        if include_title:
            text = f"{article['title']}. {text}"
        index.add_document(
            article["doc_id"],
            tokenize(text),
            {
                "title": article["title"],
                "url": article["url"],
                "category": article["category"],
            },
        )
    return index


def search_candidates(
    index: InvertedIndex,
    query: str,
    tokenize: Tokenizer = preprocess_tokenize, #changed from basic_tokenize
    **retrieval_options,
) -> list[Candidate]:
    # Tokenize a query string and return its candidates.
    return index.retrieve_candidates(tokenize(query), **retrieval_options)


def _tokenizer_name(tokenize: Tokenizer) -> str:
    if tokenize is basic_tokenize:
        return _BASIC_TOKENIZER_NAME
    return f"{tokenize.__module__}:{tokenize.__qualname__}"


def resolve_tokenizer(spec: str) -> Tokenizer:
    # Get a tokenizer from "basic" or "module:function".
    if spec == _BASIC_TOKENIZER_NAME:
        return basic_tokenize
    module_name, _, func_name = spec.partition(":")
    if not module_name or not func_name:
        raise ValueError(f"Tokenizer must look like 'module:function', got {spec!r}")
    return getattr(importlib.import_module(module_name), func_name)


# Command line


def _cmd_build(args: argparse.Namespace) -> None:
    tokenize = resolve_tokenizer(args.tokenizer)
    index = build_index(load_articles(args.input), tokenize, args.include_title)
    index.save(args.output)
    print(
        f"Indexed {index.num_docs} documents, {index.vocabulary_size} terms, "
        f"avg length {index.avg_doc_length:.1f} tokens -> {args.output}"
    )


def _cmd_query(args: argparse.Namespace) -> None:
    index = InvertedIndex.load(args.index)
    # Use the tokenizer the index was built with unless one is given.
    spec = args.tokenizer or index.metadata.get("tokenizer", _BASIC_TOKENIZER_NAME)
    tokenize = resolve_tokenizer(spec)
    tokens = tokenize(args.query)
    candidates = index.retrieve_candidates(
        tokens, min_match=args.min_match, min_fraction=args.min_fraction
    )
    print(f"Query tokens: {tokens}")
    print(f"{len(candidates)} candidates; showing top {min(args.top, len(candidates))}")
    for rank, cand in enumerate(candidates[: args.top], start=1):
        title = index.doc_info(cand.doc_id).get("title", "?")
        terms = ", ".join(cand.matched_terms)
        print(f"{rank:>3}. {title}  (doc {cand.doc_id}, score {cand.score:.2f})  [{terms}]")


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build and query the WikiFind inverted index.")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="Build an index from the articles.")
    build.add_argument("--input", type=Path, default=DEFAULT_ARTICLES)
    build.add_argument("--output", type=Path, default=DEFAULT_INDEX)
    build.add_argument("--tokenizer", default=DEFAULT_TOKENIZER, # changed from _BASIC_TOKENIZER_NAME
                       help="'basic' or 'module:function', e.g. wikifind.preprocessing:tokenize")
    build.add_argument("--include-title", action="store_true", help="Also index article titles.")
    build.set_defaults(func=_cmd_build)

    query = sub.add_parser("query", help="Get candidate documents for a description.")
    query.add_argument("query")
    query.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    query.add_argument("--tokenizer", default=None,
                       help="Use this tokenizer instead of the one saved in the index.")
    query.add_argument("--min-match", type=int, default=1)
    query.add_argument("--min-fraction", type=float, default=0.0)
    query.add_argument("--top", type=int, default=10)
    query.set_defaults(func=_cmd_query)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()