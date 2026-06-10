from services.retrieval import search_chunks

# Optional: put a real department id here
DEPARTMENT_ID = None

if __name__ == "__main__":
    query = "how to renew expired arms license"
    results = search_chunks(query=query, match_count=5, department_id=DEPARTMENT_ID)

    print(f"\nQuery: {query}\n")
    for i, item in enumerate(results, start=1):
        print(f"Result {i}")
        print(f"Similarity: {item['similarity']}")
        print(f"Chunk index: {item['chunk_index']}")
        print(f"Text: {item['chunk_text'][:400]}")
        print("-" * 80)