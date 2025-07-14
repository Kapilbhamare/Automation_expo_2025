#main_screen.py
import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QHBoxLayout, QPushButton,
                             QSizePolicy, QStackedWidget, QVBoxLayout, QSpacerItem)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QFile

from Admin_screen import AddminScreen  # Import Admin Screen
from PPC_screen import PPCScreen       # Import PPC Screen
from QA_screen import QAScreen         # Import QA Screen
from report_genration_screen import Reportscreen  # ✅ Import Report Generation Screen

class ParameterWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Main Screen')
        self.setGeometry(100, 100, 1400, 800)  
        self.setWindowState(Qt.WindowMaximized)

        self.setStyleSheet("""
            QMainWindow {
                background-color: lightgray;
            }
        """)

        navbar_layout = self.createNavbar()

        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(10, 0, 10, 0)

        logo_label = QLabel()
        # Load Logo Icon from resources folder (compatible with PyInstaller EXE & Dev)
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")

        logo_path = os.path.join(base_path, "resources", "Augle_Icon_Logo.png")

        if QFile.exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
            logo_label.setPixmap(logo_pixmap.scaled(250, 200, Qt.KeepAspectRatio))
        else:
            logo_label.setText("Logo not available")


        top_layout.addWidget(logo_label)

        spacer_left = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        top_layout.addItem(spacer_left)

        top_layout.addLayout(navbar_layout)

        spacer_right = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        top_layout.addItem(spacer_right)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("""
            QStackedWidget {
                border: 3px solid blue;
                background-color: white; 
            }
        """)

        self.stacked_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Create different screens
        self.empty_screen = QWidget()              # Default screen
        self.admin_screen = AddminScreen()         # Admin
        self.ppc_screen = PPCScreen()              # PPC
        self.qa_screen = QAScreen()                # QA
        self.report_screen = Reportscreen()        # ✅ Report Generation

        # Add all screens to stacked widget
        self.stacked_widget.addWidget(self.empty_screen)
        self.stacked_widget.addWidget(self.admin_screen)
        self.stacked_widget.addWidget(self.ppc_screen)
        self.stacked_widget.addWidget(self.qa_screen)
        self.stacked_widget.addWidget(self.report_screen)  # ✅

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(12)

        top_widget = QWidget()
        top_widget.setLayout(top_layout)
        top_widget.setFixedHeight(100)
        top_widget.setStyleSheet("background-color: lightgray;")

        main_layout.addWidget(top_widget)
        main_layout.addWidget(self.stacked_widget)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def createNavbar(self):
        self.nav_buttons = {}  # Dictionary to keep track of buttons
        button_names = ["Admin Screen", "PPC Screen", "QA Screen", "Report Generation", "Camera Setting"]

        button_layout = QHBoxLayout()
        button_layout.setSpacing(25)

        for name in button_names:
            button = QPushButton(name)
            button.setFixedSize(190, 45)
            button.setProperty("screen_name", name)  # Optional custom property
            button.setStyleSheet(self.getButtonStyle(inactive=True))  # Set default inactive style
            button.clicked.connect(self.onButtonClick)
            button_layout.addWidget(button)

            self.nav_buttons[name] = button  # Store button

        return button_layout
    
    def getButtonStyle(self, inactive=False):
        if inactive:
            return """
                QPushButton {
                    background-color: blue; 
                    border: none;
                    border-radius: 5px;
                    color: white;
                    font-size: 18px;
                }
                QPushButton:hover {
                    background-color: #0033cc;
                }
                QPushButton:pressed {
                    background-color: #001a66;
                }
            """
        else:
            return """
                QPushButton {
                    background-color: #001a66;  /* Dark blue for active */
                    border: none;
                    border-radius: 5px;
                    color: white;
                    font-size: 18px;
                }
            """


    def onButtonClick(self):
        button = self.sender()
        button_text = button.text()

        # Update active button style
        for name, btn in self.nav_buttons.items():
            if name == button_text:
                btn.setStyleSheet(self.getButtonStyle(inactive=False))
            else:
                btn.setStyleSheet(self.getButtonStyle(inactive=True))

        # Change stacked widget
        if button_text == "Admin Screen":
            self.stacked_widget.setCurrentWidget(self.admin_screen)
        elif button_text == "PPC Screen":
            self.stacked_widget.setCurrentWidget(self.ppc_screen)
        elif button_text == "QA Screen":
            self.stacked_widget.setCurrentWidget(self.qa_screen)
        elif button_text == "Report Generation":
            self.stacked_widget.setCurrentWidget(self.report_screen)
        else:
            self.stacked_widget.setCurrentWidget(self.empty_screen)

        # print(f'{button_text} was clicked!')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ParameterWindow()
    window.show()
    sys.exit(app.exec_())
