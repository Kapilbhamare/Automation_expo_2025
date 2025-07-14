import sys
import os
import pymysql  # MySQL database connector
from PyQt5.QtWidgets import (
    QApplication, QDialog, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QFormLayout, QSizePolicy, QSpacerItem, QMessageBox
)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt
from main_screen import ParameterWindow  # Your main window class

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Authentication")
        self.setFixedSize(500, 350)

        # Style
        self.setStyleSheet("""
            QDialog {
                background-color: #f7f7f7;
                border-radius: 10px;
            }
            QLabel {
                font-size: 18px;
                font-family: Arial;
                color: #333;
            }
            QLineEdit {
                padding: 12px;
                border-radius: 10px;
                border: 1px solid #b0c4de;
                background-color: #f0f8ff;
                color: #333;
                font-size: 20px;         
            }
            QPushButton {
                padding: 12px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 18px;
                font-family: Arial;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3e8e41;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)

        # ✅ Load Admin Icon from resource folder (Handles both development & PyInstaller EXE)
        icon_label = QLabel()
        if getattr(sys, 'frozen', False):
            # Running from PyInstaller bundle
            base_path = sys._MEIPASS
        else:
            # Running from source (development)
            base_path = os.path.abspath(".")

        image_path = os.path.join(base_path, "resources", "Admin_login.jpg")

        if os.path.exists(image_path):
            icon_label.setPixmap(QPixmap(image_path).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            icon_label.setText("Icon not available")
        
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Login Form
        form_layout = QFormLayout()
        self.username_input = QLineEdit()
        form_layout.addRow("Username :", self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Password :", self.password_input)
        layout.addLayout(form_layout)

        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Login Button
        self.login_button = QPushButton("Log In")
        self.login_button.setFixedHeight(50)
        self.login_button.clicked.connect(self.check_login)
        layout.addWidget(self.login_button)

    def check_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        try:
            connection = pymysql.connect(
                host='localhost',
                user='root',
                password='kapil',
                database='mayur_industries'
            )
            with connection.cursor() as cursor:
                query = "SELECT * FROM login_table WHERE username=%s AND password=%s"
                cursor.execute(query, (username, password))
                result = cursor.fetchone()

                if result:
                    self.accept()
                else:
                    QMessageBox.warning(self, "Login Failed", "Incorrect username or password.")
        except pymysql.MySQLError as e:
            QMessageBox.critical(self, "Database Error", f"Could not connect to the database.\n{e}")
        finally:
            if 'connection' in locals() and connection.open:
                connection.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    login_dialog = LoginDialog()
    
    if login_dialog.exec_() == QDialog.Accepted:
        main_window = ParameterWindow()
        main_window.show()
        sys.exit(app.exec_())
