import random
import cv2
import matplotlib.pyplot as plt
import pathlib

# 1. PATH RESOLUTION (Using pathlib to work from any CWD)
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
DATA_DIR = ROOT_DIR / "data" / "classes"

CLASSES = ['glass', 'metal', 'paper', 'plastic', 'trash']

total_files = 0

for class_name in CLASSES:
    folder = DATA_DIR / class_name
    if folder.exists():
        files = list(folder.glob("*.jpg")) + list(folder.glob("*.jpeg")) + list(folder.glob("*.png"))
        num_files = len(files)
        print(f"{class_name}:  {num_files} images")
        total_files += num_files
    else:
        print(f"{class_name}:  0 images (Folder not found)")

print(f"Total:   {total_files}")

if total_files == 0:
    print("No images found to visualize. Run capture_frame.py first to collect some data!")
    exit(0)

SAMPLES = 5
fig, axes = plt.subplots(len(CLASSES), SAMPLES, figsize=(15, 10))

for row, class_name in enumerate(CLASSES):
    folder = DATA_DIR / class_name
    if not folder.exists():
        # If folder doesn't exist, hide all axes for this row
        for col in range(SAMPLES):
            axes[row, col].axis('off')
        continue
        
    files = list(folder.glob("*.jpg")) + list(folder.glob("*.jpeg")) + list(folder.glob("*.png"))
    
    # Handle the case where folder has fewer than SAMPLES images
    sampled = random.sample(files, min(SAMPLES, len(files)))
    
    for col in range(SAMPLES):
        if col < len(sampled):
            img_path = sampled[col]
            img = cv2.imread(str(img_path))
            if img is not None:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                axes[row, col].imshow(img)
            axes[row, col].axis('off')
        else:
            # Empty plot if we have fewer images than SAMPLES
            axes[row, col].axis('off')
            
        if col == 0:
            axes[row, col].set_ylabel(class_name, fontsize=12)

plt.tight_layout()
plt.show()