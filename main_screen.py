# #main_screen.py
# import sys
# import os
# import qtawesome as qta
# from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QHBoxLayout, QPushButton,
#                              QSizePolicy, QToolButton,QStackedWidget, QVBoxLayout, QSpacerItem , QGraphicsDropShadowEffect )
# from PyQt5.QtGui import QPixmap ,QFont ,QIcon ,QColor 
# from PyQt5.QtCore import Qt, QFile , QPropertyAnimation , QSize ,QTimer
# from datetime import datetime

# from Admin_screen import AddminScreen  # Import Admin Screen
# from PPC_screen import PPCScreen       # Import PPC Screen
# from QA_screen import QAScreen         # Import QA Screen
# from report_genration_screen import Reportscreen  # ✅ Import Report Generation Screen
# from dashboard_screen import DashboardScreen

# class ParameterWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()

#         if getattr(sys, 'frozen', False):
#             self.base_path = sys._MEIPASS
#         else:
#             self.base_path = os.path.abspath(".")

#         self.setWindowTitle('Main Screen')
#         self.resize(QApplication.primaryScreen().availableGeometry().width(),
#                 QApplication.primaryScreen().availableGeometry().height())
#         self.setWindowState(Qt.WindowMaximized)

#         self.setFont(QFont("Segoe UI", 12))

#         self.setStyleSheet("""
#             QMainWindow {
#                 background-color: lightgray;
#             }
#         """)
#         main_layout = QHBoxLayout()
#         main_layout.setContentsMargins(0, 0, 0, 0)
#         main_layout.setSpacing(0)

#         self.sidebar_widget = QWidget()
#         initial_sidebar_width = 200  # same as full_width logic
#         self.sidebar_widget.setFixedWidth(initial_sidebar_width) # Full width when expanded
#         self.sidebar_widget.setStyleSheet("""
#     background-color: #0b2748;
#     color: white;
#     border-top-left-radius: 12px;
#     border-bottom-left-radius: 12px;
# """)

#         self.sidebar_layout = QVBoxLayout()
#         self.sidebar_layout.setAlignment(Qt.AlignTop)
#         self.sidebar_layout.setContentsMargins(10, 10, 10, 10)
#         self.sidebar_layout.setSpacing(20)
#         self.sidebar_expanded = True

#         # Add toggle button at the top
#         self.toggle_button = QPushButton(qta.icon("fa.bars"), "")
#         self.toggle_button.setFixedSize(36, 36)
#         self.toggle_button.setStyleSheet("""
#             QPushButton {
#                 background-color: #1a3b5d;
#                 color: white;
#                 border-radius: 8px;
#                 padding: 5px;
#     }
#             QPushButton:hover {
#                 background-color: #25557b;
#     }
# """)
#         self.toggle_button.clicked.connect(self.toggleSidebar)
#         self.sidebar_layout.addWidget(self.toggle_button, alignment=Qt.AlignLeft)

# # Augle AI logo
#         logo_label = QLabel()
#         logo_path = os.path.join(self.base_path, "resources", "Augle_Icon_Logo.png")
#         if QFile.exists(logo_path):
#             logo_pixmap = QPixmap(logo_path).scaled(140, 140, Qt.KeepAspectRatio, Qt.SmoothTransformation)
#             logo_label.setPixmap(logo_pixmap)
#             logo_label.setAlignment(Qt.AlignCenter)
#         else:
#             logo_label.setText("Logo")

#         self.sidebar_layout.addWidget(logo_label)

#         self.sidebar_widget.setLayout(self.sidebar_layout)

#         # Create stacked widget
#         self.stacked_widget = QStackedWidget()
#         self.stacked_widget.setStyleSheet("background-color: #f6f9fc;")

# # Create pages
#         self.empty_screen = self.createHomeScreen()
#         self.admin_screen = AddminScreen()
#         self.ppc_screen = PPCScreen()
#         self.qa_screen = QAScreen()
#         self.report_screen = Reportscreen()
#         self.dashboard_screen = DashboardScreen()

