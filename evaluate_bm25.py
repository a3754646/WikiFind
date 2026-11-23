"""
BM25 Evaluation and Parameter Tuning for WikiFind.

Evaluates ranking performance using 15 descriptive queries
with known expected Wikipedia articles.

Metrics:
    Hit Rate@1, Hit Rate@5, Hit Rate@10, and MRR@10.

Usage:
    python evaluate_bm25.py
    python evaluate_bm25.py --tune
    python evaluate_bm25.py --k1 0.9 --b 1.0
"""

import argparse
from pathlib import Path

from bm25 import bm25_rank
from index import InvertedIndex, resolve_tokenizer


TEST_QUERIES = [
    ("Device that uses ultraviolet light to attract and kill insects", "Bug zapper"),
    ("Electronic device used by parents to remotely listen to their sleeping infant", "Baby monitor"),
    ("Wearable digital timepiece with buttons for performing mathematical calculations", "Calculator watch"),
    ("Portable device used to record video and sound", "Camcorder"),
    ("Vacuum tube that uses an electron beam to display images on a screen", "Cathode ray tube"),
    ("Device that increases the strength of audio signals to drive loudspeakers", "Audio power amplifier"),
    ("Optical storage medium that uses a blue violet laser to read data", "Blu-ray"),
    ("System that extracts heat from outdoor air to warm a building", "Air source heat pump"),
    ("Device that uses a laser to read music stored on optical discs", "CD player"),
    ("Chemical spray used to remove dirt and oxidation from electrical connections", "Contact cleaner"),
    ("Sound system consisting of five primary speakers and one subwoofer", "5.1 surround sound"),
    ("Handheld dual band two way radio used for amateur communication", "Baofeng UV-5R"),
    ("Electronic system installed in a car dashboard for music and entertainment", "Automotive head unit"),
    ("Technology that uses electron spin in addition to electric charge", "Spintronics"),
    ("Technology that uses ultracold atoms to create circuits similar to electronic circuits", "Atomtronics"),
]


def evaluate(index, tokenize, k1=1.2, b=0.75, verbose=True):
    hit1 = hit5 = hit10 = 0
    reciprocal_rank_sum = 0.0

    if verbose:
        print(f"\nBM25 evaluation | k1={k1}, b={b}")
        print(f"{'Expected article':<30} {'Rank':<8} Top result")
        print("-" * 78)

    for query, expected in TEST_QUERIES:
        results = bm25_rank(tokenize(query), index, k1=k1, b=b, top_k=10)
        titles = [index.doc_info(doc_id)["title"] for doc_id, _ in results]
        rank = next((i for i, title in enumerate(titles, 1)
                     if title.casefold() == expected.casefold()), None)

        if rank is not None:
            hit1 += int(rank == 1)
            hit5 += int(rank <= 5)
            hit10 += 1
            reciprocal_rank_sum += 1 / rank

        if verbose:
            top = titles[0] if titles else "No results"
            found = str(rank) if rank is not None else "Miss"
            print(f"{expected:<30} {found:<8} {top}")

    n = len(TEST_QUERIES)
    return hit1 / n, hit5 / n, hit10 / n, reciprocal_rank_sum / n


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--k1", type=float, default=1.2)
    parser.add_argument("--b", type=float, default=0.75)
    parser.add_argument("--tune", action="store_true", help="Compare parameter combinations")
    args = parser.parse_args()

    path = Path(__file__).with_name("wikifind_index.json.gz")
    if not path.exists():
        parser.exit(1, "Index not found. Run python index.py build first.\n")

    index = InvertedIndex.load(str(path))
    tokenize = resolve_tokenizer(index.metadata.get("tokenizer", "basic"))

    # Avoid interpreting missing target articles as ranking failures.
    indexed_titles = {index.doc_info(doc_id)["title"].casefold() for doc_id in index.doc_ids()}
    missing = [title for _, title in TEST_QUERIES if title.casefold() not in indexed_titles]
    if missing:
        parser.exit(1, "Expected articles missing from index: " + ", ".join(missing) + "\n")

    print(f"Documents: {index.num_docs} | Queries: {len(TEST_QUERIES)}")
    h1, h5, h10, mrr = evaluate(index, tokenize, args.k1, args.b)
    print(f"\nHit Rate@1:  {h1:.2%}")
    print(f"Hit Rate@5:  {h5:.2%}")
    print(f"Hit Rate@10: {h10:.2%}")
    print(f"MRR@10:     {mrr:.4f}")

    if args.tune:
        rows = []
        for k1 in (0.5, 0.9, 1.2, 1.5, 2.0):
            for b in (0.0, 0.25, 0.5, 0.75, 1.0):
                rows.append((k1, b, *evaluate(index, tokenize, k1, b, verbose=False)))

        # Prefer high MRR, then high Hit Rate@1. Other ties remain ties.
        rows.sort(key=lambda row: (row[5], row[2]), reverse=True)
        print("\nParameter tuning (development queries)")
        print(f"{'k1':>5} {'b':>5} {'Hit@1':>9} {'Hit@5':>9} {'Hit@10':>9} {'MRR@10':>9}")
        print("-" * 52)
        for k1, b, h1, h5, h10, mrr in rows:
            print(f"{k1:5.2f} {b:5.2f} {h1:9.2%} {h5:9.2%} {h10:9.2%} {mrr:9.4f}")
        best = rows[0]
        print(f"\nBest observed combination: k1={best[0]}, b={best[1]}, MRR@10={best[5]:.4f}")


if __name__ == "__main__":
    main()
