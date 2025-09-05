# QA_screen.py
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, 
    QHBoxLayout, QComboBox, QFrame, QGridLayout, QSpacerItem, 
    QSizePolicy, QFileDialog, QDateEdit, QMessageBox, QTimeEdit,
    QLineEdit , QStyle ,QGraphicsDropShadowEffect
)
import qtawesome as qta
from PyQt5.QtCore import Qt, QDate, QTime, QTimer ,QSize
from PyQt5.QtGui import QPixmap, QFont, QImage, QPainter, QPen, QColor, QIcon
import pymysql
from Detect_hole_bracket import main  # or correct import paths
import numpy as np
import cv2
# from camera_thread import CameraThread
import io
from barcode import Code128
from PIL import Image, ImageDraw, ImageFont
# from barcode.writer import ImageWriters
# from QR_code import generate_zpl
# from QR_code import send_to_printer
# from Barcode import fetch_and_print_label
from datetime import datetime
import win32print
from PyQt5.QtGui import QPainter, QPen, QFont
from PyQt5.QtCore import QPointF
import os
import sys
from baumer_cam_thread import BaumerCamThread




db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': 'kapil',  # Replace with your MySQL password
            'database': 'mayur_industries'
            }


class QAScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QA Screen")
        self.setMinimumSize(1024, 700) 
        self.setStyleSheet("background-color: white;")
        self.camera_thread = None
        self.current_frame = None
        self.initUI()
        self.showMaximized()
        self.ok_count_for_current_packaging = 0
        self.setup_scanner_input()
        self.setFont(QFont("Segoe UI", 13))

    def autofill_fields_from_part_name(self):
        selected_part = self.inputs["Part Name"].currentText()
        if not selected_part:
            for key in self.inputs:
                if key != "Part Name":
                    self.inputs[key].setEnabled(True)
                    self.inputs[key].setCurrentIndex(0)
            return

        conn = pymysql.connect(** db_config)
        if not conn:
            return

        try:
            cursor = conn.cursor()
            query = """
                SELECT batch_number, operator_name, shift, line_number, packaging_quantity, std_quantity
                FROM ppc_batch
                WHERE part_name = %s
                ORDER BY created_date DESC
                LIMIT 1
            """
            cursor.execute(query, (selected_part,))
            row = cursor.fetchone()

            if row:
                keys = ["Batch Number", "Operator Name", "Shift", "Line Number", "Packaging Quantity", "Std.Quantity"]
                for i, key in enumerate(keys):
                    combo = self.inputs[key]
                    combo.blockSignals(True)
                    combo.setCurrentText(str(row[i]))
                    combo.setDisabled(True)
                    combo.blockSignals(False)
            else:
                QMessageBox.information(self, "No Data", f"No entry found for part: {selected_part}")
        except Exception as e:
            QMessageBox.critical(self, "Database Error", str(e))
        finally:
            cursor.close()
            conn.close()

        self.check_all_fields_filled()


    def initUI(self):
        main_layout = QVBoxLayout()
        content_layout = QHBoxLayout()

        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)

        self.batch_form = QFrame(self)
        self.batch_form.setFrameShape(QFrame.Box)
        self.batch_form.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        # self.batch_form.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.batch_form.setStyleSheet("""
    QFrame {
        background-color: white;
        border: 1px solid #ddd;
        border-radius: 12px;
    }
