"""initial words table"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'words',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('french', sa.Text(), nullable=False),
        sa.Column('english', sa.Text(), nullable=False),
        sa.Column(
            'part_of_speech',
            sa.Text(),
            sa.CheckConstraint(
                "part_of_speech IN ('noun', 'verb', 'adjective', 'adverb', 'pronoun', 'preposition', 'conjunction', 'interjection', 'phrase', 'other')"
            ),
        ),
        sa.Column(
            'gender',
            sa.Text(),
            sa.CheckConstraint("gender IN ('m', 'f', 'n/a')"),
        ),
        sa.Column('is_plural', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('is_reflexive', sa.Boolean(), server_default=sa.text('false')),
        sa.Column(
            'preposition',
            sa.Text(),
            sa.CheckConstraint(
                "preposition IN ('à', 'de', 'à + inf', 'de + inf', 'none', 'other')"
            ),
            server_default='none',
        ),
        sa.Column('example_sentence_fr', sa.Text()),
        sa.Column('example_sentence_en', sa.Text()),
        sa.Column('notes', sa.Text()),
        sa.Column('frequency_rank', sa.Integer(), sa.CheckConstraint('frequency_rank > 0')),
    )


def downgrade():
    op.drop_table('words')
