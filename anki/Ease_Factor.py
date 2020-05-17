# -*- coding: utf-8 -*-
# Ease Factor Histogram: an Anki addon appends a histogram of Ease Factor
# on the stats screen.
# Version: 0.1.2
# GitHub: https://github.com/luminousspice/anki-addons/
#
# Copyright: 2019 Luminous Spice <luminous.spice@gmail.com>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/copyleft/agpl.html

from collections import Counter
from anki.stats import CollectionStats
from anki.hooks import wrap
from anki import version

colCum = "rgba(0,0,0,0.9)"
colFactor = "#07c"
factormin = 1300
factormax = 3300


def factorGraph(self):
    data = _easefactors(self)
    realmin = min(factormin, min(data))
    realmax = max(factormax, max(data))

    realdiff = realmax - realmin
    realspan = realdiff // 20

    data = [(item // realspan) * realspan for item in data]
    data = [item / 10 for item in data]

    if not data:
        return ""
    factors = []
    all = len(data)
    c = Counter(data)
    factors = sorted(c.items(), key=lambda x: x[0])
    if not factors or not all:
        return ""
    tot = 0
    totd = []
    (low, avg, high) = self._factors()
    for f in factors:
        tot += f[1]
        totd.append([f[0], tot / float(all) * 100])
    txt = self._title(_("Ease Factor"),
                      _('''\
Index from the evaluation history in reviews to decide the next interval.''')
                      )
    if version < '2.1.12':
        txt += self._graph(id="factor", timeTicks=False, ylabel2=_("Percentage"), data=[
            dict(data=factors, color=colFactor, bars=dict(barWidth=realspan / 15)),
            dict(data=totd, color=colCum, yaxis=2,
                 bars={'show': False}, lines=dict(show=True), stack=False)
        ], conf=dict(
            xaxis=dict(min=realmin / 10 - 5, max=realmax / 10 + 5),
            yaxes=[dict(min=0), dict(position="right", min=0, max=105)]))
    else:
        txt += self._graph(id="factor", ylabel2=_("Percentage"), data=[
            dict(data=factors, color=colFactor, bars=dict(barWidth=realspan / 15)),
            dict(data=totd, color=colCum, yaxis=2,
                 bars={'show': False}, lines=dict(show=True), stack=False)
        ], conf=dict(
            xaxis=dict(min=realmin / 10 - 5, max=realmax / 10 + 5,
                       ticks=[
                           [realmin / 10, _(realmin / 10)],
                           [(realmin + realdiff / 4) / 10, _((realmin + realdiff / 4) / 10)],
                           [(realmin + realdiff / 2) / 10, _((realmin + realdiff / 2) / 10)],
                           [(realmin + realdiff * 0.75) / 10, _((realmin + realdiff * 0.75) / 10)],
                           [realmax / 10, _(realmax / 10)]
                       ]
                       ),
            yaxes=[dict(min=0), dict(position="right", min=0, max=105)]))
    i = []
    if low:
        self._line(i, _("Lowest ease"), "%d%%" % low)
        self._line(i, _("Average ease"), "%d%%" % avg)
        self._line(i, _("Highest ease"), "%d%%" % high)
    return txt + self._lineTbl(i)


def _easefactors(self):
    data = self.col.db.list("""
select factor from cards
where did in %s and queue = 2 """ % self._limit())
    return data


def newFactorGraph(self, _old):
    ret = _old(self)
    ret += factorGraph(self)
    return ret


CollectionStats.ivlGraph = wrap(CollectionStats.ivlGraph, newFactorGraph, "around")
