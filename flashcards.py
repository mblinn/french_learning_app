from dataclasses import dataclass


@dataclass
class Flashcard:
    """Simple container for a flashcard."""

    front: str  # French word
    back: str  # English translation
    frequency: str | None = None
    level: str | None = None


# Initial set of flashcards
flashcards = [
    # Levels are repeated so the UI can demonstrate color coding for each one
    Flashcard(front="Le Chat", back="Cat", level="1"),
    Flashcard(front="Le Chien", back="Dog", level="2"),
    Flashcard(front="La Maison", back="House", level="3"),
    Flashcard(front="Le Homme", back="Man", level="4"),
    Flashcard(front="L'Amour", back="Love", level="5"),
    Flashcard(front="Savoir", back="To Know", level="1"),
    Flashcard(front="Parler", back="To Talk", level="2"),
    Flashcard(front="L'Ordinateur", back="Computer", level="3"),
    Flashcard(front="La Norriture", back="Food", level="4"),
    Flashcard(front="Le Verre", back="Glass", level="5"),
    Flashcard(front="L'ecole", back="School", level="1"),
    Flashcard(front="Le nuit", back="Night", level="2"),
    Flashcard(front="Bonjour", back="Hello (Day)", level="3"),
    Flashcard(front="Bonsoir", back="Hello (Night)", level="4"),
    Flashcard(front="Voir", back="To See", level="5"),
]
