from dataclasses import dataclass

@dataclass
class Flashcard:
    front: str  # French word
    back: str   # English translation

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
]
