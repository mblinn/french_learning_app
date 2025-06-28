from dataclasses import dataclass


@dataclass
class Flashcard:
    front: str  # French word
    back: str   # English translation
    frequency: str | None = None


# Initial set of flashcards
flashcards = [
    Flashcard(front="Le Chat", back="Cat"),
    Flashcard(front="Le Chien", back="Dog"),
    Flashcard(front="La Maison", back="House"),
    Flashcard(front="Le Homme", back="Man"),
    Flashcard(front="L'Amour", back="Love"),
    Flashcard(front="Savoir", back="To Know"),
    Flashcard(front="Parler", back="To Talk"),
    Flashcard(front="L'Ordinateur", back="Computer"),
    Flashcard(front="La Norriture", back="Food"),
    Flashcard(front="Le Verre", back="Glass"),
    Flashcard(front="L'ecole", back="School"),
    Flashcard(front="Le nuit", back="Night"),
    Flashcard(front="Bonjour", back="Hello (Day)"),
    Flashcard(front="Bonsoir", back="Hello (Night)"),
    Flashcard(front="Voir", back="To See"),
]
