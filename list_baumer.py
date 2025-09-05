# print_baumer_serial.py
import neoapi

def get_str(node):
    try:
        return node.GetString()
    except Exception:
        try:
            return str(node.GetValue())
        except Exception:
            return None

def ip_from_int(v):
    if v is None:
        return None
    try:
        v = int(v)
        return ".".join(str((v >> s) & 255) for s in (24, 16, 8, 0))
    except Exception:
        return None

cam = neoapi.Cam()   # default: first reachable camera
cam.Connect()
try:
    f = cam.f
    serial = get_str(getattr(f, "DeviceSerialNumber", None)) or get_str(getattr(f, "DeviceID", None))
    model  = get_str(getattr(f, "DeviceModelName", None))
    # GevCurrentIPAddress is often an integer; convert to dotted quad
    ip_int = None
    try:
        ip_int = getattr(f, "GevCurrentIPAddress", None)
        ip_int = ip_int.GetValue() if ip_int else None
    except Exception:
        ip_int = None
    ip = ip_from_int(ip_int)

    print(f"Model={model or '?'}  Serial={serial or '?'}  IP={ip or '?'}")
finally:
    cam.Disconnect()
