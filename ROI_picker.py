import cv2
import numpy as np
import pickle

# Initialize list to store points
roi_points = []

# Mouse callback function to select points
def select_point(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        roi_points.append((x, y))
        cv2.circle(image_display, (x, y), 5, (0, 255, 0), -1)
        cv2.imshow('Select ROI', image_display)

# Load image
image_path = 'input/parking.png'  # Adjust the path to your image file
image = cv2.imread(image_path)

# Resize image for display if it's too large
max_dimension = 1000  # Maximum dimension to fit within the screen
height, width = image.shape[:2]

if height > max_dimension or width > max_dimension:
    scaling_factor = max_dimension / float(max(height, width))
    image_display = cv2.resize(image, None, fx=scaling_factor, fy=scaling_factor, interpolation=cv2.INTER_AREA)
else:
    image_display = image.copy()

# Set up window and callback
cv2.namedWindow('Select ROI', cv2.WINDOW_NORMAL)
cv2.imshow('Select ROI', image_display)
cv2.setMouseCallback('Select ROI', select_point)

print("Click to select points for ROI. Press 'q' to quit and finish.")

while True:
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):  # Press 'q' to finish selecting points
        break

cv2.destroyAllWindows()

# Display selected points
print("Selected ROI points:", roi_points)

# Optional: Save points to file for later use
with open('roi_points.pkl', 'wb') as f:
    pickle.dump(roi_points, f)

# Convert points to numpy array for further processing
roi_corners = np.array([roi_points], dtype=np.int32)

# If you want to see the selected ROI in the original image
if height > max_dimension or width > max_dimension:
    roi_points_original = [(int(x / scaling_factor), int(y / scaling_factor)) for x, y in roi_points]
else:
    roi_points_original = roi_points

print("ROI points in original image:", roi_points_original)
