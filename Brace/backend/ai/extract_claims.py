import json
import os
import re

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

SYSTEM_PROMPT = """
You are an expert neuroscience researcher.

Extract ONLY scientific claims.

A scientific claim is:

- empirical
- theoretical
- methodological

Return valid JSON ONLY.

Output:

{
  "claims": [
    {
      "text": "",
      "type": "",
      "confidence": 0.95,
      "evidence": ""
    }
  ]
}

Maximum 10 claims.
"""


def extract_claims(paper_text):

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=3500,
        temperature=0,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": paper_text[:60000]
            }
        ]
    )

    text = response.content[0].text.strip()

    print("\n========== CLAUDE RESPONSE ==========\n")
    print(text)
    print("\n=====================================\n")

    # Remove markdown code fences
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    # Find JSON object
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise Exception(f"No JSON found.\n\nClaude returned:\n{text}")

    json_text = text[start:end + 1]

    data = json.loads(json_text)

    return data["claims"]