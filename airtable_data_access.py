import requests
import sys
import traceback
from typing import List

from flashcards import Flashcard


AIRTABLE_URL = "https://api.airtable.com/v0/applW7zbiH23gDDCK/french_words"


def fetch_flashcards(api_key: str) -> List[Flashcard]:
    """Fetch flashcards from Airtable given an API key."""
    headers = {"Authorization": f"Bearer {api_key}"}
    formula = "OR(" + ",".join([f"{{Frequency}} = \"{i}\"" for i in range(1, 21)]) + ")"
    params = {
        "maxRecords": 20,
        "filterByFormula": formula,
        "sort[0][field]": "Frequency",
        "sort[0][direction]": "asc",
    }
    try:
        resp = requests.get(AIRTABLE_URL, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
        flashcards: List[Flashcard] = []
        for rec in data.get("records", []):
            fields = rec.get("fields", {})
            front = fields.get("french_word", "")
            back = fields.get("english_word", "")
            if front or back:
                flashcards.append(Flashcard(front=front, back=back))
        return flashcards
    except Exception:
        print("Error fetching flashcards from Airtable", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
    return []
