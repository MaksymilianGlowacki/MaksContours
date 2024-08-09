from PySide6.QtCore import QDir, Slot, Signal
from PySide6.QtWidgets import QWidget, QFileSystemModel, QTreeView, QVBoxLayout, QPushButton, QLabel, \
    QMessageBox


class SelectFolder(QWidget):
    success = Signal()

    def __init__(self):
        super().__init__()
        self.selected_directory = None

        self.setWindowTitle("MaksContours - select CT folder")
        self.label = QLabel("Select CT folder:")

        self.layout = QVBoxLayout()

        self.model = QFileSystemModel()
        self.model.setFilter(QDir.NoDotAndDotDot | QDir.AllDirs)
        self.model.setRootPath(QDir.rootPath())

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setMinimumWidth(600)
        self.tree.setMinimumHeight(600)
        self.tree.setColumnWidth(0, 300)
        self.tree.setRootIndex(self.model.index(QDir.rootPath()))
        # self.tree.setCurrentIndex(self.model.index(QDir.homePath()))
        self.tree.setCurrentIndex(self.model.index("C:\\Users\\Maks\\Downloads\\CT_nowa\\CT_nowa\\Pacjent"))
        # self.tree.setCurrentIndex(self.model.index("C:\\Users\\Maks\\OneDrive\\MaksContours\\CT_07.10.2020"))
        # self.tree.setCurrentIndex(self.model.index("/Users/maks/Library/CloudStorage/OneDrive-Osobisty/MaksContours/CT_07.10.2020"))

        self.buttonSelect = QPushButton('Select CT')
        self.buttonSelect.clicked.connect(self.select_directory)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.tree)
        self.layout.addWidget(self.buttonSelect)
        self.setLayout(self.layout)

    @Slot()
    def select_directory(self):
        entry = self.tree.currentIndex()
        self.selected_directory = self.model.filePath(entry)
        if QDir(self.selected_directory).isEmpty(QDir.Files):
            message = QMessageBox()
            message.setText("Error!")
            message.setInformativeText("The selected directory is empty!")
            message.exec()
        else:
            self.success.emit()
