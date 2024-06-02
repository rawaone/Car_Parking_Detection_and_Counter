import cv2
import pickle
import numpy as np

cap = cv2.VideoCapture('input/parking.mp4')

with open('park_positions', 'rb') as f:
    park_positions = pickle.load(f)

font = cv2.FONT_HERSHEY_COMPLEX_SMALL

# Parking space parameters
width, height = 40, 19
full = width * height
empty = 0.22

# Create a background subtractor
backSub = cv2.createBackgroundSubtractorMOG2()

def parking_space_counter(img_processed):
    global counter
    global occupied_counter  # New counter for occupied spaces

    counter = 0
    occupied_counter = 0  # Initialize the occupied counter

    for position in park_positions:
        x, y = position

        img_crop = img_processed[y:y + height, x:x + width]
        count = cv2.countNonZero(img_crop)

        ratio = count / full

        if ratio < empty:
            color = (0, 255, 0)
            counter += 1
        else:
            color = (0, 0, 255)
            occupied_counter += 1  # Increment the occupied counter

        cv2.rectangle(overlay, position, (position[0] + width, position[1] + height), color, -1)
        cv2.putText(overlay, "{:.2f}".format(ratio), (x + 4, y + height - 4), font, 0.7, (255, 255, 255), 1, cv2.LINE_AA)

while True:

    # Video looping
    if cap.get(cv2.CAP_PROP_POS_FRAMES) == cap.get(cv2.CAP_PROP_FRAME_COUNT):
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    _, frame = cap.read()
    overlay = frame.copy()

    # Frame processing
    img_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    img_blur = cv2.GaussianBlur(img_gray, (3, 3), 1)
    img_thresh = cv2.adaptiveThreshold(img_blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 16)

    parking_space_counter(img_thresh)

    # Apply background subtraction
    fgMask = backSub.apply(frame)

    # Apply morphological operations
    kernel = np.ones((5,5),np.uint8)
    fgMask = cv2.morphologyEx(fgMask, cv2.MORPH_OPEN, kernel)
    fgMask = cv2.morphologyEx(fgMask, cv2.MORPH_DILATE, kernel)

    # Find and draw contours
    contours, _ = cv2.findContours(fgMask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        (x, y, w, h) = cv2.boundingRect(contour)
        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

    alpha = 0.7
    frame_new = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

    w, h = 220, 60
    cv2.rectangle(frame_new, (0, 0), (w, h), (255, 0, 0), -1)
    cv2.putText(frame_new, f"Empty: {counter}/{len(park_positions)}", (int(w / 10), int(h * 4 / 3)), font, 2,
                (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(frame_new, f"Occupied: {occupied_counter}/{len(park_positions)}", (int(w / 10), int(h / 2)), font, 2,
                (255, 255, 255), 2, cv2.LINE_AA)

    cv2.namedWindow('frame', cv2.WINDOW_NORMAL)
    cv2.setWindowProperty('frame', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    cv2.imshow('frame', frame_new)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()