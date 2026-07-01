import cv2
import numpy as np
import tensorflow as tf
import pathlib
import time

# 1. PFADE UND MODELL LADEN
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
MODEL_PATH = ROOT_DIR / "models" / "mira_fine_tuned_model.keras"

print("Loading MIRA fine-tuned model...")
model = tf.keras.models.load_model(MODEL_PATH)
class_names = ['glass', 'metal', 'paper', 'plastic']

# 2. WEBCAM INITIALISIEREN
cap = cv2.VideoCapture(0)

# Optionale Webcam-Auflösung (Standard-Webcams liefern meist 640x480)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

print("Live inference active. Press 'q' to exit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read frame from webcam.")
        break

    # Vorbereitung: Bild quadratisch zuschneiden (verhindert Verzerrung)
    h, w, _ = frame.shape
    size = min(h, w)
    start_x = (w - size) // 2
    start_y = (h - size) // 2
    cropped = frame[start_y:start_y + size, start_x:start_x + size]

    # Bildgröße auf 224x224 anpassen (MobileNetV2-Standard)
    resized = cv2.resize(cropped, (224, 224))

    # Datentyp anpassen und Batch-Dimension hinzufügen (1, 224, 224, 3)
    input_tensor = tf.cast(tf.expand_dims(resized, axis=0), tf.float32)

    # Latenzzeit messen
    start_time = time.perf_counter()
    # model() ist bei Einzelbildern deutlich schneller als model.predict()
    predictions = model(input_tensor, training=False)
    end_time = time.perf_counter()
    latency_ms = (end_time - start_time) * 1000
    fps = 1000 / latency_ms if latency_ms > 0 else 0

    # Softmax anwenden, um Logits in Wahrscheinlichkeiten umzuwandeln
    probabilities = tf.nn.softmax(predictions[0]).numpy()
    class_idx = np.argmax(probabilities)
    predicted_class = class_names[class_idx]
    confidence = probabilities[class_idx] * 100

    # Visualisierungen zeichnen
    display_frame = frame.copy()

    # Quadratische Box zeichnen, die den Bereich der Klassifizierung zeigt
    cv2.rectangle(display_frame, (start_x, start_y), (start_x + size, start_y + size), (255, 0, 0), 2)

    # Textanzeigen auf dem Frame platschen
    label = f"Class: {predicted_class.upper()} ({confidence:.1f}%)"
    latency_label = f"Latency: {latency_ms:.1f} ms | FPS: {fps:.1f}"

    cv2.putText(display_frame, label, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
    cv2.putText(display_frame, latency_label, (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    # Fenster anzeigen
    cv2.imshow('MIRA Live Sorting Brain', display_frame)

    # Beenden mit der Taste 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Ressourcen freigeben
cap.release()
cv2.destroyAllWindows()