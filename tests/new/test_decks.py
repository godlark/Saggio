from tests.shared import assertException, getEmptyCol


def create_note(col, deck):
    f = col.newNote()
    f['Front'] = "1"
    f.model()['did'] = deck
    col.addNote(f)
    return f


def test_flatten():
    # ARRANGE
    col = getEmptyCol()
    parent_id = col.decks.id("deck1")
    child1_id = col.decks.id("deck1::child1")
    child2_id = col.decks.id("deck1::child2")
    note1 = create_note(col, child1_id)
    note2 = create_note(col, child2_id)

    # ACT
    col.decks.flatten(parent_id)
    note1.load()
    note2.load()

    # ASSERT
    assert note1.cards()[0].did == parent_id
    assert note2.cards()[0].did == parent_id