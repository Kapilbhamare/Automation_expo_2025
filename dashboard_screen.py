# from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox,QHBoxLayout, QLabel, QFrame, QSizePolicy ,QComboBox, QDateEdit, QPushButton,QGridLayout  
# from PyQt5.QtGui import QFont , QPainter
# from PyQt5.QtCore import Qt, QTimer ,QDate
# from PyQt5.QtChart import QChart, QChartView, QBarSet, QBarSeries, QPieSeries, QLineSeries, QCategoryAxis, QValueAxis
# import pymysql

# # ✅ Database configuration
# db_config = {
#     'host': 'localhost',
#     'user': 'root',
#     'password': 'Gayatri@30',
#     'database': 'mayur_industries'
# }
# class DashboardScreen(QWidget):
#     def __init__(self):
#         super().__init__()

#         # Main layout
#         self.layout = QVBoxLayout()
#         self.layout.setContentsMargins(15, 15, 15, 15)
#         self.layout.setAlignment(Qt.AlignTop)

#         # Cards container
#         self.cards_layout = QHBoxLayout()
#         self.cards_layout.setSpacing(30)
#         self.cards_layout.setAlignment(Qt.AlignCenter)
#         self.cards_layout.setContentsMargins(10, 10, 10, 10)
#         self.layout.addLayout(self.cards_layout)
#         self.add_filters()

#         self.chart_area = QGridLayout()
#         self.chart_area.setSpacing(15)  # Optional: add space between graphs
#         self.chart_area.setColumnStretch(0, 1)
#         self.chart_area.setColumnStretch(1, 1)
#         self.chart_area.setRowStretch(0, 1)
#         self.chart_area.setRowStretch(1, 1)

#         self.layout.addLayout(self.chart_area)

#         self.setLayout(self.layout)

#         # Initial load
#         self.refresh_dashboard()

#         # Auto refresh every 60 seconds
#         self.timer = QTimer()
#         self.timer.timeout.connect(self.refresh_dashboard)
#         self.timer.start(60000)

#     def create_labeled_widget(self, label_text, widget, label_style):
#         wrapper = QHBoxLayout()
#         wrapper.setSpacing(5)
#         wrapper.setContentsMargins(0, 0, 0, 0)

#         label = QLabel(label_text)
#         label.setStyleSheet(label_style)
#         label.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
#         label.setFixedWidth(70)  # You can adjust this width for better alignment

#         wrapper.addWidget(label)
#         wrapper.addWidget(widget)

#         container = QFrame()
#         container.setLayout(wrapper)
#         return container

        
#     def add_filters(self):
#         self.filter_layout = QHBoxLayout()
#         self.filter_layout.setAlignment(Qt.AlignVCenter)
#         self.filter_layout.setSpacing(7)
#         self.filter_layout.setContentsMargins(5, 10, 5, 10)

#         label_style = "font-weight: bold; font-size: 10pt;"
#         combo_style = """
#             QComboBox {
#     border: 1px solid #ccc;
#     border-radius: 10px;
#     padding: 4px 8px;
#     font-size: 9pt;
#     background-color: white;
#     min-width: 160px;
# }

# QComboBox::drop-down {
#     subcontrol-origin: padding;
#     subcontrol-position: top right;
#     width: 25px;
#     border-left: 1px solid #ccc;
#     border-top-right-radius: 10px;
#     border-bottom-right-radius: 10px;
# }

# QComboBox::down-arrow {
#     image: url(:/icons/down-arrow.png);  /* Replace with your arrow or use default styling */
#     width: 12px;
#     height: 12px;
# }
# """
#         date_style = """
# QDateEdit {
#     border: 1px solid #ccc;
#     border-radius: 10px;
#     padding: 4px 8px;
#     font-size: 9pt;
#     background-color: white;
#     min-width: 160px;
# }
# """
#         button_style = """
# QPushButton {
#     background-color: #1976d2;
#     color: white;
#     font-weight: 500;
#     padding: 4px 12px;
#     border-radius: 10px;
#     font-size: 9pt;
#     min-height: 28px;
#     min-width: 160px;
# }

# QPushButton:hover {
#     background-color: #125ea2;
# }

# QPushButton:disabled {
#     background-color: #ccc;
#     color: #666;
# }
# """

#         self.selection_dropdown = QComboBox()
#         self.selection_dropdown.addItems(["Select", "Date-wise", "Model-wise"])
#         self.selection_dropdown.setStyleSheet(combo_style)
#         self.selection_dropdown.setFixedWidth(200)
#         self.selection_dropdown.currentIndexChanged.connect(self.on_filter_change)

#         self.model_input = QComboBox()
#         self.model_input.setEnabled(False)
#         self.model_input.setStyleSheet(combo_style)
#         self.model_input.setFixedWidth(200)

#         self.from_date = QDateEdit()
#         self.from_date.setCalendarPopup(True)
#         self.from_date.setDate(QDate.currentDate())
#         self.from_date.setEnabled(False)
#         self.from_date.setStyleSheet(date_style)
#         self.from_date.setFixedWidth(200)

#         self.to_date = QDateEdit()
#         self.to_date.setCalendarPopup(True)
#         self.to_date.setDate(QDate.currentDate())
#         self.to_date.setEnabled(False)
#         self.to_date.setStyleSheet(date_style)
#         self.to_date.setFixedWidth(200)

#         self.generate_btn = QPushButton("Generate Report")
#         self.generate_btn.setEnabled(False)
#         self.generate_btn.clicked.connect(self.load_graph_data)
#         self.generate_btn.setStyleSheet(button_style)
#         self.generate_btn.setFixedHeight(23)  # Same as min-height of dropdowns
#         self.generate_btn.setFixedWidth(200)

