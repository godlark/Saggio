import datetime
from peewee import DecimalField, IntegerField, DateField, DateTimeField, BooleanField

from anki.database.base import BaseModel


class RevisionAnswer(BaseModel):
    datetime = IntegerField(null=False, default=lambda: datetime.datetime.now().timestamp() // 1)
    card_id = IntegerField(null=True)
    expected_ease = IntegerField(null=False)
    chosen_ease = IntegerField(null=False)
    card_due = DateField(null=False)
    card_new_ivl = DecimalField(null=False)
    card_old_ivl = DecimalField(null=False)
    card_new_factor = DecimalField(null=False)
    card_old_factor = DecimalField(null=False)
    time_taken = IntegerField(null=False)
    early = BooleanField(null=False)
    rollover_hour = IntegerField(null=False)