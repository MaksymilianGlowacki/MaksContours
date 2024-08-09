import numpy as np
from PySide6.QtCore import Qt
from skimage.measure import points_in_poly
from PySide6.QtWidgets import QTableWidgetItem


def update_mask(mask, contour):
    left = int(np.amin(contour[:, 0])) - 1
    right = int(np.amax(contour[:, 0])) + 1
    top = int(np.amin(contour[:, 1])) - 1
    bot = int(np.amax(contour[:, 1])) + 1

    for y in range(top, bot):
        for x in range(left, right):
            if points_in_poly([(x, y)], contour):
                mask[y, x] += 1


class ContourProperty:
    def __init__(self, name, frames):
        total_voxels = []
        for frame in frames:
            total_voxels.extend(frame.hu_img[frame.contours_masks[name]])

        self.mean = np.mean(total_voxels)
        self.std = np.std(total_voxels)
        self.median = np.median(total_voxels)
        self.min = np.amin(total_voxels)
        self.max = np.amax(total_voxels)
        self.volume = len(total_voxels)

        self.name = name

    def add_to_table(self, table, row):
        mean_item = QTableWidgetItem(f"{self.mean:.2f}")
        mean_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        table.setItem(row, 5, mean_item)

        std_item = QTableWidgetItem(f"{self.std:.2f}")
        std_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        table.setItem(row, 6, std_item)

        min_item = QTableWidgetItem(f"{int(self.min)}")
        min_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        table.setItem(row, 3, min_item)

        max_item = QTableWidgetItem(f"{int(self.max)}")
        max_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        table.setItem(row, 4, max_item)

        median_item = QTableWidgetItem(str(self.median))
        median_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        table.setItem(row, 7, median_item)

        volume_item = QTableWidgetItem(str(self.volume))
        volume_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        table.setItem(row, 8, volume_item)