#     # Add widgets with labels
#         self.filter_layout.addWidget(self.create_labeled_widget("Selection:", self.selection_dropdown, label_style))
#         self.filter_layout.addWidget(self.create_labeled_widget("Model:", self.model_input, label_style))
#         self.filter_layout.addWidget(self.create_labeled_widget("From:", self.from_date, label_style))
#         self.filter_layout.addWidget(self.create_labeled_widget("To:", self.to_date, label_style))
#         self.filter_layout.addWidget(self.generate_btn)

#         self.layout.addLayout(self.filter_layout)

#     def on_filter_change(self):
#         selected = self.selection_dropdown.currentText()
#         self.model_input.setEnabled(False)
#         self.from_date.setEnabled(False)
#         self.to_date.setEnabled(False)

#         if selected == "Model-wise":
#             self.model_input.setEnabled(True)
#             self.load_model_dropdown()
#         elif selected == "Date-wise":
#             self.from_date.setEnabled(True)
#             self.to_date.setEnabled(True)

#         self.generate_btn.setEnabled(True)

#     def load_model_dropdown(self):
#         try:
#             conn = pymysql.connect(**db_config)
#             cursor = conn.cursor()
#             cursor.execute("SELECT DISTINCT parent_part_name FROM parent_part ORDER BY parent_part_name ASC")
#             parts = cursor.fetchall()
#             self.model_input.clear()
#             for p in parts:
#                 self.model_input.addItem(p[0])
#         except Exception as e:
#             QMessageBox.critical(self, "Model load error:", f"An error occurred:\n{str(e)}")
#             # print(f"Model load error: {e}")
#         finally:
#             conn.close()

#     def clear_charts(self):
#         while self.chart_area.count():
#             item = self.chart_area.takeAt(0)
#             widget = item.widget()
#             if widget is not None:
#                 widget.setParent(None)

#     def load_graph_data(self):
#         self.clear_charts()
#         selected = self.selection_dropdown.currentText()

#         if selected == "Date-wise":
#             from_date = self.from_date.date().toString("yyyy-MM-dd")
#             to_date = self.to_date.date().toString("yyyy-MM-dd")
#             self.load_datewise_charts(from_date, to_date)

#         elif selected == "Model-wise":
#             model = self.model_input.currentText()
#             self.load_modelwise_charts(model)
    
#     def load_modelwise_charts(self, model):
#         try:
#             conn = pymysql.connect(**db_config)
#             cursor = conn.cursor()

#         # Chart 1: Stacked Bar Chart - Reason-wise NOK Distribution per Entry
#             cursor.execute("""
#                 SELECT id, reason, COUNT(*) FROM ok_nok
#                 WHERE part_name = %s AND reason IS NOT NULL AND reason != ''
#                 GROUP BY id, reason ORDER BY id
#             """, (model,))
#             data = cursor.fetchall()

#             entry_reason_counts = {}
#             reasons_set = set()

#             for entry_id, reason, count in data:
#                 reasons_set.add(reason)
#                 if entry_id not in entry_reason_counts:
#                     entry_reason_counts[entry_id] = {}
#                 entry_reason_counts[entry_id][reason] = count

#             sorted_entries = sorted(entry_reason_counts.keys())
#             sorted_reasons = sorted(reasons_set)

#             sets_chart1 = []
#             for reason in sorted_reasons:
#                 bar_set = QBarSet(reason)
#                 for entry in sorted_entries:
#                     count = entry_reason_counts[entry].get(reason, 0)
#                     bar_set.append(count)
#                 sets_chart1.append(bar_set)

#             series1 = QBarSeries()
#             for bar_set in sets_chart1:
#                 series1.append(bar_set)

#             chart1 = QChart()
#             chart1.addSeries(series1)
#             chart1.setTitle("Stacked Bar Chart – Reason-wise NOK Distribution per Entry")
#             axis_x1 = QCategoryAxis()
#             for i, entry in enumerate(sorted_entries):
#                 axis_x1.append(str(entry), i)
#             chart1.createDefaultAxes()
#             chart1.setAxisX(axis_x1, series1)
#             chart_view1 = QChartView(chart1)
#             chart_view1.setRenderHint(QPainter.Antialiasing)

#         # Chart 2: Bar Chart – Frequency of NOK Reasons across child parts
#             cursor.execute("""
#                 SELECT reason, COUNT(*) FROM ok_nok
#                 WHERE part_name = %s AND reason IS NOT NULL AND reason != ''
#                 GROUP BY reason
#             """, (model,))
#             data = cursor.fetchall()
#             reasons = [row[0] for row in data]
#             counts = [row[1] for row in data]

#             bar_set2 = QBarSet("Occurrences")
#             bar_set2.append(counts)

#             series2 = QBarSeries()
#             series2.append(bar_set2)

#             chart2 = QChart()
#             chart2.addSeries(series2)
#             chart2.setTitle("Bar Chart – Frequency of NOK Reasons Across Child Parts")
#             axis_x2 = QCategoryAxis()
#             for i, reason in enumerate(reasons):
#                 axis_x2.append(reason, i)
#             chart2.createDefaultAxes()
#             chart2.setAxisX(axis_x2, series2)
#             chart_view2 = QChartView(chart2)
#             chart_view2.setRenderHint(QPainter.Antialiasing)

#         # Chart 3: Line Chart – NOK Count Over Time
#             cursor.execute("""
#                 SELECT in_date, SUM(nok) FROM ok_nok
#                 WHERE part_name = %s
#                 GROUP BY in_date ORDER BY in_date
#             """, (model,))
#             data = cursor.fetchall()
#             dates = [str(row[0]) for row in data]
#             nok_counts = [row[1] for row in data]

#             series3 = QLineSeries()
#             for i, count in enumerate(nok_counts):
#                 series3.append(i, count)

#             chart3 = QChart()
#             chart3.addSeries(series3)
#             chart3.setTitle("Line Chart – NOK Count Over Time")
#             axis_x3 = QCategoryAxis()
#             for i, date in enumerate(dates):
#                 axis_x3.append(date, i)
#             chart3.createDefaultAxes()
#             chart3.setAxisX(axis_x3, series3) 
#             chart_view3 = QChartView(chart3)
#             chart_view3.setRenderHint(QPainter.Antialiasing)

