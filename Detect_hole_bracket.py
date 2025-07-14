import cv2
import numpy as np
import matplotlib.pyplot as plt
from skimage.metrics import structural_similarity
from skimage.feature import graycomatrix, graycoprops, local_binary_pattern
from skimage.measure import CircleModel, ransac
from scipy.ndimage import distance_transform_edt
import torch
import torch.nn as nn
import torchvision.transforms as transforms
import torchvision.models as models
from scipy.spatial import cKDTree
# from xgboost import XGBClassifier
from skimage import exposure
import os


device = 'cuda' if torch.cuda.is_available() else 'cpu'

# Load pretrained VGG16 model
vgg = models.vgg16(weights='DEFAULT').features
vgg.eval()  # Set model to evaluation mode



# Define a feature extractor that stops at a chosen layer (e.g., layer 16)
class VGG16_Features(nn.Module):
    def __init__(self, cutoff_layer: int):
        super(VGG16_Features, self).__init__()
        self.features = nn.Sequential(*list(vgg.children())[:cutoff_layer])

    def forward(self, x):
        return self.features(x)

# For instance, cutoff_layer = 16 captures a mid-level representation
cutoff_layer = 16
feature_extractor = VGG16_Features(cutoff_layer=cutoff_layer).to(device)
feature_extractor.eval()

# Load pretrained ResNet-50 model
resnet = models.resnet50(weights='DEFAULT').to(device)
resnet.eval()  # Set model to evaluation mode

# Define a feature extractor that stops at a chosen layer
class ResNet50_Features(nn.Module):
    def __init__(self, cutoff_layer: int):
        super(ResNet50_Features, self).__init__()
        # take the first `cutoff_layer` modules from resnet.children()
        self.features = nn.Sequential(*list(resnet.children())[:cutoff_layer])

    def forward(self, x):
        return self.features(x)

# For instance, cutoff_layer = 7 captures a mid-level representation
cutoff_layer = 9
resnet_feature_extractor = ResNet50_Features(cutoff_layer=cutoff_layer).to(device)
resnet_feature_extractor.eval()


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


def load_and_preprocess(img, transform):
    image = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    return transform(image).unsqueeze(0)  # Add batch dimension


def normalized_cross_correlation(f1, f2):
    f1 = (f1 - f1.mean()) / (f1.std() + 1e-5)
    f2 = (f2 - f2.mean()) / (f2.std() + 1e-5)
    return (f1 * f2).mean()


def DeepNCC(img1, img2, feature_extractor):

    # Define image transforms: resizing, conversion to tensor, and normalization (ImageNet stats)
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Resize((224, 224)),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],  # ImageNet means
                            std=[0.229, 0.224, 0.225])   # ImageNet stds
    ])

    img1_tensor = load_and_preprocess(img1, transform).to(device)
    img2_tensor = load_and_preprocess(img2, transform).to(device)

    with torch.no_grad():
        feat1 = feature_extractor(img1_tensor)
        feat2 = feature_extractor(img2_tensor)


    # ----- Step 3: Compute DeepNCC -----

    # Calculate the SSIM over the feature maps.
    # pytorch_msssim.ssim expects input shape [N, C, H, W]. Here, feat1 and feat2 are such tensors.
    # data_range is the difference between max and min values for normalization.
    data_range = (feat1.max() - feat1.min()).item()  # Alternatively, you may fix this if needed.

    ncc = normalized_cross_correlation(feat1, feat2)

    return ncc


# Enhance Contrast
def preprocess(img):
    img_eq = exposure.equalize_adapthist(img, clip_limit=0.0005)
    img_eq = (img_eq * 255).astype('uint8')
    sharpened = cv2.GaussianBlur(img_eq, (0, 0), 3)
    sharpened = cv2.addWeighted(img_eq, 1.5, sharpened, -0.5, 0)
    return sharpened


# Function to transform points back to original image
def transform_points_back(box_points, Minv):
    box_points = np.array(box_points, dtype="float32")  # Ensure the points are in float32
    box_points = np.column_stack((box_points, np.ones(box_points.shape[0])))  # Add a column of 1s
    original_points = np.dot(Minv, box_points.T).T  # Apply inverse transformation
    original_points /= original_points[:, 2][:, None]  # Normalize by the third column

    return original_points[:, :2]  # Return x, y coordinates


# Function to adjust rotation for points
def adjust_for_rotation(box_points, height, width, was_rotated):
    if not was_rotated:
        return box_points
    
    adjusted_points = []
    for x, y in box_points:
        adjusted_points.append([height - y - 1, x])  # Swap and adjust

    return np.array(adjusted_points, dtype="float32")


# Function to calculate translation using cross-correlation
def calculate_translation(master, target):
    result = cv2.matchTemplate(target, master, method=cv2.TM_CCORR_NORMED)
    _, _, _, max_loc = cv2.minMaxLoc(result)
    return max_loc


