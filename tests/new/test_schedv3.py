from unittest.mock import patch

from anki.consts import NEW_CARDS_RANDOM
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


def create_new_card(collection):
    note = collection.newNote()
    note['Front'] = "one"
    collection.addNote(note)
    card = note.cards()[0]
    card.type = card.queue = 0
    card.flush()
    return card


@patch('anki.schedv3.Scheduler.logRev')
@patch('anki.schedv3.Scheduler.getFuzz')
def test_if_answer_is_2_then_schedule_as_relearning(getFuzz, logRev):
    # ARRANGE
    getFuzz.return_value = False
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
    assert card.queue == 1
    assert card.type == 3
    assert new_ivl < last_ivl
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
    assert card.due == int(round(collection.sched.today + card.ivl))
    assert card.factor == new_factor


@patch('anki.schedv3.Scheduler.getFuzz')
def test_if_answer_1_decreases_ivl_and_factor_more_than_answer_2(getFuzz):
    # ARRANGE
    getFuzz.return_value = False
    last_ivl = 100
    collection = getEmptyCol()
    card1 = create_learning_card(collection, last_ivl)
    card2 = create_learning_card(collection, last_ivl)
    answer_hard = 2
    answer_wrong = 1

    # ACT
    collection.reset()
    card1.startTimer()
    collection.sched.answerCard(card1, answer_wrong)
    card2.startTimer()
    collection.sched.answerCard(card2, answer_hard)

    # ASSERT
    # Ivl and factor should be lower for the first card
    assert card1.ivl < card2.ivl
    assert card1.ivl < card2.factor


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
    assert card.due == int(round(collection.sched.today + card.ivl))
    assert card.factor == new_factor


@patch('anki.schedv3.Scheduler.logRev')
@patch('anki.schedv3.Scheduler.getFuzz')
def test_if_answer_is_3_then_schedule_with_bigger_ivl(getFuzz, logRev):
    # ARRANGE
    getFuzz.return_value = False
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
    assert card.queue == card.type == 2
    assert card.factor == last_factor
    assert last_ivl * card.factor / 1000 == card.ivl

    logRev.assert_called_once_with(collection, card, answer_good, None, 1)


@patch('anki.schedv3.Scheduler.getFuzz')
def test_if_card_parameters_stay_the_same_when_bad_result_predicted(getFuzz):
    # ARRANGE
    getFuzz.return_value = False
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
    # Failed card - but expected. Ivl should decrease, factor should stay the same.
    new_factor = card.factor
    new_ivl = card.ivl
    assert card.queue == 1
    assert card.type == 3
    assert last_ivl / (last_factor / 1000) == new_ivl
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


@patch('anki.schedv3.Scheduler.getFuzz')
def test_if_card_parameters_stay_the_same_when_hard_answer_predicted(getFuzz):
    # ARRANGE
    getFuzz.return_value = False
    last_ivl = 100
    late_days = last_ivl
    collection = getEmptyCol()
    card = create_late_learning_card(collection, last_ivl, late_days)
    last_factor = card.factor

    # ACT
    collection.reset()
    card = collection.sched.getCard()
    collection.sched.answerCard(card, 2)

    # ASSERT
    # Failed card - but expected. Ivl should stay the same, factor should stay the same.
    new_factor = card.factor
    new_ivl = card.ivl
    assert card.queue == 1
    assert card.type == 3
    assert last_ivl == new_ivl
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
    assert card.due == int(round(collection.sched.today + card.ivl))
    assert card.factor == new_factor
    assert card.lapses == 0


@patch('anki.schedv3.Scheduler.getFuzz')
def test_if_card_parameters_increase_when_hard_answered_and_wrong_answer_predicted(getFuzz):
    # ARRANGE
    getFuzz.return_value = False
    last_ivl = 100
    late_days = last_ivl * 2
    collection = getEmptyCol()
    card = create_late_learning_card(collection, last_ivl, late_days)
    last_factor = card.factor

    # ACT
    collection.reset()
    card = collection.sched.getCard()
    collection.sched.answerCard(card, 2)

    # ASSERT
    # Failed card - but expected. Ivl should increase a little, factor should increase
    new_factor = card.factor
    new_ivl = card.ivl
    assert card.queue == 1
    assert card.type == 3
    assert new_factor > last_factor
    # Both factor and ivl are increased, and than ivl is multiplied by = (new_factor/last_factor)
    assert new_ivl > last_ivl * (new_factor / last_factor)
    assert card.lapses == 0

    # ACT
    # Graduate a relearning card
    collection.sched.answerCard(card, 4)

    # ASSERT
    # Graduation of relearning card (irrespectively if answer is 3 or 4)
    # shouldn't update ivl neither factor
    assert card.queue == card.type == 2
    assert card.ivl == new_ivl
    assert card.due == int(round(collection.sched.today + card.ivl))
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
    assert card.queue == card.type == 2
    assert card.ivl > last_ivl
    assert card.factor > last_factor
    # Both factor and ivl are increased, and than ivl is multiplied by new factor
    assert card.ivl > last_ivl * card.factor / 1000