#         # Chart 4: Stacked Bar Chart – Reason-wise NOK Distribution by Child Part
#             cursor.execute("""
#                 SELECT part_name, reason, COUNT(*) FROM ok_nok
#                 WHERE part_name = %s AND reason IS NOT NULL AND reason != ''
#                 GROUP BY part_name, reason ORDER BY part_name
#             """, (model,))
#             data = cursor.fetchall()

#             child_reason_map = {}
#             child_parts = set()
#             reasons_set = set()

#             for child, reason, count in data:
#                 child_parts.add(child)
#                 reasons_set.add(reason)
#                 if child not in child_reason_map:
#                     child_reason_map[child] = {}
#                 child_reason_map[child][reason] = count

#             sorted_children = sorted(child_parts)
#             sorted_reasons = sorted(reasons_set)

#             series4 = QBarSeries()
#             for reason in sorted_reasons:
#                 bar_set = QBarSet(reason)
#                 for child in sorted_children:
#                     count = child_reason_map[child].get(reason, 0)
#                     bar_set.append(count)
#                 series4.append(bar_set)

#             chart4 = QChart()
#             chart4.addSeries(series4)
#             chart4.setTitle("Stacked Bar Chart – Reason-wise NOK Distribution by Child Part")
#             axis_x4 = QCategoryAxis()
#             for i, child in enumerate(sorted_children):
#                 axis_x4.append(child, i)
#             chart4.createDefaultAxes()
#             chart4.setAxisX(axis_x4, series4)
#             chart_view4 = QChartView(chart4)
#             chart_view4.setRenderHint(QPainter.Antialiasing)

#         # Set layout and sizes
#             for view in [chart_view1, chart_view2, chart_view3, chart_view4]:
#                 view.setMinimumSize(500, 300)
#                 view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

#             self.chart_area.addWidget(chart_view1, 0, 0)
#             self.chart_area.addWidget(chart_view2, 0, 1)
#             self.chart_area.addWidget(chart_view3, 1, 0)
#             self.chart_area.addWidget(chart_view4, 1, 1)

#         except Exception as e:
#             QMessageBox.critical(self, "Model-wise Chart Error", f"An error occurred:\n{str(e)}")
#         finally:
#             conn.close()


#     def load_datewise_charts(self, from_date, to_date):
#         try:
#             conn = pymysql.connect(**db_config)
#             cursor = conn.cursor()

#         # --- CHART 1: OK vs NOK Count per Part ---
#             cursor.execute("""
#                 SELECT part_name, SUM(ok), SUM(nok)
#                 FROM ok_nok
#                 WHERE IN_DATE BETWEEN %s AND %s
#                 GROUP BY part_name
#             """, (from_date, to_date))
#             data = cursor.fetchall()

#             part_names = [row[0] for row in data]
#             ok_values = [row[1] for row in data]
#             nok_values = [row[2] for row in data]

#             ok_set = QBarSet("OK Count")
#             nok_set = QBarSet("NOK Count")
#             ok_set.append(ok_values)
#             nok_set.append(nok_values)

#             series1 = QBarSeries()
#             series1.append(ok_set)
#             series1.append(nok_set)

#             chart1 = QChart()
#             chart1.addSeries(series1)
#             chart1.setTitle("OK vs NOK Count per Part")
#             chart1.createDefaultAxes()

#             axis_x1 = QCategoryAxis()
#             for i, name in enumerate(part_names):
#                 axis_x1.append(name, i)
#             chart1.setAxisX(axis_x1, series1)

#             chart_view1 = QChartView(chart1)
#             chart_view1.setRenderHint(QPainter.Antialiasing)

#         # --- CHART 2: Pareto Chart - NOK % & Cumulative ---
#             percentages = []
#             cum_values = []
#             total_nok = sum(nok_values)
#             running_sum = 0
#             for val in nok_values:
#                 pct = (val / total_nok) * 100 if total_nok else 0
#                 percentages.append(pct)
#                 running_sum += pct
#                 cum_values.append(running_sum)

#             bar_set = QBarSet("NOK Percentage")
#             bar_set.append(percentages)

#             bar_series = QBarSeries()
#             bar_series.append(bar_set)

#             line_series = QLineSeries()
#             for i, val in enumerate(cum_values):
#                 line_series.append(i, val)
#             line_series.setName("Cumulative NOK %")

#             chart2 = QChart()
#             chart2.addSeries(bar_series)
#             chart2.addSeries(line_series)
#             chart2.setTitle("Pareto Chart – NOK Percentage and Cumulative Impact")
#             chart2.createDefaultAxes()

#             axis_x2 = QCategoryAxis()
#             for i, name in enumerate(part_names):
#                 axis_x2.append(name, i)
#             chart2.setAxisX(axis_x2, bar_series)
#             chart2.setAxisX(axis_x2, line_series)

#             axis_right = QValueAxis()
#             axis_right.setTitleText("Cumulative NOK %")
#             axis_right.setLabelFormat("%.0f")
#             axis_right.setRange(0, 100)
#             chart2.addAxis(axis_right, Qt.AlignRight)
#             line_series.attachAxis(axis_right)

#             chart_view2 = QChartView(chart2)
#             chart_view2.setRenderHint(QPainter.Antialiasing)

#         # --- CHART 3: Pie Chart - Overall OK vs NOK ---
#             cursor.execute("""
#                 SELECT SUM(ok), SUM(nok)
#                 FROM ok_nok
#                 WHERE IN_DATE BETWEEN %s AND %s
#             """, (from_date, to_date))
#             ok_total, nok_total = cursor.fetchone()
#             ok_total = ok_total or 0
#             nok_total = nok_total or 0

#             pie_series = QPieSeries()
#             pie_series.append("OK", ok_total)
#             pie_series.append("NOK", nok_total)