# # Add to stacked widget
#         self.stacked_widget.addWidget(self.empty_screen)
#         self.stacked_widget.addWidget(self.admin_screen)
#         self.stacked_widget.addWidget(self.ppc_screen)
#         self.stacked_widget.addWidget(self.qa_screen)
#         self.stacked_widget.addWidget(self.report_screen)
#         self.stacked_widget.addWidget(self.dashboard_screen)

#         self.createNavbar()

#         self.screen_title_label = QLabel("Home Screen")  # Default
#         self.screen_title_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
#         self.screen_title_label.setStyleSheet("color: #333;")

#         # Set default screen to Home
#         self.stacked_widget.setCurrentWidget(self.empty_screen)
#         self.screen_title_label.setText("Home")
#         self.nav_buttons["Home"].setChecked(True)

# # Date Label
#         self.date_label = QLabel()
#         self.date_label.setStyleSheet("""
#             background-color: #e8f0fe;
#             padding: 6px 12px;
#             border-radius: 15px;
#             font-weight: bold;
#             color: #333;
#         """)

#         timer = QTimer(self)
#         timer.timeout.connect(self.updateDateTime)
#         timer.start(1000)
#         self.updateDateTime()


#         top_bar_layout = QHBoxLayout()
#         top_bar_layout.addWidget(self.screen_title_label)
#         top_bar_layout.addStretch()
#         top_bar_layout.addWidget(self.date_label)
#         top_bar = QWidget()
#         top_bar.setLayout(top_bar_layout)
#         top_bar.setFixedHeight(80)  # Match toggle + logo height
#         top_bar.setStyleSheet("background-color: white; padding: 0 20px;")

#         # Content layout (top bar + screens stacked)
#         content_layout = QVBoxLayout()
#         content_layout.addWidget(top_bar)
#         content_layout.addWidget(self.stacked_widget)

#         content_widget = QWidget()
#         content_widget.setLayout(content_layout)
#         content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

#         self.sidebar_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
#         self.stacked_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

# # Final layout structure
#         main_layout.addWidget(self.sidebar_widget)
#         main_layout.addWidget(content_widget)

#         central_widget = QWidget()
#         central_widget.setLayout(main_layout)
#         central_widget.setStyleSheet("""
#             background-color: #f6f9fc;
#             border-radius: 12px;
#         """)
#         self.setCentralWidget(central_widget)

#     def updateDateTime(self):
#         self.date_label.setText(datetime.now().strftime("%B %d  %H:%M:%S"))

#     def createNavbar(self):
#         button_names = ["Home", "Dashboard", "Admin Screen", "PPC Screen", "QA Screen", "Report Generation"]

#         icon_map = {
#             "Home": qta.icon("fa.home", color="white"),
#             "Dashboard": qta.icon("fa.line-chart", color="white"),  # ✅ Supported
#             "Admin Screen": qta.icon("fa.user", color="white"),     # ✅ safe fallback
#             "PPC Screen": qta.icon("fa.industry", color="white"),       # ✅ alternative for industry
#             "QA Screen": qta.icon("fa.check-circle", color="white"),       # ✅ basic check icon
#             "Report Generation": qta.icon("fa.file-text-o", color="white") # ✅ supported
#         }

#         self.nav_buttons = {}

#         for name in button_names:
#             button = QToolButton()
#             button.setText(name)
#             button.setIcon(icon_map.get(name))
#             button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
#             button.setCheckable(True)  # Allow toggle appearance
#             button.setIconSize(QSize(24, 24))
#             button.setStyleSheet(self.getSidebarButtonStyle())
#             button.clicked.connect(self.onButtonClick)
#             self.sidebar_layout.addWidget(button)
#             self.nav_buttons[name] = button

#         return self.sidebar_layout

#     def createHomeScreen(self):
#         home_widget = QWidget()
#         layout = QHBoxLayout()

#     # Left section (text)
#         text_section = QVBoxLayout()
#         welcome_label = QLabel("Welcome to the\nHome Screen")
#         welcome_label.setFont(QFont("Segoe UI", 28, QFont.Bold))
#         welcome_label.setStyleSheet("color: #1a1a1a;")

