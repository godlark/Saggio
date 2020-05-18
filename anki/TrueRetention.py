import anki.stats

todayStats_old = anki.stats.CollectionStats.todayStats


# Types: 0 - new today; 1 - review; 2 - relearn; 3 - (cram?) [before the answer was pressed]
# "Learning" corresponds to New|Relearn. "Review" corresponds to Young|Mature.
# Ease: 1 - flunk button; 2 - second; 3 - third; 4 - fourth (easy) [which button was pressed]
# Intervals: -60 <1m -600 10m etc; otherwise days (>=21 is mature)
def _line_now(self, i, a, b, bold=True):
    colon = _(":")
    if bold:
        i.append(("<tr><td align=right>%s%s</td><td><b>%s</b></td></tr>") % (a, colon, b))
    else:
        i.append(("<tr><td align=right>%s%s</td><td>%s</td></tr>") % (a, colon, b))


def _lineTbl_now(self, i):
    return "<table>" + "".join(i) + "</table>"


def statList(self, lim, span):
    flunked, revisited, passed, easy = self.col.db.first("""
    select
    sum(case when ease = 1 and type == 1 then 1 else 0 end), /* flunked */
    sum(case when ease = 2 and type == 1 then 1 else 0 end), /* revisited */
    sum(case when ease = 3 and type == 1 then 1 else 0 end), /* passed */
    sum(case when ease = 4 and type == 1 then 1 else 0 end) /* easy */
    from revlog where id > ? and due == day""" + lim, span)

    # sum(case when ivl > 0 and type == 0 then 1 else 0 end), /* learned */
    # sum(case when ivl > 0 and type == 2 then 1 else 0 end) /* relearned */
    flunked = flunked or 0
    revisited = revisited or 0
    passed = passed or 0
    easy = easy or 0

    i = []
    _line_now(self, i, "Passed reviews", passed)
    _line_now(self, i, "Flunked reviews", flunked)
    _line_now(self, i, "Revisited (hard) reviews", revisited)
    _line_now(self, i, "Easy reviews", easy)
    return _lineTbl_now(self, i)


def todayStats_new(self):
    lim = self._revlogLimit()
    if lim:
        lim = " and " + lim

    pastDay = statList(self, lim, (self.col.sched.dayCutoff - 86400) * 1000)
    pastWeek = statList(self, lim, (self.col.sched.dayCutoff - 86400 * 7) * 1000)

    if self.type == 0:
        period = 31;
        name = "Past month:"
    elif self.type == 1:
        period = 365;
        name = "Past year:"
    elif self.type == 2:
        period = float('inf');
        name = "All time:"

    pastPeriod = statList(self, lim, (self.col.sched.dayCutoff - 86400 * period) * 1000)

    return todayStats_old(self) + "<br><br><table style='text-align: center'><tr><td style='padding: 5px'>" \
           + "<span>Past day:</span>" + pastDay + "</td><td style='padding: 5px'>" \
           + "<span>Past week:</span>" + pastWeek + "</td><td style='padding: 5px'>" \
           + "<span>" + name + "</span>" + pastPeriod + "</td></tr></table>"


anki.stats.CollectionStats.todayStats = todayStats_new