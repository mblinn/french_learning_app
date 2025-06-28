import requests
import sys
import traceback
import random
from typing import List, Dict, Sequence

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
            back = fields.get("english_translation", {}).get("value", "")
            freq = str(fields.get("Frequency", ""))
            if front or back:
                flashcards.append(
                    Flashcard(front=front, back=back, frequency=freq)
                )

        # Fetch existing levels for the selected frequencies
        frequencies = [c.frequency for c in flashcards if c.frequency]
        level_map = fetch_levels(api_key, frequencies)
        for card in flashcards:
            if card.frequency:
                card.level = level_map.get(card.frequency, 1)

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


def fetch_levels(api_key: str, frequencies: Sequence[str]) -> Dict[str, int]:
    """Return a mapping of frequency to level from Airtable."""
    headers = {"Authorization": f"Bearer {api_key}"}
    if not frequencies:
        return {}
    formula = "OR(" + ",".join([f"{{Frequency}} = '{f}'" for f in frequencies]) + ")"
    params = {"filterByFormula": formula}
    try:
        resp = requests.get(SPACED_REP_URL, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
        levels = {}
        for rec in data.get("records", []):
            fields = rec.get("fields", {})
            freq = str(fields.get("Frequency", ""))
            level = int(fields.get("level", 1))
            if freq:
                levels[freq] = level
        return levels
    except Exception:
        print("Error fetching levels from Airtable", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return {}


def update_level(api_key: str, frequency: str, delta: int) -> int | None:
    """Update the level for ``frequency`` by ``delta`` and return the new level."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    formula = f"{{Frequency}} = '{frequency}'"
    try:
        resp = requests.get(
            SPACED_REP_URL, headers=headers, params={"filterByFormula": formula}
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("records"):
            rec = data["records"][0]
            record_id = rec["id"]
            current = int(rec.get("fields", {}).get("level", 1))
        else:
            record_id = None
            current = 1

        new_level = max(1, min(5, current + delta))

        if record_id is None:
            payload = {"fields": {"Frequency": frequency, "level": new_level}}
            resp = requests.post(SPACED_REP_URL, headers=headers, json=payload)
        elif new_level != current:
            url = f"{SPACED_REP_URL}/{record_id}"
            payload = {"fields": {"level": new_level}}
            resp = requests.patch(url, headers=headers, json=payload)
        else:
            return new_level

        resp.raise_for_status()
        return new_level
    except Exception:
        print("Error updating level in Airtable", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return None
