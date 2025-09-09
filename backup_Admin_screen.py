#admin_screen.py
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QLabel, QPushButton,
    QLineEdit, QDateEdit, QFrame, QFileDialog,QTableWidgetItem,QHeaderView, QGraphicsView,QTableWidget, QGraphicsScene,
    QGraphicsPixmapItem, QComboBox, QMenu, QStackedLayout, QGridLayout,
    QDialog, QWidget,QSizePolicy, QGraphicsRectItem,QGroupBox, QGraphicsItem, QGraphicsEllipseItem, QGraphicsDropShadowEffect ,QGraphicsTextItem
)
from PyQt5.QtGui import QFont, QPixmap, QPen, QBrush, QIcon, QColor, QImage
from PyQt5.QtCore import Qt, QDate, QRectF, QSize, QPointF, QTimer
import qtawesome as qta
import os
import sys
import pymysql
from datetime import datetime
import re
import cv2
import shutil
import numpy as np
from skimage.transform import rotate
from PIL import Image
from detect_part import detect_part
from Master_RoI_Extarct_v3 import save_master_crop  # adjust import

#admin_screen.py (second import block kept as-is for your file)
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QLabel, QPushButton,
    QLineEdit, QDateEdit, QFrame, QFileDialog,QTableWidgetItem,QHeaderView, QGraphicsView,QTableWidget, QGraphicsScene,
    QGraphicsPixmapItem, QComboBox, QMenu, QStackedLayout, QGridLayout,
    QDialog, QWidget, QGraphicsRectItem, QGraphicsItem, QGraphicsEllipseItem, QGraphicsDropShadowEffect
)
from PyQt5.QtGui import QFont, QPixmap, QPen, QBrush, QIcon, QColor, QImage
from PyQt5.QtCore import Qt, QDate, QRectF, QSize, QPointF

from PyQt5.QtCore import Qt, QDate, QRectF, QSize, QPointF, QThread, pyqtSignal

from grab_baumer_gige import (
    gigE_defaults,
    configure_common,
    configure_like_explorer_auto,
    configure_manual_like_explorer,
    grab_one,
)

import os
import sys
import pymysql
import cv2
import shutil
import numpy as np
from skimage.transform import rotate
from PIL import Image
from detect_part import detect_part
from Master_RoI_Extarct_v3 import save_master_crop  # adjust import
from style import calendar_input_style

db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': 'kapil',  # Replace with your MySQL password
            'database': 'mayur_industries'
            }

class ResizeHandle(QGraphicsEllipseItem):
    def __init__(self, parent, position):
        super().__init__(-4, -4, 8, 8, parent)
        self.setBrush(QBrush(QColor("blue")))
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, True)
        self.setZValue(10)
        self.position = position  # 'top-left', 'bottom-right', etc.

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            self.parentItem().updateRectFromHandle(self, value)
        return super().itemChange(change, value)


class ResizableBoundingBox(QGraphicsRectItem):
    def __init__(self, rect: QRectF):
        super().__init__(rect)
        self.setPen(QPen(Qt.green, 2))
        self.setBrush(QBrush(Qt.transparent))
        self.setFlags(
            QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable
        )
        self.handles = {}
        self.updating_handles = False  # ✅ guard
        self.initHandles()

    def initHandles(self):
        corners = {
            'top-left': self.rect().topLeft(),
            'top-right': self.rect().topRight(),
            'bottom-left': self.rect().bottomLeft(),
            'bottom-right': self.rect().bottomRight(),
        }
        for name, pos in corners.items():
            handle = ResizeHandle(self, name)
            handle.setPos(pos)
            self.handles[name] = handle

    def updateRectFromHandle(self, handle, pos: QPointF):
        rect = self.rect()
        name = handle.position

        if name == 'top-left':
            new_rect = QRectF(pos, rect.bottomRight()).normalized()
        elif name == 'top-right':
            new_rect = QRectF(QPointF(rect.left(), pos.y()), QPointF(pos.x(), rect.bottom())).normalized()
        elif name == 'bottom-left':
            new_rect = QRectF(QPointF(pos.x(), rect.top()), QPointF(rect.right(), pos.y())).normalized()
        elif name == 'bottom-right':
            new_rect = QRectF(rect.topLeft(), pos).normalized()
        else:
            return

        self.prepareGeometryChange()
        self.setRect(new_rect)
        self.updateHandles()

    def updateHandles(self):
        if self.updating_handles or not self.handles:
            return

        self.updating_handles = True
        r = self.rect()
        if 'top-left' in self.handles:
            self.handles['top-left'].setPos(r.topLeft())
        if 'top-right' in self.handles:
            self.handles['top-right'].setPos(r.topRight())
        if 'bottom-left' in self.handles:
            self.handles['bottom-left'].setPos(r.bottomLeft())
        if 'bottom-right' in self.handles:
            self.handles['bottom-right'].setPos(r.bottomRight())
        self.updating_handles = False


