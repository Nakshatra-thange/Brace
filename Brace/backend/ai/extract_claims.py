import os
import json
from anthropic import Anthropic
from dotenv import load_dotenv
load_dotenv()

client = Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

EXTRACTION_PROMPT = """You are extracting structured data from a neuroscience paper about grief, heartbreak, social rejection, or emotional pain, for a research mapping tool.

Return ONLY valid JSON. No preamble, no markdown code fences, no commentary — just the JSON object.

Extract:

1. Paper metadata (best effort from the text; use null if genuinely not present in the text — do not guess):
   - title
   - authors (array of strings, "Lastname Initial." format if that's how they appear)
   - year (integer or null)
   - journal (string or null)
   - doi (string or null)

2. Between 3 and 10 claims. A claim is a specific empirical finding or theoretical/interpretive position the paper argues for — not background facts or citations of other people's work.

For each claim, return:
   - text: one self-contained sentence. A reader should understand it WITHOUT reading the paper.
   - type: EXACTLY one of "EMPIRICAL", "THEORETICAL", "METHODOLOGICAL" (uppercase, no other values)
   - section: EXACTLY one of "ABSTRACT", "INTRODUCTION", "RESULTS", "DISCUSSION", "CONCLUSION" (uppercase, no other values — pick the closest match if the paper uses different section names, e.g. "Findings" -> "RESULTS")
   - confidence: float between 0 and 1, your confidence that this is a real, well-supported claim from the paper (not your confidence in your own extraction)
   - evidence: short quote or paraphrase (under 200 chars) of the specific sentence(s) this claim is drawn from

Respond with exactly this JSON shape:

{
  "paper": {
    "title": "",
    "authors": [],
    "year": 0,
    "journal": "",
    "doi": ""
  },
  "claims": [
    {
      "text": "",
      "type": "",
      "section": "",
      "confidence": 0.0,
      "evidence": ""
    }
  ]
}

PAPER TEXT:
{text}
"""

ALLOWED_TYPES = {"EMPIRICAL", "THEORETICAL", "METHODOLOGICAL"}
ALLOWED_SECTIONS = {"ABSTRACT", "INTRODUCTION", "RESULTS", "DISCUSSION", "CONCLUSION"}


def _strip_code_fences(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw
        if raw.endswith("```"):
            raw = raw.rsplit("```", 1)[0]
    return raw.strip()


def extract_claims(paper_text: str, max_chars: int = 15000) -> dict:
    """
    Calls Claude to extract paper metadata + claims.
    Returns raw parsed dict — NOT yet validated against schema.
    Validation happens separately in ai/validate.py
    """
    prompt = EXTRACTION_PROMPT.replace("{text}", paper_text[:max_chars])

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = response.content[0].text
    cleaned = _strip_code_fences(raw_text)

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Claude did not return valid JSON. Raw output:\n{raw_text[:500]}"
        ) from e

    return parsed