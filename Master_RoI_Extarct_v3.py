import cv2
import numpy as np
import matplotlib.pyplot as plt
import os



# Function to save images in an array to a specified directory
def save_images(image_array, save_directory, base_filename="image"):
    """
    Saves images stored in an array to the specified directory.
    Parameters:
    - image_array: List of images (numpy arrays) to save.
    - save_directory: Path to the directory where images will be saved.
    - base_filename: Base name for the saved image files.
    """
    # Create the directory if it does not exist
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)

    # Save each image in the array
    for idx, image in enumerate(image_array):
        file_path = os.path.join(save_directory, f"{base_filename}_{idx+1}.png")
        cv2.imwrite(file_path, image)
        print(f"Saved: {file_path}")


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


def save_master_crop(image, coords, save_dir, base_filename="master_feature"):

    m_dta = np.array([x[0] for x in coords]).reshape(len(coords), 1)
    coords = [x[1:] for x in coords]

    flattened_coords = np.array([[value for tup in l for value in tup] for l in coords])
    data = np.hstack((m_dta, flattened_coords))
    print(data)

    # Preprocess Image
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

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
    contour = max(contours, key=cv2.contourArea)

    # epsilon = 0.1 * cv2.arcLength(contour, True)
    # part_contour = cv2.approxPolyDP(contour, epsilon, True)

    part_contour = cv2.convexHull(contour)

    # Get the minimum area rectangle
    rect = cv2.minAreaRect(part_contour)
    center, size, angle = rect  # center = (x, y), size = (width, height), angle = rotation angle

    padding = 200

    # Expand the size by adding padding
    expanded_size = (size[0] + 2 * padding, size[1] + 2 * padding)

    # Create a new rectangle with the expanded size
    expanded_rect = (center, expanded_size, angle)

    box = cv2.boxPoints(expanded_rect)
    box = np.int64(box)

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
    warped = cv2.warpPerspective(image, M, (width, height))

    # Function to calculate center point of a box
    def calculate_center(box):
        x_coords = [box[1], box[3], box[5], box[7]]
        y_coords = [box[2], box[4], box[6], box[8]]
        x_center = sum(x_coords) / 4
        y_center = sum(y_coords) / 4
        return x_center, y_center

    # Calculate centers and sort data
    centers = [calculate_center(row) for row in data]
    data_with_centers = [(row, center) for row, center in zip(data, centers)]
    sorted_data_with_centers = sorted(data_with_centers, key=lambda x: (int(x[1][1] + x[1][0]), x[1][1], x[1][0]))  # Sort by y, then x

    # Extract sorted data
    sorted_data = np.array([row for row, center in sorted_data_with_centers])

    ### Process Bounding Boxes ###
    bounding_boxes_3d = sorted_data[:, 1:].reshape((-1, 1, 2))
    bounding_boxes_3d = bounding_boxes_3d.astype(np.int32)
    bounding_boxes_3d = bounding_boxes_3d.reshape((-1, 8))


    # ### Draw Green Bounding Box ###
    # img_test = warped.copy()
    # for label in bounding_boxes_3d:
    #     # Extract and scale corner coordinates
    #     corners = label.reshape((-1, 1, 2))

    #     # Draw the bounding box
    #     cv2.polylines(img_test, [corners], isClosed=True, color=(0, 255, 0), thickness=2)


    img_bbox = np.zeros_like(warped)

    for label in bounding_boxes_3d:
        # Extract and scale corner coordinates
        corners = label.reshape((-1, 1, 2))

        # Draw the bounding box
        cv2.polylines(img_bbox, [corners], isClosed=True, color=(255, 255, 255), thickness=2)

    img_bbox = cv2.cvtColor(img_bbox, cv2.COLOR_BGR2GRAY)


    # cv2.imshow('Master Extract',img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()


    ### Detect the green bounding boxes and get oriented bounding boxes ###
    # Convert the image to HSV color space

    # Find contours
    child_contours, _ = cv2.findContours(img_bbox, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Oriented Bound Box values for child 
    child_rect = []

    # Draw oriented bounding boxes
    for child_contour in child_contours:
        # Calculate the minimum area rectangle
        c_rect = cv2.minAreaRect(child_contour)
        child_rect.append(c_rect)

    child_rect = sorted(child_rect, key=lambda c: (int(c[0][0] + c[0][1]), c[0][1], c[0][0]))  # Sort by y-coordinate, then x-coordinate

    ### Extract and Save Cropped 
    img = warped.copy()
    child_obb = []
    child_roi = []
    for c_rec in child_rect:

        center, size, angle = c_rec  # center = (x, y), size = (width, height), angle = rotation angle

        c_padding = 0

        # Expand the size by adding padding
        expanded_c_size = (size[0] + 2 * c_padding, size[1] + 2 * c_padding)

        # Create a new rectangle with the expanded size
        expanded_c_rect = (center, expanded_c_size, angle)
        c_box = cv2.boxPoints(expanded_c_rect)
        c_box = np.int64(c_box)
        child_obb.append(c_box)

        center, size, angle = c_rec

        # Step 1: Determine the width and height of the bounding box
        c_height = int(expanded_c_size[0])
        c_width = int(expanded_c_size[1])


        # Step 3: Define the destination points for the transformation
        c_dst = np.array([
            [0, 0],
            [c_width - 1, 0],
            [c_width - 1, c_height - 1],
            [0, c_height - 1]
        ], dtype="float32")

        # Step 4: Compute the perspective transform matrix
        c_M = cv2.getPerspectiveTransform(np.float32(c_box), c_dst)

        # Step 5: Perform the perspective warp
        c_warped = cv2.warpPerspective(img, c_M, (c_width, c_height))

        if c_width > c_height:
            c_warped = cv2.rotate(c_warped, cv2.ROTATE_90_COUNTERCLOCKWISE)

        child_roi.append(c_warped)


    # Save images
    save_images(child_roi, save_dir, base_filename)



if __name__=="__main__":

    # Load Image
    img_path = '/Users/abhi/Desktop/Augle AI/Duct Defect Detection/Code/Image_20250514170757411.bmp'
    image = cv2.imread(img_path)

    # Specify the directory to save the images
    save_dir = "/Users/abhi/Desktop/Augle AI/Duct Defect Detection/Code/crop_test"

    # coords =  [
    # [0, (1081, 205), (1175, 191), (1187, 257), (1092, 271)],
    # [0, (485, 195), (580, 203), (573, 267), (478, 259)],
    # [1, (736, 409), (793, 409), (793, 446), (736, 446)],
    # [1, (878, 409), (935, 409), (935, 447), (877, 446)],
    # [2, (447, 446), (513, 466), (464, 622), (398, 600)],
    # [0, (265, 582), (310, 541), (404, 642), (360, 684)],
    # [2, (1134, 489), (1212, 445), (1293, 590), (1218, 639)],
    # [0, (1281, 634), (1333, 683), (1431, 578), (1383, 536)],
    # [0, (613, 738), (690, 736), (690, 863), (611, 863)]
    # ]

    # coords = [
    # [1, (519, 205), (551, 208), (546, 239), (515, 236)],
    # [1, (1110, 213), (1143, 204), (1151, 234), (1117, 241)],
    # [1, (291, 581), (311, 560), (334, 583), (313, 603)],
    # [1, (321, 619), (346, 594), (372, 620), (346, 644)],
    # [1, (1381, 560), (1403, 578), (1384, 602), (1361, 583)],
    # [1, (1348, 592), (1372, 615), (1347, 642), (1323, 620)],
    # [1, (627, 773), (666, 773), (666, 811), (627, 811)],
    # [1, (634, 821), (659, 820), (659, 844), (634, 844)]
    # ]

    # coords =  [
    # [0, (483, 194), (580, 205), (572, 283), (475, 272)],
    # [0, (1081, 206), (1177, 191), (1189, 264), (1092, 279)],
    # [0, (263, 582), (308, 541), (404, 648), (360, 689)],
    # [0, (611, 744), (690, 744), (690, 867), (611, 867)],
    # [0, (1383, 536), (1432, 581), (1333, 687), (1285, 641)],
    # [1, (735, 415), (792, 415), (792, 441), (735, 441)],
    # [1, (877, 411), (935, 411), (935, 445), (877, 445)],
    # ]

    coords = [
          [2, (306, 493), (328, 492), (332, 706), (309, 706)],
          [2, (1350, 432), (1382, 432), (1390, 894), (1358, 894)]
         ]


    save_master_crop(image=image, coords=coords, save_dir=save_dir, base_filename="master_feature")