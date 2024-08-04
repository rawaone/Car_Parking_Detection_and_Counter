import cv2
import pickle
import numpy as np

cap = cv2.VideoCapture('input/parking.mp4')

# Load parking positions
with open('park_positions', 'rb') as f:
    park_positions = pickle.load(f)

font = cv2.FONT_HERSHEY_COMPLEX_SMALL

# Parking space parameters
width, height = 40, 19
full = width * height
empty = 0.22

# Create a background subtractor
backSub = cv2.createBackgroundSubtractorMOG2()

# Define colors for visualization
green = (0, 255, 0)
red = (0, 0, 255)
blue = (255, 0, 0)

# Define ROI coordinates (example coordinates, adjust based on the parking area)
roi_corners = np.array([[(1735, 17), (1731, 1023), (48, 1050), (67, 650), (672, 407), (1098, 9)]], dtype=np.int32)

# Function to draw a line from a point to a parking spot
def draw_line(image, start_point, end_point, color=(255, 0, 0), thickness=2):
    cv2.line(image, start_point, end_point, color, thickness)

def parking_space_counter(img_processed):
    global counter, occupied_counter, empty_spaces
    counter = 0
    occupied_counter = 0
    empty_spaces = []

    for i, position in enumerate(park_positions):
        x, y = position

        img_crop = img_processed[y:y + height, x:x + width]
        count = cv2.countNonZero(img_crop)

        ratio = count / full

        if ratio < empty:
            color = green
            counter += 1
            empty_spaces.append(i)  # Add the index of the empty space
        else:
            color = red
            occupied_counter += 1

        cv2.rectangle(overlay, position, (position[0] + width, position[1] + height), color, -1)
        cv2.putText(overlay, "{:.2f}".format(ratio), (x + 4, y + height - 4), font, 0.7, (255, 255, 255), 1, cv2.LINE_AA)

    return empty_spaces

while True:
    if cap.get(cv2.CAP_PROP_POS_FRAMES) == cap.get(cv2.CAP_PROP_FRAME_COUNT):
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    ret, frame = cap.read()
    if not ret:
        break

    overlay = frame.copy()

    # Frame processing
    img_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    img_blur = cv2.GaussianBlur(img_gray, (3, 3), 1)
    img_thresh = cv2.adaptiveThreshold(img_blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 16)

    empty_spaces = parking_space_counter(img_thresh)

    # Apply background subtraction
    fgMask = backSub.apply(frame)

    # Apply morphological operations
    kernel = np.ones((5, 5), np.uint8)
    fgMask = cv2.morphologyEx(fgMask, cv2.MORPH_OPEN, kernel)
    fgMask = cv2.morphologyEx(fgMask, cv2.MORPH_DILATE, kernel)

    # Find contours
    contours, _ = cv2.findContours(fgMask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Create mask for ROI
    mask = np.zeros_like(frame, dtype=np.uint8)
    cv2.fillPoly(mask, roi_corners, (255, 255, 255))
    mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)

    for contour in contours:
        (x, y, w, h) = cv2.boundingRect(contour)
        if cv2.contourArea(contour) < 500:  # Ignore small contours that may not be cars
            continue
        car_center = (x + w // 2, y + h // 2)

        # Check if car center is inside ROI
        if mask[car_center[1], car_center[0]] == 0:
            continue

        cv2.rectangle(frame, (x, y), (x + w, y + h), blue, 2)

        # Find the closest empty parking spot
        if empty_spaces:
            closest_spot = min(empty_spaces, key=lambda i: np.linalg.norm(np.array(park_positions[i]) - np.array(car_center)))
            closest_spot_position = park_positions[closest_spot]

            # Draw a line from the car center to the closest spot
            draw_line(frame, car_center, closest_spot_position, green, 3)

    alpha = 0.7
    frame_new = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

    w, h = 500, 130
    cv2.rectangle(frame_new, (0, 0), (w, h), (255, 0, 0), -1)
    cv2.putText(frame_new, f"Empty: {counter}/{len(park_positions)}", (int(w / 10), int(h * 4 / 5)), font, 2,
                (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(frame_new, f"Occupied: {occupied_counter}/{len(park_positions)}", (int(w / 10), int(h / 3)), font, 2,
                (255, 255, 255), 2, cv2.LINE_AA)

    cv2.namedWindow('frame', cv2.WINDOW_NORMAL)
    cv2.setWindowProperty('frame', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    cv2.imshow('frame', frame_new)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()


