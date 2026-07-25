import json
import os

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
    "claims":[
        {
            "text":"",
            "type":"",
            "confidence":0.95,
            "evidence":""
        }
    ]
}

Maximum 10 claims.
"""


def extract_claims(paper_text):

    response = client.messages.create(

        model="claude-sonnet-4-0",

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

    text = response.content[0].text

    data = json.loads(text)

    return data["claims"]