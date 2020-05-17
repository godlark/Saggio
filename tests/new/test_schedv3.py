from unittest.mock import patch

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


def create_late_learning_card(collection, ivl, late):
    note = collection.newNote()
    note['Front'] = "one"
    collection.addNote(note)
    card = note.cards()[0]
    card.factor = 2500
    card.ivl = ivl
    card.due = collection.sched.today - late
    card.type = card.queue = 2
    card.flush()
    return card


@patch('anki.schedv3.Scheduler.logRev')
def test_if_answer_is_2_then_schedule_as_relearning(logRev):
    # ARRANGE
    last_ivl = 100
    collection = getEmptyCol()
    card = create_learning_card(collection, last_ivl)
    last_factor = card.factor
    first_answer_hard = 2

    # ACT
    collection.reset()
    card = collection.sched.getCard()
    collection.sched.answerCard(card, first_answer_hard)

    # ASSERT
    # Fail the card. Factor should be updated, ivl should
    # stay the same
    new_factor = card.factor
    new_ivl = card.ivl
    # TODO: Fix tests but not using lastIvl and making configurable contrainedIvl factor
    updated_last_ivl = card.lastIvl

    assert updated_last_ivl < last_ivl
    assert card.queue == 1
    assert card.type == 3
    # TODO: Should we decrease interval when the answer is "Hard"
    assert 0.8 * last_ivl <= new_ivl <= last_ivl
    # assert card.ivl == last_ivl
    assert new_factor < last_factor
    logRev.assert_called_once_with(collection, card, first_answer_hard, 0, 1)

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
    updated_last_ivl = card.lastIvl

    assert updated_last_ivl < last_ivl
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


@patch('anki.schedv3.Scheduler.logRev')
def test_if_answer_is_3_then_schedule_with_bigger_ivl(logRev):
    # ARRANGE
    last_ivl = 100
    collection = getEmptyCol()
    card = create_learning_card(collection, last_ivl)
    last_factor = card.factor
    answer_good = 3

    # ACT
    collection.reset()
    card = collection.sched.getCard()
    collection.sched.answerCard(card, answer_good)

    # ASSERT
    # Pass the card. Ivl should be increased, factor should stay the same.
    updated_last_ivl = card.lastIvl

    assert updated_last_ivl == last_ivl
    assert card.queue == card.type == 2
    assert card.ivl > last_ivl
    assert card.factor == last_factor

    logRev.assert_called_once_with(collection, card, answer_good, None, 1)


def test_if_card_parameters_stay_the_same_when_bad_result_predicted():
    # ARRANGE
    last_ivl = 100
    late_days = last_ivl * 2
    collection = getEmptyCol()
    card = create_late_learning_card(collection, last_ivl, late_days)
    last_factor = card.factor

    # ACT
    collection.reset()
    card = collection.sched.getCard()
    collection.sched.answerCard(card, 1)

    # ASSERT
    # Failed card - but expected. Ivl should stay the same, factor should stay the same.
    new_factor = card.factor
    new_ivl = card.ivl
    updated_last_ivl = card.lastIvl

    assert updated_last_ivl == last_ivl
    assert card.queue == 1
    assert card.type == 3
    assert new_ivl == last_ivl
    assert new_factor == last_factor
    assert card.lapses == 0

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
    assert card.lapses == 0


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
    updated_last_ivl = card.lastIvl

    assert updated_last_ivl > last_ivl
    assert card.queue == card.type == 2
    assert card.ivl > last_ivl
    assert card.factor > last_factor


def test_if_moves_learning_to_the_previous_step():
    # ARRANGE
    last_ivl = 100
    collection = getEmptyCol()
    card = create_learning_card(collection, last_ivl)
    last_factor = card.factor

    # ACT
    collection.reset()
    card = collection.sched.getCard()
    # Fail the card
    collection.sched.answerCard(card, 1)
    # Move to the next stp
    first_left = card.left
    collection.sched.answerCard(card, 3)
    second_left = card.left
    collection.sched.answerCard(card, 3)
    third_left = card.left

    # ASSERT
    # Fail the step, it should move to previous step
    collection.sched.answerCard(card, 1)
    assert card.left == second_left


def test_scatter_fairly_cards_from_different_decks_returns_the_same_cards():
    # ARRANGE
    deck_id = 1
    card_ids = list(range(1, 7))
    cards = [(card_id, deck_id) for card_id in card_ids]
    all_decks = [{'id': 1}]
    decks_parents = {1: []}

    # ACT
    from anki.schedv3 import Scheduler
    results = Scheduler.scatter_fairly_cards_from_different_decks(cards, all_decks, decks_parents)

    # ASSERT
    assert card_ids == results