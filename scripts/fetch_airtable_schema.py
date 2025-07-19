import os
import sys
import argparse
import json
import logging
from typing import Any, Dict

import requests

BASE_ID = "applW7zbiH23gDDCK"
SCHEMA_URL = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables"

logger = logging.getLogger(__name__)

def fetch_schema(api_key: str, base_id: str = BASE_ID) -> Dict[str, Any]:
    """Fetch and return the Airtable schema for ``base_id``.

    Parameters
    ----------
    api_key:
        Airtable API key.
    base_id:
        ID of the Airtable base to query.
    """
    headers = {"Authorization": f"Bearer {api_key}"}
    url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
    logger.info("Fetching schema from %s", url)
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()

def main(argv: list[str] | None = None) -> int:
    """Entry point for the fetch_airtable_schema script."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--api-key",
        help="Airtable API key. Defaults to AIRTABLE_API_KEY environment variable",
    )
    parser.add_argument(
        "--base-id",
        default=BASE_ID,
        help="Airtable base ID. Defaults to the french_words_base id",
    )
    args = parser.parse_args(argv)
    api_key = args.api_key or os.getenv("AIRTABLE_API_KEY")
    if not api_key:
        print("Error: Airtable API key not provided", file=sys.stderr)
        return 1
    try:
        schema = fetch_schema(api_key, args.base_id)
    except Exception as exc:
        logger.error("Error fetching schema: %s", exc, exc_info=True)
        return 1
    print(json.dumps(schema, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main())
