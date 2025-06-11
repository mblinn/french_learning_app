from flask import Flask, jsonify
from dataclasses import asdict
from flashcards import flashcards
import os

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello, world!"

@app.route("/flashcards")
def list_flashcards():
    """Return all flashcards as JSON."""
    return jsonify([asdict(card) for card in flashcards])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
