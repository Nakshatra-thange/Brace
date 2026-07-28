import os
import psycopg2
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
load_dotenv()
DB_URL = os.environ["DATABASE_URL"]

print("Loading SPECTER2 model (first run downloads ~440MB, cached after)...")
model = SentenceTransformer("allenai/specter2_base")


def fetch_claims_without_embeddings(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT c.id, c.text
            FROM "Claim" c
            LEFT JOIN "ClaimEmbedding" ce ON ce."claimId" = c.id
            WHERE ce.id IS NULL
        """)
        return cur.fetchall()


def store_embedding(conn, claim_id: int, vector: list[float]):
    vector_str = "[" + ",".join(str(x) for x in vector) + "]"
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO "ClaimEmbedding" (id, "claimId", provider, dimensions, vector, "createdAt")
            VALUES (
                nextval(pg_get_serial_sequence('"ClaimEmbedding"', 'id')),
                %s, 'SPECTER2', 768, %s::vector, now()
            )
        """, (claim_id, vector_str))
    conn.commit()


def run():
    conn = psycopg2.connect(DB_URL)
    claims = fetch_claims_without_embeddings(conn)
    print(f"Found {len(claims)} claims needing embeddings.")

    if not claims:
        print("Nothing to do.")
        return

    ids = [c[0] for c in claims]
    texts = [c[1] for c in claims]

    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)

    for claim_id, vector in zip(ids, embeddings):
        store_embedding(conn, claim_id, vector.tolist())

    print(f"Stored {len(ids)} embeddings.")
    conn.close()


if __name__ == "__main__":
    run()