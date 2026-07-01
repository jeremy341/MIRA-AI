import matplotlib.pyplot as plt
import numpy as np
import PIL
import tensorflow as tf
import pathlib
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.models import Sequential

# 1. PFADE UND KONSTANTEN UNIFIZIEREN
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
DATA_DIR = ROOT_DIR / "data"
MODELS_DIR = ROOT_DIR / "models"

# Verzeichnis für Modelle erstellen, falls es nicht existiert
MODELS_DIR.mkdir(parents=True, exist_ok=True)

batch_size = 32
img_height = 180
img_width = 180

# Trainings-Daten laden
train_ds = tf.keras.utils.image_dataset_from_directory(
  DATA_DIR,
  validation_split=0.2,
  subset="training",
  seed=123,
  image_size=(img_height, img_width),
  batch_size=batch_size,
  crop_to_aspect_ratio=True)

# Validierungs-Daten laden
val_ds = tf.keras.utils.image_dataset_from_directory(
  DATA_DIR,
  validation_split=0.2,
  subset="validation",
  seed=123,
  image_size=(img_height, img_width),
  batch_size=batch_size,
  crop_to_aspect_ratio=True)

class_names = train_ds.class_names
num_classes = len(class_names)

# Performance Optimierung
AUTOTUNE = tf.data.AUTOTUNE
train_ds = train_ds.cache().shuffle(1000).prefetch(buffer_size=AUTOTUNE)
val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)

# 2. DATA AUGMENTATION DEFINIEREN (Gegen Auswendiglernen)
data_augmentation = keras.Sequential([
    layers.RandomFlip("horizontal", input_shape=(img_height, img_width, 3)),
    layers.RandomRotation(0.1),
    layers.RandomZoom(0.1),
])

# 3. DAS MODELL BAUEN (Die verbesserte Version)
model = Sequential([
  data_augmentation,
  layers.Rescaling(1./255), # Pixelwerte von 0-255 auf 0-1 bringen
  layers.Conv2D(16, 3, padding='same', activation='relu'),
  layers.MaxPooling2D(),
  layers.Conv2D(32, 3, padding='same', activation='relu'),
  layers.MaxPooling2D(),
  layers.Conv2D(64, 3, padding='same', activation='relu'),
  layers.MaxPooling2D(),
  layers.Dropout(0.2), # 20% der Neuronen zufällig abschalten gegen Overfitting
  layers.Flatten(),
  layers.Dense(128, activation='relu'),
  layers.Dense(num_classes, name="outputs")
])

# 4. COMPILIEREN & TRAINIEREN
model.compile(optimizer='adam',
              loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
              metrics=['accuracy'])

model.summary()

epochs = 20
history = model.fit(
  train_ds,
  validation_data=val_ds,
  epochs=epochs
)

# 5. ERGEBNISSE PLOTTEN
acc = history.history['accuracy']
val_acc = history.history['val_accuracy']
loss = history.history['loss']
val_loss = history.history['val_loss']
epochs_range = range(epochs)

plt.figure(figsize=(12, 5))
plt.subplot(1, 2, 1)
plt.plot(epochs_range, acc, label='Training Accuracy')
plt.plot(epochs_range, val_acc, label='Validation Accuracy')
plt.title('Genauigkeit (Accuracy)')
plt.legend()

plt.subplot(1, 2, 2)
plt.plot(epochs_range, loss, label='Training Loss')
plt.plot(epochs_range, val_loss, label='Validation Loss')
plt.title('Fehlerrate (Loss)')
plt.legend()
plt.show()

# 6. MODELL SPEICHERN
# Speichert das Modell direkt im zentralen /models Ordner
MODEL_SAVE_PATH = MODELS_DIR / 'mira_waste_model.keras'
model.save(MODEL_SAVE_PATH)
print(f"Modell wurde als {MODEL_SAVE_PATH} gespeichert!")