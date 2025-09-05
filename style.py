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
    color: black;  /* 👈 This ensures weekdays are black */
    background-color: black;
    alternate-background-color: black;
}
QDateEdit::down-arrow {
    image: url("resources/calendar1.png");
    width: 16px;
    height: 16px;
}
"""
