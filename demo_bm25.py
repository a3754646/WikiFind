
# Test BM25 ranking using the collected Wikipedia dataset.
#
# Usage:
#     python index.py build
#     python demo_bm25.py

from index import InvertedIndex, resolve_tokenizer
from bm25 import bm25_rank


def main():

    # Load the inverted index
    index = InvertedIndex.load("wikifind_index.json.gz")

    # Use the same tokenizer used during indexing
    tokenize = resolve_tokenizer(
        index.metadata.get("tokenizer", "basic")
    )

    print("\nWikiFind - BM25 Search Engine")
    print("=" * 50)
    print(f"Total documents: {index.num_docs}")
    print(f"Vocabulary size: {index.vocabulary_size}")
    print(f"Average document length: {index.avg_doc_length:.2f}")
    print("Type 'exit' to quit.")

    while True:

        query = input("\nDescribe an object: ").strip()

        if query.lower() == "exit":
            break

        if not query:
            continue

        query_tokens = tokenize(query)

        results = bm25_rank(query_tokens, index, top_k=10)

        print(f"\nQuery tokens: {query_tokens}")

        if not results:
            print("No matching documents found.")
            continue

        print("\nRanked Results")
        print("=" * 50)

        for rank, (doc_id, score) in enumerate(
            results, start=1
        ):

            info = index.doc_info(doc_id)

            print(f"\nRank: {rank}")
            print(f"Title: {info['title']}")
            print(f"Document ID: {doc_id}")
            print(f"BM25 Score: {score:.4f}")
            print(f"Category: {info['category']}")
            print(f"URL: {info['url']}")
            print("-" * 50)


if __name__ == "__main__":
    main()
