import requests
import sys
import traceback
import random
from typing import List

from flashcards import Flashcard


AIRTABLE_URL = "https://api.airtable.com/v0/applW7zbiH23gDDCK/french_words"
SPACED_REP_URL = "https://api.airtable.com/v0/applW7zbiH23gDDCK/spaced_rep"


def get_random_frequencies(count: int = 20, max_frequency: int = 200) -> List[int]:
    """Return ``count`` unique random frequency values between 1 and ``max_frequency``."""
    population = list(range(1, max_frequency + 1))
    return random.sample(population, count)


def fetch_flashcards(api_key: str) -> List[Flashcard]:
    """Fetch flashcards from Airtable given an API key."""
    headers = {"Authorization": f"Bearer {api_key}"}
    selected = get_random_frequencies()
    formula = "OR(" + ",".join([f"{{Frequency}} = \"{i}\"" for i in selected]) + ")"
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
            back = fields.get("english_translation", "")
            freq = str(fields.get("Frequency", ""))
            if front or back:
                flashcards.append(
                    Flashcard(front=front, back=back, frequency=freq)
                )
        return flashcards
    except Exception:
        print("Error fetching flashcards from Airtable", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
    return []


def log_practice(api_key: str, frequency: str, date_str: str) -> bool:
    """Record a practice event in the spaced_rep table."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {"fields": {"Date": date_str, "Frequency": frequency}}
    try:
        resp = requests.post(SPACED_REP_URL, headers=headers, json=payload)
        resp.raise_for_status()
        return True
    except Exception:
        print("Error recording practice in Airtable", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return False
