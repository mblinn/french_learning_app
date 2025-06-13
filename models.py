from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy without an app for application factory compatibility
# The app will call `db.init_app(app)`
db = SQLAlchemy()

class Word(db.Model):
    __tablename__ = 'words'

    id = db.Column(db.Integer, primary_key=True)
    french = db.Column(db.Text, nullable=False)
    english = db.Column(db.Text, nullable=False)
    part_of_speech = db.Column(
        db.Text,
        db.CheckConstraint(
            "part_of_speech IN ('noun', 'verb', 'adjective', 'adverb', 'pronoun', 'preposition', 'conjunction', 'interjection', 'phrase', 'other')"
        ),
    )
    gender = db.Column(
        db.Text,
        db.CheckConstraint("gender IN ('m', 'f', 'n/a')"),
    )
    is_plural = db.Column(db.Boolean, server_default=db.text('false'))
    is_reflexive = db.Column(db.Boolean, server_default=db.text('false'))
    preposition = db.Column(
        db.Text,
        db.CheckConstraint(
            "preposition IN ('à', 'de', 'à + inf', 'de + inf', 'none', 'other')"
        ),
        server_default='none'
    )
    example_sentence_fr = db.Column(db.Text)
    example_sentence_en = db.Column(db.Text)
    notes = db.Column(db.Text)
    frequency_rank = db.Column(
        db.Integer,
        db.CheckConstraint('frequency_rank > 0')
    )

    def __repr__(self) -> str:
        return f"<Word {self.french} - {self.english}>"
