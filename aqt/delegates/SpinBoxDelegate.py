from PyQt5.QtCore import QModelIndex, pyqtSlot, QAbstractItemModel, Qt
from PyQt5.QtWidgets import QStyledItemDelegate, QWidget, QStyleOptionViewItem, QDoubleSpinBox


class SpinBoxDelegate(QStyledItemDelegate):
    def __init__(self, minimum: float, maximum: float, step: float, parent=None, suffix=""):
        super().__init__(parent)
        self.minimum = minimum
        self.maximum = maximum
        self.step = step
        self.suffix = suffix

    def _get_editor(self, parent) -> QDoubleSpinBox:
        return QDoubleSpinBox(parent)

    def createEditor(self, parent: QWidget, option: 'QStyleOptionViewItem', index: QModelIndex) -> QWidget:
        editor = self._get_editor(parent)
        editor.setMinimum(self.minimum)
        editor.setMaximum(self.maximum)
        editor.setSingleStep(self.step)
        editor.setSuffix(self.suffix)
        editor.valueChanged.connect(self.valueChanged)
        return editor

    def setEditorData(self, editor: QWidget, index: QModelIndex) -> None:
        editor.blockSignals(True)
        try:
            editor.setValue(float(index.model().data(index)))
        except ValueError:
            pass
        editor.blockSignals(False)

    def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex) -> None:
        model.setData(index, editor.value(), Qt.EditRole)

    @pyqtSlot()
    def valueChanged(self):
        self.commitData.emit(self.sender())
