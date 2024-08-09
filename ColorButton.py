from PySide6.QtWidgets import QPushButton, QColorDialog
from PySide6.QtGui import QColor
from PySide6.QtCore import Signal
import random


class ColorButton(QPushButton):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        self.color = QColor(r, g, b)
        self.setStyleSheet(f"background-color: {self.color.name()}; color: white")
        self.clicked.connect(self.open_color_dialog)

    def open_color_dialog(self):
        self.color = QColorDialog.getColor()
        if self.color.isValid():
            self.setStyleSheet(f"background-color: {self.color.name()}; color: white")
        self.changed.emit()
