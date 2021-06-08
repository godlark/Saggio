from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt5.QtWidgets import QMainWindow, QTableView, QGridLayout, QWidget, QPushButton

from anki.database.note_types import NoteTypes, NoteType


class NoteTypeModel(QAbstractTableModel):
    def __init__(self, parent, note_types):
        super().__init__(parent)
        self.note_types = note_types
        self.items = self.note_types.get_all()

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.items)

    def columnCount(self, parent=None, *args, **kwargs):
        return 3

    def data(self, index, role=None):
        if role == Qt.UserRole+1:
            return self.items[index.row()].id

        if role != Qt.DisplayRole and role != Qt.EditRole:
            return None

        if index.column() == 0:
            return self.items[index.row()].id
        if index.column() == 1:
            return self.items[index.row()].title
        if index.column() == 2:
            return self.items[index.row()].description

    def setData(self, index: QModelIndex, value, role=None):
        if role == Qt.EditRole:
            if index.column() == 1:
                self.items[index.row()].title = str(value)
            if index.column() == 2:
                self.items[index.row()].description = str(value)
            self.items[index.row()].save()
            self.dataChanged.emit(index, index)
            return True
        return False

    def flags(self, index):
        if index.column() == 0:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    def removeRow(self, row: int, parent: QModelIndex = QModelIndex()) -> bool:
        self.beginRemoveRows(parent, row, row)
        self.items[row].delete_instance()
        self.items.pop(row)
        self.endRemoveRows()

    def appendRow(self, parent: QModelIndex = QModelIndex()) -> bool:
        self.beginInsertRows(parent, self.rowCount(), self.rowCount())
        self.items.append(NoteType(title=None, description=None))
        self.endInsertRows()


class NoteTypesWindow(QMainWindow):
    def __init__(self, parent, col):
        super().__init__(parent)
        self.col = col
        self.deleteButton = QPushButton("Delete")
        self.addButton = QPushButton("Add")
        self.model = NoteTypeModel(self, NoteTypes())
        self.view = QTableView(self)

        self.addButton.clicked.connect(self.add_entry)
        self.deleteButton.clicked.connect(self.remove_entry)

        self.view.setModel(self.model)

        layout = QGridLayout()
        layout.addWidget(self.addButton)
        layout.addWidget(self.deleteButton)
        layout.addWidget(self.view)

        widget = QWidget()
        widget.setLayout(layout)

        self.setCentralWidget(widget)

    def remove_entry(self):
        self.model.removeRow(self.view.selectionModel().currentIndex().row())

    def add_entry(self):
        self.model.appendRow()