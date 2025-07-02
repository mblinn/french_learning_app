import argparse
import sys
from typing import List, Tuple

import requests

from airtable_data_access import AIRTABLE_URL, build_url


def parse_frequency_range(range_str: str) -> Tuple[int, int]:
    """Return the numeric start and end of ``range_str``.

    ``range_str`` must be in the form ``start-end`` where both ``start`` and
    ``end`` are integers and ``start`` is less than or equal to ``end``.
    """
    try:
        start_str, end_str = range_str.split("-", 1)
        start = int(start_str)
        end = int(end_str)
    except ValueError as exc:
        raise ValueError("range must be in the form start-end") from exc

    if start > end:
        raise ValueError("start must not be greater than end")
    return start, end


def fetch_words(api_key: str, start: int, end: int) -> List[str]:
    """Fetch French words whose frequency is between ``start`` and ``end``.

    Returns a list of words ordered by frequency. Any records without a
    ``french_word`` field are ignored.
    """
    headers = {"Authorization": f"Bearer {api_key}"}
    formula = f"AND({{Frequency}} >= {start}, {{Frequency}} <= {end})"
    params = {
        "filterByFormula": formula,
        "sort[0][field]": "Frequency",
        "sort[0][direction]": "asc",
    }
    url = build_url(AIRTABLE_URL, params)
    try:
        resp = requests.get(AIRTABLE_URL, headers=headers, params=params)
        resp.raise_for_status()
    except Exception:
        print(f"Error fetching records. URL: {url}", file=sys.stderr)
        raise

    data = resp.json()
    words: List[str] = []
    for rec in data.get("records", []):
        fields = rec.get("fields", {})
        word = fields.get("french_word")
        if word:
            words.append(word)
    return words


def main(argv: List[str] | None = None) -> int:
    """Entry point for the ``translate_words`` command.

    Examples
    --------
    Basic usage with explicit module execution::

        python -m scripts.translate_words 1-20 MY_API_KEY

    Or run the script directly from the project root::

        ./scripts/translate_words.py 50-100 MY_API_KEY
    """
    parser = argparse.ArgumentParser(description="Fetch French words from Airtable")
    parser.add_argument("freq_range", help="frequency range, e.g. 1-20")
    parser.add_argument("api_key", help="Airtable API key")
    args = parser.parse_args(argv)

    start, end = parse_frequency_range(args.freq_range)
    words = fetch_words(args.api_key, start, end)
    for w in words:
        print(w)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
