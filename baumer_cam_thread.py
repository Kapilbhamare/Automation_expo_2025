#baumer_cam_thread.py
from PyQt5.QtCore import QThread, pyqtSignal
import neoapi
from grab_baumer_gige import gigE_defaults, configure_common, configure_like_explorer_auto, grab_one



class BaumerCamThread(QThread):
    frame_captured = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, serial=None, mode="auto", jumbo=False, mono=False, parent=None):
        super().__init__(parent)
        self.serial = serial
        self.mode = mode
        self.jumbo = jumbo
        self.mono = mono

    def run(self):
        try:
            cam = neoapi.Cam(self.serial) if self.serial else neoapi.Cam()
            cam.Connect()

            gigE_defaults(cam, jumbo=self.jumbo)
            configure_common(cam, mono=self.mono)

            if self.mode == "auto":
                configure_like_explorer_auto(cam)
                for _ in range(0):  # warm-up frames
                    try:
                        grab_one(cam, timeout=1000)
                    except Exception:
                        pass
                frame = grab_one(cam, timeout=5000)
            else:
                from grab_baumer_gige import configure_manual_like_explorer
                configure_manual_like_explorer(cam, exposure_us=136000.0, gain=1.0)
                frame = grab_one(cam, timeout=5000)

            if frame is not None:
                self.frame_captured.emit(frame)
            else:
                raise RuntimeError("No frame received from camera.")

        except Exception as e:
            self.error.emit(str(e))
        finally:
            try:
                if cam.f.AcquisitionStop.IsCommand():
                    cam.f.AcquisitionStop.Execute()
            except Exception:
                pass
            cam.Disconnect()

    def stop(self):
        self.quit()
        self.wait()

