from flask import Flask, jsonify, render_template, request
from dataclasses import asdict
from flashcards import flashcards, Flashcard
import os
import sys
from datetime import datetime
from airtable_data_access import fetch_flashcards, log_practice, update_level

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


@app.route("/api/practice", methods=["POST"])
def record_practice():
    """Record practice of a flashcard."""
    data = request.get_json(force=True)
    freq = data.get("frequency")
    action = data.get("action")
    if not freq or action not in {"got_it", "forgot_it"}:
        return jsonify({"error": "frequency and action required"}), 400
    api_key = os.environ.get("AIRTABLE_API_KEY")
    if not api_key:
        print("AIRTABLE_API_KEY environment variable not set", file=sys.stderr)
        return jsonify({"error": "api key missing"}), 500
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    success = log_practice(api_key, freq, date_str)
    if not success:
        return jsonify({"error": "logging failed"}), 500

    delta = 1 if action == "got_it" else -1
    level = update_level(api_key, freq, delta)
    if level is None:
        return jsonify({"error": "level update failed"}), 500
    return jsonify({"status": "ok", "level": level})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