#             chart3 = QChart()
#             chart3.addSeries(pie_series)
#             chart3.setTitle("Pie Chart – Overall OK vs NOK Ratio")
#             chart_view3 = QChartView(chart3)
#             chart_view3.setRenderHint(QPainter.Antialiasing)

#         # --- CHART 4: OK & NOK Percentage Trend Line Chart ---
#             line_series_ok = QLineSeries()
#             line_series_nok = QLineSeries()
#             line_series_ok.setName("OK Percentage")
#             line_series_nok.setName("NOK Percentage")

#             for i, (ok, nok) in enumerate(zip(ok_values, nok_values)):
#                 total = ok + nok
#                 ok_pct = (ok / total) * 100 if total else 0
#                 nok_pct = (nok / total) * 100 if total else 0
#                 line_series_ok.append(i, ok_pct)
#                 line_series_nok.append(i, nok_pct)

#             chart4 = QChart()
#             chart4.addSeries(line_series_ok)
#             chart4.addSeries(line_series_nok)
#             chart4.setTitle("OK & NOK Percentage Trend per Part")
#             chart4.createDefaultAxes()

#             axis_x4 = QCategoryAxis()
#             for i, name in enumerate(part_names):
#                 axis_x4.append(name, i)
#             chart4.setAxisX(axis_x4, line_series_ok)
#             chart4.setAxisX(axis_x4, line_series_nok)

#             chart_view4 = QChartView(chart4)
#             chart_view4.setRenderHint(QPainter.Antialiasing)

#         # --- Add All Charts to Grid ---
#             for view in [chart_view1, chart_view2, chart_view3, chart_view4]:
#                 view.setMinimumSize(500, 300)
#                 view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

#             self.chart_area.addWidget(chart_view1, 0, 0)
#             self.chart_area.addWidget(chart_view2, 0, 1)
#             self.chart_area.addWidget(chart_view3, 1, 0)
#             self.chart_area.addWidget(chart_view4, 1, 1)

#         except Exception as e:
#             QMessageBox.critical(self, "Date-wise Chart Error", f"Could not load date-wise chart:\n{str(e)}")
#         finally:
#             conn.close()

#     def refresh_dashboard(self):
#         ok, nok, ok_percentage, reason = self.fetch_dashboard_data()
#         self.update_cards([
#             ("Total OK", str(ok), "#d6f5e3", "#1b5e20"),
#             ("Total NOK", str(nok), "#fbd4d4", "#b71c1c"),
#             ("OK Percentage", ok_percentage, "#fff4cc", "#795548"),
#             ("Top Defect Reason", reason, "#dceefb", "#1a237e")
#         ])

#     def fetch_dashboard_data(self):
#         try:
#             conn = pymysql.connect(**db_config)
#             cursor = conn.cursor()

#             # Get OK and NOK counts
#             cursor.execute("SELECT SUM(ok), SUM(nok) FROM ok_nok")
#             ok, nok = cursor.fetchone()
#             ok = ok or 0
#             nok = nok or 0
#             total = ok + nok

#             if total > 0:
#                 percent = round((ok / total) * 100, 2)
#                 ok_percentage = f"{percent}%"
#             else:
#                 ok_percentage = "0.00%"

#             # Get top defect reason
#             cursor.execute("""
#                 SELECT reason, COUNT(*) as cnt
#                 FROM ok_nok
#                 WHERE reason IS NOT NULL AND reason != ''
#                 GROUP BY reason
#                 ORDER BY cnt DESC
#                 LIMIT 1
#             """)
#             result = cursor.fetchone()
#             top_reason = result[0] if result else "N/A"

#             return ok, nok, ok_percentage, top_reason

#         except Exception as e:
#             QMessageBox.critical(self, "Dashboard DB Error:", f"An error occurred:\n{str(e)}")
#             # print(f"Dashboard DB Error: {e}")
#             return 0, 0, "0.00%", "N/A"
#         finally:
#             if conn:
#                 conn.close()

#     def update_cards(self, card_data):
#         # Clear existing widgets
#         for i in reversed(range(self.cards_layout.count())):
#             widget = self.cards_layout.itemAt(i).widget()
#             if widget:
#                 widget.setParent(None)

#         # Add new cards
#         for title, value, bg_color, text_color in card_data:
#             card = self.createCard(title, value, bg_color, text_color)
#             self.cards_layout.addWidget(card)

#     def createCard(self, title, value, bg_color, text_color):
#         card = QFrame()
#         card.setStyleSheet(f"""
#             QFrame {{
#                 background-color: {bg_color};
#                 border-radius: 18px;
#             }}
#         """)
#         card.setFixedSize(190, 70)
#         card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

#         layout = QVBoxLayout()
#         layout.setAlignment(Qt.AlignCenter)
#         layout.setContentsMargins(6, 6, 6, 6)
#         layout.setSpacing(4)

#         title_lbl = QLabel(title)
#         title_lbl.setFont(QFont("Segoe UI", 7))
#         title_lbl.setAlignment(Qt.AlignCenter)
#         title_lbl.setStyleSheet(f"color: {text_color};")

#         value_lbl = QLabel(value)
#         value_lbl.setFont(QFont("Segoe UI", 16, QFont.Bold))
#         value_lbl.setAlignment(Qt.AlignCenter)
#         value_lbl.setStyleSheet(f"color: {text_color}; letter-spacing: 0.5px;")

#         layout.addWidget(title_lbl)
#         layout.addWidget(value_lbl)
#         card.setLayout(layout)

#         return card



from PyQt5.QtWidgets import QWidget, QApplication,QVBoxLayout,QSizePolicy, QMessageBox,QHBoxLayout, QLabel, QFrame, QSizePolicy ,QComboBox, QDateEdit, QPushButton,QGridLayout  
from PyQt5.QtGui import QFont , QPainter , QIcon
from PyQt5.QtCore import Qt, QTimer ,QDate , QSize , QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot
import plotly.graph_objects as go
from PyQt5.QtWebEngineWidgets import QWebEngineView
import pymysql
import resources_rc
from style import calendar_input_style
import os
import sys
import re


