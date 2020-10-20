from anki.stats import CollectionStats
from tests.shared import getEmptyCol as _getEmptyCol
from datetime import datetime


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


def test_filter_by_quantiles_all_elements_are_the_same():
    data = CollectionStats.filter_by_quantiles(10, 90, [50, 50, 50])
    assert data == (50, 50, [(50, 3)])


def test_days_studied_works_with_old_logs():
    # ARRANGE
    col = getEmptyCol()
    ivl = 1
    card = create_learning_card(col, ivl)
    hard_answer = 2
    factor = 2500
    time_taken = 10 # seconds

    for day in range(1, 31):
        timestamp = datetime(2020, 4, day, 12, 0, 0, 0).timestamp()
        # days, due were added, so previous logs have 0s
        col.db.execute(
            "insert into revlog values (?,?,?,?,?,?,?,?,?,?,?)",
            int(timestamp * 1000), card.id, col.usn(), hard_answer, ivl, ivl, factor, time_taken, 1, 0, 0)

    # ACT
    collection_stats = CollectionStats(col)
    collection_stats.type = 2
    return_value = collection_stats._daysStudied()

    # ASSERT
    # number of days should be 30
    assert return_value[0] == 30