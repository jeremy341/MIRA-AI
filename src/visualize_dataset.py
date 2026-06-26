import os
import random
import cv2
import matplotlib.pyplot as plt


DATA_DIR = "../data/"

CLASSES = ['glass', 'metal', 'paper', 'plastic']


total_files = 0

for class_name in CLASSES:
    folder = os.path.join(DATA_DIR, class_name)
    if os.path.exists(folder):
        num_files = len([files for files in os.listdir(folder) if files.lower().endswith(('.jpg', '.jpeg', '.png'))])
        print(f"{class_name}:  {num_files} images")

        total_files += num_files

print(f"Total:   {total_files}")

SAMPLES = int(5)
fig, axes = plt.subplots(len(CLASSES), SAMPLES, figsize=(15, 10))

for row, class_name in enumerate(CLASSES):
    folder = os.path.join(DATA_DIR, class_name)
    files = [f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

    # Your job: handle the case where folder has fewer than SAMPLES images
    sampled = random.sample(files, min(SAMPLES, len(files)))

    for col, filename in enumerate(sampled):
        img = cv2.imread(os.path.join(folder, filename))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        axes[row, col].imshow(img)
        axes[row, col].axis('off')
        if col == 0:
            axes[row, col].set_ylabel(class_name, fontsize=12)

plt.tight_layout()
plt.show()