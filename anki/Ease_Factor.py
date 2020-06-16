# -*- coding: utf-8 -*-
# Ease Factor Histogram: an Anki addon appends a histogram of Ease Factor
# on the stats screen.
# Version: 0.1.2
# GitHub: https://github.com/luminousspice/anki-addons/
#
# Copyright: 2019 Luminous Spice <luminous.spice@gmail.com>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/copyleft/agpl.html

from collections import Counter
from statistics import quantiles
from anki.stats import CollectionStats
from anki.hooks import wrap
from anki import version

colCum = "rgba(0,0,0,0.9)"
colFactor = "#07c"


def factorGraph(self):
    data = _easefactors(self)

    data_quantiles = quantiles(data, n=100)
    filtered_data = [item for item in data if data_quantiles[9] < item < data_quantiles[89]]

    if not filtered_data:
        return ""

    realmin = min(filtered_data)
    realmax = max(filtered_data)
    realdiff = realmax - realmin
    realspan = realdiff // 18

    data = [round(item / realspan) * realspan for item in data]
    data = [item / 10 for item in data]

    all = len(data)
    c = Counter(data)
    factors = [x for x in sorted(c.items(), key=lambda x: x[0]) if
               (realmin - realspan) / 10 <= x[0] <= (realmax + realspan) / 10]

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
    ticks = []
    for i in range(5):
        realtick = round((realmin + i * realdiff / 4) / 10, 1)
        ticks.append([realtick, _(str(realtick))])

    txt += self._graph(id="factor", ylabel2=_("Percentage"), data=[
        dict(data=factors, color=colFactor, bars=dict(show=True)),
        dict(data=totd, color=colCum, yaxis=2,
             bars={'show': False}, lines=dict(show=True), stack=False)
    ], conf=dict(
        xaxis=dict(min=realmin / 10 - 10, max=realmax / 10 + 10,
                   ticks=ticks
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