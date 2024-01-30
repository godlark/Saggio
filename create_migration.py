from peewee_migrate import Router
from peewee import SqliteDatabase

from anki.database.base import BaseModel
from anki.database.learning_answers import LearningAnswer
from anki.database.note_types import NoteType
from anki.database.revision_answers import RevisionAnswer

router = Router(SqliteDatabase('/Users/sladom/Library/Application Support/Saggio/dd/collection_new.sqlite3'), migrate_dir='./anki/database/migrations')

# Create migration
router.create('learning_answers', auto=[BaseModel, LearningAnswer, NoteType, RevisionAnswer])
