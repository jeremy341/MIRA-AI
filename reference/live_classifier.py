import cv2
import numpy as np
import pathlib
import time

# Robust fallback import for TFLite Interpreter (works on PC and Raspberry Pi)
try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    from tensorflow import lite as tflite

# NumPy implementation of Softmax to avoid importing heavy TensorFlow
def softmax(x):
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum(axis=0)

# 1. PFADE UND TFLITE INTERPRETER INITIALISIEREN
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent

# Waehle das Modell: "mira_classifier_int8.tflite" (Quantisiert) oder "mira_classifier_fp32.tflite"
MODEL_PATH = ROOT_DIR / "models" / "mira_classifier_int8.tflite"

print(f"Loading TFLite Model from {MODEL_PATH}...")
interpreter = tflite.Interpreter(model_path=str(MODEL_PATH))
interpreter.allocate_tensors()

# Input & Output Details abfragen
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

class_names = ['glass', 'metal', 'paper', 'plastic', 'trash']

# 2. TEMPORAL SMOOTHING KONFIGURATION
alpha = 0.15  # Glaettungsfaktor (0.01 = extrem traege/stabil, 0.9 = flackernd/schnell)
smoothed_probs = np.zeros(len(class_names))

# 3. WEBCAM CAPTURE
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

print("Smooth TFLite Live Inference active. Press 'q' to exit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

 # 4. BILDVORBEREITUNG (Zuschneiden auf quadratischen 224x224 Ausschnitt)
    h, w, _ = frame.shape
    size = min(h, w)
    start_x = (w - size) // 2
    start_y = (h - size) // 2
    cropped = frame[start_y:start_y + size, start_x:start_x + size]

    # FIX: Convert from OpenCV BGR to TensorFlow/Keras RGB [2]
    cropped_rgb = cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB)
    resized = cv2.resize(cropped_rgb, (224, 224))

    # Batch-Dimension hinzufuegen und Typ in NumPy konvertieren (kein tf nötig!)
    input_data = np.expand_dims(resized, axis=0).astype(np.float32)

    # 5. INFERENCE (TFLite Interpreter ausfuehren)
    start_time = time.perf_counter()
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()
    predictions = interpreter.get_tensor(output_details[0]['index'])
    end_time = time.perf_counter()

    latency_ms = (end_time - start_time) * 1000
    fps = 1000 / latency_ms if latency_ms > 0 else 0

    # Raw Logits in Wahrscheinlichkeiten umrechnen (Softmax)
    raw_probs = softmax(predictions[0])

    # 6. EXPONENTIAL MOVING AVERAGE (EMA) FILTER ANWENDEN
    # Stabilisiert das zappelnde Flackern ueber die Zeitachse
    smoothed_probs = alpha * raw_probs + (1 - alpha) * smoothed_probs

    # Klassifizierung ausgeben
    class_idx = np.argmax(smoothed_probs)
    predicted_class = class_names[class_idx]
    confidence = smoothed_probs[class_idx] * 100

    # 7. ANZEIGE ERSTELLEN
    display_frame = frame.copy()
    cv2.rectangle(display_frame, (start_x, start_y), (start_x + size, start_y + size), (255, 0, 0), 2)

    label = f"Class: {predicted_class.upper()} ({confidence:.1f}%)"
    latency_label = f"Latency: {latency_ms:.1f} ms | FPS: {fps:.1f}"

    cv2.putText(display_frame, label, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
    cv2.putText(display_frame, latency_label, (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    cv2.imshow('MIRA Live Sorting Brain (TFLite)', display_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()