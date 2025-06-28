from flask import Flask, jsonify, render_template
from dataclasses import asdict
from flashcards import flashcards, Flashcard
import os
import sys
from airtable_data_access import fetch_flashcards

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello, world!"

@app.route("/flashcards")
def flashcards_page():
    """Render a page with visual flashcards."""
    return render_template("flashcards.html", flashcards=flashcards)

@app.route("/api/flashcards")
def list_flashcards():
    """Return all flashcards as JSON."""
    return jsonify([asdict(card) for card in flashcards])


@app.route("/flashcards_airtable")
def flashcards_airtable_page():
    """Render flashcards from Airtable."""
    api_key = os.environ.get("AIRTABLE_API_KEY")
    if not api_key:
        print("AIRTABLE_API_KEY environment variable not set", file=sys.stderr)
        airtable_cards = []
    else:
        airtable_cards = fetch_flashcards(api_key)

    return render_template(
        "flashcards_airtable.html",
        flashcards=airtable_cards,
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