class ChildPartTablePopup(QDialog):
    def __init__(self, parent=None, parent_part_name=None, is_memory_mode=True):
        super().__init__(parent)
        self.setWindowTitle("Child Part Table")
        self.setFixedSize(950, 800)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        self.setStyleSheet("background-color: white;")

        self.parent = parent
        self.parent_part_name = parent_part_name
        self.is_memory_mode = is_memory_mode

        layout = QVBoxLayout()
        title = QLabel("Child Part Table")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.create_table()
        layout.addWidget(self.report_table)
        self.setLayout(layout)

    def load_table_data(self):
        self.reload_table()

    def create_table(self):
        headers = ["Child Part Name", "Vision Algorithm", "Edit", "Delete"]
        self.report_table = QTableWidget()
        self.report_table.setColumnCount(len(headers))
        self.report_table.setHorizontalHeaderLabels(headers)
        self.report_table.setFont(QFont("Segoe UI", 10))
        header = self.report_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setDefaultAlignment(Qt.AlignCenter)
        header.setFont(QFont("Segoe UI", 10, QFont.Bold))
        header.setStyleSheet("""
            QHeaderView::section {
                background-color: #003366;
                color: white;
                padding: 4px;
                border: 1px solid black;
            }
        """)
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.report_table.verticalHeader().setVisible(False)
        self.report_table.setAlternatingRowColors(True)
        self.report_table.setShowGrid(False)
        self.report_table.setStyleSheet("""
        QTableWidget {
            background-color: #ffffff;
            alternate-background-color: #f9fbfc;
            border: 1px solid #cfd8dc;
            border-radius: 10px;
            font-size: 14px;
            font-family: 'Segoe UI';
            gridline-color: #e0e0e0;
        }
        QTableWidget::item {
            padding: 8px;
            border: none;
            color: #333333;
        }
        QTableWidget::item:selected {
            background-color: #e3f2fd;
            color: #0d47a1;
        }
        """)
        self.report_table.horizontalHeader().setStyleSheet("""
        QHeaderView::section {
            background-color: #1976d2;
            color: white;
            font-family: 'Segoe UI Semibold';
            font-size: 13px;
            font-weight: 600;
            padding: 10px 8px;
            border: none;
            border-bottom: 2px solid #1565c0;
        }
        QTableView QTableCornerButton::section {
            background-color: #1976d2;
            border: none;
        }
        """)
        self.report_table.verticalHeader().setVisible(False)
        self.reload_table()

    def reload_table(self):
        self.report_table.setRowCount(0)
        self.db_child_parts = []

        if self.is_memory_mode:
            for row_idx, (name, algo) in enumerate(self.parent.child_part_data):
                self.report_table.insertRow(row_idx)
                self.insert_row(row_idx, name, algo)
        else:
            try:
                conn = pymysql.connect(** db_config)
                cursor = conn.cursor()
                parent_name = self.parent.parent_part_name_input.text().strip()
                cursor.execute(
                    "SELECT id, child_part_name, vision_algorithm FROM child_part WHERE parent_part_name = %s",
                    (parent_name,)
                )
                rows = cursor.fetchall()
                self.db_child_parts = rows
                for row_idx, (id_, name, algo) in enumerate(rows):
                    self.report_table.insertRow(row_idx)
                    self.insert_row(row_idx, name, algo, id_)
            except Exception as e:
                print("Error loading DB rows:", e)
            finally:
                if conn:
                    conn.close()

    def insert_row(self, row_idx, name, algo, id_=None):
        name_item = QTableWidgetItem(name)
        name_item.setTextAlignment(Qt.AlignCenter)
        algo_item = QTableWidgetItem(algo)
        algo_item.setTextAlignment(Qt.AlignCenter)
        self.report_table.setItem(row_idx, 0, name_item)
        self.report_table.setItem(row_idx, 1, algo_item)

        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")

        edit_icon_path = os.path.join(base_path, "resources", "edit.png")
        delete_icon_path = os.path.join(base_path, "resources", "delete.png")

        button_style = """
            QPushButton {
                background-color: #2196f3;
                color: white;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1976d2; }
            QPushButton:pressed { background-color: #0d47a1; border-style: inset; color: #eeeeee; }
            QPushButton:disabled { background-color: #e0e0e0; color: #aaaaaa; }
        """

        edit_button = QPushButton()
        if os.path.exists(edit_icon_path):
            edit_button.setIcon(QIcon(edit_icon_path))
        edit_button.setIconSize(QSize(20, 20))
        edit_button.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        edit_button.setToolTip("Edit")
        edit_button.setStyleSheet(button_style)
        edit_button.setGraphicsEffect(self.create_shadow_effect())
        edit_button.clicked.connect(lambda _, r=row_idx: self.edit_row(r))
        self.report_table.setCellWidget(row_idx, 2, self.center_widget(edit_button))

        delete_button = QPushButton()
        if os.path.exists(delete_icon_path):
            delete_button.setIcon(QIcon(delete_icon_path))
        delete_button.setIconSize(QSize(20, 20))
        delete_button.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        delete_button.setToolTip("Delete")
        delete_button.setStyleSheet(button_style)
        delete_button.setGraphicsEffect(self.create_shadow_effect())
        delete_button.clicked.connect(lambda _, r=row_idx: self.delete_row(r))
        self.report_table.setCellWidget(row_idx, 3, self.center_widget(delete_button))

    def center_widget(self, button):
        wrapper = QWidget()
        layout = QHBoxLayout(wrapper)
        layout.addWidget(button)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        wrapper.setStyleSheet("background-color: transparent;")
        return wrapper

    def create_shadow_effect(self):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 60))
        return shadow

    def edit_row(self, row_idx):
        try:
            if self.is_memory_mode:
                name, algo = self.parent.child_part_data[row_idx]
                popup = BoundingBoxPopup(
                    parent=self.parent,
                    row_index=row_idx,
                    existing_name=name,
                    existing_algo=algo
                )
            else:
                id_, name, algo = self.db_child_parts[row_idx]
                popup = BoundingBoxPopup(
                    parent=self.parent,
                    existing_id=id_,
                    existing_name=name,
                    existing_algo=algo
                )
            if popup.exec_():
                self.reload_table()
        except IndexError:
            print("Invalid row index for editing.")

    def delete_row(self, row_idx):
        if row_idx < 0 or row_idx >= len(self.db_child_parts):
            print("Invalid row index for deletion.")
            return

        id_, name, algo = self.db_child_parts[row_idx]
        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete child part: '{name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            try:
                conn = pymysql.connect(** db_config)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM child_part WHERE id = %s", (id_,))
                conn.commit()
                self.reload_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete child part.\n{str(e)}")
            finally:
                if conn:
                    conn.close()


