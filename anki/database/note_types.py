from peewee import AutoField, TextField

from anki.database.base import BaseModel


class NoteType(BaseModel):
    id = AutoField()
    title = TextField()
    description = TextField(null=True)


class NoteTypes:
    def get_all(self):
        query = NoteType.select()
        return [note_type for note_type in query]