@patch('anki.decks.DeckManager.confForDid')
@patch('anki.schedv3.Scheduler.getFuzz')
def test_if_ivlFct_is_not_used(getFuzz, confForDid):
    # ARRANGE
    getFuzz.return_value = False
    confForDid.return_value = {
        'new': {'order': NEW_CARDS_RANDOM, 'perDay': 100},
        'rev': {'perDay': 100, 'ivlFct': 2, 'maxIvl': 1024},
        'dyn': {},
        'maxTaken': 60,
    }
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
    # Pass the card with "Good". Ivl should be increased and factor should stay the same
    assert card.queue == card.type == 2
    assert card.factor == last_factor
    assert card.factor / 1000 * last_ivl == card.ivl


@patch('anki.decks.DeckManager.confForDid')
@patch('anki.schedv3.Scheduler.getFuzz')
def test_if_initial_factor_is_used(getFuzz, confForDid):
    # ARRANGE
    getFuzz.return_value = False
    graduate_immediately_ivl = 4
    graduate_normally_ivl = 2
    confForDid.return_value = {
        'new': {'order': NEW_CARDS_RANDOM, 'perDay': 100, 'initialFactor': 4000, 'delays': [0, 2, 10],
                'ints': [graduate_normally_ivl, graduate_immediately_ivl]},
        'rev': {'perDay': 100, 'maxIvl': 1024},
        'dyn': {},
        'maxTaken': 60,
    }
    collection = getEmptyCol()
    card = create_new_card(collection)
    answer_gradue_immediately = 4

    # ACT
    collection.reset()
    card = collection.sched.getCard()
    collection.sched.answerCard(card, answer_gradue_immediately)

    # ASSERT
    # Pass the card with "Good". Ivl should be increased and factor should stay the same
    assert card.queue == card.type == 2
    assert card.factor == 4000
    assert card.ivl == graduate_immediately_ivl


@patch('anki.schedv3.Scheduler.getFuzz')
def test_if_ivl_for_more_mature_card_increases_less(getFuzz):
    # ARRANGE
    getFuzz.return_value = False
    collection = getEmptyCol()
    last_mature_ivl = 1000
    last_fresh_ivl = 100
    card1 = create_learning_card(collection, last_fresh_ivl)
    card2 = create_learning_card(collection, last_mature_ivl)
    answer_very_good = 4

    # ACT
    collection.reset()
    card1.startTimer()
    collection.sched.answerCard(card1, answer_very_good)
    card2.startTimer()
    collection.sched.answerCard(card2, answer_very_good)

    # ASSERT
    assert card1.factor < card2.factor
    assert card1.ivl / last_fresh_ivl > card2.ivl / last_mature_ivl


@patch('anki.schedv3.Scheduler.getFuzz')
def test_if_ivl_for_more_mature_card_decreases_more(getFuzz):
    # ARRANGE
    getFuzz.return_value = False
    collection = getEmptyCol()
    last_mature_ivl = 1000
    last_fresh_ivl = 100
    card1 = create_learning_card(collection, last_fresh_ivl)
    card2 = create_learning_card(collection, last_mature_ivl)
    answer_wrong = 1

    # ACT
    collection.reset()
    card1.startTimer()
    collection.sched.answerCard(card1, answer_wrong)
    card2.startTimer()
    collection.sched.answerCard(card2, answer_wrong)

    # ASSERT
    assert card1.factor < card2.factor
    assert card1.ivl / last_fresh_ivl > card2.ivl / last_mature_ivl


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


def test_nextIvlStr():
    last_ivl = 100
    collection = getEmptyCol()
    card = create_learning_card(collection, last_ivl)

    # Wrong answer
    assert "<10m" == collection.sched.nextIvlStr(card, 1, short=True)

    # Hard answer
    assert "2.7mo" == collection.sched.nextIvlStr(card, 2, short=True)

    # Good answer
    assert "8.3mo" == collection.sched.nextIvlStr(card, 3, short=True)

    # Easy answer
    assert "11.8mo" == collection.sched.nextIvlStr(card, 4, short=True)


@patch('anki.schedv3.Scheduler.scatter_fairly_cards_from_different_decks')
def test_scatter_fairly_cards_from_different_decks_is_used(scatter_fairly_cards_from_different_decks):
    collection = getEmptyCol()
    ivl = 100
    card1 = create_learning_card(collection, ivl)
    card2 = create_learning_card(collection, ivl)
    card3 = create_learning_card(collection, ivl)
    card4 = create_learning_card(collection, ivl)
    card5 = create_learning_card(collection, ivl)
    cards = [card1, card2, card3, card4, card5]
    card_ids = [card.id for card in cards]
    scatter_fairly_cards_from_different_decks.return_value = list(reversed(card_ids))

    # ACT
    returned_cards = [collection.sched.getCard(), collection.sched.getCard(), collection.sched.getCard(),
                      collection.sched.getCard(), collection.sched.getCard()]

    # ASSERT
    print(card_ids)
    assert [card.id for card in returned_cards] == card_ids
