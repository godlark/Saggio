import os
import tempfile
import zipfile
from unittest.mock import patch

from anki.exporting import AnkiCollectionPackageExporter
from tests.shared import getEmptyCol as _getEmptyCol


def getEmptyCol():
    return _getEmptyCol(scheduler='anki.schedv3.Scheduler')


def create_learning_card(collection, ivl):
    note = collection.newNote()
    note['Front'] = "one"
    collection.addNote(note)
    card = note.cards()[0]
    card.factor = 2500
    card.ivl = ivl
    card.due = collection.sched.today
    card.type = card.queue = 2
    card.flush()
    return card


def test_if_answer_is_2_then_schedule_as_relearning():
    # ARRANGE
    last_ivl = 100
    collection = getEmptyCol()
    card = create_learning_card(collection, last_ivl)
    exporter = AnkiCollectionPackageExporter(collection)

    # ACT & ASSERT
    (fd, nam) = tempfile.mkstemp(suffix=".zip")
    os.close(fd)
    os.unlink(nam)

    z = zipfile.ZipFile(nam, "w", zipfile.ZIP_DEFLATED, allowZip64=True)
    exporter.doExport(z, nam)