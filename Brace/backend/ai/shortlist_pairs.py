import os
import psycopg2

DB_URL = os.environ["DATABASE_URL"]
SIMILARITY_THRESHOLD = 0.55   # cosine similarity floor — tune after spot-checking
MAX_PAIRS = 500                # hard ceiling so a bad threshold can't blow up API costs


def get_candidate_pairs(conn, threshold=SIMILARITY_THRESHOLD, limit=MAX_PAIRS):
    """
    Finds claim pairs whose embeddings are close enough to be worth an LLM
    classification call. Excludes pairs from the same paper (a paper doesn't
    contradict itself in a way we care about for this graph) and excludes
    pairs already classified.
    """
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                c1.id AS claim_a_id, c1.text AS claim_a_text, c1."paperId" AS paper_a,
                c2.id AS claim_b_id, c2.text AS claim_b_text, c2."paperId" AS paper_b,
                1 - (e1.vector <=> e2.vector) AS similarity
            FROM "Claim" c1
            JOIN "ClaimEmbedding" e1 ON e1."claimId" = c1.id
            JOIN "Claim" c2 ON c2.id > c1.id
            JOIN "ClaimEmbedding" e2 ON e2."claimId" = c2.id
            WHERE c1."paperId" != c2."paperId"
              AND (1 - (e1.vector <=> e2.vector)) >= %s
              AND NOT EXISTS (
                  SELECT 1 FROM "ClaimRelationship" cr
                  WHERE (cr."sourceClaimId" = c1.id AND cr."targetClaimId" = c2.id)
                     OR (cr."sourceClaimId" = c2.id AND cr."targetClaimId" = c1.id)
              )
            ORDER BY similarity DESC
            LIMIT %s
        """, (threshold, limit))
        return cur.fetchall()


if __name__ == "__main__":
    conn = psycopg2.connect(DB_URL)
    pairs = get_candidate_pairs(conn)
    print(f"Found {len(pairs)} candidate pairs above similarity {SIMILARITY_THRESHOLD}")
    for p in pairs[:10]:
        print(f"  sim={p[6]:.3f} | {p[1][:60]}... <-> {p[4][:60]}...")
    conn.close()