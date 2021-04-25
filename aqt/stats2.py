from PyQt5.QtChart import QLineSeries, QChart, QChartView, QBarSeries, QBarSet, QStackedBarSeries, QBarCategoryAxis
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QMainWindow, QGridLayout, QWidget

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

    def _create_reviews_due_chart(self):
        ## TODO: later replace by date selector
        start, end, chunk = 0, 31, 1
        stats = CollectionStats(self.col)

        ## TODO: refactor stats._due
        data = stats.due(start, end, chunk)

        series = QStackedBarSeries(self)
        setYoung = QBarSet("Young", self)
        [setYoung.append(row[1]) for row in data]
        setAdolescent = QBarSet("Adolescent", self)
        [setAdolescent.append(row[2]) for row in data]
        setMature = QBarSet("Mature", self)
        [setMature.append(row[3]) for row in data]
        setOld = QBarSet("Old", self)
        [setOld.append(row[4]) for row in data]

        categories = QBarCategoryAxis()
        categories.setCategories([str(row[0]) for row in data])

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

        data = stats.revision_count_stats()
        print(data)

        series = QStackedBarSeries(self)
        setLearning = QBarSet("Learning", self)
        [setLearning.append(row[1]) for row in data]
        setYoung = QBarSet("Young", self)
        [setYoung.append(row[2]) for row in data]
        setMature = QBarSet("Mature", self)
        [setMature.append(row[3]) for row in data]
        setLapse = QBarSet("Lapse", self)
        [setLapse.append(row[4]) for row in data]
        setEarly = QBarSet("Early", self)
        [setEarly.append(row[5]) for row in data]

        categories = QBarCategoryAxis()
        categories.setCategories([str(-i) for i in range(-31, 0, 1)])

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