class ChartWorkerSignals(QObject):
    finished = pyqtSignal(object, object)  # Will emit chart_view1 and chart_view2

class ChartWorker(QRunnable):
    def __init__(self, mode, arg1=None, arg2=None, db_config=None):
        super().__init__()
        self.mode = mode
        self.arg1 = arg1
        self.arg2 = arg2
        self.db_config = db_config
        self.signals = ChartWorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            conn = pymysql.connect(**self.db_config)
            cursor = conn.cursor()

            if self.mode == "model":
                model = self.arg1
                cursor.execute("""
                    SELECT part_name, SUM(ok), SUM(nok)
                    FROM ok_nok WHERE part_name = %s
                    GROUP BY part_name
                """, (model,))
                bar_data = cursor.fetchall()

                cursor.execute("""
                    SELECT SUM(ok), SUM(nok)
                    FROM ok_nok WHERE part_name = %s
                """, (model,))
                ok_total, nok_total = cursor.fetchone()

                result = {
                    "bar_data": bar_data,
                    "ok_total": ok_total or 0,
                    "nok_total": nok_total or 0
                }

            elif self.mode == "date":
                from_date, to_date = self.arg1, self.arg2
                cursor.execute("""
                    SELECT part_name, SUM(ok), SUM(nok)
                    FROM ok_nok WHERE IN_DATE BETWEEN %s AND %s
                    GROUP BY part_name
                """, (from_date, to_date))
                bar_data = cursor.fetchall()

                cursor.execute("""
                    SELECT SUM(ok), SUM(nok)
                    FROM ok_nok WHERE IN_DATE BETWEEN %s AND %s
                """, (from_date, to_date))
                ok_total, nok_total = cursor.fetchone()

                result = {
                    "bar_data": bar_data,
                    "ok_total": ok_total or 0,
                    "nok_total": nok_total or 0
                }

            cursor.close()
            conn.close()
            self.signals.finished.emit(self.mode, result)

        except Exception as e:
            print(f"[ChartWorker Error] {e}")

# ✅ Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'kapil',
    'database': 'mayur_industries'
}

