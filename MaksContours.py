from PySide6.QtCore import QThreadPool
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QApplication, QGridLayout, QTableWidget, QSlider
from ColorButton import ColorButton
from SelectFiles import *
from SelectFolder import *
from Masks import *
import cv2


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumWidth(1200)
        self.alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.ids_used = set()
        self.colors_used = set()

        self.workers = QThreadPool()

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
        self.preview.setMinimumHeight(500)
        self.preview.setMinimumWidth(500)
        self.preview.setAlignment(Qt.AlignCenter)

        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Name", "Color", "Min (HU)", "Max (HU)", "Mean (HU)", "Std HU()", "Median (HU)", "Volume (voxels)"])

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
        self.frames.sort(key=lambda x: x.z)
        self.contour_frame = Frame(self.selected_contours, True)

    @Slot()
    def change_img(self, value):
        self.value = value
        img = self.frames[self.value].raw_img
        img = (img / np.amax(img) * 255).astype(np.uint8)
        self.image = np.stack((img, img, img, np.ones_like(img) * 255), 2)
        self.update_contours()
        # img = np.array(self.image[150:-150, 150:-150, :])
        img = np.array(self.image)

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
        names = self.contour_frame.contours_names
        for row, name in enumerate(names):
            self.table.insertRow(row)

            id_item = QTableWidgetItem()
            id_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            id_item.setText(self.get_id())
            id_item.setCheckState(Qt.Unchecked)
            self.table.setItem(row, 0, id_item)
            self.table.cellChanged.connect(self.handle_item_checked)

            name_item = QTableWidgetItem(name)
            name_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(row, 1, name_item)

            color_item = ColorButton()
            color_item.changed.connect(self.handle_item_clicked)
            self.table.setCellWidget(row, 2, color_item)

        for frame in self.frames:
            for i, contour_sequence in enumerate(self.contour_frame.contours_sequences):
                mask = np.zeros(frame.hu_img.shape, dtype=int)
                for contour_instance in contour_sequence:
                    if frame.sup_uid == contour_instance.ContourImageSequence[0].ReferencedSOPInstanceUID:
                        contour_raw = contour_instance.ContourData
                        contour = np.asarray(contour_raw).reshape((3, -1), order="F")[:-1].ravel(order="F").reshape(
                            (-1, 2))
                        contour -= np.asarray(self.frames[self.value].file.ImagePositionPatient[:-1])
                        contour *= np.array([self.frames[self.value].file.ImageOrientationPatient[0],
                                             self.frames[self.value].file.ImageOrientationPatient[4]])
                        contour /= np.asarray(self.frames[self.value].file.PixelSpacing)
                        contour = np.concatenate((contour, [contour[0]]))
                        update_mask(mask, contour)
                        frame.contours[names[i]].append(contour.reshape(-1, 1, 2))
                frame.contours_masks[names[i]] = np.array(mask % 2, dtype=bool)

        for row, name in enumerate(names):
            properties = ContourProperty(name, self.frames)
            properties.add_to_table(self.table, row)
            self.contour_frame.contours_properties[name] = properties

    def get_id(self):
        i = 0
        code = self.get_code(i)
        while code in self.ids_used:
            i += 1
            code = self.get_code(i)
        self.ids_used.add(code)
        return code

    def get_code(self, value):
        temp_code = [0]
        for i in range(value):
            temp_code[0] += 1

            a = len(temp_code)
            for j in range(a):
                if temp_code[j] == len(self.alphabet):
                    temp_code[j] = 0
                    if j == a - 1:
                        temp_code.append(0)
                    else:
                        temp_code[j + 1] += 1

        code = "".join([self.alphabet[i] for i in temp_code])
        return code[::-1]

    @Slot()
    def update_contours(self):
        indices = []
        for cell in range(self.table.rowCount()):
            if self.table.item(cell, 0).checkState() == Qt.Checked:
                indices.append(cell)

        alpha = 0.7

        for i in indices:
            if self.contour_frame.contours_names[i] in self.frames[self.value].contours:
                color = self.table.cellWidget(i, 2).color.getRgb()
                names = self.contour_frame.contours_names[i]

                contours_to_draw = [np.rint(x).astype(int) for x in self.frames[self.value].contours[names]]
                bit_mask = self.frames[self.value].contours_masks[names]
                color_mask = np.stack([bit_mask * 255, bit_mask * color[0], bit_mask * color[1], bit_mask * color[2]], axis=-1)
                color_mask = (255 * color_mask).astype(np.uint8)

                new_image = cv2.addWeighted(self.image, alpha, color_mask, 1 - alpha, 0)
                self.image = np.where(np.stack([bit_mask, bit_mask, bit_mask, bit_mask], axis=-1) == 0,
                                      self.image, new_image)

                cv2.drawContours(self.image, contours_to_draw, -1, color, 1, cv2.LINE_AA)

    @Slot()
    def handle_item_checked(self, _, column):
        if column == 0 or column == 2:
            self.change_img(self.value)

    @Slot()
    def handle_item_clicked(self):
        self.change_img(self.value)


app = QApplication()
window = MainWindow()
app.exec()