class BoundingBoxDrawer(QGraphicsRectItem):
    def __init__(self, x, y, width, height, parent_widget=None):
        super().__init__(x, y, width, height)
        self.setPen(QPen(Qt.green, 2, Qt.SolidLine))
        self.setBrush(QBrush(Qt.transparent))
        self.setFlags(
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        self.setZValue(1)
        self.setTransformOriginPoint(self.rect().topLeft())
        self.parent_widget = parent_widget

    def rotate_by_degree(self, angle):
        self.setTransformOriginPoint(self.rect().topLeft())
        self.setRotation(self.rotation() + angle)


class BoundingBoxPopup(QDialog):
    def __init__(self, parent=None, row_index=None, existing_id=None, existing_name=None, existing_algo=None, rect_item=None):
        super().__init__(parent)
        self.setWindowTitle("Bounding Box Details")
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        self.existing_id = existing_id
        self.parent = parent
        self.row_index = row_index
        self.rect_item = rect_item
        self.bounding_rect = rect_item.rect() if rect_item else None
        self.rect_item = rect_item

        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")

        down_arrow_icon_path = os.path.join(base_path, "resources", "down_arrow.png").replace("\\", "/")
        calendar_icon_path = os.path.join(base_path, "resources", "calendar1.png").replace("\\", "/")

        self.setStyleSheet(f"""
            QPushButton {{
                padding: 8px;
                border-radius: 8px;
                border: 1px solid #4CAF50;
                background-color: #4CAF50;
                color: white;
                font-size: 18px;
                min-width: 180px;
                min-height: 40px;
            }}
            QPushButton:hover {{ background-color: #45a049; }}
            QLineEdit, QComboBox {{
                padding: 5px;
                font-size: 16px;
                border-radius: 5px;
                border: 1px solid #b0c4de;
                min-width: 250px;
                min-height: 40px;
                background-color: white;
            }}
            QComboBox::down-arrow {{
                image: url("resources/down-arrow.png");
                width: 16px;
                height: 16px;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border-left: 1px solid #b0c4de;
                border-top-right-radius: 5px;
                border-bottom-right-radius: 5px;
            }}
        """)

        layout = QVBoxLayout()
        self.child_part_name = QLineEdit()
        self.child_part_name.setPlaceholderText("Enter Child Part Name")
        self.vision_algorithm = QComboBox()
        self.vision_algorithm.addItems(["Select", "Bracket", "Hole", "Foam"])

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_details)

        layout.addWidget(QLabel("Child Part Name:"))
        layout.addWidget(self.child_part_name)
        layout.addWidget(QLabel("Vision Algorithm:"))
        layout.addWidget(self.vision_algorithm)
        layout.addWidget(self.save_button, alignment=Qt.AlignCenter)
        self.setLayout(layout)

        if existing_name:
            self.child_part_name.setText(existing_name)
        if existing_algo:
            self.vision_algorithm.setCurrentText(existing_algo)

    @staticmethod
    def crop_and_save(image, bbox_coords, save_directory, image_name, padding=5):
        pts = np.array(bbox_coords, dtype="float32")
        widthA = np.linalg.norm(pts[0] - pts[1])
        widthB = np.linalg.norm(pts[2] - pts[3])
        maxWidth = int(max(widthA, widthB))
        heightA = np.linalg.norm(pts[0] - pts[3])
        heightB = np.linalg.norm(pts[1] - pts[2])
        maxHeight = int(max(heightA, heightB))
        padded_width = maxWidth + 2 * padding
        padded_height = maxHeight + 2 * padding
        dst = np.array([
            [padding, padding],
            [padded_width - padding - 1, padding],
            [padded_width - padding - 1, padded_height - padding - 1],
            [padding, padded_height - padding - 1]
        ], dtype="float32")
        M = cv2.getPerspectiveTransform(pts, dst)
        warped = cv2.warpPerspective(image, M, (padded_width, padded_height))
        if padded_width > padded_height:
            warped = cv2.rotate(warped, cv2.ROTATE_90_COUNTERCLOCKWISE)
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)
        base_filename = f"{image_name}"
        suffix = 1
        save_path = os.path.join(save_directory, f"{base_filename}.png")
        while os.path.exists(save_path):
            save_path = os.path.join(save_directory, f"{base_filename}_{suffix}.png")
            suffix += 1
        cv2.imwrite(save_path, warped)
        print(f"✅ Cropped image saved at: {save_path}")
        return warped, save_path

    def save_details(self):
        new_name = self.child_part_name.text().strip()
        new_algo = self.vision_algorithm.currentText().strip()

        if not new_name or new_algo.lower() == "select":
            QMessageBox.warning(self, "Invalid Input", "Please provide valid name and vision algorithm.")
            return

        # EDIT MODE
        if self.existing_id:
            try:
                conn = pymysql.connect(** db_config)
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE child_part SET child_part_name = %s, vision_algorithm = %s WHERE id = %s",
                    (new_name, new_algo, self.existing_id)
                )
                conn.commit()
                if cursor.rowcount == 0:
                    raise Exception("Update failed. No row updated.")
                QMessageBox.information(self, "Updated", f"Child part '{new_name}' updated successfully.")
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Database Error", str(e))
            finally:
                if conn:
                    conn.close()
            return

        # ADD MODE
        if not self.rect_item:
            QMessageBox.warning(self, "Missing Box", "No bounding box was drawn.")
            return

        image_view = self.parent.image_view
        pixmap = image_view.current_pixmap
        if not pixmap:
            QMessageBox.warning(self, "No Image", "No image is currently loaded.")
            return

        # Convert to OpenCV (BGR)
        qimage = pixmap.toImage().convertToFormat(4)
        ptr = qimage.bits()
        ptr.setsize(qimage.byteCount())
        img = np.array(ptr).reshape(qimage.height(), qimage.width(), 4)[:, :, :3]
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        rect = self.rect_item.rect()
        pixmap_item = None
        for item in image_view.scene().items():
            if isinstance(item, QGraphicsPixmapItem):
                pixmap_item = item
                break
        if not pixmap_item:
            QMessageBox.warning(self, "Error", "Could not find pixmap in scene.")
            return

        image_corners = [self.rect_item.mapToItem(pixmap_item, point) for point in [
            rect.topLeft(), rect.topRight(), rect.bottomRight(), rect.bottomLeft()
        ]]

        bbox_coords = [[int(p.x()), int(p.y())] for p in image_corners]
        parent_name = self.parent.parent_part_name_input.text().strip()
        folder_path = os.path.join(os.getcwd(), parent_name)
        os.makedirs(folder_path, exist_ok=True)

        coord_string = ", ".join([f"({int(p.x())}, {int(p.y())})" for p in image_corners])

        try:
            conn = pymysql.connect(** db_config)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO child_part (parent_part_name, child_part_name, vision_algorithm, coordinates) VALUES (%s, %s, %s, %s)",
                (parent_name, new_name, new_algo, coord_string)
            )
            conn.commit()
            print("✅ Child part saved to DB.")
        except Exception as e:
            print("❌ Error saving child part:", e)
            QMessageBox.critical(self, "Database Error", str(e))
        finally:
            if conn:
                conn.close()
        self.accept()


