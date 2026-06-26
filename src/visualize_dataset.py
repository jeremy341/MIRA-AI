import os

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

