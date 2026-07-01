import tensorflow as tf
import pathlib
import matplotlib.pyplot as plt
from tensorflow.keras import layers

# 1. PATH RESOLUTION
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
DATA_DIR = ROOT_DIR / "data"
MODELS_DIR = ROOT_DIR / "models"

SAVE_DIR = ROOT_DIR / 'results' / 'EXP-003_FineTuning'
SAVE_DIR.mkdir(parents=True, exist_ok=True)

batch_size = 32
img_height = 224
img_width = 224

# Load Dataset
val_ds = tf.keras.utils.image_dataset_from_directory(
    DATA_DIR,
    validation_split=0.2,
    subset="validation",
    seed=123,
    image_size=(img_height, img_width),
    batch_size=batch_size,
    crop_to_aspect_ratio=True
)

train_ds = tf.keras.utils.image_dataset_from_directory(
    DATA_DIR,
    validation_split=0.2,
    subset="training",
    seed=123,
    image_size=(img_height, img_width),
    batch_size=batch_size,
    crop_to_aspect_ratio=True
)

# Performance Tuning
AUTOTUNE = tf.data.AUTOTUNE
train_ds = train_ds.cache().shuffle(1000).prefetch(buffer_size=AUTOTUNE)
val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)

# 2. LOAD COMPLETED EXP-002 MODEL (from /models folder)
MODEL_PATH = MODELS_DIR / "mira_transfer_model.keras"
print(f"Loading previous model from {MODEL_PATH}...")
model = tf.keras.models.load_model(MODEL_PATH)

# Find the MobileNetV2 layer within our Sequential model
base_model = model.get_layer("mobilenetv2_1.00_224")

# 3. UNFREEZE THE BASE MODEL FOR FINE-TUNING
base_model.trainable = True

# Let's see how many layers are in the base model
print(f"Number of layers in base model: {len(base_model.layers)}")

# Fine-tune from layer 100 onwards (keep early layers frozen as they detect basic edges)
fine_tune_at = 100
for layer in base_model.layers[:fine_tune_at]:
    layer.trainable = False

# 4. RECOMPILE WITH VERY LOW LEARNING RATE
# Using an ultra-low learning rate prevents destroying pre-trained weights
model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),
    loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
    metrics=['accuracy']
)

model.summary()

# 5. TRAIN FOR 15 EPOCHS
fine_tune_epochs = 15
history = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=fine_tune_epochs
)

# 6. SAVE EXP-003 MODEL (to /models folder)
MODELS_DIR.mkdir(exist_ok=True)
model.save(MODELS_DIR / 'mira_fine_tuned_model.keras')
print("Fine-tuned model saved successfully!")

# Plot and save curves
acc = history.history['accuracy']
val_acc = history.history['val_accuracy']
loss = history.history['loss']
val_loss = history.history['val_loss']
epochs_range = range(fine_tune_epochs)

plt.figure(figsize=(12, 5))
plt.subplot(1, 2, 1)
plt.plot(epochs_range, acc, label='Training Accuracy')
plt.plot(epochs_range, val_acc, label='Validation Accuracy')
plt.title('EXP-003 Fine-Tuning Accuracy')
plt.legend()

plt.subplot(1, 2, 2)
plt.plot(epochs_range, loss, label='Training Loss')
plt.plot(epochs_range, val_loss, label='Validation Loss')
plt.title('EXP-003 Fine-Tuning Loss')
plt.legend()

plt.savefig(SAVE_DIR / 'training_curves.png', dpi=300)
plt.show()