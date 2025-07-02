from flask import Flask, jsonify, request
from dataclasses import asdict
import os
import sys
from datetime import datetime
from airtable_data_access import Flashcard, fetch_flashcards, log_practice, log_forget

app = Flask(__name__)

@app.route("/api/flashcards")
def list_flashcards() -> jsonify:
    """Return flashcards fetched from Airtable as JSON."""
    api_key = os.environ.get("AIRTABLE_API_KEY")
    if not api_key:
        print("AIRTABLE_API_KEY environment variable not set", file=sys.stderr)
        airtable_cards: list[Flashcard] = []
    else:
        airtable_cards = fetch_flashcards(api_key)
    return jsonify([asdict(card) for card in airtable_cards])


@app.route("/api/practice", methods=["POST"])
def record_practice():
    """Record practice of a flashcard."""
    data = request.get_json(force=True)
    freq = data.get("frequency")
    if not freq:
        return jsonify({"error": "frequency required"}), 400
    api_key = os.environ.get("AIRTABLE_API_KEY")
    if not api_key:
        print("AIRTABLE_API_KEY environment variable not set", file=sys.stderr)
        return jsonify({"error": "api key missing"}), 500
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    success = log_practice(api_key, freq, date_str)
    if not success:
        return jsonify({"error": "logging failed"}), 500
    return jsonify({"status": "ok"})


@app.route("/api/forget", methods=["POST"])
def record_forget():
    """Record forgetting a flashcard."""
    data = request.get_json(force=True)
    freq = data.get("frequency")
    if not freq:
        return jsonify({"error": "frequency required"}), 400
    api_key = os.environ.get("AIRTABLE_API_KEY")
    if not api_key:
        print("AIRTABLE_API_KEY environment variable not set", file=sys.stderr)
        return jsonify({"error": "api key missing"}), 500
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    success = log_forget(api_key, freq, date_str)
    if not success:
        return jsonify({"error": "logging failed"}), 500
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
