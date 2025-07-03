from flask import Flask, jsonify, render_template, request
from dataclasses import asdict
import os
import sys
import logging
from datetime import datetime
from airtable_data_access import fetch_flashcards, log_practice, log_forget

app = Flask(__name__)

logger = logging.getLogger(__name__)

@app.route("/flashcards_airtable")
def flashcards_airtable_page():
    """Render flashcards from Airtable."""
    api_key = os.environ.get("AIRTABLE_API_KEY")
    if not api_key:
        logger.error("AIRTABLE_API_KEY environment variable not set")
        airtable_cards = []
    else:
        airtable_cards = fetch_flashcards(api_key)
        logger.info(
            "Loaded flashcards: %s", [f"{c.front}:{c.level}" for c in airtable_cards]
        )

    return render_template(
        "flashcards_airtable.html",
        flashcards=airtable_cards,
    )


@app.route("/api/practice", methods=["POST"])
def record_practice():
    """Record practice of a flashcard."""
    data = request.get_json(force=True)
    freq = data.get("frequency")
    if not freq:
        return jsonify({"error": "frequency required"}), 400
    api_key = os.environ.get("AIRTABLE_API_KEY")
    if not api_key:
        logger.error("AIRTABLE_API_KEY environment variable not set")
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
        logger.error("AIRTABLE_API_KEY environment variable not set")
        return jsonify({"error": "api key missing"}), 500
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    success = log_forget(api_key, freq, date_str)
    if not success:
        return jsonify({"error": "logging failed"}), 500
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
