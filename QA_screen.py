# QA_screen.py
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, 
    QHBoxLayout, QComboBox, QFrame, QGridLayout, QSpacerItem, 
    QSizePolicy, QFileDialog, QDateEdit, QMessageBox, QTimeEdit,
    QLineEdit
)
from PyQt5.QtCore import Qt, QDate, QTime, QTimer
from PyQt5.QtGui import QPixmap, QFont, QImage
import pymysql
from Detect_hole_bracket import main  # or correct import paths
import numpy as np
import cv2
# from camera_thread import CameraThread
import io
from barcode import Code128
from PIL import Image, ImageDraw, ImageFont
from barcode.writer import ImageWriter
# from QR_code import generate_zpl
# from QR_code import send_to_printer
# from Barcode import fetch_and_print_label
from datetime import datetime
import win32print
from PyQt5.QtGui import QPainter, QPen, QFont
from PyQt5.QtCore import QPointF
import os
import sys





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
        self.setStyleSheet("background-color: #f5f5f5;")
        self.camera_thread = None
        self.current_frame = None
        self.initUI()
        self.showMaximized()
        self.ok_count_for_current_packaging = 0
        self.setup_scanner_input()



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
        left_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        self.batch_form = QFrame(self)
        self.batch_form.setFrameShape(QFrame.Box)
        self.batch_form.setFixedSize(580, 800)
        self.batch_form.setStyleSheet("background-color: #e6f2ff; padding: 12px; border: 1px solid #4d4d4d; border-radius: 10px")

        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")

        down_arrow_icon_path = os.path.join(base_path, "resources", "down_arrow.png").replace("\\", "/")


        input_style = f"""
            QPushButton {{
                padding: 10px;
                border-radius: 8px;
                border: 1px solid #4CAF50;
                background-color: #4CAF50;
                color: white;
                font-size: 18px;
                min-width: 190px;
                min-height: 35px;
            }}
            QPushButton:hover {{
                background-color: #45a049;
            }}
            QLineEdit {{
                padding: 6px;
                color: black;
                border-radius: 5px;
                border: 1px solid #b0c4de;
                min-width: 200px;  
                min-height: 30px;
                font-size: 16px;
                background-color: white;
            }}
            QComboBox, QDateEdit {{
                padding: 4px;
                color: black;
                border: 1px solid #b0c4de;
                border-radius: 5px;
                background-color: white;
                min-width: 200px;
                min-height: 40px;
                font-size: 16px;
            }}
            QComboBox QAbstractItemView, QDateEdit QAbstractItemView {{
                background-color: transparent; 
                border: none;
                selection-background-color: #dcdcdc;
                outline: none;
            }}
            QComboBox::drop-down,
            QDateEdit::drop-down {{
                border: none;
                background: transparent;
                subcontrol-origin: padding;
                subcontrol-position: right;
                width: 20px;
            }}
            QComboBox::down-arrow,
            QDateEdit::down-arrow {{
                image: url("{down_arrow_icon_path}");
                width: 16px;
                height: 16px;
            }}
        """


        form_layout = QGridLayout()
        form_layout.setVerticalSpacing(15)

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
        label_font = QFont("Arial", 12, QFont.Bold)

        for i, (label, options) in enumerate(dropdown_data.items()):
            lbl = QLabel(label + " :")
            lbl.setFont(label_font)
            lbl.setStyleSheet("border: none;")

            combo_box = QComboBox()
            combo_box.addItem("")
            combo_box.addItems(options)
            combo_box.setStyleSheet(input_style)
            combo_box.currentIndexChanged.connect(self.check_all_fields_filled)

            # Trigger autofill on batch number selection
            if label == "Part Name":
                combo_box.currentIndexChanged.connect(self.autofill_fields_from_part_name)


            self.inputs[label] = combo_box
            form_layout.addWidget(lbl, i, 0)
            form_layout.addWidget(combo_box, i, 1)

        # Date Input
        lbl_date = QLabel("Date :")
        lbl_date.setFont(label_font)
        lbl_date.setStyleSheet("border: none;")
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

        form_layout.addWidget(lbl_date, len(dropdown_data), 0)
        form_layout.addWidget(self.date_input, len(dropdown_data), 1)

        # Time Label (static)
        lbl_time = QLabel("Time :")
        lbl_time.setFont(label_font)
        lbl_time.setStyleSheet("border: none;")

        # Time Display Field (label styled like input)
        self.time_display = QLabel()
        self.time_display.setFixedHeight(50)
        self.time_display.setFixedWidth(280)
        self.time_display.setStyleSheet("""
            QLabel {
                padding: 8px;
                color: black;
                background-color: white;
                border-radius: 5px;
                border: 1px solid #b0c4de;
                font-size: 16px;                              
            }
        """)

        # Add to form layout
        form_layout.addWidget(lbl_time, len(dropdown_data) + 1, 0)
        form_layout.addWidget(self.time_display, len(dropdown_data) + 1, 1)


        self.capture_button = QPushButton("Capture Image")
        self.capture_button.setFixedSize(160, 45)
        self.capture_button.setFont(QFont("Arial", 11, QFont.Bold))
        self.capture_button.setStyleSheet(input_style)
        self.capture_button.setEnabled(False)
        self.capture_button.clicked.connect(self.capture_image)
        form_layout.addWidget(self.capture_button, len(dropdown_data) + 2, 0, 1, 2, alignment=Qt.AlignCenter)

        # make it the default button so Return/Enter will click it
        self.capture_button.setDefault(True)
        self.capture_button.setAutoDefault(True)

        self.batch_form.setLayout(form_layout)
        left_layout.addWidget(self.batch_form, alignment=Qt.AlignLeft)
        left_layout.addStretch(1)

        right_layout = QVBoxLayout()
        self.image_display = QLabel(self)
        self.image_display.setFrameShape(QFrame.Box)
        self.image_display.setFixedSize(1250, 750)
        self.image_display.setAlignment(Qt.AlignCenter)
        self.image_display.setStyleSheet("border-radius: 10px; background-color: white; border: 2px solid #ccc;")

        self.result_display = QLabel("")
        self.result_display.setFrameShape(QFrame.Box)
        self.result_display.setFixedSize(1250, 110)
        self.result_display.setAlignment(Qt.AlignCenter)
        self.result_display.setFont(QFont("Arial", 80, QFont.Bold))
        self.result_display.setStyleSheet("border-radius: 10px; background-color: white; border: 2px solid #ccc;")

        # first add the result box so it sits at the top...
        right_layout.addWidget(self.result_display, alignment=Qt.AlignTop)

        # then add the image display underneath
        right_layout.addWidget(self.image_display)

        content_layout.addStretch(1)
        content_layout.addLayout(left_layout)
        content_layout.addStretch(1)
        content_layout.addLayout(right_layout)
        main_layout.addLayout(content_layout)

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
                    combo.clear()
                    combo.addItem("")
                    combo.addItems(values)
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
        from camera_thread import CameraThread

        if hasattr(self, 'camera_thread') and self.camera_thread:
            self.camera_thread.stop()

        self.camera_thread = CameraThread()
        self.camera_thread.frame_captured.connect(self.process_captured_frame)
        self.camera_thread.start()


    def closeEvent(self, event):
        if hasattr(self, 'camera_thread') and self.camera_thread:
            self.camera_thread.stop()
        event.accept()


    def process_captured_frame(self, frame):
            # Stop the thread after capturing a frame
            if hasattr(self, 'camera_thread') and self.camera_thread:
                self.camera_thread.stop()
                self.camera_thread = None  # Optional: prevent double-stop calls

            # Convert frame (BGR from OpenCV) to RGB for Qt display
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            qt_image = QImage(rgb_image.data, rgb_image.shape[1], rgb_image.shape[0],
                            rgb_image.strides[0], QImage.Format_RGB888)
            result_pixmap = QPixmap.fromImage(qt_image)

            # Stretch image to fill display area (IgnoreAspectRatio = force fit)
            stretched_pixmap = result_pixmap.scaled(
                self.image_display.width(),
                self.image_display.height(),
                Qt.IgnoreAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_display.setPixmap(stretched_pixmap)

            # Save for processing
            self.captured_image_np = frame

            # --- Proceed to processing (unchanged logic after this) ---
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

            # --- Vision Algorithm Processing ---
            result_img, status, defects = main(image=frame, master_crop_path=master_crop_path, coords=coords)

            # --- After converting result to QPixmap ---
            result_rgb = cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB)
            result_qt = QImage(result_rgb.data, result_rgb.shape[1], result_rgb.shape[0],
                            result_rgb.strides[0], QImage.Format_RGB888)
            result_pixmap = QPixmap.fromImage(result_qt)

            # --- Calculate orientation angle from original frame ---
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            rotation_angle = 0.0
            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                rect = cv2.minAreaRect(largest_contour)
                angle = rect[2]
                # Normalize OpenCV angle to [0, 180)
                if rect[1][0] < rect[1][1]:
                    rotation_angle = 90 + angle
                else:
                    rotation_angle = angle


            # 🔴 Step 1: Start painter to draw axis and angle
            painter = QPainter(result_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)

            # Styling for axes
            axis_pen = QPen(Qt.red, 6)  # thicker lines
            painter.setPen(axis_pen)

            # Origin at bottom-left corner
            origin = QPointF(60, result_pixmap.height() - 60)
            x_axis_end = QPointF(origin.x() + 150, origin.y())
            y_axis_end = QPointF(origin.x(), origin.y() - 150)

            # Draw X and Y axes
            painter.drawLine(origin, x_axis_end)
            painter.drawLine(origin, y_axis_end)

            # Labels
            font = QFont("Arial", 24, QFont.Bold)
            painter.setFont(font)
            painter.drawText(int(x_axis_end.x() + 10), int(x_axis_end.y()), "X")
            painter.drawText(int(y_axis_end.x() - 25), int(y_axis_end.y() - 10), "Y")

            # 🔴 Step 2: Add angle display
            # You need to calculate actual rotation angle, below is example with fixed value
            angle_deg = rotation_angle  # Replace with actual calculated angle
            painter.setPen(QPen(Qt.white, 50))
            painter.drawText(int(origin.x() + 30), int(origin.y() - 30), f"Angle: {angle_deg}°")

            painter.end()


            # Stretch to display area
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


            try:
                conn = pymysql.connect(**db_config)
                cursor = conn.cursor()

                current_time = self.time_display.text()
                selected_date = self.date_input.date().toString("yyyy-MM-dd")

                formatted_defects = []
                for idx, defect in enumerate(defects, 1):
                    if defect:
                        formatted_defects.append(f"{idx}. {defect}")

                reason = " and ".join(formatted_defects) if formatted_defects else None

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

                # Track OK count in memory
                if not hasattr(self, "ok_count_for_current_packaging"):
                    self.ok_count_for_current_packaging = 0

                if status == "OK":
                    self.ok_count_for_current_packaging += 1

                try:
                    packaging_qty = int(self.inputs["Packaging Quantity"].currentText())
                except:
                    packaging_qty = 0

                ok_count_after_insert = self.ok_count_for_current_packaging

        
                # ✅ Generate QR Code
                if status == "OK":
                    cursor.execute("""
                        SELECT 
                            pp.part_identification_no,
                            pp.parent_part_number,
                            pp.parent_part_name,
                            pp.vendor_code
                        FROM parent_part pp
                        WHERE pp.parent_part_name = %s
                        LIMIT 1
                    """, (part_name,))
                    part_info = cursor.fetchone()

                    if part_info:
                        shift = self.inputs["Shift"].currentText()
                        operator = self.inputs["Operator Name"].currentText()
                        mfg_date = self.date_input.date().toString("dd/MM/yy")

                        cursor.execute("SELECT COUNT(*) FROM ok_nok WHERE part_name = %s", (part_name,))
                        part_count = cursor.fetchone()[0]

                        # ✅ Generate the ZPL string
                        zpl = generate_zpl(
                            part_id=part_info[0],
                            part_no=part_info[1],
                            part_name=part_info[2],
                            vendor_code=part_info[3],
                            mfg_date=mfg_date,
                            shift=shift,
                            serial_no=part_count,
                            operator=operator,
                            status=status
                        )

                        # ✅ Send it to printer
                        try:
                            send_to_printer(zpl)
                        except Exception as e:
                            QMessageBox.critical(self, "Printer Error", f"Failed to print QR label.\n{str(e)}")


                # ✅ Generate Barcode if OK count == packaging
                if ok_count_after_insert == packaging_qty:
                    self.capture_button.setEnabled(False)
                    self.awaiting_scan = True
                    self.scanner_input.setFocus()

                    try:
                        label_data = fetch_and_print_label(part_name)

                        if label_data:
                            QMessageBox.information(self, "Print Success", "Barcode label printed successfully.")
                        else:
                            QMessageBox.warning(self, "Barcode Info", "No barcode was printed (data missing or error occurred).")

                    except Exception as e:
                        QMessageBox.critical(self, "Printer Error", f"Failed to print barcode label.\n{str(e)}")

                    self.ok_count_for_current_packaging = 0



            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Failed to insert or generate QR/Barcode.\n{str(e)}")
            finally:
                cursor.close()
                conn.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QAScreen()
    window.show()
    sys.exit(app.exec_())