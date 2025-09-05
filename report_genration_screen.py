#report_genration_scree.py
import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QLineEdit, QVBoxLayout,
    QHBoxLayout, QTableWidgetItem, QDateEdit, QTableWidget, QHeaderView,
    QComboBox, QMessageBox, QGraphicsDropShadowEffect , QFrame ,QFileDialog ,QSizePolicy ,QScrollArea
)
from PyQt5.QtGui import QFont, QIcon, QColor
from PyQt5.QtCore import QDate, QSize, QTimer ,Qt
import pymysql
import qtawesome as qta
from PyQt5.QtWidgets import QFileDialog
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from PyQt5.QtCore import Qt
import re
import os
import sys

db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': 'kapil',#eplace with your MySQL password
            'database': 'mayur_industries'
            }


class Reportscreen(QWidget):
    """Report generation screen."""

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("PPC Screen")
        self.showMaximized()
        self.setFont(QFont("Segoe UI", 10))

        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")

        calendar_icon_path = os.path.join(base_path, "resources", "calendar1.png").replace("\\", "/")
        down_arrow_icon_path = os.path.join(base_path, "resources", "down-arrow.png").replace("\\", "/")

        # Shared Input Styling (Unified with PPC)
        input_style = """
QComboBox {
    border: 1px solid #ccc;
    border-radius: 5px;
    padding: 6px 10px;
    font-size: 11pt;
    background-color: white;
    min-width: 160px;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border-left: 1px solid #ccc;
    border-top-right-radius: 10px;
    border-bottom-right-radius: 10px;
    background-color: #f5f5f5;
}

QComboBox::down-arrow {
    image: url(resources/down-arrow.png);
    width: 14px;
    height: 14px;
}

QComboBox:hover {
    border: 1px solid #888;
}

QComboBox:disabled {
    background-color: #f0f0f0;
    color: #999;
}
"""


        # Use shared black calendar style
        calendar_input_style = """
        QLineEdit, QComboBox, QDateEdit {
            padding: 4px 6px;
            border: 1px solid #aaa;
            border-radius: 2px;
            font-size: 18px;
            min-height: 28px;
            background-color: white;
            color: black;
        }

        QComboBox::drop-down, QDateEdit::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: right;
            width: 22px;
            border-left: 1px solid #ccc;
        }

        /* Calendar full black styling */
        QCalendarWidget QWidget {
            background-color: black;
            alternate-background-color: black;
            color: white;
            selection-background-color: #0078d7;
            selection-color: white;
        }

        QCalendarWidget QToolButton {
            background-color: black;
            color: white;
            font-weight: bold;
            border: none;
        }

        QCalendarWidget QMenu {
            background-color: black;
            color: white;
        }

        QCalendarWidget QSpinBox {
            background-color: black;
            color: white;
            border: none;
        }

        QCalendarWidget QAbstractItemView:enabled {
            background-color: black;
            color: white;
            selection-background-color: #0078d7;
            selection-color: white;
        }

        /* Fix weekday header text (Sun, Mon, etc.) */
        QCalendarWidget QTableView {
            color: white;
            background-color: black;
            alternate-background-color: black;
        }

        QDateEdit::down-arrow {
            image: url("resources/calendar1.png");
            width: 16px;
            height: 16px;
        }
        """

        selection_layout = QHBoxLayout()
        selection_layout.setSpacing(8)

        # Wrap selection_layout in a right-aligned wrapper
        right_aligned_wrapper = QHBoxLayout()
        right_aligned_wrapper.setContentsMargins(12, 12, 12, 0)  # Optional spacing
        right_aligned_wrapper.addLayout(selection_layout)
        right_aligned_wrapper.setAlignment(Qt.AlignLeft)  # 👈 Align whole thing to right

        # Set the wrapper layout to the top widget
        top_control_widget = QWidget()
        top_control_widget.setLayout(right_aligned_wrapper)
        top_control_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        # Selection dropdown
        selection_label = QLabel("Selection:")
        selection_label.setStyleSheet("font-weight: bold; font-size: 10pt; font-family: 'Segoe UI';")

        self.selection_dropdown = QComboBox()
        self.selection_dropdown.addItems(["Select", "Model-wise", "Date-wise"])
        self.selection_dropdown.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.selection_dropdown.setStyleSheet(input_style)
        self.selection_dropdown.currentIndexChanged.connect(self.on_selection_changed)
        self.selection_dropdown.setFixedWidth(180)
        # Parent Part Name input
        self.model_input = QComboBox()
        self.model_input.setEditable(False)
        self.model_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.model_input.setFixedWidth(180)
        self.model_input.setStyleSheet(input_style)
        self.model_input.setPlaceholderText("Enter Parent Part Name")
        self.load_parent_part_names()

        # From Date
        self.from_date = QDateEdit()
        self.from_date.setCalendarPopup(True)
        self.from_date.setDate(QDate.currentDate())
        self.from_date.setDisplayFormat("MM/dd/yyyy")
        self.from_date.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.from_date.setStyleSheet(calendar_input_style)
        self.from_date.setFixedWidth(180)

        # To Date
        self.to_date = QDateEdit()
        self.to_date.setCalendarPopup(True)
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setDisplayFormat("MM/dd/yyyy")
        self.to_date.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.to_date.setStyleSheet(calendar_input_style)
        self.to_date.setFixedWidth(180)

        # Generate Report Button
        self.generate_button = QPushButton("Generate")
        self.generate_button.setStyleSheet("""
    QPushButton {
        padding: 8px 16px;
        font-size: 14px;
        background-color: #0078d7;
        color: white;
        border-radius: 8px;
        font-family: 'Segoe UI';
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #005bb5;
    }
""")
        self.generate_button.setIcon(qta.icon("fa5s.file-alt", color="white"))
        self.generate_button.clicked.connect(self.generate_report)

        # Export PDF Button
        self.export_pdf_button = QPushButton(" PDF")
        self.export_pdf_button.setStyleSheet("""
    QPushButton {
        padding: 8px 16px;
        font-size: 14px;
        background-color: #d32f2f;
        color: white;
        border-radius: 8px;
        font-family: 'Segoe UI';
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #b71c1c;
    }
""")
        self.export_pdf_button.setIcon(qta.icon("fa5s.file-pdf", color="white"))
        self.export_pdf_button.clicked.connect(self.export_pdf)

        # Export Excel Button
        self.export_excel_button = QPushButton(" Excel")
        self.export_excel_button.setStyleSheet("""
    QPushButton {
        padding: 8px 16px;
        font-size: 14px;
        background-color: #1976d2;
        color: white;
        border-radius: 8px;
        font-family: 'Segoe UI';
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #1565c0;
    }
""")
        self.export_excel_button.setIcon(qta.icon("fa5s.file-excel", color="white"))
        self.export_excel_button.clicked.connect(self.export_excel)

        for btn in [self.generate_button, self.export_pdf_button, self.export_excel_button]:
            btn.setIconSize(QSize(16, 16))

         # Ensure all buttons are the same fixed size
        button_width = 110
        button_height = 40

        for btn in [self.generate_button, self.export_pdf_button, self.export_excel_button]:
            btn.setFixedSize(button_width, button_height)
   
        # Add this HERE — inside initUI()
        generate_icon_path = os.path.join(base_path, "resources", "report generation screen.png")
        pdf_icon_path = os.path.join(base_path, "resources", "export PDF.png")
        excel_icon_path = os.path.join(base_path, "resources", "export excel.png")

        self.generate_button = QPushButton()
        self.generate_button.setIcon(QIcon(generate_icon_path))
        self.generate_button.setToolTip("Generate Report")
        self.generate_button.setFixedSize(48, 48)
        self.generate_button.setIconSize(QSize(28, 28))
        self.generate_button.setStyleSheet("""
    QPushButton {
        background-color: #0078d7;
        border: none;
        border-radius: 6px;
    }
            QPushButton:hover {
        background-color: #005bb5;
            }
        """)
        self.generate_button.clicked.connect(self.generate_report)

        # PDF Button
        self.export_pdf_button = QPushButton()
        self.export_pdf_button.setIcon(QIcon(pdf_icon_path))
        self.export_pdf_button.setToolTip("Export as PDF")
        self.export_pdf_button.setFixedSize(48, 48)
        self.export_pdf_button.setIconSize(QSize(28, 28))
        self.export_pdf_button.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                border: none;
                border-radius: 6px;
            }
        QPushButton:hover {
                background-color: #b71c1c;
            }
        """)
        self.export_pdf_button.clicked.connect(self.export_pdf)

        # Excel Button
        self.export_excel_button = QPushButton()
        self.export_excel_button.setIcon(QIcon(excel_icon_path))
        self.export_excel_button.setToolTip("Export to Excel")
        self.export_excel_button.setFixedSize(48, 48)
        self.export_excel_button.setIconSize(QSize(28, 28))
        self.export_excel_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                border: none;
                border-radius: 6px;
            }
        QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.export_excel_button.clicked.connect(self.export_excel)

        # Selection field
        selection_field_layout = QVBoxLayout()
        selection_label = QLabel("Selection")
        selection_label.setStyleSheet("font-size: 18px; font-weight: 600;")
        selection_field_layout.addWidget(selection_label)
        selection_field_layout.addWidget(self.selection_dropdown)
        selection_layout.addLayout(selection_field_layout)

        # Style for bold labels
        bold_label_style = "font-weight: bold; font-size: 18px; margin-left: 8px;"

        # Labels with bold style and spacing
        parent_label = QLabel("Parent Part Name:")
        parent_label.setStyleSheet(bold_label_style)
        # Parent Part
        parent_field_layout = QVBoxLayout()
        parent_label = QLabel("Parent Part Name")
        parent_label.setStyleSheet("font-size: 18px; font-weight: 600;")
        parent_field_layout.addWidget(parent_label)
        parent_field_layout.addWidget(self.model_input)
        selection_layout.addLayout(parent_field_layout)

        # From Date
        from_field_layout = QVBoxLayout()
        from_label = QLabel("From Date")
        from_label.setStyleSheet("font-size: 18px; font-weight: 600;")
        from_field_layout.addWidget(from_label)
        from_field_layout.addWidget(self.from_date)
        selection_layout.addLayout(from_field_layout)

        # To Date
        to_field_layout = QVBoxLayout()
        to_label = QLabel("To Date")
        to_label.setStyleSheet("font-size: 18px; font-weight: 600;")
        to_field_layout.addWidget(to_label)
        to_field_layout.addWidget(self.to_date)
        selection_layout.addLayout(to_field_layout)


        # Wrap all buttons into a horizontal layout so they sit together and align with input fields
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setAlignment(Qt.AlignBottom)

        buttons_layout.addWidget(self.generate_button)
        buttons_layout.addWidget(self.export_pdf_button)
        buttons_layout.addWidget(self.export_excel_button)

        buttons_widget = QWidget()
        buttons_widget.setLayout(buttons_layout)

        # Wrap it in a vertical layout to align height-wise like other fields
        button_field_layout = QVBoxLayout()
        button_field_layout.addStretch()  # Push buttons to bottom
        button_field_layout.addWidget(buttons_widget)

        selection_layout.addLayout(button_field_layout)

        # selection_layout.addStretch()

        # Set the wrapper layout to the top widget (reuse this!)
        top_control_widget.setLayout(right_aligned_wrapper)  # ✅ correct layout
        top_control_widget.setContentsMargins(0, 0, 0, 0)

        self.layout = QVBoxLayout()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(top_control_widget)
        scroll.setSizeAdjustPolicy(QScrollArea.AdjustToContents)
        scroll.setMaximumHeight(90) 
        self.layout.addWidget(scroll)

        self.create_table_section(self.layout)

        # Show all widgets by default
        self.model_input.show()
        self.from_date.show()
        self.to_date.show()
        self.generate_button.show()
        self.export_pdf_button.show()
        self.export_excel_button.show()

        # Set default model-wise columns
        self.update_table_headers([
            "Parent Part Name",
            "Parent Part Number",
            "Date",
            "Child Parts",
            "OK/NOK Image Counts"
        ])

        self.setLayout(self.layout)


    def on_selection_changed(self, index):
        selected = self.selection_dropdown.currentText()

        if selected == "Model-wise":
            self.load_parent_part_names()
            self.model_input.update()   # Force widget refresh
            self.model_input.repaint()
            QTimer.singleShot(0, self.load_parent_part_names)  # Ensures it loads after full init



    def load_parent_part_names(self):
        try:
            conn = pymysql.connect(** db_config)
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT parent_part_name FROM parent_part ORDER BY parent_part_name ASC")
            part_names = cursor.fetchall()

            self.model_input.blockSignals(True)
            self.model_input.clear()
            self.model_input.addItem("Select")
            self.model_input.model().item(0).setEnabled(False)

            for name in part_names:
                self.model_input.addItem(name[0])

            self.model_input.setCurrentIndex(0)
            self.model_input.blockSignals(False)

        except pymysql.MySQLError as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load parent part names: {str(e)}")
        finally:
            if conn:
                conn.close()


    def generate_report(self):
        selected_type = self.selection_dropdown.currentText()
        model = None  # ✅ Declare early to avoid UnboundLocalError

        try:
            conn = pymysql.connect(** db_config)
            cursor = conn.cursor()

            if selected_type == "Model-wise":
                model = self.model_input.currentText().strip()
                if model == "Select " or not model:
                    QMessageBox.warning(self, "Input Error", "Please enter a Parent Part Name.")
                    return

                headers = ["Parent Part Name", "Parent Part Number", "Child Parts", "OK Count", "NOK Count", "Time", "Reason"]
                self.update_table_headers(headers)

                query = """
                    SELECT 
                        ok.part_name,
                        pp.parent_part_number,
                        COUNT(cp.child_part_name) AS number_of_child_parts,
                        ok.ok,
                        ok.nok,
                        ok.time,
                        ok.reason
                    FROM ok_nok ok
                    JOIN parent_part pp ON pp.parent_part_name = ok.part_name
                    LEFT JOIN child_part cp ON cp.parent_part_name = ok.part_name
                    WHERE ok.part_name = %s
                    GROUP BY ok.id
                """


                cursor.execute(query, (model,))
                rows = cursor.fetchall()


            elif selected_type == "Date-wise":
                from_date = self.from_date.date().toString("yyyy-MM-dd")
                to_date = self.to_date.date().toString("yyyy-MM-dd")

                headers = [
                    "Part Number",
                    "Part Name",
                    "Total Parts Inspected",
                    "Std.Quantity",
                    "OK Count",
                    "NOK Count",
                    "OK Percentage",
                    "NOK Percentage"
                ]
                self.update_table_headers(headers)

                query = """
                    SELECT 
                        pp.parent_part_number,
                        pp.parent_part_name,
                        COUNT(inspect.part_name) AS total_parts,
                        (SELECT SUM(std_quantity) FROM ppc_batch pb2 
                        WHERE pb2.part_name = pp.parent_part_name) AS std_quantity,
                        SUM(inspect.ok_flag) AS ok_count,
                        SUM(inspect.nok_flag) AS nok_count,
                        CONCAT(ROUND(SUM(inspect.ok_flag) / 
                            (SUM(inspect.ok_flag) + SUM(inspect.nok_flag)) * 100, 2), '%%') AS ok_percentage,
                        CONCAT(ROUND(SUM(inspect.nok_flag) / 
                            (SUM(inspect.ok_flag) + SUM(inspect.nok_flag)) * 100, 2), '%%') AS nok_percentage
                    FROM parent_part pp
                    LEFT JOIN (
                        SELECT
                            part_name,
                            CASE WHEN ok > 0 THEN 1 ELSE 0 END AS ok_flag,
                            CASE WHEN nok > 0 THEN 1 ELSE 0 END AS nok_flag
                        FROM ok_nok
                        WHERE IN_DATE BETWEEN %s AND %s
                    ) AS inspect ON inspect.part_name = pp.parent_part_name
                    WHERE EXISTS (
                        SELECT 1 FROM ok_nok ok 
                        WHERE ok.part_name = pp.parent_part_name 
                        AND ok.IN_DATE BETWEEN %s AND %s
                    )
                    GROUP BY pp.id, pp.parent_part_number, pp.parent_part_name;
                """

                cursor.execute(query, (from_date, to_date, from_date, to_date))
                rows = cursor.fetchall()

            else:
                QMessageBox.information(self, "Notice", "Please select a report type.")
                return

            self.populate_table(rows)

        except pymysql.MySQLError as e:
            QMessageBox.critical(self, "Database Error", f"Error: {str(e)}")
        finally:
            if conn:
                conn.close()


    def update_table_headers(self, headers):
        self.report_table.clear()
        self.report_table.setColumnCount(len(headers))
        self.report_table.setHorizontalHeaderLabels(headers)
        self.report_table.setRowCount(0)

        header = self.report_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

    # ✅ Add this right after
    def populate_table(self, rows):
        self.report_table.setRowCount(0)
        for row_data in rows:
            row_pos = self.report_table.rowCount()
            self.report_table.insertRow(row_pos)
            for col, value in enumerate(row_data):
                text = str(value)

                # Check if it's the "Reason" column (e.g., 6th column index)
                if col == 6:  # Update this index as per your actual table
                    # Insert newline before each numbered item (except the first one)
                    text = re.sub(r'(?<!^)(?=\d+\.\s)', '\n', text)

                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                item.setToolTip(text)
                item.setWhatsThis(text)
                self.report_table.setItem(row_pos, col, item)

        self.report_table.setWordWrap(True)
        self.report_table.resizeRowsToContents()
        self.report_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)



    def create_table_section(self, layout):
        self.report_table = QTableWidget()
        self.report_table.setColumnCount(0)
        self.report_table.setRowCount(0)
        self.report_table.setFont(QFont("Segoe UI", 11))

        header = self.report_table.horizontalHeader()
        header.setFont(QFont("Segoe UI", 10, QFont.Bold))
        header.setStyleSheet("""
