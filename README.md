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

Testing:
Run command
$ py.test 

Profiling:
Run commands:
$ python -m cProfile -o prof.out runanki
$ gprof2dot -f pstats prof2.out -o callingGraph2.dot
$ dot callingGraph2.dot | display