import cv2
import numpy as np
import os
import datetime

cap = cv2.VideoCapture(0)

CLASSES = {
    '1' : ('glass',    "../data/glass/"),
    '2' : ('metal',   "../data/metal/"),
    '3' : ('paper',   "../data/paper/"),
    '4' : ('plastic', "../data/plastic/")
}

for label, folder in CLASSES.values():
    os.makedirs(folder, exist_ok=True)


while True:
    ret, frame = cap.read()
    if not ret:
        break
    display_frame = frame.copy()
    cv2.putText(display_frame, "1: Glass | 2: Metal | 3: Paper | 4: Plastic | q: Quit", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.imshow('Video Capture', display_frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        break  # Exit the loop if 'q' is pressed

    key_char = chr(key)
    if key_char in CLASSES:
        label, folder = CLASSES[key_char]
        filepath = os.path.join(folder, f'{label}_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.jpg')
        cv2.imwrite(filepath, frame)
        print(f"Saved: {filepath}")

cap.release()
cv2.destroyAllWindows()

