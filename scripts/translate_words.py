import argparse
import sys
import logging
from typing import List, Optional, Tuple
import os
import json

import requests
import openai
from jinja2 import Template

AIRTABLE_URL = "https://api.airtable.com/v0/applW7zbiH23gDDCK/french_words"

IMAGE_DIR = "/Users/michaelbevilacqua-linn/FrenchImages"

# Directory that stores all prompt templates
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "prompts")


def _load_prompt_template(filename: str) -> Template:
    """Return a Jinja2 template loaded from the prompts directory."""
    path = os.path.join(PROMPTS_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return Template(f.read())


# Templates for the OpenAI prompts
BASE_PROMPT_TEMPLATE = _load_prompt_template("BASE_PROMPT.txt")
TRANSLATE_PROMPT_TEMPLATE = _load_prompt_template("TRANSLATE_PROMPT.txt")

logger = logging.getLogger(__name__)


def build_url(base_url: str, params: Optional[dict] = None) -> str:
    """Return ``base_url`` with ``params`` encoded as query string."""
    req = requests.Request("GET", base_url, params=params)
    return req.prepare().url


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


def fetch_french_words(api_key: str, start: int, end: int) -> List[Tuple[str, str]]:
    """Fetch French words whose frequency is between ``start`` and ``end``.

    Returns a list of ``(record_id, word)`` tuples ordered by frequency. Any
    records without a ``french_word`` field are ignored. The record ID is
    returned so that callers can update the Airtable row with additional data.
    """
    if not api_key:
        raise ValueError("API key is required")
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
        logger.error("Error fetching records. URL: %s", url, exc_info=True)
        raise

    data = resp.json()
    words: List[Tuple[str, str]] = []
    for rec in data.get("records", []):
        fields = rec.get("fields", {})
        word = fields.get("french_word")
        rec_id = rec.get("id")
        if word and rec_id:
            words.append((rec_id, word))
    return words


def _parse_translation_json(content: str) -> dict:
    """Return the translation data parsed from ``content``.

    ``content`` is expected to be a JSON string. If parsing fails an error is
    logged and the exception is re-raised so that callers know something went
    wrong.
    """
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        logger.error("Invalid JSON from translation: %s", content)
        raise


def translate_word(api_key: str, word: str) -> dict:
    """Translate ``word`` and return rich metadata from GPT-4."""
    if not api_key:
        raise ValueError("API key is required")

    try:
        client = openai.OpenAI(api_key=api_key)
        prompt = TRANSLATE_PROMPT_TEMPLATE.render(word=word)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content.strip()
        return _parse_translation_json(raw)
    except Exception:
        logger.error("Error translating word '%s'", word, exc_info=True)
        raise


def build_image_prompt(api_key: str, word: str) -> str:
    """Return a GPT-4 generated image prompt for ``word``."""
    if not api_key:
        raise ValueError("API key is required")
    """Return a GPT-4 generated image prompt for ``word``."""
    try:
        client = openai.OpenAI(api_key=api_key)
        prompt_request = BASE_PROMPT_TEMPLATE.render(word=word)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt_request}],
        )
        return response.choices[0].message.content.strip()
    except Exception:
        logger.error("Error generating image prompt for '%s'", word, exc_info=True)
        raise


def generate_image(api_key: str, english_word: str, image_dir: str = IMAGE_DIR) -> str:
    """Generate an image for ``english_word`` using OpenAI and save it to ``image_dir``.

    The function sends a prompt to the OpenAI image generation API requesting a
    minimal colored pencil sketch of ``english_word``. The resulting image is
    downloaded and written to ``image_dir``. The path to the saved image is
    returned.
    """
    if not api_key:
        raise ValueError("API key is required")
        
    prompt = build_image_prompt(api_key, english_word)

    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url
        img_resp = requests.get(image_url)
        img_resp.raise_for_status()

        file_name = f"{english_word.replace(' ', '_')}.png"
        file_path = os.path.join(image_dir, file_name)
        with open(file_path, "wb") as f:
            f.write(img_resp.content)
        return file_path
    except Exception as exc:
        logger.error("Error generating image for '%s': %s", english_word, str(exc))
        raise


def upload_image_to_airtable(api_key: str, image_path: str) -> str:
    """Upload ``image_path`` to Airtable and return the attachment ID.

    Parameters
    ----------
    api_key:
        Airtable API key.
    image_path:
        Local path to the image file.

    Returns
    -------
    str
        The attachment ID returned by Airtable.
    """
    headers = {"Authorization": f"Bearer {api_key}"}
    url = "https://api.airtable.com/v0/bases/applW7zbiH23gDDCK/attachments"
    with open(image_path, "rb") as f:
        files = {"file": (os.path.basename(image_path), f, "image/png")}
        resp = requests.post(url, headers=headers, files=files)
    resp.raise_for_status()
    data = resp.json()
    return data.get("id")


def update_word_record(
    api_key: str, record_id: str, translation: dict, attachment_id: str | None
) -> None:
    """Update ``record_id`` in Airtable with ``translation`` and ``attachment_id``.

    ``translation`` is a dictionary returned by :func:`translate_word`. The
    relevant fields are mapped to Airtable columns according to the project
    schema. ``attachment_id`` may be ``None`` if image upload failed, in which
    case the image field is left unchanged.
    """
    fields = {
        "english_word": translation.get("english_word"),
        "example_1": translation.get("sentence_one"),
        "example_2": translation.get("sentence_two"),
        "gender": translation.get("gender"),
        "part_of_speech": translation.get("part_of_speech"),
    }
    if attachment_id:
        fields["image"] = [{"id": attachment_id}]

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    url = f"{AIRTABLE_URL}/{record_id}"
    payload = {"fields": fields}
    resp = requests.patch(url, headers=headers, json=payload)
    resp.raise_for_status()


def main(argv: List[str] | None = None) -> int:
    """Entry point for the ``translate_words`` command.

    Examples
    --------
    Basic usage::

        python -m scripts.translate_words 1-20

    Use the ``--upload-data`` flag to write the generated metadata and image
    back to Airtable. The script relies on the OPENAI_KEY and AIRTABLE_API_KEY
    environment variables for credentials.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("freq-range", help="Frequency range in the form start-end")
    parser.add_argument(
        "--upload-data",
        action="store_true",
        help="Upload translated data and images back to Airtable",
    )
    args = parser.parse_args(argv)

    try:
        start, end = parse_frequency_range(args.freq_range)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    # Get API keys from environment variables
    openai_key = os.getenv("OPENAI_KEY")
    airtable_key = os.getenv("AIRTABLE_API_KEY")

    if not openai_key:
        print("Error: OPENAI_KEY environment variable is not set", file=sys.stderr)
        return 1
    if not airtable_key:
        print("Error: AIRTABLE_API_KEY environment variable is not set", file=sys.stderr)
        return 1

    # Fetch range of words from Airtable and translate each
    try:
        french_words = fetch_french_words(airtable_key, start, end)
        translations = [
            (rec_id, translate_word(openai_key, word)) for rec_id, word in french_words
        ]
    except Exception as exc:
        print(f"Error fetching words: {exc}", file=sys.stderr)
        return 1

    # Print the translation information and then generate images
    for rec_id, data in translations:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        image_path = generate_image(openai_key, data["english_word"])
        if args.upload_data:
            try:
                attachment_id = upload_image_to_airtable(airtable_key, image_path)
                update_word_record(airtable_key, rec_id, data, attachment_id)
            except Exception as exc:
                logger.error(
                    "Error uploading data for record %s: %s", rec_id, str(exc), exc_info=True
                )

    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main())
