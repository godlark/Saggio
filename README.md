Anki
-------------------------------------

This is the development branch of Anki.

For stable builds, please see https://apps.ankiweb.net.

For non-developers who want to try this development code,
the easiest way is to use a binary package - please see
https://anki.tenderapp.com/discussions/beta-testing

To run from source, please see README.development.

[![Build Status](https://travis-ci.org/dae/anki.svg?branch=master)](https://travis-ci.org/dae/anki)



TODO:
Zmiana grupy opcji powinna być możliwa dwoma kliknięciami
Statystyki wyglądają podejrzanie, tak jakby każdy interwał miał jedną kartę
Naprawa testów
Dodanie opcji do limitu learning/new
Usunięcie card.queue = 3 (learning in days)
Dodanie card.queue = 5 (revision in seconds)
Revlog to powinien być plik txt z dowolną strukturą?
* Powinny być tylko dwa rodzaje decków: parent decki, i decki z kartami; parent decki nie powinny zawierać kart
* Powinny być grupy ustawień oraz ustawienia specyficzne dla danego decka, np. liczba nowych kart, limit powtórzeń;
albo można zrobić override-y dla decków
* Niektóre ustawienia mogą być per rodzaj karty (czyli note.template_id + card.ord)


* Regularne testowanie rozszerzeń
* Przepisanie statystyk na QtChart
* Refaktor migracji bazy danych do osobnych plików
* Użycie data klas tam, gdzie można
* Użycie jakiegoś frameworka do zarządzania bazą danych
    * https://stackoverflow.com/questions/53376099/python-dataclass-from-a-nested-dict
    * maybe Peewee https://stackoverflow.com/questions/33901178/translating-sql-sub-query-to-peewee-orm
* Automatyzacja migracji bazy danych
* Do logów dodać informację, czy to jest powtórka czy (re)learning oraz czy wynik odpowiedź była zgodna 
z przewidywaniami z algorytmu
* Zmiana liczenia lapses:
  * lapses_total
  * lapses_in_row

Testing:
Run command
$ py.test 

Profiling:
Run commands:
$ python -m cProfile -o prof.out runanki
$ gprof2dot -f pstats prof2.out -o callingGraph2.dot
$ dot callingGraph2.dot | display

## Commits with missing tests
* a3f14d53b60ed3e65a9afc574d8277e87177c9de - Add a `review_start_time`
* 4eaa877bfec959afe3af645df9250af872e76a45 - clear backlog of cards from the previous days