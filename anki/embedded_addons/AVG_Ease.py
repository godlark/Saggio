# Average Ease
# Anki 2 addon
# Author EJS
# https://eshapard.github.io/
#
# Sets the initial ease factor of a deck options group to the average
# ease factor of the mature cards within that deck options group.
from anki.consts import STARTING_FACTOR
from anki.database.note_types import NoteType
from anki.hooks import addHook
from aqt import mw
import math
#import time

# Find decks in settings group
def find_decks_in_settings_group(group_id):
    members = []
    decks = mw.col.decks.decks
    for d in decks:
        if 'conf' in decks[d] and int(decks[d]['conf']) == int(group_id):
            members.append(d)
    return members

# Find average ease and number of mature cards in deck
#   mature defined as having an interval > 90 day
def find_average_ease_in_deck(deck_id):
    mw.col.db._db.create_function("log", 2, math.log)
    mature_cards = mw.col.db.all("""select
        sum(log(ivl, factor/1000.0)), sum(log(ivl, factor/1000.0)*factor)
        from cards where
        type = 2 and
        ivl > 1 and
        did = ?""", deck_id)
    if not mature_cards or mature_cards[0][0] is None:
        return 0, 0
    return mature_cards[0]


def find_average_ease_in_deck2(deck_id):
    mw.col.db._db.create_function("log", 2, math.log)
    card_types = mw.col.db.all("""select
        notes.mid, cards.ord, sum(log(ivl, factor/1000.0)), sum(log(ivl, factor/1000.0)*factor)
        from cards 
        join notes ON notes.id=cards.nid
        where
        type = 2 and
        ivl > 1 and
        did = ?
        group by notes.mid, cards.ord
        """, deck_id)
    if not card_types or card_types[0][0] is None:
        return {}
    return [(card_type[0], card_type[1], card_type[2], card_type[3]) for card_type in card_types]


def get_note_types_ids():
    return [note_type.id for note_type in NoteType().select()]


# Average mature card ease factor in settings group
def mature_ease_in_settings_group(group_id):
    note_types_ids = get_note_types_ids()

    tot_mature_cards = {note_type_id: 0 for note_type_id in note_types_ids}
    weighted_ease = {note_type_id: 0 for note_type_id in note_types_ids}
    avg_mature_ease = {note_type_id: 0 for note_type_id in note_types_ids}
    cur_ease = {note_type_id: 0 for note_type_id in note_types_ids}

    if not group_id:
        return avg_mature_ease, cur_ease

    # Find decks and cycle through
    decks = find_decks_in_settings_group(group_id)
    for deck_id in decks:
        for model_id, card_ord, mature_cards, mature_ease in find_average_ease_in_deck2(deck_id):
            model = mw.col.models.get(model_id)
            note_type_id = model['tmpls'][card_ord]['note_type_id']
            tot_mature_cards[note_type_id] += mature_cards
            weighted_ease[note_type_id] += mature_ease

    for note_type_id in note_types_ids:
        if tot_mature_cards[note_type_id] > 0 and weighted_ease[note_type_id]:
            avg_mature_ease[note_type_id] = int(weighted_ease[note_type_id] / tot_mature_cards[note_type_id])
        else:
            # not enough data; don't change the init ease factor
            avg_mature_ease[note_type_id] = mw.col.decks.dconf[group_id]["new"]["initialFactors"].get(note_type_id, STARTING_FACTOR)

    # Copy the old value
    cur_ease = dict(mw.col.decks.dconf[group_id]["new"]["initialFactors"])
    return avg_mature_ease, cur_ease


# update initial ease factor of a settings group
def update_initial_ease_factor(group_id, ease_factors):
    if group_id:
        if group_id in mw.col.decks.dconf:
            mw.col.decks.dconf[group_id]["new"]["initialFactors"] = {note_type_id: int(ease_factor)
                                                                     for note_type_id, ease_factor in ease_factors.items()}
            mw.col.decks.save(mw.col.decks.dconf[group_id])
            #mw.col.decks.flush()
# main function
def update_ease_factor(dogID):
    avg_ease, cur_ease = mature_ease_in_settings_group(dogID)
    #utils.showInfo("dogID: %s AvgEase: %s" % (dogID, avg_ease))
    update_initial_ease_factor(dogID, avg_ease)

# run this on profile load
def update_ease_factors():
    #find all deck option groups
    dconf = mw.col.decks.dconf
    #create progress bar
    #ogs = len(dconf)
    #mw.progress.start(max = ogs, label = "Init Ease Factor: %s" % ogs)
    #cycle through them one by one
    #i = 1
    for k in dconf:
        update_ease_factor(k)
        #mw.progress.update("Init Ease Factor: %s" % dconf[k]['name'], i)
        #i += 1
        #time.sleep(1)
    #mw.progress.finish()
    mw.reset()


def initialize():
    # add hook to 'profileLoaded'
    addHook("profileLoaded", update_ease_factors)
