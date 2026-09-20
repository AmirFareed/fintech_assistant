from vectordb.postgres import db
from embeddings.generator import embed_text


def embed_all_chunks():
    res = (
        db.table("chunks")
        .select("id, chunk_text, embedding")
        .order("chunk_index")
        .execute()
    )

    chunks = res.data or []
    updated = 0

    for chunk in chunks:
        if chunk.get("embedding") is not None:
            continue

        vector = embed_text(chunk["chunk_text"])

        (
            db.table("chunks")
            .update({"embedding": vector})
            .eq("id", chunk["id"])
            .execute()
        )

        updated += 1
        print(f"Embedded chunk {chunk['id']}")

    print(f"\nDone. Embedded {updated} chunks.")


if __name__ == "__main__":
    embed_all_chunks()