class DashboardScreen(QWidget):
    def __init__(self):
        super().__init__()

        GAP = 20  # <-- one gap to rule them all

        self.threadpool = QThreadPool()

        # Main layout
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(30, 20, 30, 20)
        self.layout.setSpacing(GAP)
        self.layout.setAlignment(Qt.AlignTop)

        # Cards container
        self.cards_layout = QHBoxLayout()
        self.cards_layout.setSpacing(GAP)  
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setAlignment(Qt.AlignCenter)
        self.layout.addLayout(self.cards_layout)

        self.setup_filters_once = False
        self.add_filters(GAP)

        # Charts grid
        self.chart_area = QGridLayout()
        self.chart_area.setContentsMargins(0, 0, 0, 0)
        self.chart_area.setHorizontalSpacing(GAP)
        self.chart_area.setVerticalSpacing(GAP)
        self.chart_area.setColumnStretch(0, 1)
        self.chart_area.setColumnStretch(1, 1)
        self.chart_area.setRowStretch(0, 1)

        # self.layout.addSpacing(25) 

        self.note_label = QLabel("ℹ️ Please select a filter type (Model-wise or Date-wise) and click 'Generate Report Icon' to view the dashboard Graphs.")
        self.note_label.setAlignment(Qt.AlignCenter)
        self.note_label.setStyleSheet("""
            color: #444;
            background-color: #f0f8ff;
            border: 1px solid #b0c4de;
            padding: 10px;
            border-radius: 8px;
            font-size: 10pt;
            font-style: italic;
        """)
        self.note_label.setVisible(True)
        self.layout.addWidget(self.note_label)
        self.layout.addLayout(self.chart_area)
        self.setLayout(self.layout)

        # Initial load
        self.refresh_dashboard()
        # Auto refresh every 60 seconds
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_dashboard)
        self.timer.start(60000)

    def create_labeled_widget(self, label_text, widget, label_style):
        container = QVBoxLayout()
        container.setSpacing(0)
        container.setContentsMargins(0, 0, 0, 0)

        label = QLabel(label_text)
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label.setFont(QFont("Segoe UI", 11, QFont.DemiBold))
        label.setStyleSheet(label_style)
        label.setContentsMargins(0, 0, 0, 0)
        label.setStyleSheet(label_style + " margin-bottom: -4px;")  # reduce spacing manually

        container.addWidget(label)
        container.addWidget(widget)

        frame = QFrame()
        frame.setLayout(container)
        frame.setContentsMargins(0, 0, 0, 0)
        return frame

    def add_filters(self, GAP=16):
        if getattr(self, "setup_filters_once", False):
            return  # Prevent adding filters multiple times
        self.setup_filters_once = True

        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")

        generate_icon_path = os.path.join(base_path, "resources", "generate graph.png")

        # Container layout for filter section
        self.filter_container_layout = QVBoxLayout()
        self.filter_container_layout.setSpacing(10)
        self.filter_container_layout.setContentsMargins(20, 20, 20, 20)

        # === Label Row ===
        grid = QGridLayout()
        grid.setSpacing(20)
        grid.setAlignment(Qt.AlignCenter)

        label_style = """
        QLabel {
            color: #2c3e50;
            border: none;
            font-weight: 600;
            background-color: transparent;
            padding-bottom: 0px;
            margin-bottom: -4px; /* ✨ KEY CHANGE */
        }
        """

        common_style = """
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
                image: url("resources/down-arrow.png");
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

        # Selection Dropdown
        self.selection_dropdown = QComboBox()
        self.selection_dropdown.addItems(["Select", "Date-wise", "Model-wise"])
        self.selection_dropdown.setStyleSheet(common_style)
        self.selection_dropdown.setFixedSize(180, 36)
        self.selection_dropdown.currentIndexChanged.connect(self.on_filter_change)

        # Model Input
        self.model_input = QComboBox()
        self.model_input.setEnabled(False)
        self.model_input.setStyleSheet(common_style)
        self.model_input.setFixedSize(180, 36)

        # From Date
        self.from_date = QDateEdit()
        self.from_date.setCalendarPopup(True)
        self.from_date.setDate(QDate.currentDate())
        self.from_date.setFixedHeight(34)
        self.from_date.setEnabled(False)
        self.from_date.setStyleSheet(calendar_input_style)
        self.from_date.setStyleSheet(self.from_date.styleSheet() + """
            QDateEdit {
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: white;
                padding: 2px 4px;
                font-size: 9pt;
            }
        """)
        self.from_date.setFixedSize(180, 36)

        # To Date
        self.to_date = QDateEdit()
        self.to_date.setCalendarPopup(True)
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setEnabled(False)
        self.to_date.setFixedHeight(34)
        self.to_date.setStyleSheet(calendar_input_style)
        self.to_date.setStyleSheet(self.to_date.styleSheet() + """
            QDateEdit {
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: white;
                padding: 2px 4px;
                font-size: 9pt;
            }
        """)
        self.to_date.setFixedSize(180, 36)


        # Generate Button
        self.generate_btn = QPushButton()
        self.generate_btn.setToolTip("Generate graph")
        self.generate_btn.setEnabled(False)
        if os.path.exists(generate_icon_path):
            self.generate_btn.setIcon(QIcon(generate_icon_path))
            self.generate_btn.setIconSize(QSize(38 , 40))
        self.generate_btn.clicked.connect(self.load_graph_data)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                font-weight: bold;
                padding: 6px 10px;
                border-radius: 10px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #125ea2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #888888;
            }
        """)
        self.generate_btn.setFixedSize(50, 55)

        # Create compact labeled widgets
        grid.addWidget(self.create_labeled_widget("Selection", self.selection_dropdown, label_style), 0, 0)
        grid.addWidget(self.create_labeled_widget("Model", self.model_input, label_style), 0, 1)
        grid.addWidget(self.create_labeled_widget("From", self.from_date, label_style), 0, 2)
        grid.addWidget(self.create_labeled_widget("To", self.to_date, label_style), 0, 3)

        # Generate button in aligned cell
        btn_wrapper = QVBoxLayout()
        btn_wrapper.setContentsMargins(0, 8, 0, 0)
        btn_wrapper.setAlignment(Qt.AlignBottom)
        btn_wrapper.addWidget(self.generate_btn)

        btn_frame = QFrame()
        btn_frame.setLayout(btn_wrapper)
        grid.addWidget(btn_frame, 0, 4)

        # Add grid to the container layout
        self.filter_container_layout.addLayout(grid)


        # White frame wrapper
        white_frame = QFrame()
        white_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: none;
            }
        """)
        white_frame.setLayout(self.filter_container_layout)

        # Add to main layout
        self.layout.insertWidget(1, white_frame)

    def handle_chart_data(self, mode, data):
        self.clear_charts()

        bar_data = data["bar_data"]
        ok_total = data["ok_total"]
        nok_total = data["nok_total"]

        # If no chart data, show the note and return
        if not bar_data:
            self.note_label.setVisible(True)
            return
        else:
            self.note_label.setVisible(False)

        parts = [row[0] for row in bar_data]
        ok_vals = [row[1] for row in bar_data]
        nok_vals = [row[2] for row in bar_data]

        # ✅ Chart 1: Bar Chart – OK and NOK Count per Part
        fig_bar = go.Figure(data=[
            go.Bar(name="OK", x=parts, y=ok_vals, marker_color="#3fb984"),
            go.Bar(name="NOK", x=parts, y=nok_vals, marker_color="#e45755")
        ])
        fig_bar.update_layout(
            title=dict(
                text="<b>OK and NOK Count Per Part</b>",
                font=dict(size=18, family="Segoe UI"),
                x=0.5
            ),
            xaxis=dict(
                title="Child Part Name",
                titlefont=dict(size=14),
                tickfont=dict(size=12)
            ),
            yaxis=dict(
                title="Occurrences (Nos)",
                titlefont=dict(size=14),
                tickfont=dict(size=12)
            ),
            barmode="group",
            template="plotly_white",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.3,
                xanchor="center",
                x=0.5,
                font=dict(size=12)
            ),
            margin=dict(t=70, b=80, l=60, r=60)
        )
        chart_view1 = self.render_plotly_chart(fig_bar)

        # ✅ Chart 2: Pie Chart – OK vs NOK
        labels = ["OK", "NOK"]
        values = [ok_total, nok_total]
        label_color_map = {
            "OK": "#6fcf97",     # Green
            "NOK": "#eb5757"     # Red
        }
        colors = [label_color_map[label] for label in labels]

        fig_pie = go.Figure(data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.3,
                marker=dict(colors=colors),
                textinfo='label+percent',
                insidetextorientation='radial',
                textfont=dict(size=18),
                pull=[0, 0.05],
                sort=False
            )
        ])
        fig_pie.update_layout(
            title=dict(
                text="<b>OK vs NOK Ratio</b>",
                font=dict(size=18, family="Segoe UI"),
                x=0.5
            ),
            template="plotly_white",
            showlegend=True,
            legend=dict(
                traceorder="normal",
                font=dict(size=12),
                orientation="v",
                yanchor="middle",
                y=0.5,
                x=1.05
            ),
            margin=dict(t=70, b=60, l=60, r=60)
        )
        chart_view2 = self.render_plotly_chart(fig_pie)

        # ✅ Add charts to layout
        self.chart_area.addWidget(chart_view1, 0, 0)
        self.chart_area.addWidget(chart_view2, 0, 1)

    def on_filter_change(self):
        selected = self.selection_dropdown.currentText()
        self.model_input.setEnabled(False)
        self.from_date.setEnabled(False)
        self.to_date.setEnabled(False)

        if selected == "Model-wise":
            self.model_input.setEnabled(True)
            self.load_model_dropdown()
        elif selected == "Date-wise":
            self.from_date.setEnabled(True)
            self.to_date.setEnabled(True)

        self.generate_btn.setEnabled(True)

    def load_model_dropdown(self):
        try:
            conn = pymysql.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT parent_part_name FROM parent_part ORDER BY parent_part_name ASC")
            parts = cursor.fetchall()
            self.model_input.clear()
            for p in parts:
                self.model_input.addItem(p[0])
        except Exception as e:
            QMessageBox.critical(self, "Model load error:", f"An error occurred:\n{str(e)}")
            # print(f"Model load error: {e}")
        finally:
            conn.close()

        

    def clear_charts(self):
        while self.chart_area.count():
            item = self.chart_area.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
        self.note_label.setVisible(True)

    # ✅ Insert here
    def render_plotly_chart(self, fig):
        chart_frame = QFrame()
        chart_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dcdcdc;
                border-radius: 14px;
                padding: 10px;
            }
        """)

        chart_layout = QVBoxLayout()
        chart_layout.setContentsMargins(10, 10, 10, 10)
        chart_layout.setSpacing(0)

        view = QWebEngineView()
        html = fig.to_html(include_plotlyjs='cdn')
        view.setHtml(html)
        view.setMinimumSize(500, 600)
        view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        chart_layout.addWidget(view)
        chart_frame.setLayout(chart_layout)

        return chart_frame
        
    def load_graph_data(self):
        self.clear_charts()
        self.note_label.setVisible(False)

        selected = self.selection_dropdown.currentText()

        if selected == "Model-wise":
            model = self.model_input.currentText()
            worker = ChartWorker("model", model, db_config=db_config)

        elif selected == "Date-wise":
            from_date = self.from_date.date().toString("yyyy-MM-dd")
            to_date = self.to_date.date().toString("yyyy-MM-dd")
            worker = ChartWorker("date", from_date, to_date, db_config=db_config)

        else:
            QMessageBox.warning(self, "Invalid Selection", "Please select a valid filter type.")
            return

        worker.signals.finished.connect(self.handle_chart_data)
        self.threadpool.start(worker)

    
    def load_modelwise_charts(self, model):
        self.note_label.setVisible(False)
        try:
            conn = pymysql.connect(**db_config)
            cursor = conn.cursor()

           # --- Chart 1: Bar Chart – OK and NOK Count for Selected Model Across Child Parts ---
            cursor.execute("""
                SELECT part_name, SUM(ok), SUM(nok)
                FROM ok_nok
                WHERE part_name = %s
                GROUP BY part_name
            """, (model,))
            data = cursor.fetchall()

            if not data:
                raise Exception("No data found for selected model.")

            parts = [row[0] for row in data]
            ok_vals = [row[1] for row in data]
            nok_vals = [row[2] for row in data]

            fig_bar = go.Figure(data=[
                go.Bar(name="OK", x=parts, y=ok_vals, marker_color="#3fb984"),   # Green
                go.Bar(name="NOK", x=parts, y=nok_vals, marker_color="#e45755")  # Red
            ])

            fig_bar.update_layout(
            title=dict(
                text="<b>OK and NOK Count Per Part</b>",
                font=dict(size=18, family="Segoe UI"),
                x=0.5
            ),
            xaxis=dict(
                title="Child Part Name",
                titlefont=dict(size=14),
                tickfont=dict(size=12),
                automargin=True    # ✅ Add this line if needed
            ),
            yaxis=dict(
                title="Occurrences (Nos)",   # ✅ Your intended title
                titlefont=dict(size=14),
                tickfont=dict(size=12),
                automargin=True              # ✅ This is the key to ensure title is not clipped
            ),
            barmode="group",
            template="plotly_white",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.3,
                xanchor="center",
                x=0.5,
                font=dict(size=12)
            ),
            margin=dict(t=70, b=80, l=80, r=60)  # ⬅️ Add more left margin if needed
        )


            chart_view1 = self.render_plotly_chart(fig_bar)

            # --- Chart 2: Pie Chart – OK vs NOK ---
            cursor.execute("""
                SELECT SUM(ok), SUM(nok)
                FROM ok_nok
                WHERE part_name = %s
            """, (model,))
            ok_total, nok_total = cursor.fetchone()
            ok_total = ok_total or 0
            nok_total = nok_total or 0

            labels = ["OK", "NOK"]
            values = [ok_total, nok_total]

            # Explicit color mapping
            label_color_map = {
                "OK": "#6fcf97",     # Green for OK
                "NOK": "#eb5757"     # Red for NOK
            }
            colors = [label_color_map[label] for label in labels]

            # Build pie chart
            fig_pie = go.Figure(data=[
                go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.3,
                    marker=dict(colors=colors),
                    textinfo='label+percent',
                    insidetextorientation='radial',
                    textfont=dict(size=18),         # 👈 Larger font inside pie
                    pull=[0, 0.05] ,
                    sort=False                  # Optional: separate NOK slightly
                )
            ])

            fig_pie.update_layout(
                title=dict(
                text="<b>OK vs NOK Ratio</b>",
                font=dict(size=18, family="Segoe UI"),
                x=0.5  # Center title
            ),
            template="plotly_white",
            showlegend=True,
            legend=dict(
                traceorder="normal",  # 👈 Force legend order to match labels
                font=dict(size=12),
                orientation="v",
                yanchor="middle",
                y=0.5,
                x=1.05
        )
    )

            # Render using your existing function
            chart_view2 = self.render_plotly_chart(fig_pie)
            self.chart_area.addWidget(chart_view1, 0, 0)  
            self.chart_area.addWidget(chart_view2, 0, 1)

        except Exception as e:
            QMessageBox.critical(self, "Model-wise Chart Error", f"An error occurred:\n{str(e)}")
        finally:
            conn.close()

    def load_datewise_charts(self, from_date, to_date):
        self.note_label.setVisible(False)
        try:
            conn = pymysql.connect(**db_config)
            cursor = conn.cursor()

            # --- Chart 1: Bar Chart – OK and NOK per Part ---
            cursor.execute("""
                SELECT part_name, SUM(ok), SUM(nok)
                FROM ok_nok
                WHERE IN_DATE BETWEEN %s AND %s
                GROUP BY part_name
            """, (from_date, to_date))
            data = cursor.fetchall()

            part_names = [row[0] for row in data]
            ok_values = [row[1] for row in data]
            nok_values = [row[2] for row in data]

            fig_bar = go.Figure(data=[
                go.Bar(name="OK", x=part_names, y=ok_values, marker_color="#3fb984"),
                go.Bar(name="NOK", x=part_names, y=nok_values, marker_color="#e45755")
            ])
            fig_bar.update_layout(
                title=dict(
                text="<b>OK and NOK Count Per Part</b>",
                font=dict(size=18, family="Segoe UI"),
                x=0.5  # Center the title
            ),
            xaxis_title="Child Part Name",
            yaxis_title="Count",
            barmode='group',
            template="plotly_white"
        )

            chart_view1 = self.render_plotly_chart(fig_bar)

           # --- Chart 2: Pie Chart – OK vs NOK (Overall) ---
            cursor.execute("""
            SELECT SUM(ok), SUM(nok)
            FROM ok_nok
            WHERE IN_DATE BETWEEN %s AND %s
            """, (from_date, to_date))
            ok_total, nok_total = cursor.fetchone()
            ok_total = ok_total or 0
            nok_total = nok_total or 0

            labels = ["OK", "NOK"]
            values = [ok_total, nok_total]

            label_color_map = {
                "OK": "#6fcf97",   # Green for OK
                "NOK": "#eb5757"   # Red for NOK
            }
            colors = [label_color_map[label] for label in labels]

            fig_pie = go.Figure(data=[
                go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.3,
                    marker=dict(colors=colors),
                    textinfo='label+percent',
                    insidetextorientation='radial',
                    textfont=dict(size=18),
                    pull=[0, 0.05],
                    sort=False
                )
            ])

            fig_pie.update_layout(
                title=dict(
                    text="<b>Overall OK vs NOK Ratio</b>",
                    font=dict(size=18, family="Segoe UI"),
                    x=0.5
                ),
                template="plotly_white",
                showlegend=True,
                legend=dict(
                    traceorder="normal",
                    font=dict(size=12),
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    x=1.05
                )
            )

            chart_view2 = self.render_plotly_chart(fig_pie)

            # Add to layout
            self.chart_area.addWidget(chart_view1, 0, 0)
            self.chart_area.addWidget(chart_view2, 0, 1)

        except Exception as e:
            QMessageBox.critical(self, "Date-wise Chart Error", f"Could not load date-wise chart:\n{str(e)}")
        finally:
            conn.close()

    def refresh_dashboard(self):
        ok, nok, ok_percentage, reason = self.fetch_dashboard_data()
        self.update_cards([
            ("Total OK", str(ok), "#d6f5e3", "#1b5e20"),
            ("Total NOK", str(nok), "#fbd4d4", "#b71c1c"),
            ("OK Percentage", ok_percentage, "#fff4cc", "#795548"),
            ("Top Defect Reason", reason, "#dceefb", "#1a237e")
        ])

    def fetch_dashboard_data(self):
        try:
            conn = pymysql.connect(**db_config)
            cursor = conn.cursor()

            # Get OK and NOK counts
            cursor.execute("SELECT SUM(ok), SUM(nok) FROM ok_nok")
            ok, nok = cursor.fetchone()
            ok = ok or 0
            nok = nok or 0
            total = ok + nok

            if total > 0:
                percent = round((ok / total) * 100, 2)
                ok_percentage = f"{percent}%"
            else:
                ok_percentage = "0.00%"

            # Get top defect reason
            cursor.execute("""
                SELECT reason, COUNT(*) as cnt
                FROM ok_nok
                WHERE reason IS NOT NULL AND reason != ''
                GROUP BY reason
                ORDER BY cnt DESC
                LIMIT 1
            """)
            result = cursor.fetchone()
            if result:
                # Remove leading digits and dot (e.g., '6. Foam Absent' -> 'Foam Absent')
                top_reason = re.sub(r'^\d+\.\s*', '', result[0])
            else:
                top_reason = "N/A"

            return ok, nok, ok_percentage, top_reason

        except Exception as e:
            QMessageBox.critical(self, "Dashboard DB Error:", f"An error occurred:\n{str(e)}")
            # print(f"Dashboard DB Error: {e}")
            return 0, 0, "0.00%", "N/A"
        finally:
            if conn:
                conn.close()

    def update_cards(self, card_data):
        # Clear existing widgets
        for i in reversed(range(self.cards_layout.count())):
            widget = self.cards_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # Add new cards
        for title, value, bg_color, text_color in card_data:
            card = self.createCard(title, value, bg_color, text_color)
            self.cards_layout.addWidget(card)

    def createCard(self, title, value, bg_color, text_color):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: 14px;
                border: none;
            }}
        """)

        card.setFixedSize(230, 90)
        card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Segoe UI", 10))
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet(f"color: {text_color};")

        value_lbl = QLabel(value)
        value_lbl.setFont(QFont("Segoe UI", 16, QFont.Bold))
        value_lbl.setAlignment(Qt.AlignCenter)
        value_lbl.setStyleSheet(f"color: {text_color}; letter-spacing: 0.5px;")

        layout.addWidget(title_lbl)
        layout.addWidget(value_lbl)
        card.setLayout(layout)

        return card

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = DashboardScreen()
    window.setWindowTitle("Mayur Industries Dashboard")
    window.resize(1280, 800)
    window.show()

    sys.exit(app.exec_())