import matplotlib.pyplot as plt
import pathlib
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

# 1. PATHS AND CONSTANTS (solved via pathlib)
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
DATA_DIR = ROOT_DIR / "data" / "classes"
MODELS_DIR = ROOT_DIR / "models" / "classifier"

SAVE_DIR = ROOT_DIR / 'results' / 'EXP-002_MobileNetV2'
SAVE_DIR.mkdir(parents=True, exist_ok=True)

BATCH_SIZE = 32
img_height = 224 # Standard size for MobileNetV2
img_width = 224

# 2. LOAD DATASETS
print("Loading training data...")
train_dataset = tf.keras.utils.image_dataset_from_directory(
    DATA_DIR,
    validation_split=0.2,
    subset="training",
    seed=123,
    image_size=(img_height, img_width),
    batch_size=BATCH_SIZE,
    crop_to_aspect_ratio=True
)

print("Loading validation data...")
validation_dataset = tf.keras.utils.image_dataset_from_directory(
    DATA_DIR,
    validation_split=0.2,
    subset="validation",
    seed=123,
    image_size=(img_height, img_width),
    batch_size=BATCH_SIZE,
    crop_to_aspect_ratio=True
)

class_names = train_dataset.class_names
num_classes = len(class_names)

# Performance optimization for CPU
AUTOTUNE = tf.data.AUTOTUNE
train_dataset = train_dataset.cache().prefetch(buffer_size=AUTOTUNE)
validation_dataset = validation_dataset.cache().prefetch(buffer_size=AUTOTUNE)

# 3. DATA AUGMENTATION
data_augmentation = keras.Sequential([
    layers.RandomFlip("horizontal"),
    layers.RandomRotation(0.1),
    layers.RandomZoom(0.1),
])

# 4. LOAD BASE MODEL (MobileNetV2)
# include_top=False removes Google's own classification layer.
IMG_SHAPE = (img_height, img_width, 3)
base_model = tf.keras.applications.MobileNetV2(
    input_shape=IMG_SHAPE,
    include_top=False,
    weights='imagenet'
)

# We freeze Google's weights
base_model.trainable = False

# 5. BUILD ARCHITECTURE
# Rescaling normalizes pixel values from [0, 255] to [-1, 1] for MobileNetV2
model = keras.Sequential([
    data_augmentation,
    layers.Rescaling(scale=1./127.5, offset=-1),
    base_model,
    layers.GlobalAveragePooling2D(),
    layers.Dropout(0.2),
    layers.Dense(num_classes, name="outputs")
])

# 6. COMPILE & TRAIN
# Small learning rate (0.0001) for stable weights in the new classification head.
model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=0.0001),
    loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
    metrics=['accuracy']
)

model.summary()

epochs = 20
print("Starte Training für EXP-002 (Transfer Learning)...")
history = model.fit(
    train_dataset,
    validation_data=validation_dataset,
    epochs=epochs
)

# 7. PLOT RESULTS
acc = history.history['accuracy']
val_acc = history.history['val_accuracy']
loss = history.history['loss']
val_loss = history.history['val_loss']
epochs_range = range(epochs)

plt.figure(figsize=(12, 5))
plt.subplot(1, 2, 1)
plt.plot(epochs_range, acc, label='Training Accuracy')
plt.plot(epochs_range, val_acc, label='Validation Accuracy')
plt.title('EXP-002 Accuracy')
plt.legend()

plt.subplot(1, 2, 2)
plt.plot(epochs_range, loss, label='Training Loss')
plt.plot(epochs_range, val_loss, label='Validation Loss')
plt.title('EXP-002 Loss')
plt.legend()

# Speichere die Kurven automatisch
plot_save_path = SAVE_DIR / 'training_curves.png'
plt.savefig(plot_save_path, dpi=300)
print(f"Training curves saved to: {plot_save_path}")
plt.show()

# Save model as .keras file in the central /models folder
MODELS_DIR = ROOT_DIR / "models" / "classifier"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
MODEL_SAVE_PATH = MODELS_DIR / "mira_classifier_transfer.keras"
model.save(MODEL_SAVE_PATH)
print(f"Model saved successfully to {MODEL_SAVE_PATH}!")
