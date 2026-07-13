import pathlib
from ultralytics import YOLO

# 1. PFADE
ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT_DIR / "models" / "mira_exp006.pt"

# 2. MODELL LADEN
model = YOLO(MODEL_PATH)

# 3. EXPORT ZU INT8 TFLITE
# int8=True aktiviert die Quantisierung
# data='dataset.yaml' wird zur Kalibrierung genutzt (sehr wichtig!)
print("Starte YOLOv8 Quantisierung zu INT8...")
data_yaml = ROOT_DIR / "datasets" / "mira_v2" / "dataset.yaml"
model.export(format="tflite", int8=True, data=str(data_yaml))

print(f"Fertig! Das Modell liegt nun im Ordner: {ROOT_DIR}/models/")