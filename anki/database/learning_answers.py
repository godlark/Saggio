import datetime
from peewee import DecimalField, IntegerField, DateField, DateTimeField, BooleanField, TimeField

from anki.database.base import BaseModel


class LearningAnswer(BaseModel):
    datetime = IntegerField(null=False, default=lambda: datetime.datetime.now().timestamp() // 1)
    card_id = IntegerField(null=False)
    chosen_ease = IntegerField(null=False)
    card_old_ivl = DecimalField(null=False)
    card_old_factor = DecimalField(null=False)
    card_due_in = TimeField(null=False)
    time_taken = IntegerField(null=False)
    rollover_hour = IntegerField(null=False)
