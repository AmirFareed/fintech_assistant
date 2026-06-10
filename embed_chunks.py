from services.supabase_client import supabase
from services.embeddings import embed_text


def embed_all_chunks():
    res = (
        supabase.table("chunks")
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
            supabase.table("chunks")
            .update({"embedding": vector})
            .eq("id", chunk["id"])
            .execute()
        )

        updated += 1
        print(f"Embedded chunk {chunk['id']}")

    print(f"\nDone. Embedded {updated} chunks.")


if __name__ == "__main__":
    embed_all_chunks()