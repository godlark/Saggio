from collections import defaultdict

import numpy
import pandas
import pyqtgraph
from PyQt5.QtChart import QLineSeries, QChart, QChartView, QBarSeries, QBarSet, QStackedBarSeries, QBarCategoryAxis
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QMainWindow, QGridLayout, QWidget
from matplotlib import pyplot
from pyqtgraph.widgets.MatplotlibWidget import MatplotlibWidget

from anki.database.revision_answers import RevisionAnswer
from anki.lang import _
from anki.stats import CollectionStats
from anki.utils import ids2str


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

    def _create_revision_count_graph(self):
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
        chosen_ease = ['1', '2', '3', '4']
        expected_ease = ['1', '2', '3']

        answers = [[t.expected_ease, t.chosen_ease] for t in RevisionAnswer.select(RevisionAnswer.expected_ease, RevisionAnswer.chosen_ease)]
        df = pandas.DataFrame(answers, columns=['expected_ease', 'chosen_ease']).groupby(['expected_ease', 'chosen_ease']).size().unstack(fill_value=0)
        mat = df.to_numpy()
        print(mat)

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