#         about_label = QLabel("""
#     <b style="font-size: 16px;">➤ About the Software</b><br><br>
#     <span style="font-size: 13px;">
#     This application helps monitor <b>QA, Admin</b>, and <b>Production</b> data for your manufacturing workflow.<br>
#     Navigate using the left menu to access dashboards, generate reports, or configure system parameters.
#     </span>
#         """)
#         about_label.setWordWrap(True)
#         about_label.setStyleSheet("""
#     font-size: 13px;
#     color: #1a1a1a;
#     background-color: #eef7ff;
#     border: 1px solid #4599e6;
#     border-radius: 12px;
#     padding: 20px;
#     max-width: 400px;
#     min-height: 150px;
# """)
#         about_label.setWordWrap(True)

#         text_section.addWidget(welcome_label)
#         text_section.addSpacing(10)
#         text_section.addWidget(about_label)
#         text_section.addStretch()

#     # Right section (image)
#         self.image_section = QLabel()
#         self.image_section.setFixedSize(440, 440) 
#         image_path = os.path.join(self.base_path, "resources", "industrial_welcome.png")
#         if QFile.exists(image_path):
#             image_pixmap = QPixmap(image_path).scaled(
#                 int(0.9 * self.width()), 
#                 int(0.9 * self.height()), 
#                 Qt.KeepAspectRatio, 
#                 Qt.SmoothTransformation
#             )
#             self.image_section.setPixmap(image_pixmap)
#             self.image_section.setStyleSheet("""
#                 background-color: white;
#                 border-radius: 12px;
#                 padding: 10px;
#             """)


#         layout.addLayout(text_section, 2)
#         layout.addWidget(self.image_section, 1)

#         home_widget.setLayout(layout)
#         return home_widget

    
#     def toggleSidebar(self):
#         self.sidebar_expanded = not self.sidebar_expanded
#         for btn in self.nav_buttons.values():
#             btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon if self.sidebar_expanded else Qt.ToolButtonIconOnly)
#         full_width = int(0.12 * self.width())  # ~12% width
#         collapsed_width = int(0.05 * self.width())  # ~5%
#         self.sidebar_widget.setFixedWidth(full_width if self.sidebar_expanded else collapsed_width)

        
#     def getButtonStyle(self, inactive=False):
#         if inactive:
#             return """
#             QToolButton {
#             background-color: #f0f4fa;
#             border-radius: 16px;
#             color: #333;
#             font-family: 'Segoe UI';
#             font-size: 13px;
#             font-weight: 500;
#             padding: 10px;
#             border: none;
#         }
#         QToolButton:hover {
#             background-color: #e6effc;
#         }
#         QToolButton:pressed {
#             background-color: #d2e1f7;
#         }
#         """
#         else:
#             return """
#             QToolButton {
#             background-color: #4599e6;
#             color: white;
#             font-family: 'Segoe UI';
#             font-size: 13px;
#             font-weight: 600;
#             padding: 10px;
#             border-radius: 16px;
#             border: none;
#         }
#         QToolButton:hover {
#             background-color: #378ad4;
#         }
#         QToolButton:pressed {
#             background-color: #2f76bb;
#         }
#         """

#     def getSidebarButtonStyle(self):
#         return """
#             QToolButton {
#                 background-color: transparent;
#                 color: white;
#                 font-size: 13px;
#                 padding: 6px 14px;
#                 border-radius: 10px;
#                 text-align: left;
#             }
#             QToolButton:hover {
#                 background-color: #1a3b5d;
#             }
#             QToolButton:checked {
#                 background-color: #25557b;
#             }
#         """

#     def applyShadow(self, widget):
#         shadow = QGraphicsDropShadowEffect()
#         shadow.setBlurRadius(8)
#         shadow.setXOffset(0)
#         shadow.setYOffset(2)
#         shadow.setColor(QColor(0, 0, 0, 50))
#         widget.setGraphicsEffect(shadow)