""")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(18)
        shadow.setXOffset(0)
        shadow.setYOffset(3)
        shadow.setColor(QColor(0, 0, 0, 40))
        self.batch_form.setGraphicsEffect(shadow)

        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")

        down_arrow_icon_path = os.path.join(base_path, "resources", "down_arrow.png").replace("\\", "/")
        calendar_icon_path = os.path.join(base_path, "resources", "calendar1.png").replace("\\", "/")

        input_style = f"""
            QPushButton {{
                padding: 8px;
                border-radius: 8px;
                background-color: #4CAF50;
                color: white;
                font-size: 18px;
                min-width: 180px;
                min-height: 35px;
            }}
            QPushButton:hover {{
                background-color: #45a049;
            }}
            QLineEdit, QComboBox, QDateEdit {{
                font-size: 16px;
                font-family: 'Segoe UI';
                min-height: 30px;
                padding: 6px 8px;
                border: 1px solid #d3dce6;
                border-radius: 6px;
                background-color: white;
                color: black;
            }}
            QComboBox::drop-down {{
                border: none;
                background: transparent;
                subcontrol-origin: padding;
                subcontrol-position: right;
                width: 25px;
            }}
            QComboBox::down-arrow {{
                image: url("resources/down-arrow.png");
                width: 16px;
                height: 16px;
            }}
            QDateEdit::drop-down {{
                border: none;
                background: transparent;
                subcontrol-origin: padding;
                subcontrol-position: right;
                width: 25px;
            }}
            QDateEdit::down-arrow {{
                image: url("{calendar_icon_path}");
                width: 20px;
                height: 20px;
            }}
            """


        form_layout = QVBoxLayout()
        form_layout.setSpacing(4)

        # Note: Batch Number is placed first now
        dropdown_data = {
            "Part Name": [],
            "Batch Number": [],
            "Operator Name": [],
            "Shift": [],
            "Line Number": [],
            "Packaging Quantity": [],
            "Std.Quantity": []
        }

        self.inputs = {}
        label_font = QFont("Segoe UI", 17, QFont.Bold)

        for label, options in dropdown_data.items():
            lbl = QLabel(label)
            lbl.setFont(label_font)
            lbl.setStyleSheet("""
                color: #555;
                font-size: 17px;
                font-weight: 600;
                background: white;
                border: none;
                margin: 0px;
                padding: 0px;
            """)

            combo_box = QComboBox()
            combo_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            combo_box.setMaximumWidth(280)
            combo_box.setMinimumWidth(400)
            combo_box.addItem("")
            combo_box.setCurrentIndex(0)
            combo_box.addItems(options)
            combo_box.setStyleSheet(input_style)
            combo_box.currentIndexChanged.connect(self.check_all_fields_filled)

            if label == "Part Name":
                combo_box.currentIndexChanged.connect(self.autofill_fields_from_part_name)

            self.inputs[label] = combo_box

            field_layout = QVBoxLayout()
            field_layout.setSpacing(10)
            field_layout.setContentsMargins(0, 0, 0, 0)
            field_layout.addWidget(lbl)
            field_layout.addWidget(combo_box)
            form_layout.addLayout(field_layout)
            form_layout.addSpacing(10)  # Adjust spacing as needed

        # Date Input
        lbl_date = QLabel("Date :")
        lbl_date.setFont(label_font)
        lbl_date.setStyleSheet("""
    color: #555;
    font-size: 16px;
    font-weight: 600;
    background: white;
    border: none;
    margin: 0px;
    padding: 0px;
""")
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setStyleSheet(input_style)
        self.date_input.dateChanged.connect(self.check_all_fields_filled)

        calendar = self.date_input.calendarWidget()
        calendar.setStyleSheet("""
            QWidget {
                alternate-background-color: black;
                background-color: black;
                color: white;
            }
            QToolButton {
                background-color: black;
                color: white;
                font-weight: bold;
            }
            QMenu {
                background-color: black;
                color: white;
            }
            QSpinBox {
                background-color: black;
                color: white;
            }
            QAbstractItemView:enabled {
                background-color: black;
                color: white;
                selection-background-color: #0078d7;
                selection-color: white;
            }
        """)

        # Date
        date_layout = QVBoxLayout()
        date_layout.addWidget(lbl_date)
        # self.date_input.setFixedWidth(280)
        self.date_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.date_input.setMaximumWidth(280)
        self.date_input.setMinimumWidth(400)
        date_layout.addWidget(self.date_input)
        form_layout.addLayout(date_layout)
        form_layout.addSpacing(20)

        lbl_time = QLabel("Time :")
        lbl_time.setFont(label_font)
        lbl_time.setStyleSheet("""
            color: #555;
    font-size: 18px;
    font-weight: 600;
    background: white;
    border: none;
    margin: 0px;
    padding: 0px;
        """)

        self.time_display = QLabel()
        self.time_display.setFont(QFont("Segoe UI", 10))
        self.time_display.setAlignment(Qt.AlignLeft)
        self.time_display.setStyleSheet("""
    font-size: 16px;              /* ⬅️ Increased font size */
    font-family: 'Segoe UI';
    min-height: 30px;             /* ⬅️ Increased height */
    padding: 6px 8px;
    font-weight: 600;
    border: 1px solid #d3dce6;
    border-radius: 6px;
    background-color: white;
    color: black;
