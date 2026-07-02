import tensorflow as tf
from tensorflow import keras
import pathlib
import numpy as np
import os

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
DATA_DIR = ROOT_DIR / "data"
MODELS_DIR = ROOT_DIR / "models"


def representative_data_gen():
    image_paths = list(DATA_DIR.glob("*/*.jpg")) + list(DATA_DIR.glob("*/*.png"))
    if len(image_paths) == 0:
        raise FileNotFoundError("No images found in data directory")

    sample_paths = np.random.choice(image_paths, size=min(100, len(image_paths)), replace=False)

    for path in sample_paths:
        img = tf.io.read_file(str(path))
        img = tf.image.decode_jpeg(img, channels=3)

        # Get image dimensions dynamically
        shape = tf.shape(img)
        h, w = shape[0], shape[1]
        box_size = tf.minimum(h, w)

        # Center crop the image to a square first to avoid stretching
        img = tf.image.resize_with_crop_or_pad(img, box_size, box_size)

        # Resize to MobileNet target size
        img = tf.image.resize(img, (224, 224))

        img = tf.expand_dims(img, 0)
        yield [tf.cast(img, tf.float32)]


MODEL_PATH = MODELS_DIR / "mira_fine_tuned_model.keras"
print(f"Loading model from {MODEL_PATH}")
model = keras.models.load_model(MODEL_PATH)

print("Converting to Standard TFLite (Float32)...")
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_fp32_model = converter.convert()

FP32_SAVE_PATH = MODELS_DIR / "mira_model_fp32.tflite"
with open(FP32_SAVE_PATH, "wb") as f:
    f.write(tflite_fp32_model)
print(f"Float32 TFLite saved under: {FP32_SAVE_PATH}")

print("Converting to quantized TFLite (Full INT8)...")
converter_int8 = tf.lite.TFLiteConverter.from_keras_model(model)
converter_int8.optimizations = [tf.lite.Optimize.DEFAULT]
converter_int8.representative_dataset = representative_data_gen

converter_int8.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
converter_int8.inference_input_type = tf.float32
converter_int8.inference_output_type = tf.float32

tflite_int8_model = converter_int8.convert()

INT8_SAVE_PATH = MODELS_DIR / "mira_model_int8.tflite"
with open(INT8_SAVE_PATH, "wb") as f:
    f.write(tflite_int8_model)
print(f"INT8 TFLite saved under: {INT8_SAVE_PATH}")

# Compare file sizes
size_keras = os.path.getsize(MODEL_PATH) / (1024 * 1024)
size_fp32 = os.path.getsize(FP32_SAVE_PATH) / (1024 * 1024)
size_int8 = os.path.getsize(INT8_SAVE_PATH) / (1024 * 1024)

print("\n" + "=" * 50)
print("COMPRESSION SUMMARY")
print("=" * 50)
print(f"Keras Full Model:  {size_keras:.2f} MB")
print(f"Standard TFLite:   {size_fp32:.2f} MB")
print(f"Quantized INT8:    {size_int8:.2f} MB")
print(f"Compression Ratio (Keras -> INT8): {size_keras / size_int8:.1f}x smaller")
print("=" * 50)