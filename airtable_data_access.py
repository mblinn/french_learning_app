import requests
import sys
import traceback
import random
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

AIRTABLE_URL = "https://api.airtable.com/v0/applW7zbiH23gDDCK/french_words"
SPACED_REP_URL = "https://api.airtable.com/v0/applW7zbiH23gDDCK/spaced_rep"

@dataclass
class Flashcard:
    """Container for a single flashcard."""

    front: str
    back: str
    frequency: str | None = None
    level: str | None = None

def build_url(base_url: str, params: Optional[dict] = None) -> str:
    """Return ``base_url`` with ``params`` encoded as query string."""
    req = requests.Request("GET", base_url, params=params)
    return req.prepare().url


def log_airtable_error(message: str, url: str, payload: Optional[dict] = None) -> None:
    """Print an error ``message`` with ``url`` and optional ``payload``."""
    print(f"{message}. URL: {url}", file=sys.stderr)
    if payload is not None:
        print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
    traceback.print_exc(file=sys.stderr)


def get_random_frequencies(count: int = 20, max_frequency: int = 200) -> List[int]:
    """Return ``count`` unique random frequency values between 1 and ``max_frequency``."""
    population = list(range(1, max_frequency + 1))
    return random.sample(population, count)

def fetch_spaced_rep_frequencies(api_key: str, count: int = 5) -> List[Tuple[int, int]]:
    """Return spaced repetition frequencies and their knowledge levels.

    ``count`` frequencies are retrieved for each knowledge level from 1-5.
    Older cards are preferred according to the following schedule:

    - Level 1: at least 1 day old
    - Level 2: at least 1 week old
    - Level 3: at least 2 weeks old
    - Level 4: at least 1 month old
    - Level 5: no age requirement

    The spaced_rep table contains each frequency exactly once, so the results do
    not need deduplication. Frequencies are returned sorted for deterministic
    tests.
    """

    headers = {"Authorization": f"Bearer {api_key}"}
    level_age = {1: 1, 2: 7, 3: 14, 4: 30, 5: None}
    results: List[Tuple[int, int]] = []

    for lvl in range(1, 6):
        age = level_age[lvl]
        if age is not None:
            formula = (
                f"AND({{Level}} = '{lvl}', "
                f"IS_BEFORE({{Date}}, DATEADD(TODAY(), -{age}, 'day')))"
            )
        else:
            formula = f"{{Level}} = '{lvl}'"

        params = {
            "maxRecords": count,
            "filterByFormula": formula,
            "sort[0][field]": "Date",
            "sort[0][direction]": "asc",
        }

        url = build_url(SPACED_REP_URL, params)
        try:
            resp = requests.get(SPACED_REP_URL, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()

            for rec in data.get("records", []):
                fields = rec.get("fields", {})
                freq = fields.get("Frequency")
                if freq is None:
                    continue
                try:
                    freq_int = int(freq)
                except (TypeError, ValueError):
                    continue
                results.append((freq_int, lvl))
        except Exception:
            # Log the error but continue processing other levels so that the
            # caller gets as many frequencies as possible.
            log_airtable_error("Error fetching spaced repetition data", url)
            continue

    # Sort so that unit tests have deterministic output
    print(f"Fetched spaced repetition levels: {sorted(results)}")
    return sorted(results)


def fetch_flashcards(api_key: str) -> List[Flashcard]:
    """Fetch a set of flashcards using spaced repetition rules."""
    headers = {"Authorization": f"Bearer {api_key}"}
    spaced_pairs = fetch_spaced_rep_frequencies(api_key)
    # Convert the list of tuples into a dictionary for quick lookups
    spaced_map = {freq: lvl for freq, lvl in spaced_pairs}
    spaced_freqs = [freq for freq, _ in spaced_pairs]
    random_freqs = get_random_frequencies(count=25)
    unique_randoms = [f for f in random_freqs if f not in spaced_map]
    selected = spaced_freqs + unique_randoms[: 25 - len(spaced_freqs)]
    formula = "OR(" + ",".join([f'{{Frequency}} = "{i}"' for i in selected]) + ")"
    params = {
        "maxRecords": 25,
        "filterByFormula": formula,
        "sort[0][field]": "Frequency",
        "sort[0][direction]": "asc",
    }
    url = build_url(AIRTABLE_URL, params)
    try:
        resp = requests.get(AIRTABLE_URL, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
        flashcards: List[Flashcard] = []
        for rec in data.get("records", []):
            fields = rec.get("fields", {})
            front = fields.get("french_word", "")
            back = fields.get("english_translation", {}).get("value", "")
            freq_raw = fields.get("Frequency", "")
            # ``Frequency`` may come back as an int or float from Airtable.
            freq_str = str(freq_raw)
            try:
                freq_int = int(float(freq_raw))
            except (TypeError, ValueError):
                freq_int = None
            level = str(spaced_map.get(freq_int, 1)) if freq_int is not None else "1"
            if front or back:
                flashcards.append(
                    Flashcard(front=front, back=back, frequency=freq_str, level=level)
                )
        print("Returning flashcards with levels:", [f"{c.front}:{c.level}" for c in flashcards])
        return flashcards
    except Exception:
        log_airtable_error("Error fetching flashcards from Airtable", url)
    return []


def log_practice(api_key: str, frequency: str, date_str: str) -> bool:
    """Record a practice event in the spaced_rep table.

    If an entry already exists for ``frequency`` its ``Date`` is updated and the
    ``Level`` field is incremented up to a maximum of 5. Otherwise a new row is
    created with ``Level`` set to 1.
    """

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload: Optional[dict] = None
    # Look for an existing record for this frequency
    params = {"filterByFormula": f"{{Frequency}} = '{frequency}'", "maxRecords": 1}
    current_url = build_url(SPACED_REP_URL, params)
    try:
        resp = requests.get(
            SPACED_REP_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()
        records = data.get("records", [])

        if records:
            rec = records[0]
            rec_id = rec.get("id")
            level = rec.get("fields", {}).get("Level", 0)
            try:
                level = int(level)
            except (TypeError, ValueError):
                level = 0
            level = min(level + 1, 5)
            level_str = str(level)

            payload = {"fields": {"Date": date_str, "Level": level_str}}
            update_url = f"{SPACED_REP_URL}/{rec_id}"
            current_url = update_url
            resp = requests.patch(update_url, headers=headers, json=payload)
        else:
            payload = {
                "fields": {"Date": date_str, "Frequency": frequency, "Level": "1"}
            }
            current_url = SPACED_REP_URL
            resp = requests.post(SPACED_REP_URL, headers=headers, json=payload)

        resp.raise_for_status()
        return True
    except Exception:
        log_airtable_error("Error recording practice in Airtable", current_url, payload)
        return False


def log_forget(api_key: str, frequency: str, date_str: str) -> bool:
    """Record a forgotten flashcard in the spaced_rep table.

    If an entry exists for ``frequency`` its ``Date`` is updated and the ``Level``
    field is decremented down to a minimum of 1. If no record exists a new row is
    created with ``Level`` set to 1.
    """

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload: Optional[dict] = None
    params = {"filterByFormula": f"{{Frequency}} = '{frequency}'", "maxRecords": 1}
    current_url = build_url(SPACED_REP_URL, params)
    try:
        resp = requests.get(
            SPACED_REP_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()
        records = data.get("records", [])

        if records:
            rec = records[0]
            rec_id = rec.get("id")
            level = rec.get("fields", {}).get("Level", 0)
            try:
                level = int(level)
            except (TypeError, ValueError):
                level = 0
            level = max(level - 1, 1)
            level_str = str(level)

            payload = {"fields": {"Date": date_str, "Level": level_str}}
            update_url = f"{SPACED_REP_URL}/{rec_id}"
            current_url = update_url
            resp = requests.patch(update_url, headers=headers, json=payload)
        else:
            payload = {
                "fields": {"Date": date_str, "Frequency": frequency, "Level": "1"}
            }
            current_url = SPACED_REP_URL
            resp = requests.post(SPACED_REP_URL, headers=headers, json=payload)

        resp.raise_for_status()
        return True
    except Exception:
        log_airtable_error("Error recording forget in Airtable", current_url, payload)
        return False