# Function to perform template matching
def perform_template_matching(master, aligned_image):
    result = cv2.matchTemplate(aligned_image, master, method=cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    h, w = master.shape
    return max_loc, (max_loc[0] + w, max_loc[1] + h)


# Function to calculate SSIM between the master image and the matched region in the aligned image
def calculate_ssim(master_image, test_image):

    # Ensure the matched region has the same size as the master image
    test_image_resized = cv2.resize(test_image, (master_image.shape[1], master_image.shape[0]))

    # Calculate SSIM
    score, _ = structural_similarity(master_image, test_image_resized, full=True)
    return score


# Function to compute GLCM features using an adaptive sliding window
def compute_glcm_features_with_adaptive_window(image, window_fraction=4, step_fraction=4):
    """
    Computes GLCM features using an adaptive sliding window approach.
    Parameters:
    - image: Input image (grayscale or RGB; if RGB, it will be converted to grayscale).
    - window_fraction: Fraction of the image dimensions to use as the window size.
    - step_fraction: Fraction of the image dimensions to use as the step size.
    Returns:
    - averaged_features: A list of averaged GLCM features [contrast, correlation, energy, homogeneity].
    """
    # Ensure the image is grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

    # Determine adaptive window size and step size
    h, w = gray.shape
    window_size = (h // window_fraction, w // window_fraction)
    step = (h // step_fraction, w // step_fraction)

    # Initialize a list to store features for all windows
    all_features = []

    # Sliding window iteration
    for y in range(0, gray.shape[0] - window_size[1] + 1, step[1]):
        for x in range(0, gray.shape[1] - window_size[0] + 1, step[0]):
            # Extract the current window
            window = gray[y:y+window_size[1], x:x+window_size[0]]

            # Compute GLCM for the current window
            glcm = graycomatrix(window, distances=[1], angles=[0, np.pi/4, np.pi/2, 3*np.pi/4], levels=256, symmetric=True, normed=True)

            # Extract GLCM properties for this window
            contrast = graycoprops(glcm, 'contrast').mean()
            correlation = graycoprops(glcm, 'correlation').mean()
            energy = graycoprops(glcm, 'energy').mean()
            homogeneity = graycoprops(glcm, 'homogeneity').mean()

            # Store the features for this window
            all_features.append([contrast, correlation, energy, homogeneity])

    # Average the features across all windows
    averaged_features = np.mean(all_features, axis=0)

    return averaged_features.tolist()


# Function to compute LBP features
def compute_lbp_features(image, radius=1, n_points=8):
    """
    Computes LBP features for the entire image.
    Parameters:
    - image: Input image (grayscale or RGB; if RGB, it will be converted to grayscale).
    - radius: Radius of the circular neighborhood for LBP.
    - n_points: Number of neighbors to consider.
    Returns:
    - lbp_hist: Normalized histogram of LBP codes.
    """
    # Ensure the image is grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

    # Compute the LBP
    lbp = local_binary_pattern(gray, n_points, radius, method='uniform')

    # Compute the histogram of LBP
    n_bins = int(lbp.max() + 1)
    hist, _ = np.histogram(lbp.ravel(), bins=n_bins, range=(0, n_bins))

    # Normalize the histogram
    hist = hist.astype('float')
    hist /= hist.sum()  # Normalize to sum 1

    return hist.tolist()


# Function to combine GLCM and LBP features
def extract_combined_features(image, window_fraction=4, step_fraction=8, radius=1, n_points=8):
    """
    Combines GLCM features from adaptive sliding windows with LBP features into a single feature vector.
    Parameters:
    - image: Input image.
    - window_fraction: Fraction of the image dimensions to use as the window size.
    - step_fraction: Fraction of the image dimensions to use as the step size.
    - radius: Radius of the circular neighborhood for LBP.
    - n_points: Number of neighbors for LBP.
    Returns:
    - combined_features: Normalized concatenated feature vector of GLCM and LBP features.
    """
    glcm_features = compute_glcm_features_with_adaptive_window(image)
    lbp_features = compute_lbp_features(image, radius, n_points)
    combined_features = glcm_features + lbp_features   # Combine GLCM and LBP features
    return combined_features


# Reduce GLCM matrix size
def quantize_image(image, num_levels=16):
    """
    Quantize the image into fewer intensity levels.
    Parameters:
    - image: Input grayscale image (values 0-255).
    - num_levels: Number of levels to reduce the range to.
    Returns:
    - quantized_image: Image with reduced intensity levels.
    """
    # Normalize the image to the range 0–(num_levels - 1)
    max_gray = 255
    quantized_image = (image / (max_gray / (num_levels - 1))).astype(np.uint8)
    return quantized_image


# def detect_sponge(sponge_img):
#     quantized_image = quantize_image(sponge_img, num_levels=32)
#     features = extract_combined_features(quantized_image)
#     prediction = loaded_model.predict([features])

#     if not prediction:
#         return 'Defective'
#     elif prediction:
#         return 'Not Defective'
    

def compute_ncc_with_clahe(master_image, test_image):
    """
    Computes normalized cross-correlation between a master image (template)
    and a test image (subject) after applying CLAHE to the test image.
    Parameters:
        master_image (numpy.ndarray): The template image (can be color or grayscale).
        test_image (numpy.ndarray): The image to test (can be color or grayscale).
    Returns:
        max_val (float): Maximum normalized cross-correlation value.
        max_loc (tuple): Location (x, y) of the best match in the test image.
        result (numpy.ndarray): The full normalized cross-correlation result map.
    """

    # Convert master image to grayscale if needed.
    if len(master_image.shape) == 3:
        master_gray = cv2.cvtColor(master_image, cv2.COLOR_BGR2GRAY)
    else:
        master_gray = master_image.copy()

    # Convert test image to grayscale if needed.
    if len(test_image.shape) == 3:
        test_gray = cv2.cvtColor(test_image, cv2.COLOR_BGR2GRAY)
    else:
        test_gray = test_image.copy()

    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to the test image.
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    test_clahe = clahe.apply(test_gray)

    # Perform normalized cross-correlation using the master image as the template.
    # Note: cv2.matchTemplate expects the template to be smaller than or equal to the test image.
    result = cv2.matchTemplate(test_clahe, master_gray, cv2.TM_CCOEFF_NORMED)

    # Find the best match location and the corresponding correlation value.
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    return max_val, max_loc, result
    

def detect_holes(edges):
    img_height, img_width = edges.shape[:2]
    # Find contours in the edge image.
    contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # print(len(contours))

    # Array to store good circles.
    # Each circle is stored as (center_x, center_y, radius, fitness_score)
    good_circles = []
    skip_indices = set()

    # Set a fitness threshold (in pixels) for a circle to be considered a good fit.
    fitness_threshold = 2.0  # Adjust based on your image resolution and expected noise

    # Angular coverage threshold: at least 80% of 2π radians.
    min_coverage = 0.8 * 2 * np.pi  # ~5.03 radians

    # Loop through each contour.
    for i, cnt in enumerate(contours):

        # Skip if this contour index is marked for removal.
        if i in skip_indices:
            continue

        area = cv2.contourArea(cnt)
        # Skip very small contours that are unlikely to form a circle.
        if len(cnt) < 5 and area < 500:
            continue

        # Reshape the contour points from (N, 1, 2) to (N, 2)
        points = cnt.reshape(-1, 2)

        # Ensure there are enough points to fit a circle (CircleModel requires at least 3)
        if points.shape[0] < 3:
            continue

        try:
            # Use RANSAC to robustly fit a circle to the contour's points.
            # min_samples=3 means RANSAC uses 3 random points per trial.
            # residual_threshold defines the maximum allowed distance for a point to be considered an inlier.
            model_robust, inliers = ransac(points, CircleModel,
                                          min_samples=3,
                                          residual_threshold=50.0,
                                          max_trials=15000)
        except Exception as e:
            # If RANSAC fails for any reason, skip this contour.
            continue

        # If no model was found, skip to the next contour.
        if model_robust is None:
            continue

        # Extract circle parameters: (center_x, center_y, radius)
        xc, yc, r = model_robust.params

        # Calculate the fitness score:
        # For each point in the contour, compute the absolute difference between its distance to (xc, yc) and the radius.
        distances = np.sqrt((points[:, 0] - xc)**2 + (points[:, 1] - yc)**2)
        residuals = np.abs(distances - r)
        mean_residual = np.mean(residuals)

        # If the mean residual (fitness score) is below the threshold, accept this circle.
        if mean_residual > fitness_threshold:
            continue

        # Discard circles with center outside the image area.
        if not (0 <= xc < img_width and 0 <= yc < img_height):
            continue

        # Discard circles with diameter bigger than the image.
        if (2 * r > img_width) or (2 * r > img_height):
            continue

        # --- New: Check for angular coverage of inlier points ---
        # Use only inlier points from RANSAC to compute angular distribution.
        inlier_points = points[inliers]
        if inlier_points.shape[0] < 3:
            continue  # Not enough inliers for a meaningful coverage

        # Compute angles (in radians) of each inlier point relative to the circle's center.
        angles = np.arctan2(inlier_points[:, 1] - yc, inlier_points[:, 0] - xc)
        # Map angles to [0, 2π]
        angles = np.mod(angles, 2 * np.pi)
        # Sort the angles.
        angles_sorted = np.sort(angles)

        # Compute differences between successive angles.
        angle_diffs = np.diff(angles_sorted)
        # Also consider the gap between the last and first angle (with wrap-around).
        wrap_diff = (2 * np.pi + angles_sorted[0]) - angles_sorted[-1]
        max_gap = max(np.max(angle_diffs), wrap_diff)
        # Coverage is the complement of the largest gap.
        coverage = 2 * np.pi - max_gap

        # Accept the circle only if the inlier points cover at least 80% of the circumference.
        if coverage < min_coverage:
            continue
        # --- End angular coverage check ---

        if r<5:
            continue

        good_circles.append((xc, yc, r))

        # --- Remove child contours ---
        # hierarchy[i][2] gives the first child of the i-th contour.
        child_idx = hierarchy[0][i][2]
        while child_idx != -1:
            # Mark this child contour to be skipped.
            skip_indices.add(child_idx)
            # Move to the next sibling: hierarchy[child_idx][0] gives the next contour at the same level.
            child_idx = hierarchy[0][child_idx][0]
        # --- End Remove child contours ---

    # Now, good_circles holds the circles that fit well according to the fitness score.
    # print("Good circles found:", len(good_circles))

    # # Visualization: draw the accepted circles on the image.
    # output_img = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    # for (xc, yc, r) in good_circles:
    #     center = (int(xc), int(yc))
    #     radius = int(r)
    #     print(f"radius: {radius}")
    #     # Draw the circle outline (green) and its center (red)
    #     cv2.circle(output_img, center, radius, (0, 255, 0), 1)
    #     cv2.circle(output_img, center, 2, (0, 0, 255), 1)

    # plt.figure(figsize=(8, 8))
    # plt.imshow(output_img)
    # plt.title("Good-Fit Circles via RANSAC on Contours")
    # plt.axis('off')
    # plt.show()

    return good_circles


def chamfer_distance(edges1, edges2):
    """
    Computes the symmetric chamfer distance between two binary edge images.
    
    Parameters:
        edges1 (np.ndarray): First binary edge image.
        edges2 (np.ndarray): Second binary edge image.
    
    Returns:
        float: The symmetric chamfer distance.
    """
    # Convert input images to boolean type in case they aren't already
    edges1 = np.asarray(edges1, dtype=bool)
    edges2 = np.asarray(edges2, dtype=bool)
    
    # Compute the distance transform for the complement of the edge images
    # The distance transform computes the distance from each pixel to the nearest zero pixel.
    dt_edges1 = distance_transform_edt(~edges1)
    dt_edges2 = distance_transform_edt(~edges2)
    
    # Compute the average distance from edge pixels in one image to the other.
    # Use np.any to check that there is at least one edge pixel.
    d1 = np.mean(dt_edges2[edges1]) if np.any(edges1) else 0.0
    d2 = np.mean(dt_edges1[edges2]) if np.any(edges2) else 0.0
    
    # The symmetric chamfer distance is the average of the two directional distances.
    chamfer = (d1 + d2) / 2.0
    return chamfer


def iou_edge_images(edges1, edges2):
    """
    Compute the Intersection-over-Union (IoU) between two binary edge images.
    
    Parameters:
        edges1 (np.ndarray): First binary edge image.
        edges2 (np.ndarray): Second binary edge image.
    
    Returns:
        float: The IoU value. If both images contain no edges, returns 1.0.
    """
    # Convert inputs to boolean arrays (ensuring True for edges, False otherwise)
    edges1_bool = np.asarray(edges1, dtype=bool)
    edges2_bool = np.asarray(edges2, dtype=bool)
    
    # Calculate the intersection (common edge pixels)
    intersection = np.logical_and(edges1_bool, edges2_bool).sum()
    
    # Calculate the union (all edge pixels in either image)
    union = np.logical_or(edges1_bool, edges2_bool).sum()
    
    # Handle the edge case where there are no edges in both images.
    if union == 0:
        return 1.0  # Both images have no edges, so they match perfectly.
    
    # IoU is the ratio between the intersection and the union.
    return intersection / union


def plot_ssim_difference(img1: np.array, img2: np.array,
                         *, as_gray: bool = True, invert: bool = True) -> None:
    """
    Display Image 1, Image 2, and an SSIM‑based difference map.
    Parameters
    ----------
    img1_path, img2_path : str
        Paths to the two images. They MUST have identical height/width.
    as_gray : bool, default True
        Read images in grayscale. Set to False for colour, but note that SSIM
        is usually defined on luminance.
    invert : bool, default True
        If True, darker pixels in the diff map mean bigger differences
        (i.e. show 1 – SSIM instead of SSIM).
    """
    # 1 · Load images
    if img1.shape != img2.shape:
        raise ValueError("Input images must have the same shape")

    # 2 · Compute SSIM
    score, ssim_map = structural_similarity(img1, img2, full=True)

    # 3 · Turn similarity into a visual “difference” map
    diff = 1 - ssim_map if invert else ssim_map            # [0, 1]
    diff_img = (diff * 255).astype(np.uint8)               # uint8 for crisper display

    thresh = cv2.threshold(diff_img, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    thresh = cv2.bitwise_not(thresh)

    contours = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = contours[0] if len(contours) == 2 else contours[1]

    mask = np.zeros(img1.shape, dtype='uint8')
    filled_after = img2.copy()

    before = cv2.cvtColor(img1.copy(), cv2.COLOR_GRAY2BGR)
    after = cv2.cvtColor(img2.copy(), cv2.COLOR_GRAY2BGR)

    for c in contours:
        area = cv2.contourArea(c)
        if area > 10000:
            # print(area)
            x,y,w,h = cv2.boundingRect(c)
            cv2.rectangle(before, (x, y), (x + w, y + h), (36,255,12), 2)
            cv2.rectangle(after, (x, y), (x + w, y + h), (36,255,12), 2)
            # cv2.rectangle(diff_box, (x, y), (x + w, y + h), (36,255,12), 2)
            cv2.drawContours(mask, [c], 0, (255,255,255), -1)
            cv2.drawContours(filled_after, [c], 0, (0,255,0), -1)

    # # 4 · Plot
    # fig, axes = plt.subplots(1, 5, figsize=(13, 4))
    # titles = [f"Difference map\nSSIM = {score:.4f}", "Before", "After", "Mask", "Filled After"]
    # for ax, im, title in zip(axes, [diff_img, thresh, after, mask, filled_after], titles):
    #     ax.imshow(im, cmap='gray')
    #     ax.set_title(title)
    #     ax.axis('off')

    # plt.tight_layout()
    # plt.show()

    return mask


def ellipse_fit_error(contour, ellipse):
    # ellipse = ((cx,cy),(major,minor),angle_deg)
    (cx, cy), (major, minor), angle = ellipse
    a, b = major/2, minor/2
    θ = np.deg2rad(angle)
    cos, sin = np.cos(θ), np.sin(θ)
    
    # shift and rotate
    pts = contour[:,0,:].astype(np.float32)
    x = pts[:,0] - cx
    y = pts[:,1] - cy
    u =  ( x * cos + y * sin) / a
    v = ( -x * sin + y * cos) / b
    
    errs = np.abs(np.sqrt(u*u + v*v) - 1.0)
    return np.mean(errs), np.max(errs)


def detect_and_draw_ellipses(
    binary_img,
    image_to_draw=None,
    min_contour_area: float = 100.0,
    max_contour_area: float = 500.0,
    min_ellipse_area: float = 50.0,
    max_ellipse_area: float = 10000.0,
    max_axis_ratio: float = 5.0,
    font_scale: float = 0.5,
    thickness: int = 1
):
    """
    Detect ellipses in a binary image, draw them, and label each with its area.
    
    Returns
    -------
    ellipses : List[tuple]
        Each ellipse is ((cx, cy), (major_axis, minor_axis), angle_deg).
    image_rgb : np.ndarray
        RGB image with ellipses drawn in blue and area labels in white.
    """
    # Prepare an RGB copy for drawing
    if image_to_draw is None:
        image_to_draw = cv2.cvtColor(binary_img, cv2.COLOR_GRAY2BGR)

    image_to_draw = cv2.cvtColor(image_to_draw.copy(), cv2.COLOR_GRAY2BGR) if len(image_to_draw.shape)<3 else image_to_draw

    contours, _ = cv2.findContours(
        binary_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE
    )
    ellipses = []

    for cnt in contours:
        if len(cnt) < 5:
            continue

        area = cv2.contourArea(cnt)
        if area < min_contour_area or area > max_contour_area:
            continue

        ellipse = cv2.fitEllipse(cnt)
        (center, axes, angle) = ellipse
        major, minor = axes

        # true geometric area of the ellipse
        ellipse_area = np.pi * (major / 2) * (minor / 2)
        if ellipse_area < min_ellipse_area or ellipse_area > max_ellipse_area:
            continue

        axis_ratio = max(major, minor) / (min(major, minor) + 1e-6)
        if axis_ratio > max_axis_ratio:
            continue

        mean_err, max_err = ellipse_fit_error(cnt, ellipse)
        ellipse_area = np.pi*(major/2)*(minor/2)
        ratio = cv2.contourArea(cnt) / ellipse_area

        # print(f"mean_err: {mean_err}, max_err:{max_err}")
        # print(f"ratio: {ratio}")

        if mean_err > 0.05 or max_err > 0.1:
            continue
        if not (0.96 < ratio < 1.15):
            continue

        # accept and draw the ellipse
        ellipses.append(ellipse)
        cv2.ellipse(image_to_draw, ellipse, (0, 255, 0), 2)

        # prepare and draw the area label
        cx, cy = map(int, center)
        label = f"{ellipse_area:.1f}"
        # compute text size so we can center it
        (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
        text_origin = (cx - w//2, cy + h//2)
        cv2.putText(
            image_to_draw, label, text_origin,
            cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0,255,0), thickness, cv2.LINE_AA
        )

    # convert to RGB for display
    image_rgb = cv2.cvtColor(image_to_draw, cv2.COLOR_BGR2RGB)
    return ellipses, image_rgb

    
def detect_defect(master_image, target_image, analysis_type,
                  feature_extractor=feature_extractor, ssim_thresh=0.60,
                  nnc_thresh=0.50, hausdorff_dist_thresh=100,
                  identity_score_thresh=0.5, iou_thresh=0.5,
                  chamfer_thresh=25.0):

    defect = ""

    if analysis_type==0:


        ### Contour Analysis ###

        # Calculate SSIM for the matched region
        ssim_score = calculate_ssim(master_image, target_image)
        nnc_score, _, _ = compute_ncc_with_clahe(master_image, target_image)


        # Check if the target_image has similar structure as master
        if ssim_score <= ssim_thresh and nnc_score<=nnc_thresh:
            print('SSIM Bracket')
            defect = "Bracket Absent/Wrong Orientation"
            return "Defective", defect



        # 1) Create a CLAHE object (you can tune clipLimit and tileGridSize)
        clahe_1 = cv2.createCLAHE(clipLimit=1.0, tileGridSize=(3,3))
        master_clahe_result = clahe_1.apply(master_image)
        target_clahe_result = clahe_1.apply(target_image)



        master_bilateral_filtered = cv2.bilateralFilter(master_clahe_result, d=9, sigmaColor=45, sigmaSpace=45)
        target_bilateral_filtered = cv2.bilateralFilter(target_clahe_result, d=9, sigmaColor=45, sigmaSpace=45)

        # Apply Non-Local Means Denoising.
        master_denoised = cv2.fastNlMeansDenoising(master_bilateral_filtered, None, h=10, templateWindowSize=7, searchWindowSize=51)
        target_denoised = cv2.fastNlMeansDenoising(target_bilateral_filtered, None, h=10, templateWindowSize=7, searchWindowSize=51)


        resized_master = cv2.resize(master_denoised, (0, 0), fx=10, fy=10, interpolation=cv2.INTER_CUBIC)
        resized_target = cv2.resize(target_denoised, (0, 0), fx=10, fy=10, interpolation=cv2.INTER_CUBIC)

        resized_master_2 = cv2.resize(master_image, (0, 0), fx=10, fy=10, interpolation=cv2.INTER_CUBIC)
        resized_target_2 = cv2.resize(target_image, (0, 0), fx=10, fy=10, interpolation=cv2.INTER_CUBIC)

        sharpened_master = cv2.GaussianBlur(resized_master_2, (0, 0), 3)
        sharpened_master = cv2.addWeighted(resized_master_2, 1.5, sharpened_master, -0.5, 0)

        sharpened_target = cv2.GaussianBlur(resized_target_2, (0, 0), 3)
        sharpened_target = cv2.addWeighted(resized_target_2, 1.5, sharpened_target, -0.5, 0)

        master_thr = cv2.threshold(resized_master_2, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        target_thr = cv2.threshold(resized_target_2, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

        master_edge = cv2.Canny(master_thr, 50, 180)
        target_edge = cv2.Canny(target_thr, 50, 180)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (49, 49))
        master_edges_dilated = cv2.dilate(master_edge,kernel,iterations = 1)
        target_edges_dilated = cv2.dilate(target_edge,kernel,iterations = 1)

        chamfer_score = chamfer_distance(master_edges_dilated, target_edges_dilated)

        iou_score = iou_edge_images(master_edges_dilated, target_edges_dilated)

        # Check if the matched_region has similar structure as master
        if round(iou_score)<iou_thresh and round(chamfer_score)>chamfer_thresh:
            print('IoU_Score & Chmafer_Score Bracket')
            defect = "Bracket Hole Absent/ Wrong Orientation"
            return "Defective", defect

        # identity_score = DeepNCC(resized_master, resized_target, feature_extractor)
        resnet_identity_score = DeepNCC(sharpened_master, sharpened_target, resnet_feature_extractor)
        # print(identity_score.item())

        # # Check if the matched_region has similar structure as master
        # if identity_score.item()<identity_score_thresh:
        #     print('Identity')
        #     return "Defective"

        # Check if the matched_region has similar structure as master
        if resnet_identity_score.item()<0.6:
            print('Resnet Identity')
            defect = "Bracket Hole Absent/ Wrong Orientation"
            return "Defective", defect

        mask = plot_ssim_difference(resized_master, resized_target)
        ellipses, image_rgb = detect_and_draw_ellipses(mask, resized_master, min_contour_area=10000, max_contour_area=100000, min_ellipse_area=13000, max_ellipse_area=100000)

        # plt.figure(figsize=(8, 8))
        # plt.imshow(image_rgb)
        # plt.title('Master Edges')
        # plt.axis('on')
        # plt.show()

        if len(ellipses) > 0:
            print('Bracket Holes')
            defect = "Bracket Hole Absent"
            return "Defective", defect


    elif analysis_type==1:
        ### Hole Analysis ###

        # Calculate SSIM for the matched region
        ssim_score = calculate_ssim(master_image, target_image)

        # Check if the target_image has similar structure as master
        if ssim_score <= 0.52:
            print('SSIM Hole')
            defect = "Hole Absent"
            return "Defective", defect

        # 1) Create a CLAHE object (you can tune clipLimit and tileGridSize)
        clahe_1 = cv2.createCLAHE(clipLimit=1.0, tileGridSize=(3,3))
        master_clahe_result = clahe_1.apply(master_image)
        target_clahe_result = clahe_1.apply(target_image)

        master_bilateral_filtered = cv2.bilateralFilter(master_clahe_result, d=9, sigmaColor=45, sigmaSpace=45)
        target_bilateral_filtered = cv2.bilateralFilter(target_clahe_result, d=9, sigmaColor=45, sigmaSpace=45)

        # Apply Non-Local Means Denoising.
        master_denoised = cv2.fastNlMeansDenoising(master_bilateral_filtered, None, h=10, templateWindowSize=7, searchWindowSize=51)
        target_denoised = cv2.fastNlMeansDenoising(target_bilateral_filtered, None, h=10, templateWindowSize=7, searchWindowSize=51)


        resized_master = cv2.resize(master_denoised, (0, 0), fx=10, fy=10, interpolation=cv2.INTER_CUBIC)
        resized_target = cv2.resize(target_denoised, (0, 0), fx=10, fy=10, interpolation=cv2.INTER_CUBIC)

        resized_master_2 = cv2.resize(master_image, (0, 0), fx=10, fy=10, interpolation=cv2.INTER_CUBIC)
        resized_target_2 = cv2.resize(target_image, (0, 0), fx=10, fy=10, interpolation=cv2.INTER_CUBIC)

        sharpened_master = cv2.GaussianBlur(resized_master_2, (0, 0), 3)
        sharpened_master = cv2.addWeighted(resized_master_2, 1.5, sharpened_master, -0.5, 0)

        sharpened_target = cv2.GaussianBlur(resized_target_2, (0, 0), 3)
        sharpened_target = cv2.addWeighted(resized_target_2, 1.5, sharpened_target, -0.5, 0)

        master_thr = cv2.threshold(resized_master_2, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        target_thr = cv2.threshold(resized_target_2, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

        master_edge = cv2.Canny(master_thr, 50, 180)
        target_edge = cv2.Canny(target_thr, 50, 180)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (49, 49))
        master_edges_dilated = cv2.dilate(master_edge,kernel,iterations = 1)
        target_edges_dilated = cv2.dilate(target_edge,kernel,iterations = 1)

        chamfer_score = chamfer_distance(master_edges_dilated, target_edges_dilated)

        iou_score = iou_edge_images(master_edges_dilated, target_edges_dilated)

        # Check if the matched_region has similar structure as master
        if iou_score<0.6 and chamfer_score>10.0:
            print('IoU_Score & Chmafer_Score')
            defect = "Hole Absent"
            return "Defective", defect

        # identity_score = DeepNCC(resized_master, resized_target, feature_extractor)
        resnet_identity_score = DeepNCC(sharpened_master, sharpened_target, resnet_feature_extractor)
        # print(identity_score.item())

        # # Check if the matched_region has similar structure as master
        # if identity_score.item()<identity_score_thresh:
        #     print('Identity')
        #     return "Defective"

        # Check if the matched_region has similar structure as master
        if resnet_identity_score.item()<0.6:
            print('Resnet Identity')
            defect = "Hole Absent"
            return "Defective", defect


    elif analysis_type==2:
        ### Texture Analysis ###
        # Calculate SSIM for the matched region
        ssim_score_sponge = calculate_ssim(master_image, target_image)
        # print(ssim_score_sponge)
        # nnc_score, _, _ = compute_ncc_with_clahe(master_image, target_image)


        # Check if the target_image has similar structure as master
        if ssim_score_sponge <= 0.55:
            print('SSIM_Sponge')
            defect = "Foam Absent"
            return "Defective", defect


        # 1) Create a CLAHE object (you can tune clipLimit and tileGridSize)
        clahe_1 = cv2.createCLAHE(clipLimit=1.0, tileGridSize=(3,3))
        master_clahe_result = clahe_1.apply(master_image)
        target_clahe_result = clahe_1.apply(target_image)

        master_bilateral_filtered = cv2.bilateralFilter(master_clahe_result, d=9, sigmaColor=45, sigmaSpace=45)
        target_bilateral_filtered = cv2.bilateralFilter(target_clahe_result, d=9, sigmaColor=45, sigmaSpace=45)

        # Apply Non-Local Means Denoising.
        master_denoised = cv2.fastNlMeansDenoising(master_bilateral_filtered, None, h=10, templateWindowSize=7, searchWindowSize=51)
        target_denoised = cv2.fastNlMeansDenoising(target_bilateral_filtered, None, h=10, templateWindowSize=7, searchWindowSize=51)


        resized_master = cv2.resize(master_denoised, (0, 0), fx=10, fy=10, interpolation=cv2.INTER_CUBIC)
        resized_target = cv2.resize(target_denoised, (0, 0), fx=10, fy=10, interpolation=cv2.INTER_CUBIC)

        resized_master_2 = cv2.resize(master_image, (0, 0), fx=10, fy=10, interpolation=cv2.INTER_CUBIC)
        resized_target_2 = cv2.resize(target_image, (0, 0), fx=10, fy=10, interpolation=cv2.INTER_CUBIC)

        sharpened_master = cv2.GaussianBlur(resized_master_2, (0, 0), 3)
        sharpened_master = cv2.addWeighted(resized_master_2, 1.5, sharpened_master, -0.5, 0)

        sharpened_target = cv2.GaussianBlur(resized_target_2, (0, 0), 3)
        sharpened_target = cv2.addWeighted(resized_target_2, 1.5, sharpened_target, -0.5, 0)

        resnet_identity_score = DeepNCC(sharpened_master, sharpened_target, resnet_feature_extractor)
        # print(identity_score.item())

        # # Check if the matched_region has similar structure as master
        # if identity_score.item()<identity_score_thresh:
        #     print('Identity')
        #     return "Defective"



        # Check if the matched_region has similar structure as master
        if resnet_identity_score.item()<0.6:
            print('Resnet Identity')
            defect = "Foam Absent"
            return "Defective", defect


    return "Not Defective", None


# Function to calculate center point of a box
def calculate_center(box):
    x_coords = [box[1], box[3], box[5], box[7]]
    y_coords = [box[2], box[4], box[6], box[8]]
    x_center = sum(x_coords) / 4
    y_center = sum(y_coords) / 4
    return x_center, y_center


def main(image, master_crop_path, coords):

    m_dta = np.array([x[0] for x in coords]).reshape(len(coords), 1)
    coords = [x[1:] for x in coords]

    flattened_coords = np.array([[value for tup in l for value in tup] for l in coords])
    data = np.hstack((m_dta, flattened_coords))
    
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


    # Calculate centers and sort data
    centers = [calculate_center(row) for row in data]
    data_with_centers = [(row, center) for row, center in zip(data, centers)]
    sorted_data_with_centers = sorted(data_with_centers, key=lambda x: (int(x[1][1] + x[1][0]), x[1][1], x[1][0]))  # Sort by y, then x

    # Extract sorted data
    sorted_data = np.array([row for row, center in sorted_data_with_centers])

    # Analysis Type of each bounding box
    meta_data = sorted_data[:, 0]


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

        c_padding = 40

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

    ### Draw ROI
    # _ = warped.copy()
    # for c_obb in child_obb:

    #     # Draw the rectangle on the image
    #     cv2.drawContours(_, [c_obb], 0, (0, 0, 255), 2)

    # cv2.imshow('ROI', _)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()


    img = image.copy()
    defects = []
    stat = [0] * len(child_roi)
    for i in range(len(child_roi)):
        color  = (0, 255, 0)
        master_path = os.path.join(master_crop_path, f"master_feature_{i+1}.png")

        master_img = cv2.imread(master_path)
        roi = child_roi[i]
        analysis_type = meta_data[i]

        # Read images in grayscale
        master_image = cv2.cvtColor(master_img, cv2.COLOR_BGR2GRAY)
        second_image = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        # Align the second image
        translation = calculate_translation(master_image, second_image)
        # aligned_image = align_image(second_image, translation)

        # Perform template matching
        top_left, bottom_right = perform_template_matching(master_image, second_image)

        # Visualize results
        matched_image = second_image.copy()

        # Template size from the master image
        template_size = master_image.shape

        # Visualize the matched region
        matched_region = second_image[top_left[1]:top_left[1]+template_size[0], top_left[0]:top_left[0]+template_size[1]]

        res, text = detect_defect(master_image, matched_region, analysis_type, feature_extractor)

        defects.append(text)

        if res == 'Defective':
            color = (0, 0, 255)
            stat[i] = 1

        elif res == 'Not Defective':
            color = (0, 255, 0)


        # # Draw the rectangle on the image
        # cv2.drawContours(img, [child_obb[i]], 0, color, 2)

        Minv = np.linalg.inv(M)

        adjusted_box = adjust_for_rotation(child_obb[i], height, width, was_rotated=False)
        original_box = transform_points_back(adjusted_box, Minv)
        original_box = original_box.astype(int)  # Convert coordinates to integers
        cv2.drawContours(img, [original_box], -1, color, 2)

        if text is not None:

            # Define the main text and its properties
            main_text = text
            main_font_face = cv2.FONT_HERSHEY_SIMPLEX
            main_font_scale = 0.7
            main_thickness = 1

            # Define the position and rotation of the main text
            pts = original_box.reshape(4,2)
            top2_idx = np.argsort(pts[:,1])[:2]
            pt1, pt2 = pts[top2_idx][np.argsort(pts[top2_idx][:,0])]
            mid_x, mid_y = np.mean([pt1, pt2], axis=0).astype(int)
            dx, dy = pt2 - pt1
            main_x, main_y = int(pt1[0]), int(pt1[1])
            angle_rad = np.arctan2(dy, dx)
            
            if angle_rad < 0:
                angle_rad += 2*np.pi
            main_rotation = np.degrees(angle_rad)

            if np.abs(main_rotation)>90:
                main_rotation-=360

            main_rotation *= -1

            # Calculate the size and baseline of the main text
            main_text_size, _ = cv2.getTextSize(main_text, main_font_face, main_font_scale, main_thickness)


            # Calculate the rotation matrix for the main text
            main_rotation_matrix = cv2.getRotationMatrix2D((main_x, main_y), main_rotation, 1)

            # Create a black image with the same size as the input image
            text_img = np.zeros((img.shape[0], img.shape[1]))


            # Add the main text to the text image with rotation
            cv2.putText(text_img, main_text, (main_x, main_y), main_font_face, main_font_scale, (255, 255, 255), main_thickness, cv2.LINE_AA)
            rotated_text_img = cv2.warpAffine(text_img, main_rotation_matrix, (img.shape[1], img.shape[0]))

            # Overlay the rotated main text on the input image
            img[rotated_text_img!=0] = (0, 0, 255)

    if any(stat):
        rslt = 'Not OK'
        ob_color = (0, 0, 255)

    elif not all(stat):
        rslt = 'OK'
        ob_color = (0, 255, 0)

    cv2.drawContours(img, [box], -1, ob_color, 2)

    return img, rslt, defects

if __name__=="__main__":
    # Load Image
    img_path = '/Users/abhi/Desktop/Augle AI/Duct Defect Detection/Code/defective_part_one/image0000073.jpg'
    image = cv2.imread(img_path)

    # # Load the model from XGBoost's JSON file
    # loaded_model = XGBClassifier()
    # loaded_model.load_model('/Users/abhi/Desktop/Augle AI/Duct Defect Detection/Code/Sponge Models/xgboost_sponge_model.json')

    # Get the ROI Bounding Box for Master
    # BoundingBox_Coordinates_path = "/Users/abhi/Desktop/Augle AI/Duct Defect Detection/Code/C_box_tight.txt"  # Replace with your file path
    # data = np.loadtxt(BoundingBox_Coordinates_path)

    # Path to Master cropped region
    master_crop_path = '/Users/abhi/Desktop/Augle AI/Duct Defect Detection/Code/Master_Extracted_Test'

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

    coords =  [
    [0, (483, 194), (580, 205), (572, 283), (475, 272)],
    [0, (1081, 206), (1177, 191), (1189, 264), (1092, 279)],
    [0, (263, 582), (308, 541), (404, 648), (360, 689)],
    [0, (611, 744), (690, 744), (690, 867), (611, 867)],
    [0, (1383, 536), (1432, 581), (1333, 687), (1285, 641)],
    [1, (735, 415), (792, 415), (792, 441), (735, 441)],
    [1, (877, 411), (935, 411), (935, 445), (877, 445)],
    ]
    
    img, rslt, defects = main(image=image, master_crop_path=master_crop_path, coords=coords)

    plt.figure(figsize=(8, 8))
    plt.imshow(img)
    plt.title('Final Result')
    plt.axis('on')
    plt.show()