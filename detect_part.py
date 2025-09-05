import cv2
import numpy as np

# 1) Order points function
def order_points(pts):
    # pts: N×2 array of (x,y)
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)

    tl = pts[np.argmin(s)]
    br = pts[np.argmax(s)]
    tr = pts[np.argmin(diff)]
    bl = pts[np.argmax(diff)]

    return np.array([tl, tr, br, bl], dtype="float32")

def detect_part(frame):
    # Preprocess Image
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Threshold the image to segment the box
    # _, binary = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)
    # binary = cv2.bitwise_not(binary)
    # kernel = np.ones((170, 170), np.uint8)
    # closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    part_thr = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    kernel = np.ones((40,40),np.uint8)
    closed = cv2.morphologyEx(part_thr, cv2.MORPH_CLOSE, kernel)

    # Find contours
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter contours based on area
    contours = [contour for contour in contours if cv2.contourArea(contour) >= 10000]

    if len(contours) < 1:
        return False, None, None

    contour = max(contours, key=cv2.contourArea)

    part_contour = cv2.convexHull(contour)

    # Get the minimum area rectangle
    rect = cv2.minAreaRect(part_contour)
    center, size, angle = rect

    padding = 200
    expanded_size = (size[0] + 2 * padding, size[1] + 2 * padding)
    expanded_rect = (center, expanded_size, angle)

    box = cv2.boxPoints(expanded_rect)
    box = np.intp(box)  # platform dependent int type, usually np.int32 or np.int64

    # Draw parent bounding box
    img_bbox = cv2.drawContours(frame.copy(), [box], -1, (0, 255, 0), 2)


    # 2) Grab rectified src_pts
    src_pts = order_points(box)

    (tl, tr, br, bl) = src_pts

    # 3) Compute the width and height of the new image
    widthA  = np.linalg.norm(br - bl)
    widthB  = np.linalg.norm(tr - tl)
    width  = int(max(widthA, widthB))

    heightA = np.linalg.norm(tr - br)
    heightB = np.linalg.norm(tl - bl)
    height = int(max(heightA, heightB))

    # 4) Define destination points in the same order
    dst_pts = np.array([
        [0, 0],
        [width - 1, 0],
        [width - 1, height - 1],
        [0, height - 1]
    ], dtype="float32")

    # 5) Compute the transform and warp
    M = cv2.getPerspectiveTransform(src_pts, dst_pts)
    warped = cv2.warpPerspective(frame, M, (width, height))

    return True, img_bbox, warped