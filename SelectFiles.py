from pydicom.errors import InvalidDicomError
from PySide6.QtCore import QDir, Qt, Slot, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QListWidget, \
    QListWidgetItem, QMessageBox
from pydicom import read_file
from collections import defaultdict


class Frame:
    def __init__(self, x, rt_struct=False):

        self.file = read_file(x)
        self.sup_uid = self.file.SOPInstanceUID

        self.raw_img = None
        self.rescale_slope = None
        self.rescale_intercept = None
        self.hu_img = None

        self.num_contours = None
        self.contours_names = None
        self.contours_sequences = None
        self.contours_properties = None

        self.contours_masks = None
        self.contours = None
        self.z = None

        if not rt_struct:
            self.raw_img = self.file.pixel_array
            self.rescale_slope = self.file.RescaleSlope
            self.rescale_intercept = self.file.RescaleIntercept
            self.hu_img = self.raw_img * self.rescale_slope + self.rescale_intercept
            self.contours = defaultdict(list)
            self.contours_masks = {}
            self.z = self.file.ImagePositionPatient[-1]
        else:
            self.num_contours = len(self.file.StructureSetROISequence)
            self.contours_names = [self.file.StructureSetROISequence[i].ROIName for i in range(self.num_contours)]
            self.contours_sequences = [self.file.ROIContourSequence[i].ContourSequence for i in range(self.num_contours)]
            self.contours_properties = {}


class SelectFiles(QWidget):
    success = Signal()
    failure = Signal()

    def __init__(self):
        super().__init__()

        self.files = None
        self.selected_directory = None
        self.selected_files = None

        self.setWindowTitle("MaksContours - select CT files")
        self.setMinimumWidth(600)
        self.setMinimumHeight(600)

        self.label = QLabel("Select CT files (without RT struct):")

        self.buttonAccept = QPushButton("Accept CT files")
        self.buttonBack = QPushButton("Back")
        self.buttonAccept.clicked.connect(self.accept_files)
        self.buttonBack.clicked.connect(self.back)

        self.scan_list = QListWidget()

        self.layout = QVBoxLayout()

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.scan_list)
        self.layout.addWidget(self.buttonAccept)
        self.layout.addWidget(self.buttonBack)
        self.setLayout(self.layout)

    def populate_list(self):
        self.files = self.selected_directory.entryInfoList(QDir.NoDotAndDotDot | QDir.Files)
        self.scan_list.clear()
        for file in self.files:
            item = QListWidgetItem(file.fileName())
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            if file.fileName().lower()[-4:] == ".dcm" and file.fileName().lower()[:2] == "ct":
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            self.scan_list.addItem(item)

    @Slot()
    def accept_files(self):
        indices = []
        for index, item in enumerate(self.scan_list.findItems("", Qt.MatchContains)):
            if item.checkState() == Qt.Checked:
                indices.append(index)

        if len(indices) == 0:
            message = QMessageBox()
            message.setText("Error!")
            message.setInformativeText("No files selected!")
            message.exec()
        else:
            for index in indices:
                try:
                    Frame(self.files[index].absoluteFilePath())
                except InvalidDicomError:
                    message = QMessageBox()
                    message.setText("Error!")
                    message.setInformativeText(f"Invalid file: {self.files[index].absoluteFilePath()}")
                    message.exec()
                    return
            self.selected_files = [self.files[i].absoluteFilePath() for i in indices]
            self.success.emit()

    @Slot()
    def back(self):
        self.failure.emit()


class SelectContour(SelectFiles):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("MaksContours - select contour file")
        self.label.setText("Select file containing contours:")
        self.buttonAccept.setText("Accept contour file")

    def populate_list(self):
        super().populate_list()
        for i in range(self.scan_list.count()):

            if self.scan_list.item(i).text().lower()[-4:] == ".dcm" and self.scan_list.item(i).text().lower()[:2] == "rs":
                self.scan_list.item(i).setCheckState(Qt.Checked)
            else:
                self.scan_list.item(i).setCheckState(Qt.Unchecked)

    @Slot()
    def accept_files(self):
        indices = []
        for index, item in enumerate(self.scan_list.findItems("", Qt.MatchContains)):
            if item.checkState() == Qt.Checked:
                indices.append(index)

        if len(indices) == 0:
            message = QMessageBox()
            message.setText("Error!")
            message.setInformativeText("No files selected!")
            message.exec()
        elif len(indices) > 1:
            message = QMessageBox()
            message.setText("Error!")
            message.setInformativeText("Select only one file!")
            message.exec()
        else:
            for index in indices:
                try:
                    Frame(self.files[index].absoluteFilePath(), True)
                except InvalidDicomError:
                    message = QMessageBox()
                    message.setText("Error!")
                    message.setInformativeText(f"Invalid file: {self.files[index].absoluteFilePath()}")
                    message.exec()
                    return
            self.selected_files = self.files[indices[0]].absoluteFilePath()
            self.success.emit()
