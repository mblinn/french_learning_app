import argparse
import sys
import logging
from typing import List, Optional, Tuple
import os

import requests
import openai

AIRTABLE_URL = "https://api.airtable.com/v0/applW7zbiH23gDDCK/french_words"

IMAGE_DIR = "/Users/michaelbevilacqua-linn/FrenchImages"

# Base prompt for GPT-4 to generate the image prompt
BASE_PROMPT = (
    "Act as a prompt engineer creating a prompt for an image generation model. "
    "You will be given a word and will need to generate a prompt for it. Use the "
    "following as the base prompt.\n\nCreate a simple colorful line sketch of #WORD# "
    "The drawings should have a soft, textured look, with visible strokes that vary in intensity. " 
    "You should be able to see individual lines or hatching marks, giving them a sketchbook feel. "
    "\n\nFor simple nouns, replace #WORD# with " 
    " the letter 'a' followed by the word.\n\nFor verbs, "
    "replace #WORD# with a description that demonstrates the action. Examples:\n\n"
    "run -> replace #WORD# with the phrase \"a running man\"\njump -> replace "
    "#WORD# with the phrase \"a jumping woman\"\nthrow -> replace #WORD# with "
    "the phrase \"a ball being thrown\"\n\nFor abstract concepts, think and "
    "come up with an image that represents the concept. Examples:\n\nlove -> "
    "replace #WORD# with a heart\nhate -> replace #WORD# with two people "
    "arguing\ntime -> replace #WORD# with a clock\n\nThe word is: "
    "#INITIAL_REPLACED_WORD#"
)

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


def fetch_french_words(api_key: str, start: int, end: int) -> List[str]:
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
    words: List[str] = []
    for rec in data.get("records", []):
        fields = rec.get("fields", {})
        word = fields.get("french_word")
        if word:
            words.append(word)
    return words


def translate_word(api_key: str, word: str) -> str:
    """Translate ``word`` from English to French using GPT-4."""
    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "user",
                    "content": f"Translate the French word '{word}' into English. Respond only with the English translation. If the word cannot be translated directly, respond with 'N/A'.",
                }
            ],
        )
        return response.choices[0].message.content.strip()
    except Exception:
        logger.error("Error translating word '%s'", word, exc_info=True)
        raise


def build_image_prompt(api_key: str, word: str) -> str:
    """Return a GPT-4 generated image prompt for ``word``."""
    try:
        client = openai.OpenAI(api_key=api_key)
        prompt_request = BASE_PROMPT.replace("#INITIAL_REPLACED_WORD#", word)
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
    prompt = build_image_prompt(api_key, english_word)

    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.images.generate(
            prompt=prompt,
            n=1,
            size="1024x1024",
            model="dall-e-3",
        )
        image_url = response.data[0].url

        img_resp = requests.get(image_url)
        img_resp.raise_for_status()

        os.makedirs(image_dir, exist_ok=True)
        file_name = f"{english_word.replace(' ', '_')}.png"
        file_path = os.path.join(image_dir, file_name)
        with open(file_path, "wb") as f:
            f.write(img_resp.content)
        return file_path
    except Exception:
        logger.error("Error generating image for '%s'", english_word, exc_info=True)
        raise


def main(argv: List[str] | None = None) -> int:
    """Entry point for the ``translate_words`` command.

    Examples
    --------
    Basic usage with explicit module execution::

        python -m scripts.translate_words 1-20 MY_API_KEY

    Or run the script directly from the project root::

        ./scripts/translate_words.py --freq_range=50-100 --api_key==MY_API_KEY
    """
    parser = argparse.ArgumentParser(description="Fetch French words from Airtable")
    parser.add_argument("--freq_range", help="frequency range, e.g. 1-20")
    parser.add_argument("--api_key", help="Airtable API key")
    parser.add_argument(
        "--translate",
        action="store_true",
        help="translate fetched words using OpenAI",
    )
    parser.add_argument(
        "--generate_image",
        action="store_true",
        help="generate an illustrative image for each word using OpenAI",
    )
    parser.add_argument("--open_ai_api_key", help="OpenAI API key", default=None)
    args = parser.parse_args(argv)

    start, end = parse_frequency_range(args.freq_range)
    french_words = fetch_french_words(args.api_key, start, end)

    need_openai = args.translate or args.generate_image
    if need_openai and not args.open_ai_api_key:
        parser.error("--open_ai_api_key is required when --translate or --generate_image is set")

    if need_openai:
        translations = [
            (french_word, translate_word(args.open_ai_api_key, french_word))
            for french_word in french_words
        ]
    else:
        translations = [(french_word, None) for french_word in french_words]

    if args.translate:
        for french_word, english_word in translations:
            print(f"French: {french_word} -- English: {english_word}")
    else:
        for french_word, _ in translations:
            print(french_word)

    if args.generate_image:
        for _, english_word in translations:
            if english_word:
                generate_image(args.open_ai_api_key, english_word)

    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main())