#     def onButtonClick(self):
#         button = self.sender()
#         button_text = button.text()

#         self.screen_title_label.setText(button_text)

#         # Update active button style
#         for name, btn in self.nav_buttons.items():
#             btn.setChecked(name == button_text)


#         # Change stacked widget
#         if button_text == "Admin Screen":
#             self.transitionToScreen(self.admin_screen)
#         elif button_text == "PPC Screen":
#             self.transitionToScreen(self.ppc_screen)
#         elif button_text == "QA Screen":
#             self.transitionToScreen(self.qa_screen)
#         elif button_text == "Report Generation":
#             self.transitionToScreen(self.report_screen)
#         elif button_text == "Dashboard":
#             self.transitionToScreen(self.dashboard_screen)
#         else:
#             self.transitionToScreen(self.empty_screen)

#         # print(f'{button_text} was clicked!')

#     def transitionToScreen(self, new_widget):
#         old_widget = self.stacked_widget.currentWidget()
#         if old_widget == new_widget:
#             return  # Skip if the user clicks the same button

#         self.stacked_widget.setCurrentWidget(new_widget)

#         # Optional: Simple fade animation on the new widget (can be extended for slide)
#         animation = QPropertyAnimation(new_widget, b"windowOpacity")
#         new_widget.setWindowOpacity(0.0)
#         animation.setDuration(300)
#         animation.setStartValue(0.0)
#         animation.setEndValue(1.0)
#         animation.start()

#     def resizeEvent(self, event):
#         super().resizeEvent(event)
#         # Example: Dynamically scale the welcome image
#         if hasattr(self, 'image_section') and isinstance(self.image_section, QLabel) and self.image_section.pixmap():
#             scaled_pixmap = self.image_section.pixmap().scaled(
#                 int(0.3 * self.width()), int(0.3 * self.height()),
#                 Qt.KeepAspectRatio, Qt.SmoothTransformation
#             )
#             self.image_section.setPixmap(scaled_pixmap)


# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     app.setFont(QFont("Segoe UI", 11))
#     window = ParameterWindow()
#     window.show()
#     sys.exit(app.exec_())



# main_screen.py
import sys
import os
import qtawesome as qta
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QHBoxLayout, QPushButton,
                             QSizePolicy,QScrollArea, QToolButton, QStackedWidget, QVBoxLayout, QGraphicsDropShadowEffect, QGridLayout)
from PyQt5.QtGui import QPixmap, QFont, QColor ,QIcon ,QTransform
from PyQt5.QtCore import Qt, QFile, QPropertyAnimation, QSize, QTimer
from datetime import datetime

from Admin_screen import AddminScreen
from PPC_screen import PPCScreen
from QA_screen import QAScreen
from report_genration_screen import Reportscreen
from dashboard_screen import DashboardScreen

class HoverCard(QWidget):
    def __init__(self, image_path, bg_color, description_points, parent=None):
        super().__init__(parent)
        self.bg_color = bg_color
        self.setFixedSize(380, 380)
        self.setStyleSheet(self.getStyle())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Image
        img_label = QLabel()
        if QFile.exists(image_path):
            pixmap = QPixmap(image_path).scaled(190, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            img_label.setPixmap(pixmap)
        else:
            img_label.setText("Image not found")
        img_label.setAlignment(Qt.AlignCenter)

        # Bullet points
        bullet_html = "<ul style='font-size: 15px; color: #333333; padding-left: 14px; margin: 0;'>"
        for point in description_points:
            bullet_html += f"<li>{point}</li>"
        bullet_html += "</ul>"

        bullets = QLabel(bullet_html)
        bullets.setWordWrap(True)

        layout.addWidget(img_label)
        layout.addWidget(bullets)

    def enterEvent(self, event):
        self.setFixedSize(430, 400)
        self.setGraphicsEffect(self.getShadowEffect())
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setFixedSize(420, 390)
        self.setGraphicsEffect(None)
        super().leaveEvent(event)

    def getStyle(self):
        return f"""
            QWidget {{
                background-color: {self.bg_color};
                border-radius: 14px;
            }}
        """

    def getShadowEffect(self):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 60))
        return shadow



class ParameterWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        if getattr(sys, 'frozen', False):
            self.base_path = sys._MEIPASS
        else:
            self.base_path = os.path.abspath(".")

        self.setWindowTitle('Main Screen')
        self.resize(QApplication.primaryScreen().availableGeometry().width(),
                    QApplication.primaryScreen().availableGeometry().height())
        self.setWindowState(Qt.WindowMaximized)

        self.setFont(QFont("Segoe UI", 12))
        self.setStyleSheet("QMainWindow { background-color: lightgray; }")

        self.sidebar_widget = QWidget()
        self.sidebar_widget.setFixedWidth(280)
        self.sidebar_widget.setStyleSheet("""
            background-color: #1b3d5c;
            color: white;
            border-top-left-radius: 2px;
            border-bottom-left-radius: 2px;
        """)

        self.sidebar_layout = QVBoxLayout()
        self.sidebar_layout.setAlignment(Qt.AlignTop)
        self.sidebar_layout.setContentsMargins(10, 0, 10, 10)
        self.sidebar_layout.setSpacing(20)
        self.sidebar_expanded = True

        self.toggle_button = QPushButton(qta.icon("fa5s.bars", color="white"), "")
        self.toggle_button.setFixedSize(36, 36)
        self.toggle_button.setStyleSheet("""
            QPushButton {
                background-color: #1a3b5d;
                color: white;
                border-radius: 8px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #25557b;
            }
        """)
        self.toggle_button.clicked.connect(self.toggleSidebar)

        # ⬇️ Wrapper to control horizontal centering
        self.toggle_button_wrapper = QWidget()
        self.toggle_button_wrapper_layout = QHBoxLayout()
        self.toggle_button_wrapper_layout.setContentsMargins(0, 10, 0, 10)  # Add vertical spacing if needed
        self.toggle_button_wrapper_layout.addWidget(self.toggle_button, alignment=Qt.AlignHCenter)  # ⬅️ Always centered
        self.toggle_button_wrapper.setLayout(self.toggle_button_wrapper_layout)

        self.sidebar_layout.addWidget(self.toggle_button_wrapper)

        # -- Logo container (white background for expanded state) --
        self.logo_label = QLabel()
        logo_path = os.path.join(self.base_path, "resources", "augle")
        self.updateSidebarLogo()

        # This container adds the white rounded box
        self.logo_container = QWidget()
        self.logo_container_layout = QVBoxLayout()
        self.logo_container_layout.setContentsMargins(2, 2, 2, 2)
        self.logo_container_layout.setSpacing(0)
        self.logo_container.setLayout(self.logo_container_layout)
        self.logo_container_layout.addWidget(self.logo_label, alignment=Qt.AlignCenter)

        # Default style for expanded state
        self.logo_container.setStyleSheet("background-color: transparent;")

        # self.logo_label.setFixedSize(100, 20)
        logo_wrapper = QWidget()
        logo_wrapper_layout = QHBoxLayout()
        logo_wrapper_layout.setContentsMargins(0, 0, 0, 0)
        logo_wrapper_layout.addWidget(self.logo_container, alignment=Qt.AlignCenter)
        logo_wrapper.setLayout(logo_wrapper_layout)

        self.sidebar_layout.addWidget(logo_wrapper)

        self.sidebar_widget.setLayout(self.sidebar_layout)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("background-color: #f6f9fc;")

        self.empty_screen = self.createHomeScreen()
        self.admin_screen = AddminScreen()
        self.ppc_screen = PPCScreen()
        self.qa_screen = QAScreen()
        self.report_screen = Reportscreen()
        self.dashboard_screen = DashboardScreen()

        self.stacked_widget.addWidget(self.empty_screen)
        self.stacked_widget.addWidget(self.admin_screen)
        self.stacked_widget.addWidget(self.ppc_screen)
        self.stacked_widget.addWidget(self.qa_screen)
        self.stacked_widget.addWidget(self.report_screen)
        self.stacked_widget.addWidget(self.dashboard_screen)

        self.createNavbar()

        self.screen_title_label = QLabel("Home Screen")
        self.screen_title_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
        self.screen_title_label.setStyleSheet("color: white;")

        self.stacked_widget.setCurrentWidget(self.empty_screen)
        self.screen_title_label.setText("Home")
        self.nav_buttons["Home"].setChecked(True)

        self.date_widget = QWidget()

        # Create layout
        date_layout = QHBoxLayout()
        date_layout.setContentsMargins(0, 0, 0, 0)
        date_layout.setSpacing(0)  # Removes all horizontal gap

        # Calendar icon
        self.calendar_icon_label = QLabel()
        pixmap = QPixmap(os.path.join(self.base_path, "resources", "calendar.png")).scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.calendar_icon_label.setPixmap(pixmap)
        self.calendar_icon_label.setFixedSize(20, 20)
        self.calendar_icon_label.setStyleSheet("margin: 0px; padding: 0px;")

        # Date label
        self.date_label = QLabel()
        self.date_label.setStyleSheet("color: white; font-weight: bold; font-size: 16px; margin-left: 2px;")

        # Add widgets
        date_layout.addWidget(self.calendar_icon_label, alignment=Qt.AlignVCenter)
        date_layout.addWidget(self.date_label, alignment=Qt.AlignVCenter)

        # Set layout
        self.date_widget.setLayout(date_layout)

        self.date_widget.setStyleSheet("""
            background-color: transparent;
            font-size: 18px;
    """)

        timer = QTimer(self)
        timer.timeout.connect(self.updateDateTime)
        timer.start(1000)
        self.updateDateTime()

        top_bar_layout = QHBoxLayout()
        top_bar_layout.setContentsMargins(0, 0, 0, 0)
        top_bar_layout.addWidget(self.screen_title_label)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.date_widget)

        top_bar = QWidget()
        top_bar.setLayout(top_bar_layout)
        top_bar.setFixedHeight(70)
        top_bar.setStyleSheet("""
            background-color: #1b3d5c;
            padding: 0 20px;
            color: white;
        """)

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addWidget(top_bar)
        content_layout.addWidget(self.stacked_widget)

        content_widget = QWidget()
        content_widget.setLayout(content_layout)
        content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.sidebar_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.stacked_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.sidebar_widget)
        main_layout.addWidget(content_widget)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        central_widget.setStyleSheet("background-color: #f6f9fc;")
        self.setCentralWidget(central_widget)

    def updateDateTime(self):
        self.date_label.setText(datetime.now().strftime("%B %d  %H:%M:%S"))

    def updateSidebarLogo(self):
        if self.sidebar_expanded:
            logo_file = "augle1.png"  # or .png if you have correct format
            width, height = 180, 48
        else:
            logo_file = "logo.png"
            width, height = 50, 50

        logo_path = os.path.join(self.base_path, "resources", logo_file)

        if QFile.exists(logo_path):
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.logo_label.setPixmap(scaled_pixmap)
                self.logo_label.setAlignment(Qt.AlignCenter)
                self.logo_label.setFixedSize(width, height)  # ✅ Resize the label
            else:
                self.logo_label.setText("Invalid Image")
        else:
            self.logo_label.setText("Logo Missing")


    def createNavbar(self):
        button_names = ["Home", "Dashboard", "Admin Screen", "PPC Screen", "QA Screen", "Report Generation"]
    
        icon_map = {
            "Home": QIcon(os.path.join(self.base_path, "resources", "home screen.png")),
            "Dashboard": QIcon(os.path.join(self.base_path, "resources", "dashboard screen.png")),
            "Admin Screen": QIcon(os.path.join(self.base_path, "resources", "admin screen.png")),
            "PPC Screen": QIcon(os.path.join(self.base_path, "resources", "PPC screen.png")),
            "QA Screen": QIcon(os.path.join(self.base_path, "resources", "QA screen.png")),
            "Report Generation": QIcon(os.path.join(self.base_path, "resources", "report generation screen.png"))
        }

        self.nav_buttons = {}
        for name in button_names:
            button = QToolButton()
            button.setText(f"  {name}") 
            button.setIcon(icon_map.get(name))
            button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            button.setCheckable(True)
            button.setIconSize(QSize(36, 36))
            button.setStyleSheet(self.getSidebarButtonStyle())
            button.setToolTip(name)
            button.clicked.connect(self.onButtonClick)
            self.sidebar_layout.addWidget(button)
            self.nav_buttons[name] = button

    def createHomeScreen(self):
        home_widget = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        scroll_content = QWidget()
        grid_layout = QGridLayout(scroll_content)
        grid_layout.setContentsMargins(10, 10, 10, 10)
        grid_layout.setHorizontalSpacing(10)
        grid_layout.setVerticalSpacing(10)
        grid_layout.setAlignment(Qt.AlignCenter)

        # Arrow paths
        arrow_right = os.path.join(self.base_path, "resources", "11right-arrow.png")
        arrow_left = os.path.join(self.base_path, "resources", "11left-arrow.png")
        arrow_down = os.path.join(self.base_path, "resources", "11down-arrow.png")

        # Top row: Home → Admin → PPC
        grid_layout.addWidget(self.buildCard("1imageHome.png", "#e0f3ff"), 0, 0)
        grid_layout.addWidget(self.buildArrow(arrow_right), 0, 1)
        grid_layout.addWidget(self.buildCard("2Admin screen.png", "#e5f3fc"), 0, 2)
        grid_layout.addWidget(self.buildArrow(arrow_right), 0, 3)
        grid_layout.addWidget(self.buildCard("3imagePPC.png", "#fff6d9"), 0, 4)

        # Down arrow under PPC
        grid_layout.addWidget(self.buildArrow(arrow_down), 1, 4, alignment=Qt.AlignCenter)

        # Bottom row: Dashboard ← Report ← QA
        grid_layout.addWidget(self.buildCard("6imageDashboard.png", "#e0f8e0"), 2, 0)
        grid_layout.addWidget(self.buildArrow(arrow_left), 2, 1, alignment=Qt.AlignCenter)  # ← is image flipped
        grid_layout.addWidget(self.buildCard("5reportgeneration.png", "#fde4e4"), 2, 2)
        grid_layout.addWidget(self.buildArrow(arrow_left), 2, 3, alignment=Qt.AlignCenter)  # ← is image flipped
        grid_layout.addWidget(self.buildCard("4QAscreen.png", "#d9f0f5"), 2, 4)

        scroll_area.setWidget(scroll_content)

        final_layout = QVBoxLayout(home_widget)
        final_layout.addWidget(scroll_area)
        home_widget.setLayout(final_layout)
        return home_widget

    def buildCard(self, image_file, bg_color):
        image_path = os.path.join(self.base_path, "resources", image_file)

        descriptions = {
            "1imageHome.png": [
                "Central navigation hub for the application",
                "Visual overview of system modules",
                "Use this screen to explore system features"
            ],
            "2Admin screen.png": [
                "Enter and manage parent part master data",
                "Capture live images using Baumer GigE camera",
                "Create & label child parts using bounding boxes",
                "Save parent-child part info with image coordinates",
                "Add, Edit, delete, or rotate bounding boxes"
            ],
            "3imagePPC.png": [
                "Create batches linked to part entries",
                "Save and display batch data in table",
                "Edit or delete batch records anytime",
                "Filter data by custom date range"
            ],
            "4QAscreen.png": [
                "Select part and auto-fill batch details",
                "Capture live image using Baumer camera",
                "Run part inspection and view OK/NOK result",
                "Log image and result with time & date"
            ],
            "5reportgeneration.png": [
                "Generate reports model-wise or date-wise",
                "View inspection results with OK/NOK counts",
                "Export reports in PDF and Excel formats",
                "Filter data using part name and date range"
            ],
            "6imageDashboard.png": [
                "Track total OK/NOK and pass percentage",
                "Visualize part-wise inspection results",
                "Generate model-wise or date-wise graphs",
                "Identify top defect reason instantly"
            ]
        }

        return HoverCard(image_path, bg_color, descriptions.get(image_file, []))


    def buildArrow(self, path, rotate=0):
        label = QLabel()
        label.setContentsMargins(0, 0, 0, 0)  # Tight arrow spacing
        if QFile.exists(path):
            pixmap = QPixmap(path).scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            if rotate:
                transform = QTransform().rotate(rotate)
                pixmap = pixmap.transformed(transform, Qt.SmoothTransformation)
            label.setPixmap(pixmap)
        else:
            label.setText("→" if not rotate else "←")
            label.setStyleSheet("font-size: 32px; color: #666;")
        label.setAlignment(Qt.AlignCenter)
        return label

    def toggleSidebar(self):
        self.sidebar_expanded = not self.sidebar_expanded
        expanded_width = 280
        collapsed_width = 100
        self.sidebar_widget.setFixedWidth(expanded_width if self.sidebar_expanded else collapsed_width)

        for btn in self.nav_buttons.values():
            if self.sidebar_expanded:
                btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
                btn.setText(f"  {btn.toolTip()}")
                btn.setIconSize(QSize(36, 36))
                btn.setStyleSheet(self.getSidebarButtonStyle(aligned_center=False))
            else:
                btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
                btn.setText("")
                btn.setIconSize(QSize(40, 40))  # Optional: slightly smaller for compact view
                btn.setStyleSheet(self.getSidebarButtonStyle(aligned_center=True))

        # Adjust logo visuals
        self.logo_container.setStyleSheet("background-color: transparent;")
        self.logo_label.setFixedSize(48, 48)
        self.logo_container_layout.setContentsMargins(4, 4, 4, 4)

        self.updateSidebarLogo()

    def getSidebarButtonStyle(self, aligned_center=False):
        if aligned_center:
            return """
                QToolButton {
                    background-color: transparent;
                    color: white;
                    padding: 12px;
                    border-radius: 10px;
                    font-size: 0px;  /* Hides text completely */
                    qproperty-iconSize: 32px;
                    text-align: center;
                }
                QToolButton:hover {
                    background-color: #2b4c6f;
                }
                QToolButton:checked {
                    background-color: #336a93;
                }
            """
        else:
            return """
                QToolButton {
                    background-color: transparent;
                    color: white;
                    font-size: 18px;
                    padding: 12px 24px;
                    border-radius: 10px;
                    text-align: left;
                    font-family: 'Segoe UI';
                    font-weight: 600;
                }
                QToolButton:hover {
                    background-color: #2b4c6f;
                }
                QToolButton:checked {
                    background-color: #336a93;
                }
            """

    def onButtonClick(self):
        button = self.sender()
        button_text = button.toolTip()
        # button_text = button.text()
        self.screen_title_label.setText(button_text)
        for name, btn in self.nav_buttons.items():
            btn.setChecked(name == button_text)

        screens = {
            "Admin Screen": self.admin_screen,
            "PPC Screen": self.ppc_screen,
            "QA Screen": self.qa_screen,
            "Report Generation": self.report_screen,
            "Dashboard": self.dashboard_screen,
            "Home": self.empty_screen
        }
        self.transitionToScreen(screens.get(button_text, self.empty_screen))

    def transitionToScreen(self, new_widget):
        old_widget = self.stacked_widget.currentWidget()
        if old_widget == new_widget:
            return
        self.stacked_widget.setCurrentWidget(new_widget)
        animation = QPropertyAnimation(new_widget, b"windowOpacity")
        new_widget.setWindowOpacity(0.0)
        animation.setDuration(300)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'image_section') and isinstance(self.image_section, QLabel) and self.image_section.pixmap():
            scaled_pixmap = self.image_section.pixmap().scaled(
                600, 700, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_section.setPixmap(scaled_pixmap)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 14))
    window = ParameterWindow()
    window.show()
    sys.exit(app.exec_())