from collections import defaultdict
from datetime import timedelta, datetime, date

import numpy
import pandas
import peewee
import pyqtgraph
from PyQt5.QtChart import QLineSeries, QChart, QChartView, QBarSeries, QBarSet, QStackedBarSeries, QBarCategoryAxis
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QMainWindow, QGridLayout, QWidget
from matplotlib import pyplot
from pyqtgraph.widgets.MatplotlibWidget import MatplotlibWidget

from anki.database.learning_answers import LearningAnswer
from anki.database.revision_answers import RevisionAnswer
from anki.lang import _
from anki.stats import CollectionStats
from anki.utils import ids2str

R_OLD = 'relearning old'

R_MATURE = 'relearning mature'

R_ADOLESCENT = 'relearning adolescent'

R_YOUNG = 'relearning young'

LEARNING = 'learning'


class Stats2Window(QMainWindow):
    # TODO: think if we should take `col` as parmater or CollectionStats
    def __init__(self, parent, col, deck):
        super().__init__(parent)

        self.deck = deck
        self.col = col

        self.layout = QGridLayout()
        widget = QWidget()
        self.setCentralWidget(widget)
        widget.setLayout(self.layout)

        self._create_reviews_due_chart()
        self._create_revision_count_graph()
        self._create_learned_count_graph()
        self._create_expected_answered_ease_heatmap()

    def _create_reviews_due_chart(self):
        ## TODO: later replace by date selector
        start, end, chunk = 0, 31, 1
        stats = CollectionStats(self.col)

        ## TODO: refactor stats._due
        categories_labels = list(range(0, 31, 1))
        data = stats.due(start, end, chunk)
        data = self._transform_first_column_to_key(data)
        data = self._add_default_value_for_missing_keys(data, [0, 0, 0, 0], categories_labels)

        series = QStackedBarSeries(self)
        setYoung = QBarSet("Young", self)
        [setYoung.append(row[0]) for row in data]
        setAdolescent = QBarSet("Adolescent", self)
        [setAdolescent.append(row[1]) for row in data]
        setMature = QBarSet("Mature", self)
        [setMature.append(row[2]) for row in data]
        setOld = QBarSet("Old", self)
        [setOld.append(row[3]) for row in data]

        categories = QBarCategoryAxis()
        categories.setCategories([str(i) for i in categories_labels])

        series.append(setOld)
        series.append(setMature)
        series.append(setAdolescent)
        series.append(setYoung)

        chart = QChart()
        chart.addSeries(series)
        chart.createDefaultAxes()
        chart.setAxisX(categories, series)

        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setTitle("Forecast: the number of reviews due in the future")

        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)

        chartview = QChartView(chart)
        chartview.setRenderHint(QPainter.Antialiasing)

        self.layout.addWidget(chartview)

    def _create_learned_count_graph(self):
        card_categories = [LEARNING, R_YOUNG, R_ADOLESCENT, R_MATURE, R_OLD]
        days_past = 10
        filter_day = date.today() - timedelta(days=days_past - 1)

        dates_past = [pandas.to_datetime(filter_day + timedelta(days=i)) for i in range(days_past)]
        whole_index = pandas.MultiIndex.from_product([card_categories, dates_past], names=['category', 'date'])

        query = LearningAnswer \
            .select(peewee.fn.Count().alias('ct'),
                    peewee.fn.strftime('%d-%m-%Y', LearningAnswer.datetime).alias('date'), LearningAnswer.card_old_ivl) \
            .where(LearningAnswer.card_due_in > timedelta())\
            .group_by(peewee.fn.strftime('%d-%m-%Y', LearningAnswer.datetime), LearningAnswer.card_old_ivl) \
            .dicts()
        df = pandas.DataFrame([row for row in query])
        df['date'] = pandas.to_datetime(df['date'], dayfirst=True)
        df['category'] = df['card_old_ivl'].apply(Stats2Window.categorize_learning_ivl)
        df = df[df['date'] >= pandas.to_datetime(filter_day)]
        df_grouped = df.groupby(['category', 'date'])['ct'].sum()

        print(df_grouped)

        df_final = df_grouped.reindex(index=whole_index, fill_value=0)

        series = QStackedBarSeries(self)
        categories = QBarCategoryAxis()
        categories.setCategories([d.strftime('%b %d') for d in dates_past])

        values_for_bars = {card_category: df_final[df_final.index.get_level_values('category') == card_category] for card_category in card_categories}
        bars = {card_category: QBarSet(card_category, self) for card_category in card_categories}

        for card_category in card_categories:
            [bars[card_category].append(value) for value in values_for_bars[card_category]]
            series.append(bars[card_category])

        chart = QChart()
        chart.addSeries(series)
        chart.createDefaultAxes()
        chart.setAxisX(categories, series)

        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setTitle("Number of (re)learned cards in the past")

        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)

        chartview = QChartView(chart)
        chartview.setRenderHint(QPainter.Antialiasing)

        self.layout.addWidget(chartview)

    def _create_revision_count_graph(self):
        k = RevisionAnswer\
            .select(peewee.fn.Count().alias('ct'), peewee.fn.strftime('%d-%m-%Y', RevisionAnswer.datetime).alias('date'), RevisionAnswer.card_old_ivl)\
            .group_by(peewee.fn.strftime('%d-%m-%Y', RevisionAnswer.datetime), RevisionAnswer.card_old_ivl)\
            .dicts()

        stats = CollectionStats(self.col)

        categories_labels = list(range(-30, 1, 1))
        data = stats.revision_count_stats()
        data = self._transform_first_column_to_key(data)
        data = self._add_default_value_for_missing_keys(data, [0, 0, 0, 0, 0], categories_labels)

        series = QStackedBarSeries(self)
        setLearning = QBarSet("Learning", self)
        [setLearning.append(row[0]) for row in data]
        setYoung = QBarSet("Young", self)
        [setYoung.append(row[1]) for row in data]
        setMature = QBarSet("Mature", self)
        [setMature.append(row[2]) for row in data]
        setLapse = QBarSet("Lapse", self)
        [setLapse.append(row[3]) for row in data]
        setEarly = QBarSet("Early", self)
        [setEarly.append(row[4]) for row in data]

        categories = QBarCategoryAxis()
        categories.setCategories([str(-i) for i in categories_labels])

        series.append(setLearning)
        series.append(setYoung)
        series.append(setMature)
        series.append(setLapse)
        series.append(setEarly)

        chart = QChart()
        chart.addSeries(series)
        chart.createDefaultAxes()
        chart.setAxisX(categories, series)

        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setTitle("Number of cards reviewed recently")

        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)

        chartview = QChartView(chart)
        chartview.setRenderHint(QPainter.Antialiasing)

        self.layout.addWidget(chartview)

    def _create_expected_answered_ease_heatmap(self):
        chosen_ease = [1, 2, 3, 4]
        expected_ease = [1, 2, 3]
        whole_index = pandas.MultiIndex.from_product([expected_ease, chosen_ease], names=['expected_ease', 'chosen_ease'])

        answers = [[t.expected_ease, t.chosen_ease] for t in RevisionAnswer.select(RevisionAnswer.expected_ease, RevisionAnswer.chosen_ease)]
        df = pandas.DataFrame(answers, columns=['expected_ease', 'chosen_ease']).groupby(['expected_ease', 'chosen_ease']).size()\
            .reindex(index=whole_index, fill_value=0).unstack()
        mat = df.to_numpy()

        mw = MatplotlibWidget()
        fig = mw.getFigure()
        ax = fig.add_subplot()
        im = ax.imshow(df)

        ax.set_xticks(numpy.arange(len(chosen_ease)))
        ax.set_yticks(numpy.arange(len(expected_ease)))

        ax.set_xticklabels(chosen_ease)
        ax.set_yticklabels(expected_ease)

        ax.set_xlabel("Chosen ease")
        ax.set_ylabel("Expected ease")

        pyplot.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

        for i in range(len(chosen_ease)):
            for j in range(len(expected_ease)):
                text = ax.text(i, j, mat[j, i], ha="center", va="center", color="w")

        fig.tight_layout()
        mw.draw()
        self.layout.addWidget(mw)

    def _transform_first_column_to_key(self, data):
        return {row[0]: row[1::] for row in data}

    def _add_default_value_for_missing_keys(self, data, default_value, keys):
        data = defaultdict(lambda: default_value, data)
        return [data[key] for key in keys]

    @staticmethod
    def categorize_learning_ivl(ivl):
        if ivl == 0:
            return LEARNING
        if ivl < 21:
            return R_YOUNG
        if ivl < 90:
            return R_ADOLESCENT
        if ivl < 365:
            return R_MATURE
        return R_OLD

    @staticmethod
    def last_x_days(format, n):
        today = datetime.now()
        return [(today - timedelta(i)).strftime(format) for i in range(n)]