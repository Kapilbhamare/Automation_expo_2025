#ppc_screen.py
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QHBoxLayout, QTableWidgetItem, QDateEdit,
    QTableWidget, QHeaderView, QFrame, QComboBox,  QGraphicsDropShadowEffect, 
    QDialog,  QMessageBox, QVBoxLayout, QFormLayout, QLabel, QLineEdit
)
from PyQt5.QtGui import QFont, QRegExpValidator, QIntValidator, QIcon, QColor
from PyQt5.QtCore import Qt, QRegExp, QDate, QSize
import sys
import os
import pymysql


db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': 'kapil',  # Replace with your MySQL password
            'database': 'mayur_industries'
            }


class CreateBatchForm(QDialog):
    def __init__(self, parent=None, row_data=None):
        super().__init__(parent)
        self.setWindowTitle("Create Batch" if row_data is None else "Edit Batch")
        self.setFixedSize(580, 720)
        self.setStyleSheet("background-color: white; padding: 10px;")

        self.row_data = row_data

        # Frame
        self.frame = QFrame(self)
        self.frame.setStyleSheet("background-color: #f5f5f5; border: 1px solid #d1e0e0; border-radius: 10px;")
        self.frame.setGeometry(15, 15, 430, 560)
        self.frame_layout = QVBoxLayout(self.frame)
        self.frame_layout.setContentsMargins(15, 15, 15, 15)

        # Layouts
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.form_layout = QFormLayout()
        self.form_layout.setVerticalSpacing(10)
        self.form_layout.setLabelAlignment(Qt.AlignLeft)

        # Styling
        # Detect base path (compatible with PyInstaller EXE and normal script)
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")

        down_arrow_icon_path = os.path.join(base_path, "resources", "down_arrow.png").replace("\\", "/")  # Cross-platform

        input_style = f"""
            QPushButton {{
                padding: 8px;
                border-radius: 8px;
                border: 1px solid #4CAF50;
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
                min-width: 180px;
                min-height: 30px;
            }}
            QPushButton:hover {{
                background-color: #45a049;
            }}

            QLineEdit, QDateEdit, QComboBox {{
                padding: 8px;
                border-radius: 5px;
                border: 1px solid #b0c4de;
                font-size: 15px;
                min-width: 250px;
                min-height: 35px;
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
                image: url("{down_arrow_icon_path}");
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
                image: url("{down_arrow_icon_path}");
                width: 16px;
                height: 16px;
            }}

            QCalendarWidget QWidget {{
                alternate-background-color: black;
                background-color: black;
                color: white;
                selection-background-color: #0078d7;
                selection-color: white;
            }}
            QCalendarWidget QToolButton {{
                background-color: black;
                color: white;
                font-weight: bold;
                border: none;
            }}
            QCalendarWidget QMenu {{
                background-color: black;
                color: white;
            }}
            QCalendarWidget QSpinBox {{
                background-color: black;
                color: white;
                border: none;
            }}
            QCalendarWidget QAbstractItemView:enabled {{
                background-color: black;
                color: white;
                selection-background-color: #0078d7;
                selection-color: white;
            }}
        """


        label_style = """
            QLabel {
                font-size: 10pt;
                font-weight: bold;
                color: #333;
                padding-right: 15px;
                border: none;
                background: transparent;
            }
        """

        # Fields
        self.shift = QComboBox()
        self.shift.addItems(["Select", "1", "2", "3"])


        self.batch_number = QLineEdit()
        self.batch_number.setPlaceholderText("Enter batch number")

        self.line_number = QLineEdit()
        self.line_number.setPlaceholderText("Enter line number")

        self.operator_name = QLineEdit()
        self.operator_name.setPlaceholderText("Enter operator name")
        self.operator_name.setValidator(QRegExpValidator(QRegExp("[A-Za-z ]+")))

        self.part_name = QComboBox()

        self.part_number = QLineEdit()  # <-- Initialize before connection
        self.part_name.currentTextChanged.connect(self.on_part_name_changed)

        # ✅ Add this line to populate part names
        self.load_part_names()

        # Add after self.part_name = QComboBox()
        self.part_number = QLineEdit()
        self.part_number.setPlaceholderText("Auto-filled part number")
        self.part_number.setReadOnly(True)  # auto-filled from DB

        self.customer_name = QLineEdit()
        self.customer_name.setPlaceholderText("Enter customer name")

        self.packaging_quantity = QLineEdit()
        self.packaging_quantity.setPlaceholderText("Enter packaging quantity")
        self.packaging_quantity.setValidator(QIntValidator())

        self.std_quantity = QLineEdit()
        self.std_quantity.setPlaceholderText("Enter quantity")
        self.std_quantity.setValidator(QIntValidator())

        self.date = QDateEdit()
        self.date.setDate(QDate.currentDate())
        self.date.setDisplayFormat("MM/dd/yyyy")
        self.date.setCalendarPopup(True)

        # Row layout
        fields = [
            ("Shift:", self.shift),
            ("Batch Number:", self.batch_number),
            ("Line Number:", self.line_number),
            ("Operator Name:", self.operator_name),
            ("Part Name:", self.part_name),
            ("Part Number:", self.part_number),             # new
            ("Customer Name:", self.customer_name),         # new
            ("Packaging Quantity:", self.packaging_quantity),
            ("Std.Quantity:", self.std_quantity),
            ("Date:", self.date),
        ]

        for label_text, field in fields:
            label = QLabel(label_text)
            label.setStyleSheet(label_style)
            field.setStyleSheet(input_style)
            self.form_layout.addRow(label, field)
        # Prefill for edit
        if self.row_data:
            index = self.shift.findText(self.row_data[0])
            if index != -1:
                self.shift.setCurrentIndex(index)

            self.batch_number.setText(self.row_data[1])
            self.line_number.setText(self.row_data[2])
            self.operator_name.setText(self.row_data[3])
            self.part_name.setCurrentText(self.row_data[4])
            self.part_number.setText(self.row_data[5])
            self.customer_name.setText(self.row_data[6])
            self.packaging_quantity.setText(self.row_data[7])
            self.std_quantity.setText(self.row_data[8])
            self.date.setDate(QDate.fromString(self.row_data[9], "MM/dd/yyyy"))

        # Save button
        self.save_btn = QPushButton("Save")
        self.save_btn.setStyleSheet(input_style)
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.save_data)
        self.form_layout.addRow(self.save_btn)

        # ✅ Now it's safe to validate
        if self.row_data:
            self.validate_form()

        # Validate inputs
        for field in [
            self.batch_number, self.line_number,
            self.operator_name, self.customer_name,
            self.packaging_quantity, self.std_quantity
        ]:
            field.textChanged.connect(self.validate_form)

        self.shift.currentIndexChanged.connect(self.validate_form)
        self.part_name.currentTextChanged.connect(self.validate_form)
        self.date.dateChanged.connect(self.validate_form)

        # Attach layouts
        self.frame_layout.addLayout(self.form_layout)
        self.layout.addWidget(self.frame)
        self.setLayout(self.layout)

    def on_part_name_changed(self, part_name):
        try:
            conn = pymysql.connect(** db_config)
            cursor = conn.cursor()
            cursor.execute("SELECT parent_part_number FROM parent_part WHERE parent_part_name = %s", (part_name,))
            result = cursor.fetchone()
            if result:
                self.part_number.setText(result[0])
            else:
                self.part_number.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not fetch part number.\n{e}")
        finally:
            if conn:
                conn.close()


    def load_part_names(self):
        try:
            conn = pymysql.connect(** db_config)
            cursor = conn.cursor()
            cursor.execute("SELECT parent_part_name FROM parent_part")
            part_names = cursor.fetchall()

            # print("Fetched part names:", part_names)  # Debug output

            self.part_name.clear()
            for name in part_names:
                self.part_name.addItem(name[0])

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load part names.\n{e}")
        finally:
            if conn:
                conn.close()


    def validate_form(self):
        """Enable save only if all fields are filled."""
        # inside validate_form():
        all_filled = (
            all(field.text().strip() for field in [
                self.batch_number, self.line_number, self.operator_name,
                self.customer_name, self.packaging_quantity, self.std_quantity
            ])
            and self.shift.currentText() != "Select"
            and bool(self.part_name.currentText().strip())
        )
        self.save_btn.setEnabled(all_filled)

    def save_data(self):
        """Insert or update batch into the database."""
        try:
            conn = pymysql.connect(** db_config)
            cursor = conn.cursor()

            shift = self.shift.currentText().strip()
            batch_number = self.batch_number.text().strip()
            line_number = self.line_number.text().strip()
            operator_name = self.operator_name.text().strip()
            part_name = self.part_name.currentText().strip()
            part_number = self.part_number.text().strip()
            customer_name = self.customer_name.text().strip()
            packaging_quantity = int(self.packaging_quantity.text().strip())
            std_quantity = int(self.std_quantity.text().strip())
            created_date = self.date.date().toString("yyyy-MM-dd")

            if hasattr(self, "record_id") and self.record_id:
                # ✅ Update existing record
                cursor.execute("""
                    UPDATE ppc_batch SET
                        shift=%s, batch_number=%s, line_number=%s, operator_name=%s,
                        part_name=%s, part_number=%s, customer_name=%s,
                        packaging_quantity=%s, std_quantity=%s, created_date=%s
                    WHERE id=%s
                """, (
                    shift, batch_number, line_number, operator_name,
                    part_name, part_number, customer_name,
                    packaging_quantity, std_quantity, created_date, self.record_id
                ))
            else:
                # ✅ Insert new record
                cursor.execute("""
                    INSERT INTO ppc_batch (
                        shift, batch_number, line_number, operator_name,
                        part_name, part_number, customer_name,
                        packaging_quantity, std_quantity, created_date
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    shift, batch_number, line_number, operator_name,
                    part_name, part_number, customer_name,
                    packaging_quantity, std_quantity, created_date
                ))

                self.record_id = cursor.lastrowid  # Save for future edits


            conn.commit()
            QMessageBox.information(self, "Success", "Batch saved successfully.")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            conn.close()


    def get_data(self):
        return [
            self.shift.currentText(),
            self.batch_number.text(),
            self.line_number.text(),
            self.operator_name.text(),
            self.part_name.currentText(),
            self.part_number.text(),
            self.customer_name.text(),
            self.packaging_quantity.text(),
            self.std_quantity.text(),
            self.date.text()
        ]

class PPCScreen(QWidget):
    """Main PPC Screen."""

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):

        # Central shared style for inputs
        # Detect base path (compatible with PyInstaller and normal script)
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")

        down_arrow_icon_path = os.path.join(base_path, "resources", "down_arrow.png").replace("\\", "/")

        input_style = f"""
            QLineEdit, QComboBox, QDateEdit {{
                padding: 5px;
                font-size: 15px;
                color: black;
                border-radius: 5px;
                border: 1px solid #0078d7;
                min-width: 150px;
                min-height: 25px;
                background-color: transparent;
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

            QCalendarWidget QWidget {{
                alternate-background-color: black;
                background-color: black;
                color: white;
                selection-background-color: #0078d7;
                selection-color: white;
            }}
            QCalendarWidget QToolButton {{
                background-color: black;
                color: white;
                font-weight: bold;
                border: none;
            }}
            QCalendarWidget QMenu {{
                background-color: black;
                color: white;
            }}
            QCalendarWidget QSpinBox {{
                background-color: black;
                color: white;
                border: none;
            }}
            QCalendarWidget QAbstractItemView:enabled {{
                background-color: black;
                color: white;
                selection-background-color: #0078d7;
                selection-color: white;
            }}
        """


        self.setWindowTitle("PPC Screen")
        self.showMaximized()
        self.setStyleSheet("background-color: #f0f0f0;")

        self.layout = QVBoxLayout()

        from_date_label = QLabel("From Date:")
        to_date_label = QLabel("To Date:")

        self.from_date_edit = QDateEdit()
        self.from_date_edit.setDate(QDate.currentDate().addDays(-7))  # default to a week ago
        self.from_date_edit.setDisplayFormat("MM/dd/yyyy")
        self.from_date_edit.setCalendarPopup(True)
        self.from_date_edit.setStyleSheet(input_style)

        self.to_date_edit = QDateEdit()
        self.to_date_edit.setDate(QDate.currentDate())
        self.to_date_edit.setDisplayFormat("MM/dd/yyyy")
        self.to_date_edit.setCalendarPopup(True)
        self.to_date_edit.setStyleSheet(input_style)

        self.filter_btn = QPushButton("Filter")
        self.filter_btn.setStyleSheet(
            "background-color: #0078d7; color: white; padding: 12px 18px; border-radius: 5px; font-size: 16px;"
        )
        self.filter_btn.clicked.connect(self.filter_data_by_date)


        label_style = """
            font-size: 15px;
            font-weight: bold;
            color: black;
            background: transparent;
            margin-right: 5px;
        """
        from_date_label.setStyleSheet(label_style)
        to_date_label.setStyleSheet(label_style)

        self.create_batch_btn = QPushButton("Create Batch")
        self.create_batch_btn.setStyleSheet(
            "background-color: #4CAF50; color: white; padding: 16px; border-radius: 5px; font-size: 16px"
        )
        self.create_batch_btn.clicked.connect(self.open_create_batch_form)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(14)
        button_layout.addStretch()

        button_layout.addWidget(from_date_label)
        button_layout.addWidget(self.from_date_edit)
        button_layout.addWidget(to_date_label)
        button_layout.addWidget(self.to_date_edit)

        button_layout.addWidget(self.filter_btn)

        button_layout.addWidget(self.create_batch_btn)

        self.layout.addLayout(button_layout)

        self.create_table_section(self.layout)

        self.load_data_from_db()  # 👈 Load data after table is created

        self.setLayout(self.layout)


    def create_table_section(self, layout):
        """Create the table layout to display the report."""
        self.report_table = QTableWidget()

        headers = [
            "Shift", "Batch Number", "Line Number", "Operator Name",
            "Part Name", "Part Number", "Customer Name",
            "Packaging Quantity", "Std.Quantity", "Date", "Edit", "Delete"
        ]

        self.report_table.setColumnCount(len(headers))
        self.report_table.setHorizontalHeaderLabels(headers)
        self.report_table.setRowCount(0)

        # Table Styling
        header = self.report_table.horizontalHeader()
        header.setFont(QFont("Arial", 10, QFont.Bold))
        header.setStyleSheet("""
            QHeaderView::section {
                background-color: #003366;
                color: white;
                padding: 4px;
                height: 20px;
                border: 1px solid black;
            }
        """)

        # Set to Interactive so we can manually assign widths
        header.setSectionResizeMode(QHeaderView.Interactive)

        # Set individual column widths (in pixels)
        self.report_table.setColumnWidth(0, 90)   # Shift
        self.report_table.setColumnWidth(1, 130)  # Batch Number
        self.report_table.setColumnWidth(2, 140)  # Line Number
        self.report_table.setColumnWidth(3, 160)  # Operator Name
        self.report_table.setColumnWidth(4, 200)  # Part Name
        self.report_table.setColumnWidth(5, 200)  # Part Number
        self.report_table.setColumnWidth(6, 200)  # Customer Name
        self.report_table.setColumnWidth(7, 180)  # Packaging Quantity ✅ Give it more space
        self.report_table.setColumnWidth(8, 160)  # Std.Quantity
        self.report_table.setColumnWidth(9, 150)  # Date ✅ Reduced width
        self.report_table.setColumnWidth(10, 150)  # Edit
        self.report_table.setColumnWidth(11, 150)  # Delete

        self.report_table.setAlternatingRowColors(True)
        self.report_table.setStyleSheet("""
            QTableWidget {
                border: 2px solid black;
                background-color: white;
                alternate-background-color: #f2f2f2;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)

        layout.addWidget(self.report_table)


    def open_create_batch_form(self):
        """Open the create batch pop-up form."""
        self.create_batch_form = CreateBatchForm(self)
        if self.create_batch_form.exec_() == QDialog.Accepted:
            self.add_to_table()

    def load_data_from_db(self):
        """Fetch existing batch data from DB and populate table."""
        conn = pymysql.connect(** db_config)
        try:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id, shift, batch_number, line_number, operator_name,
                part_name, part_number, customer_name,
                packaging_quantity, std_quantity, created_date
            FROM ppc_batch
        """)
            rows = cursor.fetchall()

            for row_data in rows:
                row = self.report_table.rowCount()
                self.report_table.insertRow(row)

                record_id = row_data[0]
                values = row_data[1:]  # Skip ID for display

                for col, value in enumerate(values):
                    self.report_table.setItem(row, col, QTableWidgetItem(str(value)))

                # Save record ID in vertical header
                id_item = QTableWidgetItem()
                id_item.setData(32, record_id)
                self.report_table.setVerticalHeaderItem(row, id_item)

                # Add Edit/Delete buttons
                self.add_edit_delete_buttons(row)

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            conn.close()

    
    def filter_data_by_date(self):
        """Filter data between selected from and to dates."""
        try:
            from_date = self.from_date_edit.date().toString("yyyy-MM-dd")
            to_date = self.to_date_edit.date().toString("yyyy-MM-dd")

            conn = pymysql.connect(** db_config)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, shift, batch_number, line_number, operator_name,
                    part_name, part_number, customer_name,
                    packaging_quantity, std_quantity, created_date
                FROM ppc_batch
                WHERE created_date BETWEEN %s AND %s
            """, (from_date, to_date))
            rows = cursor.fetchall()

            self.report_table.setRowCount(0)  # Clear current data

            for row_data in rows:
                row = self.report_table.rowCount()
                self.report_table.insertRow(row)

                record_id = row_data[0]
                values = row_data[1:]

                for col, value in enumerate(values):
                    self.report_table.setItem(row, col, QTableWidgetItem(str(value)))

                id_item = QTableWidgetItem()
                id_item.setData(32, record_id)
                self.report_table.setVerticalHeaderItem(row, id_item)

                self.add_edit_delete_buttons(row)

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            conn.close()

    def add_to_table(self):
        row = self.report_table.rowCount()
        self.report_table.insertRow(row)

        values = self.create_batch_form.get_data()
        db_id = getattr(self.create_batch_form, "record_id", None)

        for col, value in enumerate(values):
            self.report_table.setItem(row, col, QTableWidgetItem(value))

        # Store DB ID in vertical header item using custom role
        id_item = QTableWidgetItem()
        id_item.setData(32, db_id)  # Qt.UserRole = 32
        self.report_table.setVerticalHeaderItem(row, id_item)

        # Load icons from absolute paths
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")

        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")

        edit_icon_path = os.path.join(base_path, "resources", "edit.png")
        delete_icon_path = os.path.join(base_path, "resources", "delete.png")


        # Create shadow effect (lighter for better fit)
        def create_shadow_effect():
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(5)
            shadow.setXOffset(1)
            shadow.setYOffset(5)
            shadow.setColor(QColor(50, 50, 50, 100))
            return shadow

        row_height = self.report_table.rowHeight(row)

        # Edit button
        edit_btn = QPushButton()
        edit_btn.setIcon(QIcon(edit_icon_path))
        edit_btn.setIconSize(QSize(20, 20))
        edit_btn.setFixedSize(120, row_height - 10)
        edit_btn.setStyleSheet("border: none; background-color: white; padding: 2px;")
        edit_btn.setGraphicsEffect(create_shadow_effect())
        edit_btn.clicked.connect(lambda _, r=row: self.edit_row(r))
        self.report_table.setCellWidget(row, 10, edit_btn)

        # Delete button
        delete_btn = QPushButton()
        delete_btn.setIcon(QIcon(delete_icon_path))
        delete_btn.setIconSize(QSize(20, 20))
        delete_btn.setFixedSize(120, row_height - 10)
        delete_btn.setStyleSheet("border: none; background-color: white; padding: 2px;")
        delete_btn.setGraphicsEffect(create_shadow_effect())
        delete_btn.clicked.connect(self.handle_delete)
        self.report_table.setCellWidget(row, 11, delete_btn)

    def edit_row(self, row):
        row_data = [self.report_table.item(row, col).text() for col in range(10)]
        record_id_item = self.report_table.verticalHeaderItem(row)
        record_id = int(record_id_item.data(32)) if record_id_item else None

        form = CreateBatchForm(self, row_data)
        form.record_id = record_id  # Pass ID for DB update

        if form.exec_() == QDialog.Accepted:
            updated_values = form.get_data()
            for col, value in enumerate(updated_values):
                self.report_table.setItem(row, col, QTableWidgetItem(value))



    def handle_delete(self):
        """Determine row dynamically and delete it."""
        button = self.sender()
        if button:
            # Loop through rows to find the button
            for row in range(self.report_table.rowCount()):
                if self.report_table.cellWidget(row, 11) == button:  # Column 11 for Delete
                    self.delete_row(row)
                    break

    def delete_row(self, row):
        record_id_item = self.report_table.verticalHeaderItem(row)
        record_id = int(record_id_item.data(32)) if record_id_item else None

        if record_id is None:
            QMessageBox.warning(self, "Error", "Could not find record ID.")
            return

        try:
            conn = pymysql.connect(** db_config)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ppc_batch WHERE id=%s", (record_id,))
            conn.commit()
            self.report_table.removeRow(row)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            conn.close()


    def add_edit_delete_buttons(self, row):
        from PyQt5.QtGui import QIcon, QColor
        from PyQt5.QtWidgets import QGraphicsDropShadowEffect

        def create_shadow_effect():
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(5)
            shadow.setXOffset(1)
            shadow.setYOffset(5)
            shadow.setColor(QColor(50, 50, 50, 100))
            return shadow

        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")

        edit_icon_path = os.path.join(base_path, "resources", "edit.png")
        delete_icon_path = os.path.join(base_path, "resources", "delete.png")


        row_height = self.report_table.rowHeight(row)

        edit_btn = QPushButton()
        edit_btn.setIcon(QIcon(edit_icon_path))
        edit_btn.setIconSize(QSize(18, 18))
        edit_btn.setFixedSize(120, row_height - 10)
        edit_btn.setStyleSheet("border: none; background-color: white; padding: 2px;")
        edit_btn.setGraphicsEffect(create_shadow_effect())
        edit_btn.clicked.connect(lambda _, r=row: self.edit_row(r))
        self.report_table.setCellWidget(row, 10, edit_btn)

        delete_btn = QPushButton()
        delete_btn.setIcon(QIcon(delete_icon_path))
        delete_btn.setIconSize(QSize(18, 18))
        delete_btn.setFixedSize(120, row_height - 10)
        delete_btn.setStyleSheet("border: none; background-color: white; padding: 2px;")
        delete_btn.setGraphicsEffect(create_shadow_effect())
        delete_btn.clicked.connect(self.handle_delete)
        self.report_table.setCellWidget(row, 11, delete_btn)

    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PPCScreen()
    window.show()
    sys.exit(app.exec_())