""")


        # Time
        time_layout = QVBoxLayout()
        time_layout.addWidget(lbl_time)
        # self.time_display.setFixedSize(280 , 36)
        self.time_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.time_display.setMaximumWidth(400)
        self.time_display.setMinimumWidth(240)
        time_layout.addWidget(self.time_display)
        form_layout.addLayout(time_layout)
        form_layout.addSpacing(20)

        # Detect base path
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")

        capture_icon_path = os.path.join(base_path, "resources", "capture image.png")

        # Setup QPushButton styled like admin
        self.capture_button = QPushButton(" Capture Image")
        self.capture_button.setFont(QFont("Segoe UI", 13))
        self.capture_button.setCursor(Qt.PointingHandCursor)
        self.capture_button.setEnabled(False)
        self.capture_button.setFixedHeight(52)
        self.capture_button.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                font-family: 'Segoe UI';
                font-size: 18px;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #1565c0;
        }
        QPushButton:pressed {
            background-color: #0d47a1;
        }
    """)

        # Add the icon from resources folder
        if os.path.exists(capture_icon_path):
            self.capture_button.setIcon(QIcon(capture_icon_path))
            self.capture_button.setIconSize(QSize(24, 24))

        self.capture_button.clicked.connect(self.capture_image)

        form_layout.addWidget(self.capture_button, alignment=Qt.AlignCenter)

        # make it the default button so Return/Enter will click it
        self.capture_button.setDefault(True)
        self.capture_button.setAutoDefault(True)

        self.batch_form.setLayout(form_layout)
        left_layout.addWidget(self.batch_form, alignment=Qt.AlignLeft)
        left_layout.setAlignment(Qt.AlignTop)

        right_layout = QVBoxLayout()
        self.image_display = QLabel(self)
        self.image_display.setFrameShape(QFrame.Box)
        self.image_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_display.setAlignment(Qt.AlignCenter)
        self.image_display.setStyleSheet("border-radius: 10px; background-color: white; border: 1px solid #e0e0e0;")

        self.result_display = QLabel("")
        self.result_display.setFrameShape(QFrame.Box)
        self.result_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.result_display.setAlignment(Qt.AlignCenter)
        self.result_display.setFont(QFont("Segoe UI", 60, QFont.Bold))
        self.result_display.setStyleSheet("border-radius: 10px; background-color: white; border: 2px solid #ccc;")

        # first add the result box so it sits at the top...
        right_layout.addWidget(self.result_display, 0)  # Take 1 part of vertical space
        right_layout.addWidget(self.image_display, 6)   # Take 4 parts (more space)

        content_layout.addLayout(left_layout)
        content_layout.addLayout(right_layout)

        left_layout.addStretch()
        right_layout.addStretch()

        content_layout.setStretch(3, 4)  # left layout takes 1x space
        content_layout.setStretch(1, 11)  # right layout takes 2x space

        main_layout.addLayout(content_layout)
        main_layout.setContentsMargins(10, 10, 10, 10)

        self.setLayout(main_layout)
        self.fetch_dropdown_values()

        # Real-time clock updater
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # update every second
        self.update_time()  # initial call

    def update_time(self):
        current_time = QTime.currentTime().toString("HH:mm:ss")
        self.time_display.setText(current_time)

    def showEvent(self, event):
        super().showEvent(event)
        self.fetch_dropdown_values()

    def check_all_fields_filled(self):
        for widget in self.inputs.values():
            if widget.currentText().strip() == "":
                self.capture_button.setEnabled(False)
                return
        if self.date_input.date().isNull():
            self.capture_button.setEnabled(False)
            return
        self.capture_button.setEnabled(True)

    def fetch_dropdown_values(self):
        conn = pymysql.connect(** db_config)
        if not conn:
            print("Database connection failed.")
            return

        try:
            cursor = conn.cursor()
            fetch_queries = {
                "Batch Number": "SELECT DISTINCT batch_number FROM ppc_batch",
                "Operator Name": "SELECT DISTINCT operator_name FROM ppc_batch",
                "Shift": "SELECT DISTINCT shift FROM ppc_batch",
                "Line Number": "SELECT DISTINCT line_number FROM ppc_batch",
                "Part Name": "SELECT DISTINCT part_name FROM ppc_batch",
                "Packaging Quantity": "SELECT DISTINCT packaging_quantity FROM ppc_batch",
                "Std.Quantity": "SELECT DISTINCT std_quantity FROM ppc_batch"
            }

            for label, query in fetch_queries.items():
                cursor.execute(query)
                results = cursor.fetchall()
                values = [str(row[0]) for row in results if row[0] is not None]

                if label in self.inputs:
                    combo = self.inputs[label]
                    combo.blockSignals(True)
                    combo.blockSignals(True)
                    combo.clear()
                    combo.addItem("")  # Placeholder
                    combo.model().item(0).setEnabled(False)   # Make it unselectable
                    combo.addItems(values)
                    combo.setCurrentIndex(0)
                    combo.blockSignals(False)
        except Exception as e:
            QMessageBox.critical(self, "DB Error", str(e))
        finally:
            cursor.close()
            conn.close()

    def setup_scanner_input(self):
        # Hidden QLineEdit to capture barcode scanner input
        self.scanner_input = QLineEdit(self)
        self.scanner_input.setFixedSize(1, 1)
        self.scanner_input.setStyleSheet("border: none; background: transparent;")
        self.layout().addWidget(self.scanner_input)
        self.scanner_input.returnPressed.connect(self.handle_scanner_input)
        self.scanner_input.setFocusPolicy(Qt.StrongFocus)
        self.scanner_input.setFocus()

    
    def handle_scanner_input(self):
        scanned_data = self.scanner_input.text().strip()
        print(f"🔍 Barcode scanned: {scanned_data}")

        if self.awaiting_scan and scanned_data:
            QMessageBox.information(self, "Scan Received", f"Scanned: {scanned_data}")
            self.capture_button.setEnabled(True)
            self.awaiting_scan = False

        self.scanner_input.clear()
        self.scanner_input.setFocus()



    def reset_form_after_packaging(self):
        for key, widget in self.inputs.items():
            if key != "Part Name":
                widget.setEnabled(True)
            widget.setCurrentIndex(0)
        self.date_input.setDate(QDate.currentDate())
        self.image_display.clear()
        self.result_display.clear()
        self.capture_button.setEnabled(False)


    def capture_image(self):
        self.capture_button.setEnabled(False)  # prevent double-click

        # Clean up previous camera thread if still running
        if self.camera_thread:
            if self.camera_thread.isRunning():
                self.camera_thread.quit()
                self.camera_thread.wait()
            try:
                self.camera_thread.frame_captured.disconnect()
                self.camera_thread.error.disconnect()
            except:
                pass
            self.camera_thread = None


        # Step 2: Disable button during capture
        self.capture_button.setEnabled(False)

        # Step 3: Create new BaumerCamThread each time
        self.camera_thread = BaumerCamThread(mono=False, parent=self)
        self.camera_thread.frame_captured.connect(self.process_captured_frame)
        self.camera_thread.error.connect(lambda msg: QMessageBox.critical(self, "Camera Error", msg))
        self.camera_thread.start()



    def closeEvent(self, event):
        if hasattr(self, 'camera_thread') and self.camera_thread:
            self.camera_thread.stop()
        event.accept()


    def process_captured_frame(self, frame):
        print("✅ Received frame from camera thread")

        # Disconnect signals and stop thread cleanly
        if hasattr(self, 'camera_thread') and self.camera_thread:
            try:
                self.camera_thread.frame_captured.disconnect()
                self.camera_thread.error.disconnect()
            except:
                pass
            try:
                self.camera_thread.quit()
                self.camera_thread.wait()
            except:
                pass
            self.camera_thread = None

        # Convert frame (BGR from OpenCV) to RGB for Qt display
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        qt_image = QImage(rgb_image.data, rgb_image.shape[1], rgb_image.shape[0],
                        rgb_image.strides[0], QImage.Format_RGB888)
        result_pixmap = QPixmap.fromImage(qt_image)

        # Display preview
        stretched_pixmap = result_pixmap.scaled(
            self.image_display.width(),
            self.image_display.height(),
            Qt.IgnoreAspectRatio,
            Qt.SmoothTransformation
        )
        self.image_display.setPixmap(stretched_pixmap)

        self.captured_image_np = frame

        # --- Vision Processing Setup ---
        part_name = self.inputs["Part Name"].currentText().strip()
        if not part_name:
            QMessageBox.warning(self, "Input Error", "Please select a valid Part Name.")
            return

        try:
            conn = pymysql.connect(**db_config)
            cursor = conn.cursor()

            cursor.execute("SELECT folder_path FROM parent_part WHERE parent_part_name = %s", (part_name,))
            result = cursor.fetchone()
            if not result:
                QMessageBox.warning(self, "Missing Data", f"No master crop path found for part: {part_name}")
                return
            master_crop_path = result[0]

            cursor.execute(
                "SELECT coordinates, vision_algorithm FROM child_part WHERE parent_part_name = %s", (part_name,))
            coord_rows = cursor.fetchall()
            if not coord_rows:
                QMessageBox.warning(self, "No Coordinates", f"No child parts found for part: {part_name}")
                return

            coords = []
            vision_map = {"Bracket": 0, "Hole": 1, "Foam": 2}
            for coord_str, algo in coord_rows:
                raw_points = coord_str.split("),")
                coord_points = []
                for pt in raw_points:
                    pt_clean = pt.strip().replace("(", "").replace(")", "")
                    x, y = map(int, pt_clean.split(","))
                    coord_points.append((x, y))
                if len(coord_points) == 4:
                    coords.append([vision_map.get(algo, -1)] + coord_points)

        except Exception as e:
            QMessageBox.critical(self, "Database Error", str(e))
            return
        finally:
            cursor.close()
            conn.close()

        # --- Vision Algorithm ---
        result_img, status, defects = main(image=frame, master_crop_path=master_crop_path, coords=coords)

        # --- Annotate result image ---
        result_rgb = cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB)
        result_qt = QImage(result_rgb.data, result_rgb.shape[1], result_rgb.shape[0],
                        result_rgb.strides[0], QImage.Format_RGB888)
        result_pixmap = QPixmap.fromImage(result_qt)

        # --- Orientation Angle ---
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        rotation_angle = 0.0
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            rect = cv2.minAreaRect(largest_contour)
            angle = rect[2]
            rotation_angle = 90 + angle if rect[1][0] < rect[1][1] else angle

        # Draw angle + axis
        painter = QPainter(result_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        axis_pen = QPen(Qt.red, 6)
        painter.setPen(axis_pen)
        origin = QPointF(60, result_pixmap.height() - 60)
        x_axis_end = QPointF(origin.x() + 150, origin.y())
        y_axis_end = QPointF(origin.x(), origin.y() - 150)
        painter.drawLine(origin, x_axis_end)
        painter.drawLine(origin, y_axis_end)
        font = QFont("Segoe UI", 24, QFont.Bold)
        painter.setFont(font)
        painter.drawText(int(x_axis_end.x() + 10), int(x_axis_end.y()), "X")
        painter.drawText(int(y_axis_end.x() - 25), int(y_axis_end.y() - 10), "Y")
        painter.setPen(QPen(Qt.white, 50))
        painter.drawText(int(origin.x() + 30), int(origin.y() - 30), f"Angle: {rotation_angle:.1f}°")
        painter.end()

        # Display result
        scaled_result_pixmap = result_pixmap.scaled(
            self.image_display.width(),
            self.image_display.height(),
            Qt.IgnoreAspectRatio,
            Qt.SmoothTransformation
        )
        self.image_display.setPixmap(scaled_result_pixmap)
        self.result_display.setText(status)
        self.result_display.setStyleSheet(
            f"color: {'green' if status == 'OK' else 'red'}; "
            f"background-color: white; border-radius: 10px; border: 2px solid #ccc;"
        )

        # --- Log to DB ---
        try:
            conn = pymysql.connect(**db_config)
            cursor = conn.cursor()

            current_time = self.time_display.text()
            selected_date = self.date_input.date().toString("yyyy-MM-dd")
            reason = " and ".join([f"{i+1}. {d}" for i, d in enumerate(defects) if d]) or None

            cursor.execute(
                "INSERT INTO ok_nok (part_name, ok, nok, time, IN_DATE, reason) VALUES (%s, %s, %s, %s, %s, %s)",
                (
                    part_name,
                    1 if status == "OK" else 0,
                    0 if status == "OK" else 1,
                    current_time,
                    selected_date,
                    reason
                )
            )
            conn.commit()

            # Update OK counter for packaging
            if not hasattr(self, "ok_count_for_current_packaging"):
                self.ok_count_for_current_packaging = 0
            if status == "OK":
                self.ok_count_for_current_packaging += 1

            try:
                packaging_qty = int(self.inputs["Packaging Quantity"].currentText())
            except:
                packaging_qty = 0

            # Reset if limit reached
            if self.ok_count_for_current_packaging == packaging_qty:
                self.ok_count_for_current_packaging = 0
                QMessageBox.information(self, "Batch Complete", "Packaging quantity reached. Please scan next batch barcode.")
                self.capture_button.setEnabled(False)
                self.awaiting_scan = True
                self.scanner_input.setFocus()
            else:
                self.capture_button.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to insert result.\n{str(e)}")
        finally:
            cursor.close()
            conn.close()

        print("🎯 Capture complete, button re-enabled")


    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.image_display.pixmap():
            pixmap = self.image_display.pixmap()
            scaled_pixmap = pixmap.scaled(
                self.image_display.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.image_display.setPixmap(scaled_pixmap)

if __name__ == "__main__":
    from PyQt5.QtCore import Qt
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    window = QAScreen()
    window.show()
    sys.exit(app.exec_())