class EditParentPartPopup(QDialog):
    def __init__(self, parent=None, record=None, refresh_callback=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Parent Part Details")
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        self.refresh_callback = refresh_callback
        self.record = record

        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")

        down_arrow_icon_path = os.path.join(base_path, "resources", "down-arrow.png").replace("\\", "/")

        self.setStyleSheet(f"""
            QLabel {{ font-weight: bold; font-size: 14px; }}
            QLineEdit, QDateEdit {{
                padding: 5px; font-size: 16px; border-radius: 5px;
                border: 1px solid #b0c4de; min-width: 250px; min-height: 40px;
                background-color: white; color: black;
            }}
            QDateEdit::drop-down {{ border: none; background: white; subcontrol-origin: padding; subcontrol-position: right; width: 25px; }}
            QDateEdit::down-arrow {{ image: url("{down_arrow_icon_path}"); width: 16px; height: 16px; }}
            QPushButton {{
                padding: 10px; border-radius: 8px; border: 1px solid #4CAF50; background-color: #4CAF50;
                color: white; font-size: 16px; min-height: 40px;
            }}
            QPushButton:hover {{ background-color: #45a049; }}
        """)

        layout = QVBoxLayout()
        self.name_input = QLineEdit(record["name"])
        self.number_input = QLineEdit(record["number"])
        self.date_input = QDateEdit(QDate.fromString(record["date"], "yyyy-MM-dd"))
        self.date_input.setCalendarPopup(True)
        self.vendor_input = QLineEdit(record["vendor"])
        self.vendor_code_input = QLineEdit(record["vendor_code"])
        self.part_id_input = QLineEdit(record["part_id"])

        layout.addWidget(QLabel("Parent Part Name:"))
        layout.addWidget(self.name_input)
        layout.addWidget(QLabel("Parent Part Number:"))
        layout.addWidget(self.number_input)
        layout.addWidget(QLabel("Date:"))
        layout.addWidget(self.date_input)
        layout.addWidget(QLabel("Vendor Name:"))
        layout.addWidget(self.vendor_input)
        layout.addWidget(QLabel("Vendor Code:"))
        layout.addWidget(self.vendor_code_input)
        layout.addWidget(QLabel("Part Identification No:"))
        layout.addWidget(self.part_id_input)

        save_button = QPushButton("Save Changes")
        save_button.clicked.connect(self.save_changes)
        layout.addWidget(save_button, alignment=Qt.AlignCenter)
        self.setLayout(layout)

    def save_changes(self):
        try:
            conn = pymysql.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE parent_part SET
                    parent_part_name = %s,
                    parent_part_number = %s,
                    created_date = %s,
                    vendor_name = %s,
                    vendor_code = %s,
                    part_identification_no = %s
                WHERE id = %s
            """, (
                self.name_input.text(),
                self.number_input.text(),
                self.date_input.date().toString("yyyy-MM-dd"),
                self.vendor_input.text(),
                self.vendor_code_input.text(),
                self.part_id_input.text(),
                self.record["id"]
            ))
            conn.commit()
            QMessageBox.information(self, "Success", "Parent part updated successfully!")
            self.accept()
            if self.refresh_callback:
                self.refresh_callback()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update.\n{str(e)}")
        finally:
            if conn:
                conn.close()


class ParentPartTablePopup(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Parent Part Table")
        self.setFixedSize(1500, 800)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        self.setStyleSheet("background-color: #e6f2ff;")
        self.parent = parent

        layout = QVBoxLayout()
        title = QLabel("Parent Part Table")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Parent Part Name", "Parent Part Number", "Date",
            "Vendor Name", "Vendor Code", "Part Identification No",
            "Edit", "Delete"
        ])

        header = self.table.horizontalHeader()
        header.setFont(QFont("Segoe UI", 10, QFont.Bold))
        header.setStyleSheet("""
            QHeaderView::section { background-color: #003366; color: white; padding: 4px; border: 1px solid black; }
        """)
        header.setSectionResizeMode(QHeaderView.Interactive)
        self.table.setColumnWidth(0, 250)
        self.table.setColumnWidth(1, 200)
        self.table.setColumnWidth(2, 200)
        self.table.setColumnWidth(3, 180)
        self.table.setColumnWidth(4, 180)
        self.table.setColumnWidth(5, 190)
        self.table.setColumnWidth(6, 120)
        self.table.setColumnWidth(7, 120)
        self.table.verticalHeader().setVisible(False)

        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setStyleSheet("""
            QTableWidget { background-color: #ffffff; alternate-background-color: #f9fbfc;
                           border: 1px solid #cfd8dc; border-radius: 10px; font-size: 14px; font-family: 'Segoe UI'; gridline-color: #e0e0e0; }
            QTableWidget::item { padding: 8px; border: none; color: #333333; }
            QTableWidget::item:selected { background-color: #e3f2fd; color: #0d47a1; border: none; }
        """)

        self.table.horizontalHeader().setStyleSheet("""
            QHeaderView::section { background-color: #1976d2; color: white; font-family: 'Segoe UI Semibold';
                                   font-size: 13px; font-weight: 600; padding: 10px 8px; border: none; border-bottom: 2px solid #1565c0; }
            QTableView QTableCornerButton::section { background-color: #1976d2; border: none; }
        """)

        layout.addWidget(self.table)
        self.setLayout(layout)
        self.load_data()

    def load_data(self):
        try:
            conn = pymysql.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, parent_part_name, parent_part_number, created_date,
                    vendor_name, vendor_code, part_identification_no
                FROM parent_part
            """)
            rows = cursor.fetchall()
            self._rows = rows
            self.table.clearContents()
            self.table.setRowCount(len(rows))

            for row_idx, (id_, name, number, date, vname, vcode, part_id) in enumerate(rows):
                values = [name, str(number), str(date), vname, vcode, str(part_id)]
                for col, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row_idx, col, item)

                base_path = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.abspath(".")
                edit_icon_path = os.path.join(base_path, "resources", "edit.png")
                delete_icon_path = os.path.join(base_path, "resources", "delete.png")

                edit_btn = QPushButton()
                if os.path.exists(edit_icon_path):
                    edit_btn.setIcon(QIcon(edit_icon_path))
                edit_btn.setIconSize(QSize(20, 20))
                edit_btn.setToolTip("Edit")
                edit_btn.setStyleSheet(self.button_style())
                edit_btn.setGraphicsEffect(self.create_shadow_effect())
                edit_btn.clicked.connect(lambda _, i=id_: self.edit_entry(i))
                self.table.setCellWidget(row_idx, 6, self.center_widget(edit_btn))

                del_btn = QPushButton()
                if os.path.exists(delete_icon_path):
                    del_btn.setIcon(QIcon(delete_icon_path))
                del_btn.setIconSize(QSize(20, 20))
                del_btn.setToolTip("Delete")
                del_btn.setStyleSheet(self.button_style())
                del_btn.setGraphicsEffect(self.create_shadow_effect())
                del_btn.clicked.connect(lambda _, i=id_: self.delete_entry(i))
                self.table.setCellWidget(row_idx, 7, self.center_widget(del_btn))

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            try:
                if conn:
                    conn.close()
            except NameError:
                pass

    def center_widget(self, button):
        wrapper = QWidget()
        layout = QHBoxLayout(wrapper)
        layout.addWidget(button)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        wrapper.setStyleSheet("background-color: transparent;")
        return wrapper

    def create_shadow_effect(self):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 60))
        return shadow

    def button_style(self):
        return """
            QPushButton { background-color: transparent; border: none; padding: 2px; }
            QPushButton:hover { background-color: #e0e0e0; }
            QPushButton:pressed { background-color: #cccccc; }
        """

    def edit_entry(self, id_):
        try:
            conn = pymysql.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, parent_part_name, parent_part_number, created_date,
                    vendor_name, vendor_code, part_identification_no
                FROM parent_part WHERE id = %s
            """, (id_,))
            row = cursor.fetchone()

            if row:
                record = {
                    "id": row[0],
                    "name": row[1],
                    "number": row[2],
                    "date": str(row[3]),
                    "vendor": row[4],
                    "vendor_code": row[5],
                    "part_id": row[6]
                }
                edit_popup = EditParentPartPopup(self, record, refresh_callback=self.load_data)
                edit_popup.exec_()
            else:
                QMessageBox.warning(self, "Not Found", f"No data found for ID {id_}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            if conn:
                conn.close()

    def delete_entry(self, id_):
        confirm = QMessageBox.question(
            self, "Delete Confirmation",
            f"Delete entry with ID {id_}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            try:
                conn = pymysql.connect(** db_config)
                cursor = conn.cursor()
                cursor.execute("SELECT folder_path FROM parent_part WHERE id = %s", (id_,))
                folder_result = cursor.fetchone()
                folder_path = folder_result[0] if folder_result else None
                cursor.execute("DELETE FROM parent_part WHERE id = %s", (id_,))
                conn.commit()
                if folder_path and os.path.exists(folder_path):
                    shutil.rmtree(folder_path)
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
            finally:
                if conn:
                    conn.close()


class ImageGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setScene(QGraphicsScene())
        self.setStyleSheet("background-color: white;")
        self.drawing = False
        self.start_pos = None
        self.rect_item = None
        self.bounding_box_enabled = False
        self.interaction_mode = None
        self.current_pixmap = None
        self.last_drawn_box = None
        self.drawn_rectangles = []

    def enable_bounding_box(self, enabled):
        self.bounding_box_enabled = enabled

    def set_interaction_mode(self, mode):
        self.interaction_mode = mode

    def mousePressEvent(self, event):
        if self.bounding_box_enabled:
            self.drawing = True
            self.start_pos = self.mapToScene(event.pos())
            self.rect_item = ResizableBoundingBox(QRectF(self.start_pos, self.start_pos))
            self.scene().addItem(self.rect_item)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.drawing and self.rect_item:
            end_pos = self.mapToScene(event.pos())
            rect = QRectF(self.start_pos, end_pos).normalized()
            self.rect_item.setRect(rect)
            if hasattr(self.rect_item, "updateHandles") and hasattr(self.rect_item, "handles"):
                self.rect_item.updateHandles()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.bounding_box_enabled and self.rect_item:
            self.drawing = False
            self.start_pos = None
            if not self.rect_item.rect().isEmpty():
                self.last_drawn_box = self.rect_item
            else:
                self.scene().removeItem(self.rect_item)
                self.rect_item = None
        else:
            super().mouseReleaseEvent(event)

    def delete_last_rectangle(self):
        for item in self.scene().items():
            if isinstance(item, QGraphicsRectItem):
                self.scene().removeItem(item)
                break

    def rotate_selected_boxes(self, angle):
        for item in self.scene().selectedItems():
            if isinstance(item, QGraphicsRectItem):
                item.setTransformOriginPoint(item.rect().topLeft())
                item.setRotation(item.rotation() + angle)

    def keyPressEvent(self, event):
        key = event.key()
        if self.interaction_mode == "rotate":
            if key == Qt.Key_E:
                self.rotate_selected_boxes(1)
            elif key == Qt.Key_R:
                self.rotate_selected_boxes(-1)
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)


class BaumerCamThread(QThread):
    frame_captured = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, serial=None, mode="auto", jumbo=False, mono=False, parent=None):
        super().__init__(parent)
        self.serial = serial
        self.mode = mode
        self.jumbo = jumbo
        self.mono = mono
        self._stopped = False

    def run(self):
        try:
            import neoapi
            cam = neoapi.Cam(self.serial) if self.serial else neoapi.Cam()
            cam.Connect()
            try:
                gigE_defaults(cam, jumbo=self.jumbo)
                configure_common(cam, mono=self.mono)
                if self.mode == "auto":
                    configure_like_explorer_auto(cam)
                    for _ in range(8):
                        try:
                            grab_one(cam, timeout=2000)
                        except Exception:
                            pass
                    frame = grab_one(cam, timeout=5000)
                else:
                    configure_manual_like_explorer(cam, exposure_us=136000.0, gain=1.0)
                    try:
                        grab_one(cam, timeout=2000)
                    except Exception:
                        pass
                    frame = grab_one(cam, timeout=5000)

                if frame is None:
                    raise RuntimeError("No image received from camera.")
                self.frame_captured.emit(frame)
            finally:
                try:
                    if cam.f.AcquisitionStop.IsCommand():
                        cam.f.AcquisitionStop.Execute()
                except Exception:
                    pass
                cam.Disconnect()
        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        self._stopped = True
        self.quit()
        self.wait(1000)


class AddminScreen(QWidget):

    def get_button_style(self):
        return """
            QPushButton {
                padding: 10px; border-radius: 8px; font-family: 'Segoe UI';
                border: 1px solid #4CAF50; background-color: #4CAF50; color: white;
                font-size: 16px; min-height: 40px; min-width: 180px;
            }
            QPushButton:hover { background-color: #45a049; }
        """

    def get_action_button_style(self):
        return """
            QPushButton {
            background-color: #1a73e8; color: white; font-family: 'Segoe UI';
            font-weight: 500; font-size: 13px; border: 1px solid #1669c1;
            border-radius: 12px; padding: 8px 12px; min-width: 130px; min-height: 35px;
        }
        QPushButton:hover { background-color: #1669c1; }
        QPushButton:pressed { background-color: #1358a4; }
    """

    def get_top_button_style(self):
        return """
            QPushButton {
            background-color: #008CBA; color: white; font-family: 'Segoe UI'; font-size: 14px;
            font-weight: bold; padding: 6px 12px; border: none; border-radius: 6px; min-width: 70px; min-height: 20px;
        }
        QPushButton:hover { background-color: #007bb5; }
        QPushButton:pressed { background-color: #006a9c; }
    """

    def set_active_icon_button(self, active_button):
        if active_button.property("active") is True:
            self.clear_active_icon_buttons()
        for btn in [self.add_button, self.edit_button, self.delete_button, self.rotate_button]:
            btn.setProperty("active", btn is active_button)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def clear_active_icon_buttons(self):
        for btn in [self.add_button, self.edit_button, self.delete_button, self.rotate_button]:
            btn.setProperty("active", False)
            btn.setChecked(False)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #f5f5f5;")
        self.child_part_data = []
        self.current_frame = None
        self.camera_thread = None
        self.last_captured_image_bgr = None

        # ▶ ADDED: keep a copy of the last shown master image (BGR) for saving
        self.last_master_image_bgr = None

        self.initUI()

    def toggle_sidebar(self):
        is_visible = self.parameters_frame.isVisible()
        self.parameters_frame.setVisible(not is_visible)

    def initUI(self):
        self.button_style = self.get_button_style()
        screen_geometry = QApplication.desktop().screenGeometry()
        self.resize(1400, 1000)

        main_layout = QVBoxLayout()
        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        main_layout.addLayout(self.main_layout)
        self.setLayout(main_layout)
        self.setFont(QFont("Segoe UI", 11))

        self.parameters_layout = QVBoxLayout()
        self.parameters_layout.setAlignment(Qt.AlignTop)
        self.parameters_layout.setContentsMargins(15, 25, 15, 25)
        self.parameters_layout.setSpacing(3)

        self.parameters_frame = QFrame()
        self.parameters_frame.setStyleSheet("""
    QFrame { background-color: white; border-radius: 16px; border: none; border-radius: 12px; }
""")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(18); shadow.setXOffset(0); shadow.setYOffset(3); shadow.setColor(QColor(0, 0, 0, 40))
        self.parameters_frame.setGraphicsEffect(shadow)
        self.parameters_frame.setLayout(self.parameters_layout)
        self.parameters_frame.setMaximumWidth(480)
        self.parameters_frame.setMinimumWidth(430)
        self.parameters_frame.setMinimumHeight(650)
        self.parameters_frame.setMaximumHeight(850)

        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")

        add_icon = QIcon(os.path.join(base_path, "resources", "add.png"))
        edit_icon = QIcon(os.path.join(base_path, "resources", "edit.png"))
        delete_icon = QIcon(os.path.join(base_path, "resources", "delete.png"))
        rotate_icon = QIcon(os.path.join(base_path, "resources", "rotate.png"))

        save_icon = QIcon(os.path.join(base_path, "resources", "save.png"))
        capture_icon = QIcon(os.path.join(base_path, "resources", "capture image.png"))
        image_box_icon = QIcon(os.path.join(base_path, "resources", "image box.png"))
        child_part_icon = QIcon(os.path.join(base_path, "resources", "child part.png"))
        down_arrow_icon_path = os.path.join(base_path, "resources", "down_arrow.png").replace("\\", "/")
        calendar_icon_path = os.path.join(base_path, "resources", "calendar1.png").replace("\\", "/")

        input_style = f"""
            QPushButton {{
                padding: 8px; border-radius: 8px; border: 1px solid #4CAF50; background-color: #4CAF50;
                color: white; font-size: 16px; min-width: 200px; min-height: 35px;
            }}
            QPushButton:hover {{ background-color: #45a049; }}
            QLineEdit, QDateEdit {{
                padding: 5px; font-size: 15px; font-family: 'Segoe UI'; border-radius: 5px;
                border: 1px solid #b0c4de; min-width: 250px; min-height: 40px; background-color: white; color: black;
            }}
            QDateEdit::drop-down {{ border: none; background: white; subcontrol-origin: padding; subcontrol-position: right; width: 25px; }}
            QDateEdit::down-arrow {{ image: url("{calendar_icon_path}"); width: 16px; height: 16px; }}
            QCalendarWidget QWidget {{
                alternate-background-color: black; background-color: black; color: white;
                selection-background-color: #0078d7; selection-color: white;
            }}
            QCalendarWidget QToolButton {{ background-color: black; color: white; font-weight: bold; border: none; }}
            QCalendarWidget QMenu {{ background-color: black; color: white; }}
            QCalendarWidget QSpinBox {{ background-color: black; color: white; border: none; }}
            QCalendarWidget QAbstractItemView:enabled {{
                background-color: black; color: white; selection-background-color: #0078d7; selection-color: white;
            }}
        """

        self.parent_part_name_input = QLineEdit()
        self.parent_part_name_input.setStyleSheet(input_style)

        self.parent_part_number_input = QLineEdit()
        self.parent_part_number_input.setStyleSheet(input_style)

        self.vendor_name_input = QLineEdit()
        self.vendor_name_input.setStyleSheet(input_style)

        self.vendor_code_input = QLineEdit()
        self.vendor_code_input.setStyleSheet(input_style)

        self.part_identification_input = QLineEdit()
        self.part_identification_input.setStyleSheet(input_style)

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setStyleSheet(calendar_input_style + """
        QDateEdit {
            padding: 5px; font-size: 15px; font-family: 'Segoe UI';
            border-radius: 5px; border: 1px solid #b0c4de; min-width: 250px; min-height: 40px;
            background-color: white; color: black;
        }
        QDateEdit::drop-down { border: none; background: white; subcontrol-origin: padding; subcontrol-position: right; width: 25px; }
        QDateEdit::down-arrow { image: url(resources/calendar1.png); width: 16px; height: 16px; }
        """)
        self.date_input.calendarWidget().setStyleSheet(calendar_input_style)

        self.capture_image_button = QPushButton()
        self.capture_image_button.setIcon(capture_icon)
        self.capture_image_button.setToolTip("Capture Image")
        self.capture_image_button.setStyleSheet(self.get_action_button_style())
        self.capture_image_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.capture_image_button.clicked.connect(self.capture_image)

        self.view_parent_button = QPushButton()
        self.view_parent_button.setIcon(qta.icon("fa5s.list", color="white"))
        self.view_parent_button.setToolTip("View parent Details")
        self.view_parent_button.setStyleSheet(self.get_action_button_style())
        self.view_parent_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.view_parent_button.clicked.connect(self.view_parent_details_popup)

        self.create_bounding_box_button = QPushButton()
        self.create_bounding_box_button.setIcon(image_box_icon)
        self.create_bounding_box_button.setToolTip("Create bounding box")
        self.create_bounding_box_button.setStyleSheet(self.get_action_button_style())
        self.create_bounding_box_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.create_bounding_box_button.clicked.connect(self.enable_bounding_box)

        self.view_child_parts_button = QPushButton()
        self.view_child_parts_button.setIcon(child_part_icon)
        self.view_child_parts_button.setToolTip("View child part details")
        self.view_child_parts_button.setStyleSheet(self.get_action_button_style())
        self.view_child_parts_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.view_child_parts_button.clicked.connect(self.open_child_part_table)

        self.save_details_button = QPushButton()
        self.save_details_button.setIcon(save_icon)
        self.save_details_button.setToolTip("Save details")
        self.save_details_button.setStyleSheet(self.get_action_button_style())
        self.save_details_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.save_details_button.clicked.connect(self.save_details)

        self.save_child_button = QPushButton()
        self.save_child_button.setIcon(qta.icon("fa5s.save", color="white"))
        self.save_child_button.setToolTip("Save child details")
        self.save_child_button.setStyleSheet(self.get_action_button_style())
        self.save_child_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.save_child_button.clicked.connect(self.save_child_details)

        self.add_parameter_to_layout("Parent Part Name", self.parent_part_name_input)
        self.add_parameter_to_layout("Parent Part Number", self.parent_part_number_input)
        self.add_parameter_to_layout("Vendor Name", self.vendor_name_input)
        self.add_parameter_to_layout("Vendor Code", self.vendor_code_input)
        self.add_parameter_to_layout("Part Identification No", self.part_identification_input)
        self.add_parameter_to_layout("Date", self.date_input)

        button_grid = QGridLayout()
        button_grid.setSpacing(5)
        button_grid.setContentsMargins(0, 10, 0, 5)
        for btn in [
            self.save_details_button, self.capture_image_button, self.view_parent_button,
            self.view_child_parts_button, self.create_bounding_box_button, self.save_child_button
        ]:
            btn.setIconSize(QSize(30, 30))
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
            btn.setMinimumSize(53, 44)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #1976d2; color: white; font-family: 'Segoe UI';
                    font-size: 13px; border: none; border-radius: 6px; padding: 8px 12px;
                }
                QPushButton:hover { background-color: #1565c0; }
                QPushButton:pressed { background-color: #0d47a1; }
            """)

        button_grid.addWidget(self.save_details_button, 0, 0, alignment=Qt.AlignCenter)
        button_grid.addWidget(self.capture_image_button, 0, 1, alignment=Qt.AlignCenter)
        button_grid.addWidget(self.view_parent_button, 0, 2, alignment=Qt.AlignCenter)
        button_grid.addWidget(self.view_child_parts_button, 1, 0, alignment=Qt.AlignCenter)
        button_grid.addWidget(self.create_bounding_box_button, 1, 1, alignment=Qt.AlignCenter)
        button_grid.addWidget(self.save_child_button, 1, 2, alignment=Qt.AlignCenter)

        self.parameters_layout.addSpacing(20)
        button_box = QWidget()
        button_box.setLayout(button_grid)
        button_box.setStyleSheet("background-color: transparent;")
        self.parameters_layout.addWidget(button_box)

        self.left_container = QWidget()
        self.left_layout = QVBoxLayout(self.left_container)
        self.left_container.setStyleSheet("background-color:transparent;")
        self.left_layout.addWidget(self.parameters_frame, alignment=Qt.AlignTop)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.left_container)
        self.main_layout.setSpacing(20)

        self.right_box = QFrame()
        self.right_box.setStyleSheet("""
    QFrame { background-color: #ffffff; border-radius: 20px; }
""")
        self.right_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.image_frame = QFrame()
        frame_layout = QVBoxLayout(self.image_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(10)

        button_row = QHBoxLayout()
        button_row.setContentsMargins(0, 0, 0, 0)
        button_row.setSpacing(8)
        self.add_button = QPushButton()
        self.add_button.setIcon(add_icon)
        self.add_button.setToolTip("Add Box")

        self.edit_button = QPushButton()
        self.edit_button.setIcon(edit_icon)
        self.edit_button.setToolTip("Edit Box")

        self.delete_button = QPushButton()
        self.delete_button.setIcon(delete_icon)
        self.delete_button.setToolTip("Delete Box")

        self.rotate_button = QPushButton()
        self.rotate_button.setIcon(rotate_icon)
        self.rotate_button.setToolTip("Rotate Box")

        icon_button_style = """
            QPushButton {
                background-color: transparent; border: 2px solid transparent; border-radius: 8px; padding: 6px;
            }
            QPushButton[active="true"] { border: 2px solid gray; background-color: #f8f8f8; }
            """
        for btn in [self.add_button, self.edit_button, self.delete_button, self.rotate_button]:
            btn.setStyleSheet(icon_button_style)
            btn.setIconSize(QSize(24, 24))
            btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
            btn.setMinimumSize(32, 32)
            btn.setCursor(Qt.PointingHandCursor)

        self.add_button.setCheckable(True)
        self.edit_button.setCheckable(True)
        self.delete_button.setCheckable(True)
        self.rotate_button.setCheckable(True)

        self.add_button.clicked.connect(lambda: self.set_active_icon_button(self.add_button))
        self.edit_button.clicked.connect(lambda: self.set_active_icon_button(self.edit_button))
        self.delete_button.clicked.connect(lambda: self.set_active_icon_button(self.delete_button))
        self.rotate_button.clicked.connect(lambda: self.set_active_icon_button(self.rotate_button))

        button_row.addWidget(self.add_button)
        button_row.addWidget(self.edit_button)
        button_row.addWidget(self.delete_button)
        button_row.addWidget(self.rotate_button)
        button_row.addStretch()
        frame_layout.addLayout(button_row)

        self.image_view = ImageGraphicsView(self)
        self.image_view.setFocusPolicy(Qt.StrongFocus)
        self.image_view.setFocus()
        self.image_scene = QGraphicsScene()
        self.image_view.setScene(self.image_scene)
        self.image_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        frame_layout.addWidget(self.image_view)

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.image_frame)
        self.right_box.setLayout(right_layout)
        self.main_layout.addWidget(self.right_box)

        self.main_layout.setStretch(0, 0)
        self.main_layout.setStretch(1, 2)

        self.add_button.clicked.connect(self.on_add_clicked)
        self.delete_button.clicked.connect(self.on_delete_clicked)
        self.edit_button.clicked.connect(self.on_edit_clicked)
        self.rotate_button.clicked.connect(self.on_rotate_clicked)

        self.show_placeholder_image()

    def show_placeholder_image(self):
        QTimer.singleShot(0, self._render_placeholder)

    def _render_placeholder(self):
        self.image_scene.clear()
        target_width = 1190
        target_height = 830
        self.image_scene.setSceneRect(0, 0, target_width, target_height)
        border_rect = QGraphicsRectItem(0, 0, target_width, target_height)
        border_rect.setPen(QPen(Qt.black, 3))
        self.image_scene.addItem(border_rect)
        text_item = QGraphicsTextItem("No image captured")
        font = QFont("Segoe UI", 16, QFont.Bold)
        text_item.setFont(font)
        text_item.setDefaultTextColor(QColor("gray"))
        text_width = text_item.boundingRect().width()
        text_height = text_item.boundingRect().height()
        text_item.setPos((target_width - text_width) / 2, (target_height - text_height) / 2)
        self.image_scene.addItem(text_item)
        self.image_view.setScene(self.image_scene)

    def on_add_clicked(self):
        last_box = self.image_view.last_drawn_box
        if not last_box or last_box.rect().isEmpty() or last_box.rect().width() == 0 or last_box.rect().height() == 0:
            QMessageBox.warning(self, "No Box", "Please draw a bounding box first.")
            return
        popup = BoundingBoxPopup(parent=self, rect_item=last_box)
        popup.exec_()
        self.clear_active_icon_buttons()

    def on_edit_clicked(self):
        self.image_view.enable_bounding_box(False)
        self.image_view.setDragMode(QGraphicsView.RubberBandDrag)
        for item in self.image_view.scene().items():
            if isinstance(item, ResizableBoundingBox):
                item.setFlag(QGraphicsItem.ItemIsSelectable, True)
                item.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.clear_active_icon_buttons()

    def view_parent_details_popup(self):
        popup = ParentPartTablePopup(self)
        popup.exec_()

    def on_delete_clicked(self):
        self.image_view.delete_last_rectangle()

    def on_rotate_clicked(self):
        self.image_view.set_interaction_mode("rotate")
        self.image_view.setFocus()

    def add_parameter_to_layout(self, label_text, widget):
        label = QLabel(label_text)
        label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        label.setStyleSheet("color: #333; margin-bottom: 4px;")
        widget.setMinimumHeight(45)
        if isinstance(widget, QDateEdit):
            widget.setCalendarPopup(True)
        form_item_layout = QVBoxLayout()
        form_item_layout.setSpacing(8)
        form_item_layout.setContentsMargins(0, 0, 0, 15)
        form_item_layout.addWidget(label)
        form_item_layout.addWidget(widget)
        wrapper = QWidget()
        wrapper.setLayout(form_item_layout)
        wrapper.setStyleSheet("background-color: transparent;")
        self.parameters_layout.addWidget(wrapper)

    def capture_image(self):
        self.camera_thread = BaumerCamThread(
            serial=None, mode="auto", jumbo=False, mono=False, parent=self
        )
        self.camera_thread.frame_captured.connect(self.display_captured_image)
        self.camera_thread.error.connect(lambda msg: QMessageBox.critical(self, "Camera Error", msg))
        self.camera_thread.start()

    # (first display_captured_image exists above in your file; this one overrides)
    def display_captured_image(self, frame):
        print("[DBG] display_captured_image: received frame shape:", None if frame is None else frame.shape)

        # 1) Run detection
        try:
            success, img_bbox, warped = detect_part(frame)
            print(f"[DBG] detect_part -> success={success}, bbox={img_bbox if success else None}")
        except Exception as e:
            print("[ERR] detect_part raised:", e)
            QMessageBox.critical(self, "Detection Error", f"detect_part failed:\n{e}")
            return

        if not success or warped is None:
            print("[ERR] Detection failed or warped is None.")
            QMessageBox.warning(self, "Detection Failed", "Could not detect part in the frame.")
            return

        # 2) Cache the warped image for saving later
        self.last_captured_image_bgr = warped.copy()
        self.last_master_image_bgr = warped.copy()
        print("[DBG] Cached warped image. shape:", self.last_captured_image_bgr.shape)

        # 3) Show the warped image
        rgb_image = cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_img)

        self.image_scene.clear()
        pixmap_item = QGraphicsPixmapItem(pixmap)
        self.image_scene.addItem(pixmap_item)

        self.image_view.setScene(self.image_scene)
        self.image_view.setSceneRect(QRectF(pixmap.rect()))

        self.image_view.current_pixmap = pixmap
        self.image_view.pixmap_item = pixmap_item

        print(f"[DBG] Warped frame displayed: {w}x{h}")

    def closeEvent(self, event):
        if self.camera_thread:
            self.camera_thread.stop()
        event.accept()

    def enable_bounding_box(self):
        self.image_view.enable_bounding_box(True)
        self.image_view.set_interaction_mode("draw")
        self.image_view.last_drawn_box = None

    def open_child_part_table(self):
        is_memory = self.parent_part_number_input.text().strip() == ""
        popup = ChildPartTablePopup(self, is_memory_mode=is_memory)
        popup.load_table_data()
        popup.exec_()

    # ▶ ADDED: helper to save the current (warped) master image reliably
    def _save_master_image(self, save_dir, filename=None):
        """
        Saves the full master image currently shown on the Admin Screen (warped).
        Returns the full path of the saved image.
        Raises an Exception if writing fails.
        """
        if not os.path.exists(save_dir):
            os.makedirs(save_dir, exist_ok=True)

        # Use the captured BGR image if available; else fallback to pixmap conversion
        img_bgr = None
        if self.last_master_image_bgr is not None:
            img_bgr = self.last_master_image_bgr
        else:
            # Fallback: extract from current pixmap
            pixmap = self.image_view.current_pixmap
            if pixmap is not None:
                qimage = pixmap.toImage().convertToFormat(4)  # ARGB32
                ptr = qimage.bits(); ptr.setsize(qimage.byteCount())
                img = np.array(ptr).reshape(qimage.height(), qimage.width(), 4)[:, :, :3]
                img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        if img_bgr is None:
            raise RuntimeError("No master image available to save.")

        if filename is None:
            from datetime import datetime
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"master_image_{ts}.png"

        full_path = os.path.join(save_dir, filename)
        ok = cv2.imwrite(full_path, img_bgr)
        if not ok:
            raise IOError(f"cv2.imwrite failed for path: {full_path}")
        print(f"✅ Full master image saved at: {full_path}")
        return full_path

    def save_child_details(self):
        parent_name = self.parent_part_name_input.text().strip()
        if not parent_name:
            QMessageBox.warning(self, "Missing Parent Name", "Please enter the parent part name first.")
            return

        try:
            # Step 1: Extract image from QPixmap (kept for crops)
            pixmap = self.image_view.current_pixmap
            if not pixmap:
                QMessageBox.warning(self, "No Image", "No image loaded.")
                return

            qimage = pixmap.toImage().convertToFormat(4)  # QImage.Format_ARGB32
            ptr = qimage.bits()
            ptr.setsize(qimage.byteCount())
            img = np.array(ptr).reshape(qimage.height(), qimage.width(), 4)[:, :, :3]
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

            # Step 2: Fetch all child coordinates from DB
            conn = pymysql.connect(** db_config)
            cursor = conn.cursor()
            cursor.execute("SELECT coordinates, vision_algorithm FROM child_part WHERE parent_part_name = %s", (parent_name,))
            coords_rows = cursor.fetchall()
            conn.close()

            if not coords_rows:
                QMessageBox.warning(self, "No Coordinates", "No child parts found to crop.")
                return

            # Step 3: Parse and structure coordinates
            parsed_coords = []
            for row in coords_rows:
                coord_str = row[0]
                vision_algorithm = row[1]
                try:
                    parts = coord_str.split("),")
                    coord_pairs = []
                    for part in parts:
                        clean = part.strip().replace("(", "").replace(")", "")
                        if not clean:
                            continue
                        x, y = map(int, clean.split(","))
                        coord_pairs.append((x, y))
                    if len(coord_pairs) != 4:
                        raise ValueError(f"Expected 4 coordinates, got {len(coord_pairs)}: {coord_str}")
                    prefix_map = {"Bracket": 0, "Hole": 1, "Foam": 2}
                    prefix = prefix_map.get(vision_algorithm, -1)
                    formatted = [prefix] + coord_pairs
                    parsed_coords.append(formatted)
                except Exception as e:
                    print(f"❌ Parsing Error for row: {coord_str}\n{e}")
                    continue

            # Step 4: Save crops and the full master image in the SAME directory
            save_dir = os.path.join(os.getcwd(), parent_name)

            # ▶ ADDED: save the full master image first (from the displayed warped frame)
            try:
                saved_master_path = self._save_master_image(save_dir)
            except Exception as e:
                # Don't block crops if master save fails; show a warning instead
                QMessageBox.warning(self, "Master Image Save Warning", f"Failed to save full master image:\n{e}")

            # Save child crops
            save_master_crop(img, parsed_coords, save_dir)

            QMessageBox.information(self, "Success", "Child parts cropped and full master image saved successfully.")

        except Exception as e:
            print("❌ Error in save_child_details():", e)
            QMessageBox.critical(self, "Cropping Error", f"Failed to crop/save:\n{str(e)}")

    def _safe_filename(self, s: str) -> str:
        s = s.strip().lower()
        s = re.sub(r'[^a-z0-9._-]+', '_', s)
        s = re.sub(r'_{2,}', '_', s).strip('_')
        return s or "part"
    
    def save_details(self):
        print("\n===== [DBG] save_details() called =====")
        parent_name   = self.parent_part_name_input.text().strip()
        parent_number = self.parent_part_number_input.text().strip()
        date          = self.date_input.date().toString("yyyy-MM-dd")
        vendor_name   = self.vendor_name_input.text().strip()
        vendor_code   = self.vendor_code_input.text().strip()
        part_id       = self.part_identification_input.text().strip()

        print(f"[DBG] Inputs -> name='{parent_name}', number='{parent_number}', date='{date}', vendor='{vendor_name}', code='{vendor_code}', part_id='{part_id}'")

        if not parent_name or not parent_number:
            print("[ERR] Missing required fields (name/number).")
            QMessageBox.warning(self, "Missing Fields", "Please enter both Parent Part Name and Number.")
            return

        # 1) Ensure folder
        folder_path = os.path.join(os.getcwd(), parent_name)
        try:
            os.makedirs(folder_path, exist_ok=True)
            print(f"[DBG] Folder ensured: {folder_path}")
            print("[DBG] Folder exists? ->", os.path.exists(folder_path))
            # quick permission probe
            probe_path = os.path.join(folder_path, "__write_test__.tmp")
            try:
                with open(probe_path, "w") as f:
                    f.write("ok")
                os.remove(probe_path)
                print("[DBG] Write probe OK in folder.")
            except Exception as pe:
                print("[ERR] Write probe failed in folder:", pe)
        except Exception as e:
            print("[ERR] os.makedirs failed:", e)
            QMessageBox.critical(self, "Folder Error", f"Failed to create folder.\n{e}")
            return

        # 2) Save captured (warped) parent image if any
        parent_image_path = None
        if self.last_captured_image_bgr is None:
            print("[WARN] No captured image cached (last_captured_image_bgr is None). Skipping image save.")
        else:
            try:
                stamp    = datetime.now().strftime("%Y%m%d_%H%M%S")
                name_stub = self._safe_filename(f"{parent_name}_{parent_number}")
                filename = f"{name_stub}_{stamp}.png"
                parent_image_path = os.path.join(folder_path, filename)

                print(f"[DBG] Attempting to save image -> {parent_image_path}")
                ok = cv2.imwrite(parent_image_path, self.last_captured_image_bgr)
                print(f"[DBG] cv2.imwrite returned: {ok}")
                print(f"[DBG] File exists after write? -> {os.path.exists(parent_image_path)}")

                if not ok or not os.path.exists(parent_image_path):
                    raise IOError("cv2.imwrite returned False or file not found after write.")

                # Double-check by reading size
                try:
                    size_bytes = os.path.getsize(parent_image_path)
                    print(f"[DBG] Saved image size: {size_bytes} bytes")
                except Exception as se:
                    print("[WARN] Could not stat saved image:", se)

            except Exception as e:
                print("[ERR] Failed to save parent image:", e)
                QMessageBox.warning(self, "Image Save Warning", f"Could not save the captured image.\n{e}")
                parent_image_path = None

        # 3) Insert DB row (with parent_image_path if possible)
        conn = None
        try:
            conn = pymysql.connect(**db_config)
            cursor = conn.cursor()

            # Prefer insert with parent_image_path
            try:
                print("[DBG] Trying INSERT (with parent_image_path) ...")
                cursor.execute(
                    """
                    INSERT INTO parent_part (
                        parent_part_name, parent_part_number, created_date, folder_path,
                        part_identification_no, vendor_name, vendor_code, parent_image_path
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (parent_name, parent_number, date, folder_path,
                    part_id, vendor_name, vendor_code, parent_image_path)
                )
                print("[DBG] Insert with image path -> OK")
            except Exception as insert_with_path_err:
                print("[WARN] Insert with parent_image_path failed:", insert_with_path_err)
                print("[DBG] Retrying INSERT without parent_image_path ...")
                cursor.execute(
                    """
                    INSERT INTO parent_part (
                        parent_part_name, parent_part_number, created_date, folder_path,
                        part_identification_no, vendor_name, vendor_code
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (parent_name, parent_number, date, folder_path,
                    part_id, vendor_name, vendor_code)
                )
                print("[DBG] Insert without image path -> OK (column likely missing)")

            conn.commit()
            print(f"[DBG] Commit OK. Lastrowid = {cursor.lastrowid}")

            msg = f"Parent part '{parent_name}' saved successfully!\nFolder: {folder_path}"
            if parent_image_path:
                msg += f"\nImage: {parent_image_path}"
            else:
                msg += "\nImage: (not saved / not available)"
            QMessageBox.information(self, "Success", msg)

            print("===== [DBG] save_details() done =====\n")

        except Exception as e:
            print("[ERR] Database error:", e)
            QMessageBox.critical(self, "Database Error", f"Failed to save parent part.\n{e}")
        finally:
            if conn:
                conn.close()


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    window = AddminScreen()
    window.show()
    sys.exit(app.exec_())
