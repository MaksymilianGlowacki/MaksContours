import numpy as np
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QApplication, QGridLayout, QTableWidget, QSlider, QTableWidgetItem

from SelectFiles import *
from SelectFolder import *
import cv2


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.ids_used = set()

        self.folder_selector = SelectFolder()
        self.file_selector = SelectFiles()
        self.contour_selector = SelectContour()

        self.folder_selector.success.connect(self.folder_selected)
        self.file_selector.success.connect(self.files_selected)
        self.contour_selector.success.connect(self.contours_selected)

        self.file_selector.failure.connect(self.files_back)
        self.contour_selector.failure.connect(self.contour_back)

        self.hide()
        self.folder_selector.show()
        self.file_selector.hide()
        self.contour_selector.hide()

        self.selected_folder = None
        self.selected_files = None
        self.selected_contours = None

        self.setWindowTitle("MaksContours")
        self.layout = QGridLayout()

        self.preview = QLabel()
        self.preview.setMinimumHeight(600)
        self.preview.setMinimumWidth(600)
        self.preview.setAlignment(Qt.AlignCenter)

        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Min (HU)", "Max (HU)", "Mean (HU)", "Std HU()", "Median (HU)", "Volume (voxels)", ""])

        self.exp_pics_button = QPushButton("Save pictures")
        self.exp_contours_button = QPushButton("Save contours")
        self.exp_data_button = QPushButton("Save data")
        self.add_contour_button = QPushButton("Add contour")
        self.add_area_button = QPushButton("Add area")

        self.preview_slider = QSlider(Qt.Horizontal)
        self.value = 0
        self.preview_slider.setMinimum(0)
        self.preview_slider.setValue(self.value)
        self.preview_slider.valueChanged.connect(self.change_img)

        self.layout.addWidget(self.preview, 0, 0, 4, 3)
        self.layout.addWidget(self.preview_slider, 4, 0, 1, 3)
        self.layout.addWidget(self.add_contour_button, 0, 3, 1, 3)
        self.layout.addWidget(self.add_area_button, 1, 3, 1, 3)
        self.layout.addWidget(self.table, 2, 3, 2, 3)
        self.layout.addWidget(self.exp_pics_button, 4, 3)
        self.layout.addWidget(self.exp_contours_button, 4, 4)
        self.layout.addWidget(self.exp_data_button, 4, 5)
        self.setLayout(self.layout)

        self.frames = None
        self.contour_frame = None
        self.image = None

    def read_data(self):
        self.frames = [Frame(x) for x in self.selected_files]
        self.contour_frame = Frame(self.selected_contours, True)

    @Slot()
    def change_img(self, value):
        self.value = value
        img = self.frames[self.value].raw_img
        img = (img / np.amax(img) * 255).astype(np.uint8)
        self.image = np.stack((img, img, img, np.ones_like(img) * 255), 2)
        self.update_contours()
        img = np.array(self.image[150:-150, 150:-150, :])

        pixmap = QPixmap.fromImage(QImage(img.data,
                                          img.shape[1], img.shape[0], img.shape[1] * 4,
                                          QImage.Format_RGBA8888))
        pixmap = pixmap.scaled(self.preview.size(), Qt.KeepAspectRatio)
        self.preview.setPixmap(pixmap)

    @Slot()
    def folder_selected(self):
        self.selected_folder = self.folder_selector.selected_directory
        self.file_selector.selected_directory = QDir(self.selected_folder)
        self.contour_selector.selected_directory = QDir(self.selected_folder)
        self.file_selector.populate_list()
        self.contour_selector.populate_list()
        self.folder_selector.hide()
        self.file_selector.show()

    @Slot()
    def files_selected(self):
        self.selected_files = self.file_selector.selected_files
        self.file_selector.hide()
        self.contour_selector.show()

    @Slot()
    def contours_selected(self):
        self.selected_contours = self.contour_selector.selected_files
        self.contour_selector.hide()

        self.read_data()
        self.generate_rows()

        self.preview_slider.setMaximum(len(self.frames) - 1)
        self.preview_slider.setValue(0)
        self.change_img(0)

        self.show()

    @Slot()
    def files_back(self):
        self.selected_folder = None
        self.file_selector.hide()
        self.folder_selector.show()

    @Slot()
    def contour_back(self):
        self.selected_files = None
        self.contour_selector.hide()
        self.file_selector.show()

    def generate_rows(self):
        for row, name in enumerate(self.contour_frame.contours_names):
            self.table.insertRow(row)

            id_item = QTableWidgetItem()
            id_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            id_item.setText(self.get_id())
            id_item.setCheckState(Qt.Unchecked)
            self.table.setItem(row, 0, id_item)

            name_item = QTableWidgetItem(name)
            name_item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(row, 1, name_item)

        for frame in self.frames:
            for i, contour_sequence in enumerate(self.contour_frame.contours_sequences):
                for contour_instance in contour_sequence:
                    if frame.sup_uid == contour_instance.ContourImageSequence[0].ReferencedSOPInstanceUID:
                        contour_raw = contour_instance.ContourData
                        contour = np.asarray(contour_raw).reshape((3, -1), order="F")[:-1].ravel(order="F").reshape(
                            (-1, 2))
                        contour *= np.array([self.frames[self.value].file.ImageOrientationPatient[0],
                                             self.frames[self.value].file.ImageOrientationPatient[4]])
                        contour -= np.asarray(self.frames[self.value].file.ImagePositionPatient[:-1])
                        contour /= np.asarray(self.frames[self.value].file.PixelSpacing)
                        contour = np.concatenate((contour, [contour[0]]))
                        frame.contours[self.contour_frame.contours_names[i]].append(np.rint(contour.reshape(-1, 1, 2)).astype(int))

    def get_id(self):
        i = 0
        code = self.get_code(i)
        while code in self.ids_used:
            i += 1
            code = self.get_code(i)
        self.ids_used.add(code)
        return code

    def get_code(self, value):
        code = ""

        while value > len(self.alphabet):
            digit = value % len(self.alphabet)
            code += self.alphabet[digit]
            value //= len(self.alphabet)

        digit = value % len(self.alphabet)
        code += self.alphabet[digit]

        return code[::-1]

    @Slot()
    def update_contours(self):
        indices = []
        for cell in range(self.table.rowCount()):
            if self.table.item(cell, 0).checkState() == Qt.Checked:
                indices.append(cell)

        for i in indices:
            if self.contour_frame.contours_names[i] in self.frames[self.value].contours:
                cv2.drawContours(self.image, self.frames[self.value].contours[self.contour_frame.contours_names[i]],
                                 -1, (0, 0, 255, 255), 1, cv2.LINE_AA)


app = QApplication()
window = MainWindow()
app.exec()