QHeaderView::section {
    background-color: #1976d2;
    color: white;
    font-family: 'Segoe UI Semibold';
    font-size: 13px;
    font-weight: 600;
    padding: 2px 4px;
    border: none;
    border-bottom: 2px solid #1565c0;
}
QTableView QTableCornerButton::section {
    background-color: #1976d2;
    border: none;
}
""")


        header.setSectionResizeMode(QHeaderView.Stretch)

        # ✅ Hide serial number (row index) header
        self.report_table.verticalHeader().setVisible(False)

        self.report_table.setAlternatingRowColors(True)
        self.report_table.setStyleSheet("""
QTableWidget {
    background-color: #ffffff;
    alternate-background-color: #f9fbfc;
    border: 1px solid #cfd8dc;
    border-radius: 10px;
    font-size: 14px;
    font-family: 'Segoe UI', 'Segoe UI';
    gridline-color: #e0e0e0;
}

QTableWidget::item {
    padding: 4px;
    border: none;
    color: #333333;
}

QTableWidget::item:selected {
    background-color: #e3f2fd;
    color: #0d47a1;
    border: none;
}
""")

        table_frame = QFrame()
        table_frame.setFrameShape(QFrame.NoFrame)
        table_frame.setStyleSheet("background-color: white; border-radius: 8px;")

        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(10, 10, 10, 10)
        table_layout.addWidget(self.report_table)

        layout.addWidget(table_frame)


    def export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Report as PDF", "", "PDF Files (*.pdf)"
        )
        if not path:
            return

        # ⚡ Reduce the top margin to, say, 0.3"
        doc = SimpleDocTemplate(
            path,
            pagesize=letter,
            topMargin=0.3*inch,
            leftMargin=1*inch,
            rightMargin=0.5*inch,
            bottomMargin=0.5*inch,
        )
        elements = []

        # … your existing logo + name Table or flowables …
        # (exactly as in the last snippet, e.g.)
        logo = None
        try:
            logo = Image("Mayur_ind_logo.jpg", width=1*inch, height=1*inch)
        except IOError:
            pass

        name_style = ParagraphStyle(
            name="CompanyName",
            fontName="Helvetica-Bold",
            fontSize=20,
            textColor=colors.red,
            alignment=0,
            leftIndent=25
        )
        name_par = Paragraph("MAYUR INDUSTRIES PVT.LTD.", name_style)

        if logo:
            header = Table(
                [[logo, name_par]],
                colWidths=[1*inch, doc.width - 1*inch]
            )
            header.setStyle(TableStyle([
                ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                ('LEFTPADDING',(0,0),(0,0),0),
                ('RIGHTPADDING',(0,0),(0,0),0),
            ]))
            elements.append(header)
        else:
            # fallback
            name_style.alignment = 1
            elements.append(Paragraph("MAYUR INDUSTRIES PVT.LTD.", name_style))

        elements.append(Spacer(1, 0.2*inch))

        # 3) then your table as before…
        headers = [
            "parent part\nname",
            "parent part\nnumber",
            "number of\nchild parts",
            "OK\nCount",
            "NOK\nCount",
            "Time",
            "Reason"
        ]
        data = [headers]
        for r in range(self.report_table.rowCount()):
            row = []
            for c in range(self.report_table.columnCount()):
                cell_text = self.report_table.item(r, c).text() if self.report_table.item(r, c) else ""
                if headers[c].strip().lower() == "reason":
                    # Insert line break before each numbered item
                    cell_text = re.sub(r'(?<!^)(?=\d+\.\s)', '\n', cell_text)
                row.append(cell_text)
            data.append(row)


        col_widths = [1.8*inch, 1.1*inch, 0.7*inch, 0.5*inch, 0.5*inch, 0.6*inch, 2.2*inch]  # Adjust as neededS
        body = Table(data, colWidths=col_widths, repeatRows=1)

        body.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#003366")),
            ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
            ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
            ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME',   (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE',   (0,0), (-1,-1), 8),
            ('GRID',       (0,0), (-1,-1), 0.5, colors.black),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f2f2f2")]),
        ]))
        elements.append(body)

        doc.build(elements)
        QMessageBox.information(self, "Export Successful", "PDF exported with logo and name side-by-side.")


    def export_excel(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Report as Excel", "", "Excel Files (*.xlsx)"
        )
        if not path:
            return

        # 1) Build headers & data
        headers = [
            self.report_table.horizontalHeaderItem(c).text()
            for c in range(self.report_table.columnCount())
        ]
        data = [
            [
                self.report_table.item(r, c).text()
                if self.report_table.item(r, c) else ""
                for c in range(self.report_table.columnCount())
            ]
            for r in range(self.report_table.rowCount())
        ]

        # 2) Create df
        df = pd.DataFrame(data, columns=headers)

        # 3) Write with XlsxWriter
        with pd.ExcelWriter(path, engine='xlsxwriter') as writer:
            # write table starting at row 1 (so row 0 is free)
            df.to_excel(writer, sheet_name='Report', startrow=1, index=False)

            wb = writer.book
            ws = writer.sheets['Report']

            # make room for logo & text
            ws.set_row(0, 80)

            # insert logo into A1
            logo_path = "Mayur_ind_logo.jpg"
            try:
                ws.insert_image('A1', logo_path, {'x_scale': 0.5, 'y_scale': 0.5})
            except FileNotFoundError:
                pass

            # merge from B1 across to the last column for the company name
            last_col = chr(ord('A') + len(headers) - 1)
            comp_fmt = wb.add_format({
                'bold': True,
                'font_color': 'red',
                'font_size': 14,
                'align': 'left',
                'valign': 'vcenter'
            })
            ws.merge_range(f'B1:{last_col}1',
                        "MAYUR INDUSTRIES PVT.LTD.",
                        comp_fmt)

        QMessageBox.information(
            self, "Export Successful",
            "Excel exported with logo in A1 and company name beside it."
        )


if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app = QApplication(sys.argv)
    window = Reportscreen()
    window.show()
    sys.exit(app.exec_())
