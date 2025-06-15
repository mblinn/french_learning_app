from flask import Flask, jsonify, render_template
from dataclasses import asdict
from flashcards import flashcards, Flashcard
import requests
import os

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
    airtable_cards = []
    if api_key:
        url = "https://api.airtable.com/v0/french_words_base/french_words"
        headers = {"Authorization": f"Bearer {api_key}"}
        params = {"maxRecords": 20}
        try:
            resp = requests.get(url, headers=headers, params=params)
            if resp.status_code == 200:
                data = resp.json()
                for rec in data.get("records", []):
                    fields = rec.get("fields", {})
                    front = fields.get("french_word", "")
                    back = fields.get("english_word", "")
                    if front or back:
                        airtable_cards.append(Flashcard(front=front, back=back))

    return render_template(
        "flashcards_airtable.html",
        flashcards=airtable_cards,
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
