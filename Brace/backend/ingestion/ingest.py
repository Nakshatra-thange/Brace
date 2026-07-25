import json
import os
import sys


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from extract_text import extract_all_papers
from ai.extract_claims import extract_claims

PAPERS_DIR = "../papers/heartbreak"
OUTPUT_DIR = "../output"

os.makedirs(OUTPUT_DIR, exist_ok=True)

papers = extract_all_papers(PAPERS_DIR)

print(f"\nFound {len(papers)} papers\n")

for paper in papers:

    print(f"Processing {paper['filename']}...")

    try:

        claims = extract_claims(paper["text"])

        output = {
            "filename": paper["filename"],
            "claims": claims
        }

        output_file = os.path.join(
            OUTPUT_DIR,
            paper["filename"].replace(".pdf", ".json")
        )

        with open(output_file, "w") as f:
            json.dump(output, f, indent=4)

        print("✓ Saved")

    except Exception as e:

        print(f"✗ Failed: {e}")