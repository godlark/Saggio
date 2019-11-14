from tests.shared import getEmptyCol as _getEmptyCol


def getEmptyCol():
    return _getEmptyCol(scheduler='anki.schedv3.Scheduler')


def checkRevIvl(d, c, targetIvl):
    min, max = d.sched._fuzzIvlRange(targetIvl)
    return min <= c.ivl <= max


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
    last_factor = card.factor

    # ACT
    collection.reset()
    card = collection.sched.getCard()
    collection.sched.answerCard(card, 2)

    # ASSERT
    # Fail the card. Factor should be updated, ivl should
    # stay the same
    new_factor = card.factor
    assert card.queue == 1
    assert card.type == 3
    assert card.ivl == last_ivl
    assert new_factor < last_factor

    # ACT
    # Graduate a relearning card
    collection.sched.answerCard(card, 4)

    # ASSERT
    # Graduation of relearning card (irrespectively if answer is 3 or 4)
    # shouldn't update ivl neither factor
    assert card.queue == card.type == 2
    assert card.ivl == last_ivl
    assert card.due == collection.sched.today + card.ivl
    assert card.factor == new_factor


def test_if_answer_is_1_then_schedule_as_relearning():
    # ARRANGE
    last_ivl = 100
    collection = getEmptyCol()
    card = create_learning_card(collection, last_ivl)
    last_factor = card.factor

    # ACT
    collection.reset()
    card = collection.sched.getCard()
    collection.sched.answerCard(card, 1)

    # ASSERT
    # Fail the card. Factor and ivl should be updated
    new_factor = card.factor
    new_ivl = card.ivl
    assert card.queue == 1
    assert card.type == 3
    assert new_ivl < last_ivl
    assert new_factor < last_factor

    # ACT
    # Graduate a relearning card
    collection.sched.answerCard(card, 4)

    # ASSERT
    # Graduation of relearning card (irrespectively if answer is 3 or 4)
    # shouldn't update ivl neither factor
    assert card.queue == card.type == 2
    assert card.ivl == new_ivl
    assert card.due == collection.sched.today + card.ivl
    assert card.factor == new_factor


def test_if_answer_is_3_then_schedule_with_bigger_ivl():
    # ARRANGE
    last_ivl = 100
    collection = getEmptyCol()
    card = create_learning_card(collection, last_ivl)
    last_factor = card.factor

    # ACT
    collection.reset()
    card = collection.sched.getCard()
    collection.sched.answerCard(card, 3)

    # ASSERT
    # Pass the card. Ivl should be increased, factor should stay the same.
    assert card.queue == card.type == 2
    assert card.ivl > last_ivl
    assert card.factor == last_factor


def test_if_answer_is_4_then_schedule_with_bigger_ivl_and_factor():
    # ARRANGE
    last_ivl = 100
    collection = getEmptyCol()
    card = create_learning_card(collection, last_ivl)
    last_factor = card.factor

    # ACT
    collection.reset()
    card = collection.sched.getCard()
    collection.sched.answerCard(card, 4)

    # ASSERT
    # Pass the card with "Easy". Ivl and factor should be increased.
    assert card.queue == card.type == 2
    assert card.ivl > last_ivl
    assert card.factor > last_factor
