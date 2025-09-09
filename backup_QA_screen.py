# QA_screen.py
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QComboBox, QFrame, QSizePolicy, QDateEdit, QMessageBox,
    QLineEdit, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QDate, QTime, QTimer, QSize
from PyQt5.QtGui import QPixmap, QFont, QImage, QIcon
from PyQt5.QtGui import QPixmap, QFont, QImage, QPainter, QPen, QColor, QIcon

import os
import glob
import cv2
import numpy as np
import pymysql

from Detect_hole_bracket import main
from baumer_cam_thread import BaumerCamThread

# ---------- CONFIG ----------
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'kapil',
    'database': 'mayur_industries'
}
# 0 = Bracket, 1 = Hole, 2 = Foam   (we only want Hole on the orange bar)
ALLOWED_ALGOS = {1}

IMG_EXTS = (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp")
# ----------------------------

def is_image_path(p: str) -> bool:
    return isinstance(p, str) and p.lower().endswith(IMG_EXTS)

def first_image_in_dir(dir_path: str) -> str:
    files = []
    for ext in IMG_EXTS:
        files.extend(glob.glob(os.path.join(dir_path, f"*{ext}")))
        files.extend(glob.glob(os.path.join(dir_path, f"*{ext.upper()}")))
    files = sorted(set(files))
    return files[0] if files else ""

class QAScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QA Screen")
        self.setMinimumSize(1024, 700)
        self.setStyleSheet("background-color: white;")
        self.setFont(QFont("Segoe UI", 13))

        self.camera_thread = None
        self.ok_count_for_current_packaging = 0
        self.awaiting_scan = False

        self.master_image_path_cache = None
        self.master_dir_for_main = None

        # cached, after filtering
        self.current_coords = []
        # basis used for pre-capture blue guides (prefer master image size)
        self.coord_basis_w = None
        self.coord_basis_h = None

        # whether live panel is currently showing pre-capture guides
        self.showing_guides = False

        self.initUI()
        self.showMaximized()
        self.setup_scanner_input()

    # ---------------- UI ----------------
    def initUI(self):
        main_layout = QVBoxLayout()
        content_layout = QHBoxLayout()

        # LEFT — form
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)

        self.batch_form = QFrame(self)
        self.batch_form.setFrameShape(QFrame.Box)
        self.batch_form.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.batch_form.setStyleSheet("""
            QFrame { background-color: white; border: 1px solid #ddd; border-radius: 12px; }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(18)
        shadow.setXOffset(0)
        shadow.setYOffset(3)
        shadow.setColor(QColor(0, 0, 0, 40))
        self.batch_form.setGraphicsEffect(shadow)

        base_path = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.abspath(".")
        calendar_icon_path = os.path.join(base_path, "resources", "calendar1.png").replace("\\", "/")

        input_style = f"""
            QPushButton {{
                padding: 8px; border-radius: 8px; background-color: #4CAF50; color: white;
                font-size: 18px; min-width: 180px; min-height: 35px;
            }}
            QPushButton:hover {{ background-color: #45a049; }}
            QLineEdit, QComboBox, QDateEdit {{
                font-size: 16px; font-family: 'Segoe UI'; min-height: 30px; padding: 6px 8px;
                border: 1px solid #d3dce6; border-radius: 6px; background-color: white; color: black;
            }}
            QComboBox::drop-down {{ border: none; background: transparent; subcontrol-origin: padding;
                subcontrol-position: right; width: 25px; }}
            QComboBox::down-arrow {{ image: url("resources/down-arrow.png"); width: 16px; height: 16px; }}
            QDateEdit::drop-down {{ border: none; background: transparent; subcontrol-origin: padding;
                subcontrol-position: right; width: 25px; }}
            QDateEdit::down-arrow {{ image: url("{calendar_icon_path}"); width: 20px; height: 20px; }}
        """

        form_layout = QVBoxLayout()
        form_layout.setSpacing(4)

        dropdown_data = {
            "Part Name": [], "Batch Number": [], "Operator Name": [],
            "Shift": [], "Line Number": [], "Packaging Quantity": [],
            "Std.Quantity": []
        }
        self.inputs = {}
        label_font = QFont("Segoe UI", 17, QFont.Bold)
        for label in dropdown_data.keys():
            lbl = QLabel(label); lbl.setFont(label_font)
            lbl.setStyleSheet("color:#555;font-size:17px;font-weight:600;background:white;border:none;")
            combo = QComboBox()
            combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            combo.setMaximumWidth(280); combo.setMinimumWidth(400)
            combo.addItem(""); combo.setCurrentIndex(0); combo.setStyleSheet(input_style)
            combo.currentIndexChanged.connect(self.check_all_fields_filled)
            if label == "Part Name":
                combo.currentIndexChanged.connect(self.on_part_changed)
            self.inputs[label] = combo
            fl = QVBoxLayout(); fl.setSpacing(10); fl.setContentsMargins(0,0,0,0)
            fl.addWidget(lbl); fl.addWidget(combo); form_layout.addLayout(fl); form_layout.addSpacing(10)

        # Date
        lbl_date = QLabel("Date :"); lbl_date.setFont(label_font)
        lbl_date.setStyleSheet("color:#555;font-size:16px;font-weight:600;")
        self.date_input = QDateEdit(); self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate()); self.date_input.setStyleSheet(input_style)
        self.date_input.dateChanged.connect(self.check_all_fields_filled)

        dl = QVBoxLayout(); dl.addWidget(lbl_date)
        self.date_input.setMaximumWidth(280); self.date_input.setMinimumWidth(400)
        dl.addWidget(self.date_input); form_layout.addLayout(dl); form_layout.addSpacing(20)

        # Time
        lbl_time = QLabel("Time :"); lbl_time.setFont(label_font)
        lbl_time.setStyleSheet("color:#555;font-size:18px;font-weight:600;")
        self.time_display = QLabel(); self.time_display.setFont(QFont("Segoe UI", 10))
        self.time_display.setAlignment(Qt.AlignLeft)
        self.time_display.setStyleSheet("""
            font-size:16px; min-height:30px; padding:6px 8px; font-weight:600;
            border:1px solid #d3dce6; border-radius:6px; background:#fff; color:#000;
        """)
        tl = QVBoxLayout(); tl.addWidget(lbl_time)
        self.time_display.setMaximumWidth(400); self.time_display.setMinimumWidth(240)
        tl.addWidget(self.time_display); form_layout.addLayout(tl); form_layout.addSpacing(20)

        # Capture
        capture_icon_path = os.path.join(base_path, "resources", "capture image.png")
        self.capture_button = QPushButton(" Capture Image")
        self.capture_button.setFont(QFont("Segoe UI", 13))
        self.capture_button.setCursor(Qt.PointingHandCursor)
        self.capture_button.setEnabled(False)
        self.capture_button.setFixedHeight(52)
        self.capture_button.setStyleSheet("""
            QPushButton {
                background-color:#1976d2; color:white; font-size:18px; font-weight:bold;
                border:none; border-radius:8px; padding:8px 16px;
            }
            QPushButton:hover { background-color:#1565c0; }
            QPushButton:pressed { background-color:#0d47a1; }
        """)
        if os.path.exists(capture_icon_path):
            self.capture_button.setIcon(QIcon(capture_icon_path))
            self.capture_button.setIconSize(QSize(24, 24))
        self.capture_button.clicked.connect(self.capture_image)
        self.capture_button.setDefault(True); self.capture_button.setAutoDefault(True)
        form_layout.addWidget(self.capture_button, alignment=Qt.AlignCenter)

        self.batch_form.setLayout(form_layout)
        left_layout.addWidget(self.batch_form, alignment=Qt.AlignLeft)
        left_layout.setAlignment(Qt.AlignTop)

        # RIGHT — result + split
        right_layout = QVBoxLayout()
        self.result_display = QLabel("")
        self.result_display.setFrameShape(QFrame.Box)
        self.result_display.setAlignment(Qt.AlignCenter)
        self.result_display.setFont(QFont("Segoe UI", 60, QFont.Bold))
        self.result_display.setStyleSheet("border-radius:10px;background:#fff;border:2px solid #ccc;")
        right_layout.addWidget(self.result_display, 0)

        hdr = QHBoxLayout()
        lh = QLabel("Live View"); lh.setFont(QFont("Segoe UI", 14, QFont.Bold)); lh.setStyleSheet("color:#333;")
        rh = QLabel("Master Reference"); rh.setFont(QFont("Segoe UI", 14, QFont.Bold)); rh.setStyleSheet("color:#333;")
        hdr.addWidget(lh, alignment=Qt.AlignLeft); hdr.addStretch(1); hdr.addWidget(rh, alignment=Qt.AlignRight)
        right_layout.addLayout(hdr)

        split = QHBoxLayout()
        self.live_image_display = QLabel(self); self.live_image_display.setFrameShape(QFrame.Box)
        self.live_image_display.setAlignment(Qt.AlignCenter)
        self.live_image_display.setStyleSheet("border-radius:10px;background:#fff;border:1px solid #e0e0e0;")
        self.live_image_display.setMinimumSize(300,300)

        self.master_image_display = QLabel(self); self.master_image_display.setFrameShape(QFrame.Box)
        self.master_image_display.setAlignment(Qt.AlignCenter)
        self.master_image_display.setStyleSheet("border-radius:10px;background:#fff;border:1px solid #e0e0e0;")
        self.master_image_display.setMinimumSize(300,300)
        split.addWidget(self.live_image_display, 1); split.addWidget(self.master_image_display, 1)
        right_layout.addLayout(split, 6)

        content_layout.addLayout(left_layout); content_layout.addLayout(right_layout)
        content_layout.setStretch(0,3); content_layout.setStretch(1,7)
        main_layout.addLayout(content_layout); main_layout.setContentsMargins(10,10,10,10)
        self.setLayout(main_layout)

        self.fetch_dropdown_values()
        self.timer = QTimer(self); self.timer.timeout.connect(self.update_time)
        self.timer.start(1000); self.update_time()

    # -------------- helpers --------------
    def update_time(self):
        self.time_display.setText(QTime.currentTime().toString("HH:mm:ss"))

    def showEvent(self, e):
        super().showEvent(e); self.fetch_dropdown_values()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        # Re-apply the current pixmaps with aspect-preserving scaling
        for lbl in (self.live_image_display, self.master_image_display):
            pm = lbl.pixmap()
            if pm:
                lbl.setPixmap(pm.scaled(lbl.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        # If guides are currently shown, re-render them to the new size
        if self.showing_guides and self.current_coords and self.coord_basis_w and self.coord_basis_h:
            self._render_pre_capture_guides()

    def setup_scanner_input(self):
        self.scanner_input = QLineEdit(self)
        self.scanner_input.setFixedSize(1,1)
        self.scanner_input.setStyleSheet("border:none;background:transparent;")
        self.layout().addWidget(self.scanner_input)
        self.scanner_input.returnPressed.connect(self.handle_scanner_input)
        self.scanner_input.setFocusPolicy(Qt.StrongFocus); self.scanner_input.setFocus()

    def handle_scanner_input(self):
        scanned = self.scanner_input.text().strip()
        if self.awaiting_scan and scanned:
            QMessageBox.information(self, "Scan Received", f"Scanned: {scanned}")
            self.capture_button.setEnabled(True); self.awaiting_scan = False
        self.scanner_input.clear(); self.scanner_input.setFocus()

    def check_all_fields_filled(self):
        for w in self.inputs.values():
            if w.currentText().strip() == "":
                self.capture_button.setEnabled(False); return
        if self.date_input.date().isNull():
            self.capture_button.setEnabled(False); return
        self.capture_button.setEnabled(True)

    def fetch_dropdown_values(self):
        conn = pymysql.connect(**db_config)
        if not conn: return
        try:
            c = conn.cursor()
            queries = {
                "Batch Number": "SELECT DISTINCT batch_number FROM ppc_batch",
                "Operator Name": "SELECT DISTINCT operator_name FROM ppc_batch",
                "Shift": "SELECT DISTINCT shift FROM ppc_batch",
                "Line Number": "SELECT DISTINCT line_number FROM ppc_batch",
                "Part Name": "SELECT DISTINCT part_name FROM ppc_batch",
                "Packaging Quantity": "SELECT DISTINCT packaging_quantity FROM ppc_batch",
                "Std.Quantity": "SELECT DISTINCT std_quantity FROM ppc_batch"
            }
            for label, q in queries.items():
                c.execute(q); values = [str(r[0]) for r in c.fetchall() if r[0] is not None]
                combo = self.inputs[label]; combo.blockSignals(True); combo.clear()
                combo.addItem("")
                try: combo.model().item(0).setEnabled(False)
                except: pass
                combo.addItems(values); combo.setCurrentIndex(0); combo.blockSignals(False)
        except Exception as e:
            QMessageBox.critical(self, "DB Error", str(e))
        finally:
            try: c.close(); conn.close()
            except: pass

    # -------- part change: setup guides ----------
    def on_part_changed(self):
        self.autofill_fields_from_part_name()
        part = self.inputs["Part Name"].currentText().strip()
        if not part:
            self._clear_all_views()
            return

        try:
            conn = pymysql.connect(**db_config); c = conn.cursor()
            c.execute("SELECT folder_path FROM parent_part WHERE parent_part_name=%s", (part,))
            row = c.fetchone()
            if not row or not row[0]:
                self._clear_all_views()
                return

            base_path = row[0].strip()

            # Decide directory and master image path
            if os.path.isdir(base_path):
                self.master_dir_for_main = base_path
                pref = []
                for name in ("master","Master","template","Template","golden","Golden","ref","reference","Reference"):
                    pref.extend(glob.glob(os.path.join(base_path, f"{name}.*")))
                pref = [p for p in pref if is_image_path(p)]
                self.master_image_path_cache = pref[0] if pref else first_image_in_dir(base_path)
            elif is_image_path(base_path):
                self.master_dir_for_main = os.path.dirname(base_path)
                self.master_image_path_cache = base_path
            else:
                self.master_dir_for_main = ""
                self.master_image_path_cache = ""

            # Load child coords
            c.execute("SELECT coordinates, vision_algorithm FROM child_part WHERE parent_part_name=%s", (part,))
            coord_rows = c.fetchall()
            coords_all = self._parse_coords(coord_rows)
            coords = self._filter_holes_inside_brackets(coords_all)
            self.current_coords = coords

            # BASIS: prefer the actual master image size (so guides match)
            master_w = master_h = None
            if self.master_image_path_cache and os.path.exists(self.master_image_path_cache):
                tmp = cv2.imread(self.master_image_path_cache, cv2.IMREAD_COLOR)
                if tmp is not None:
                    master_h, master_w = tmp.shape[:2]

            if master_w and master_h:
                self.coord_basis_w, self.coord_basis_h = master_w, master_h
            else:
                self.coord_basis_w, self.coord_basis_h = self._coord_basis_from_coords(coords)

            # Right panel: master with guides (for visual reference only)
            if self.master_image_path_cache and os.path.exists(self.master_image_path_cache):
                qpix_master = self._load_master_with_guides(
                    self.master_image_path_cache, coords, self.coord_basis_w, self.coord_basis_h
                )
                if qpix_master:
                    self._set_scaled_pixmap(self.master_image_display, qpix_master)
                else:
                    self.master_image_display.clear()
            else:
                self.master_image_display.clear()

            # Live panel: show ONLY blue guides on a blank canvas
            self._render_pre_capture_guides()
            self.showing_guides = True

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed loading master: {e}")
        finally:
            try: c.close(); conn.close()
            except: pass

    def _render_pre_capture_guides(self):
        lw = max(10, self.live_image_display.width())
        lh = max(10, self.live_image_display.height())
        guide_qpix = self._boxes_on_canvas_keep_ar(
            canvas_w=lw, canvas_h=lh, coords=self.current_coords,
            basis_w=self.coord_basis_w, basis_h=self.coord_basis_h,
            color_bgr=(255, 0, 0),  # BLUE
            thickness=3, label_text=""
        )
        if guide_qpix:
            self.live_image_display.setPixmap(
                guide_qpix.scaled(self.live_image_display.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )

    def _clear_all_views(self):
        self.master_image_display.clear()
        self.live_image_display.clear()
        self.master_image_path_cache = None
        self.master_dir_for_main = None
        self.current_coords = []
        self.coord_basis_w = None
        self.coord_basis_h = None
        self.showing_guides = False

    def _coord_basis_from_coords(self, coords):
        max_x = 1
        max_y = 1
        for r in coords:
            for (x, y) in r[1:5]:
                if x > max_x: max_x = x
                if y > max_y: max_y = y
        return max_x, max_y

    def autofill_fields_from_part_name(self):
        part = self.inputs["Part Name"].currentText()
        if not part:
            for k,w in self.inputs.items():
                if k!="Part Name": w.setEnabled(True); w.setCurrentIndex(0)
            return
        conn = pymysql.connect(**db_config)
        if not conn: return
        try:
            c = conn.cursor()
            c.execute("""
                SELECT batch_number, operator_name, shift, line_number, packaging_quantity, std_quantity
                FROM ppc_batch WHERE part_name=%s ORDER BY created_date DESC LIMIT 1
            """, (part,))
            row = c.fetchone()
            if row:
                keys = ["Batch Number","Operator Name","Shift","Line Number","Packaging Quantity","Std.Quantity"]
                for i,k in enumerate(keys):
                    combo = self.inputs[k]; combo.blockSignals(True)
                    combo.setCurrentText(str(row[i])); combo.setDisabled(True); combo.blockSignals(False)
        except Exception as e:
            QMessageBox.critical(self, "Database Error", str(e))
        finally:
            try: c.close(); conn.close()
            except: pass
        self.check_all_fields_filled()

    # -------------- capture --------------
    def capture_image(self):
        self.capture_button.setEnabled(False)
        # Once capture starts, we won't show pre-capture guides anymore
        self.showing_guides = False

        if self.camera_thread:
            if self.camera_thread.isRunning():
                self.camera_thread.quit(); self.camera_thread.wait()
            try:
                self.camera_thread.frame_captured.disconnect(); self.camera_thread.error.disconnect()
            except: pass
            self.camera_thread = None

        self.camera_thread = BaumerCamThread(mono=False, parent=self)
        self.camera_thread.frame_captured.connect(self.process_captured_frame)
        self.camera_thread.error.connect(lambda msg: QMessageBox.critical(self, "Camera Error", msg))
        self.camera_thread.start()

    def closeEvent(self, e):
        if hasattr(self,'camera_thread') and self.camera_thread: self.camera_thread.stop()
        e.accept()

    def _qpix_from_bgr(self, img_bgr):
        rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        qimg = QImage(rgb.data, rgb.shape[1], rgb.shape[0], rgb.strides[0], QImage.Format_RGB888)
        return QPixmap.fromImage(qimg)

    def process_captured_frame(self, frame_bgr):
        # Disconnect/stop thread
        if hasattr(self,'camera_thread') and self.camera_thread:
            try: self.camera_thread.frame_captured.disconnect(); self.camera_thread.error.disconnect()
            except: pass
            try: self.camera_thread.quit(); self.camera_thread.wait()
            except: pass
            self.camera_thread = None

        part = self.inputs["Part Name"].currentText().strip()
        if not part:
            QMessageBox.warning(self,"Input Error","Please select a valid Part Name."); 
            self.capture_button.setEnabled(True)
            return

        # Clear the guide pixmap so it never shows under the result
        self.live_image_display.clear()

        # fetch master dir + file + coords
        try:
            conn = pymysql.connect(**db_config); c = conn.cursor()
            c.execute("SELECT folder_path FROM parent_part WHERE parent_part_name=%s", (part,))
            row = c.fetchone()
            base_path = row[0].strip() if row else ""

            if os.path.isdir(base_path):
                master_dir_for_main = base_path
                pref=[]
                for name in ("master","Master","template","Template","golden","Golden"):
                    pref.extend(glob.glob(os.path.join(base_path, f"{name}.*")))
                pref=[p for p in pref if is_image_path(p)]
                master_path = pref[0] if pref else first_image_in_dir(base_path)
            elif is_image_path(base_path):
                master_dir_for_main = os.path.dirname(base_path)
                master_path = base_path
            else:
                master_dir_for_main = ""
                master_path = ""

            self.master_dir_for_main = master_dir_for_main
            self.master_image_path_cache = master_path

            c.execute("SELECT coordinates, vision_algorithm FROM child_part WHERE parent_part_name=%s",(part,))
            coord_rows = c.fetchall()
            coords_all = self._parse_coords(coord_rows)
            coords = self._filter_holes_inside_brackets(coords_all)
            self.current_coords = coords

            # basis for any fallbacks
            if self.master_image_path_cache and os.path.exists(self.master_image_path_cache):
                tmp = cv2.imread(self.master_image_path_cache, cv2.IMREAD_COLOR)
                if tmp is not None:
                    h, w = tmp.shape[:2]
                    self.coord_basis_w, self.coord_basis_h = w, h
                else:
                    self.coord_basis_w, self.coord_basis_h = self._coord_basis_from_coords(coords)
            else:
                self.coord_basis_w, self.coord_basis_h = self._coord_basis_from_coords(coords)

        except Exception as e:
            QMessageBox.critical(self,"Database Error",str(e)); 
            self.capture_button.setEnabled(True)
            return
        finally:
            try: c.close(); conn.close()
            except: pass

        if not self.master_dir_for_main or not os.path.isdir(self.master_dir_for_main):
            QMessageBox.critical(self, "Master Missing",
                                 "Cannot find the master folder for this part.\nPlease check 'folder_path' in DB.")
            self.capture_button.setEnabled(True)
            return

        # ----- Run vision
        try:
            # main() should return an annotated image; if so, we will NOT draw boxes again.
            result_img_bgr, status, defects = main(
                image=frame_bgr,
                master_crop_path=self.master_dir_for_main,
                coords=coords
            )
        except Exception as e:
            QMessageBox.critical(self, "Vision Error", f"Processing failed:\n{e}")
            self.capture_button.setEnabled(True)
            return

        # Determine OK/NOK
        status_text = str(status).strip()
        is_ok = status_text.lower() == "ok"

        # LIVE VIEW = show the annotated image from vision AS-IS (avoid double overlay)
        if result_img_bgr is not None:
            live_qpix = self._qpix_from_bgr(result_img_bgr)
        else:
            # Fallback: draw a single overlay on the raw frame (should rarely happen)
            live_qpix = self._qpix_from_bgr(frame_bgr)

        if live_qpix:
            self._set_scaled_pixmap(self.live_image_display, live_qpix)

        # MASTER (right panel) with blue guides (unchanged from on_part_changed)
        master_qpix = None
        if self.master_image_path_cache and os.path.exists(self.master_image_path_cache):
            master_qpix = self._load_master_with_guides(self.master_image_path_cache, coords,
                                                        self.coord_basis_w, self.coord_basis_h)
        if master_qpix:
            self._set_scaled_pixmap(self.master_image_display, master_qpix)
        else:
            self.master_image_display.clear()

        self.result_display.setText("OK" if is_ok else "NOT OK")
        self.result_display.setStyleSheet(
            f"color: {'green' if is_ok else 'red'}; background:#fff; border-radius:10px; border:2px solid #ccc;"
        )

        # log
        try:
            conn = pymysql.connect(**db_config); c = conn.cursor()
            current_time = self.time_display.text()
            selected_date = self.date_input.date().toString("yyyy-MM-dd")
            reason = " and ".join([f"{i+1}. {d}" for i,d in enumerate(defects or []) if d]) or None
            c.execute(
                "INSERT INTO ok_nok (part_name, ok, nok, time, IN_DATE, reason) VALUES (%s,%s,%s,%s,%s,%s)",
                (part, 1 if is_ok else 0, 0 if is_ok else 1, current_time, selected_date, reason)
            )
            conn.commit()
            if is_ok: self.ok_count_for_current_packaging += 1
            try: packaging = int(self.inputs['Packaging Quantity'].currentText())
            except: packaging = 0
            if packaging>0 and self.ok_count_for_current_packaging==packaging:
                self.ok_count_for_current_packaging=0
                QMessageBox.information(self,"Batch Complete","Packaging quantity reached. Please scan next batch barcode.")
                self.capture_button.setEnabled(False); self.awaiting_scan=True; self.scanner_input.setFocus()
            else:
                self.capture_button.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self,"Database Error",f"Failed to insert result.\n{e}")
        finally:
            try: c.close(); conn.close()
            except: pass

    # ---------- drawing / scaling ----------
    def _parse_coords(self, rows):
        """
        rows: [(coord_str, vision_algorithm), ...]
        returns: [[algo_id, (x1,y1),(x2,y2),(x3,y3),(x4,y4)], ...]
        """
        coords = []
        def algomap(name: str):
            n = (name or "").strip().lower()
            if n == "bracket": return 0
            if n == "hole":    return 1
            if n == "foam":    return 2
            return -1

        for coord_str, algo in rows:
            s = str(coord_str).strip()
            s = s.replace("[","").replace("]","").replace("{","").replace("}","")
            tokens = s.split("),")
            pts=[]
            for t in tokens:
                t = t.replace("(","").replace(")","").strip()
                if not t: continue
                parts = [p.strip() for p in t.split(",") if p.strip()]
                if len(parts)>=2:
                    try:
                        x = int(float(parts[0])); y = int(float(parts[1]))
                        pts.append((x,y))
                    except: pass
            if len(pts)>=4:
                coords.append([algomap(algo)] + pts[:4])
        return coords

    def _filter_holes_inside_brackets(self, coords_all):
        """Keep only Hole ROIs whose centroid is inside a Bracket polygon."""
        brackets = [r for r in coords_all if r and r[0] == 0]
        holes    = [r for r in coords_all if r and r[0] == 1]
        if not brackets:
            return [r for r in coords_all if r and r[0] in ALLOWED_ALGOS]

        bracket_polys = []
        for b in brackets:
            _, p1, p2, p3, p4 = b
            bracket_polys.append(np.array([p1, p2, p3, p4], dtype=np.float32))

        def inside(pt, poly):  # >=0 -> inside/on edge
            return cv2.pointPolygonTest(poly, (float(pt[0]), float(pt[1])), False) >= 0

        def centroid(roi):
            _, p1, p2, p3, p4 = roi
            return ((p1[0]+p2[0]+p3[0]+p4[0])/4.0, (p1[1]+p2[1]+p3[1]+p4[1])/4.0)

        out = []
        for h in holes:
            c = centroid(h)
            if any(inside(c, poly) for poly in bracket_polys):
                out.append(h)
        return out or [r for r in coords_all if r and r[0] in ALLOWED_ALGOS]

    def _boxes_on_canvas_keep_ar(self, canvas_w, canvas_h, coords, basis_w, basis_h,
                                 color_bgr=(255,0,0), thickness=3, label_text=""):
        """
        Draw boxes onto a blank canvas while preserving QLabel's aspect-ratio fit.
        Coordinates are in the (basis_w, basis_h) space (ideally = master image size).
        """
        if not basis_w or not basis_h:
            return None

        # white canvas
        img = np.full((canvas_h, canvas_w, 3), 255, dtype=np.uint8)

        scale = min(canvas_w / float(basis_w), canvas_h / float(basis_h))
        off_x = int(round((canvas_w - basis_w * scale) / 2.0))
        off_y = int(round((canvas_h - basis_h * scale) / 2.0))

        for roi in coords:
            _, p1,p2,p3,p4 = roi
            pts = []
            for (x, y) in (p1, p2, p3, p4):
                pts.append( (int(round(off_x + x * scale)), int(round(off_y + y * scale))) )
            poly = np.array(pts, dtype=np.int32)
            cv2.polylines(img, [poly], True, color_bgr, thickness=thickness)
            if label_text:
                cv2.putText(img, label_text, (pts[0][0]+5, max(20, pts[0][1]-8)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, color_bgr, 2, cv2.LINE_AA)

        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        qimg = QImage(rgb.data, rgb.shape[1], rgb.shape[0], rgb.strides[0], QImage.Format_RGB888)
        return QPixmap.fromImage(qimg)

    def _load_master_with_guides(self, master_path, coords, basis_w, basis_h):
        """Overlay BLUE guides on master image."""
        if not master_path or not os.path.exists(master_path): return None
        master_bgr = cv2.imread(master_path, cv2.IMREAD_COLOR)
        if master_bgr is None: return None

        img = master_bgr.copy()
        h, w = img.shape[:2]
        sx = w / float(basis_w if basis_w > 0 else 1)
        sy = h / float(basis_h if basis_h > 0 else 1)

        BLUE = (255, 0, 0)  # BGR
        for roi in coords:
            _, p1,p2,p3,p4 = roi
            pts = []
            for (x, y) in (p1, p2, p3, p4):
                pts.append((int(round(x * sx)), int(round(y * sy))))
            poly = np.array(pts, dtype=np.int32)
            cv2.polylines(img, [poly], True, BLUE, thickness=2)

        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        qimg = QImage(rgb.data, rgb.shape[1], rgb.shape[0], rgb.strides[0], QImage.Format_RGB888)
        return QPixmap.fromImage(qimg)

    def _set_scaled_pixmap(self, label: QLabel, pixmap: QPixmap):
        label.setPixmap(pixmap.scaled(label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    # -------------- reset --------------
    def reset_form_after_packaging(self):
        for k,w in self.inputs.items():
            if k!="Part Name": w.setEnabled(True)
            w.setCurrentIndex(0)
        self.date_input.setDate(QDate.currentDate())
        self.live_image_display.clear(); self.master_image_display.clear()
        self.result_display.clear(); self.capture_button.setEnabled(False)
        self.showing_guides = False

if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    window = QAScreen()
    window.show()
    sys.exit(app.exec_())
