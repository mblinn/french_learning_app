from flask import Flask, jsonify, render_template
from dataclasses import asdict
from flashcards import flashcards
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
