#grab_baumer_gige_fast.py
import argparse, time
import cv2
import neoapi

def try_set(node, value, use_string=False):
    if not node:
        return False
    try:
        if node.IsWritable():
            if use_string:
                node.SetString(value)
            else:
                # choose Set vs SetString based on value type
                if isinstance(value, str):
                    node.SetString(value)
                else:
                    node.Set(value)
            return True
    except Exception:
        pass
    return False

def try_get_string(node, fallback=None):
    try:
        return node.GetString()
    except Exception:
        return fallback

def try_get_value(node, fallback=None):
    try:
        return node.GetValue()
    except Exception:
        try:
            return node.Get()
        except Exception:
            return fallback

def gigE_defaults(cam, jumbo=False):
    f = cam.f
    try:
        if jumbo:
            try_set(getattr(f, "GevSCPSPacketSize", None), 8192)
        else:
            try_set(getattr(f, "GevSCPSPacketSize", None), 1500)
    except Exception:
        pass
    try_set(getattr(f, "GevSCPD", None), 2000)  # 8 µs delay
    for name in ("DeviceLinkThroughputLimit", "StreamBytesPerSecond"):
        node = getattr(f, name, None)
        if node and hasattr(node, "Set"):
            try:
                if node.IsWritable():
                    node.Set(120 * 1024 * 1024)
            except Exception:
                pass

def configure_common(f, mono=False):
    try_set(getattr(f, "TriggerMode", None), "Off", use_string=True)
    try_set(getattr(f, "AcquisitionMode", None), "Continuous", use_string=True)
    if mono:
        try_set(getattr(f, "PixelFormat", None), "Mono8", use_string=True)
    else:
        try_set(getattr(f, "PixelFormat", None), "BGR8", use_string=True)

def configure_like_explorer_auto(f):
    # Auto exposure / gain
    for node_name in ("ExposureAuto", "GainAuto"):
        try_set(getattr(f, node_name, None), "Continuous", use_string=True)

    # Target brightness variations
    for name in ("TargetBrightness", "AutoTargetBrightness", "BrightnessTarget"):
        node = getattr(f, name, None)
        if node and hasattr(node, "Set"):
            if node.IsWritable():
                try:
                    node.Set(50.0)
                except Exception:
                    try:
                        node.Set(0.5)
                    except Exception:
                        pass

    # Gamma enable + value
    try_set(getattr(f, "GammaEnable", None), True)
    try_set(getattr(f, "Gamma", None), 1.20)

def configure_manual_like_explorer(f, exposure_us=136000.0, gain=1.0):
    # Turn auto off
    for node_name in ("ExposureAuto", "GainAuto"):
        try_set(getattr(f, node_name, None), "Off", use_string=True)

    # Exposure
    if hasattr(f, "ExposureTime"):
        try:
            if f.ExposureTime.IsWritable():
                f.ExposureTime.Set(exposure_us)
        except Exception:
            pass

    # Gain variants
    for name in ("Gain", "AnalogGain", "GainRaw"):
        node = getattr(f, name, None)
        if node and hasattr(node, "Set"):
            try:
                if node.IsWritable():
                    node.Set(gain)
                    break
            except Exception:
                pass

    # Gamma
    try_set(getattr(f, "GammaEnable", None), True)
    try_set(getattr(f, "Gamma", None), 1.20)

def grab_one(cam, timeout=5000):
    try:
        if cam.f.AcquisitionStart.IsCommand():
            cam.f.AcquisitionStart.Execute()
    except Exception:
        pass
    img = cam.GetImage(timeout)
    if img is None:
        raise RuntimeError("Timeout: no image")
    return img.GetNPArray()

def auto_settle(f, cam, timeout_s=1.0, epsilon=1.0):
    """Wait until exposure time stabilizes (or timeout)."""
    prev = try_get_value(getattr(f, "ExposureTime", None), None)
    start = time.time()
    while time.time() - start < timeout_s:
        try:
            # grab a lightweight frame to advance auto algorithms
            if cam.f.AcquisitionStart.IsCommand(): cam.f.AcquisitionStart.Execute()
        except Exception:
            pass
        _ = cam.GetImage(1000)  # low timeout
        curr = try_get_value(getattr(f, "ExposureTime", None), None)
        if prev is not None and curr is not None:
            try:
                if abs(curr - prev) < epsilon:
                    return  # stabilized
            except Exception:
                pass
        prev = curr
    # fallback: do nothing, time exhausted

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--serial", help="Camera serial (recommended)")
    ap.add_argument("--out", default="vcxg_capture.png")
    ap.add_argument("--mode", choices=["auto","manual"], default="auto",
                    help="auto = like Explorer (auto brightness); manual = fixed exposure≈136ms")
    ap.add_argument("--jumbo", action="store_true", help="try jumbo packets")
    args = ap.parse_args()

    cam = neoapi.Cam(args.serial) if args.serial else neoapi.Cam()
    cam.Connect()
    try:
        gigE_defaults(cam, jumbo=args.jumbo)
        configure_common(cam.f, mono=False)

        if args.mode == "auto":
            configure_like_explorer_auto(cam.f)
            # Smart settling: wait until exposure stabilizes (short-circuit if fast)
            auto_settle(cam.f, cam, timeout_s=0.8, epsilon=0.5)
            frame = grab_one(cam, 5000)
        else:  # manual
            configure_manual_like_explorer(cam.f, exposure_us=8000.0, gain=0)
            # minimal warm-up
            try:
                grab_one(cam, 2000)
            except Exception:
                pass
            frame = grab_one(cam, 5000)

        if not cv2.imwrite(args.out, frame):
            raise RuntimeError(f"Failed to save {args.out}")
        print(f"Saved: {args.out}")

        # Print effective values
        try:
            pf = try_get_string(getattr(cam.f, "PixelFormat", None), "?")
            et = try_get_value(getattr(cam.f, "ExposureTime", None), -1)
            gn = None
            for name in ("Gain", "AnalogGain", "GainRaw"):
                candidate = try_get_value(getattr(cam.f, name, None), None)
                if candidate is not None:
                    gn = candidate
                    break
            gm = try_get_value(getattr(cam.f, "Gamma", None), None)
            print(f"PixelFormat={pf}  ExposureTime(us)={et}  Gain={gn}  Gamma={gm}")
        except Exception:
            pass

    finally:
        try:
            if cam.f.AcquisitionStop.IsCommand():
                cam.f.AcquisitionStop.Execute()
        except Exception:
            pass
        cam.Disconnect()

if __name__ == "__main__":
    main()
