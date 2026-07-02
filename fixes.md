## Critical Diagnostic: The Silent RGB/BGR Mismatch Bug

Before analyzing high-level design strategies, we must address a **critical, silent bug** in your current real-time inference pipeline that explains why your live testing performs significantly worse than offline evaluations.

In `src/visualize_dataset.py` and your training data pipeline, you correctly handle or display images in **RGB** format (TensorFlow’s default). However, in your live inference scripts (`live_inference.py` and `live_inference_tflite.py`), you capture frames using OpenCV (`cv2.VideoCapture`):

```python
# From your live_inference_tflite.py
ret, frame = cap.read()  # Captured in BGR format
...
cropped = frame[start_y:start_y + size, start_x:start_x + size]
resized = cv2.resize(cropped, (224, 224))
input_data = np.expand_dims(resized, axis=0).astype(np.float32)
```

**The Bug:** OpenCV loads and captures images in **BGR** order, but your MobileNetV2 model expects inputs in **RGB** order [2]. Passing BGR frames directly to the model means the Red and Blue color channels are swapped during inference. 

This explains the erratic classification behavior in live testing. While a plastic bottle under a neutral light might still have enough geometric features to be recognized, subtle color and texture boundaries (especially for glass and paper) collapse [1, 2].

#### The Fix:
You must convert the cropped or resized frame to RGB before passing it to the input tensor:

```python
# Convert BGR to RGB
frame_rgb = cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB)
resized = cv2.resize(frame_rgb, (224, 224))
```

---

## 1. Training Data & Generalization Strategy

Your current dataset of ~800 custom images captured under a single webcam is a classic **overfit-to-domain** hazard [2]. The model is highly sensitive to your specific background, the distance of your camera, and the ambient lighting in your room. If you take this setup to a different room with fluorescent lighting during the competition, the system's accuracy is highly likely to degrade.

```
                  ┌─────────────────────────────────────────┐
                  │        HYBRID DATASET STRATEGY          │
                  └─────────────────────────────────────────┘
                                       │
         ┌─────────────────────────────┴─────────────────────────────┐
         ▼                                                           ▼
┌─────────────────────────────────┐                         ┌─────────────────────────────────┐
│       CUSTOM DOMAIN DATA        │                         │       PUBLIC SEMANTIC DATA      │
│  - Captures exact camera angle  │                         │  - Injects material variance    │
│  - Captures local background    │                         │  - Millions of texture features │
│  - High local precision         │                         │  - High generalization capacity │
└─────────────────────────────────┘                         └─────────────────────────────────┘
         │                                                           │
         └─────────────────────────────┬─────────────────────────────┘
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │          Model Training Loop            │
                  └─────────────────────────────────────────┘
```

### Evaluation of Options:
*   **Replacing with a Public Dataset (e.g., TrashNet, TACO):** This is a weak option on its own. Public datasets are shot under studio conditions or in outdoor environments that do not match the specific top-down geometry, camera lens, and background of your physical sorting rig.
*   **Combining Custom and Public Data (Recommended):** This is the strongest approach. Use your custom capture tool to retain local domain features (camera height, lens distortion), but mix in curated subsets of public datasets to introduce variations in material shapes, labels, and deformations.
*   **Synthetic Domain Randomization (Data Augmentation):** Instead of manually taking 5,000 more photos, apply mathematical transformations offline.

### Actionable Implementation Steps:
1.  **Background Subtraction / Augmentation:** Capture 20 images of your empty sorting background. Write a script that takes your cropped objects, separates them from their background (using classical thresholding or alpha masking), and programmatically pastes them onto randomized, textured backgrounds (wood patterns, conveyor belt textures, metallic sheets) before training.
2.  **Color Space Augmentation:** In your training pipelines, expand your `data_augmentation` block to dynamically simulate lighting variations [2]:
    ```python
    data_augmentation = keras.Sequential([
        layers.RandomFlip("horizontal"),
        layers.RandomRotation(0.15),
        layers.RandomZoom(0.15),
        layers.RandomContrast(0.2),  # Simulates varying camera exposures
        layers.RandomBrightness(0.2) # Simulates shifting ambient light
    ])
    ```

---

## 2. Model Retraining & Architectures

Retraining MobileNetV2 from scratch on a small dataset is highly counterproductive. It has 2.2 million parameters [2]; without pre-trained ImageNet weights, it will overfit your training set and struggle to generalize [2]. 

### Architecture Comparison for Edge Deployment:

| Architecture | Parameters | CPU Latency (Pi 4) | Top-1 Accuracy (ImageNet) | Suitability for MIRA |
|---|---|---|---|---|
| **MobileNetV2** | ~2.2M [2] | ~80 ms | 71.3% | **Good standard.** Balanced, but exhibits slightly higher latency on entry-level MCUs [2]. |
| **EfficientNet-Lite0**| ~3.4M | ~55 ms | 75.1% | **Highly Recommended.** Quantization-friendly, structurally optimized for INT8 without accuracy collapse. |
| **MobileNetV3-Small** | ~1.5M | ~25 ms | 67.4% | **Best for Low-Spec Edge.** Fastest inference, but slightly less robust features on complex textures. |

### Advanced Training Techniques to Implement:
1.  **Cosine Decay Learning Rate Scheduling:** Instead of a static or step-down learning rate, use a cosine curve with warm restarts. This helps the optimizer find deeper local minima during fine-tuning.
    ```python
    lr_schedule = tf.keras.optimizers.schedules.CosineDecay(
        initial_learning_rate=1e-5,
        decay_steps=1000
    )
    optimizer = tf.keras.optimizers.Adam(learning_rate=lr_schedule)
    ```
2.  **Label Smoothing:** When calculating loss, use label smoothing (e.g., `label_smoothing=0.1`). This prevents the model from predicting classes with extreme, overconfident probabilities ($1.0$ or $0.0$), improving generalization on noisy real-world materials.

---

## 3. Real-Time Inference Optimization

Apart from the RGB/BGR color channel bug, several hardware and execution bottlenecks limit your live framerate and consistency:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      REAL-TIME EXECUTION FLOW                           │
└─────────────────────────────────────────────────────────────────────────┘
      │
      ▼
┌──────────────────────────┐     Disabled      ┌──────────────────────────┐
│  Disable Auto-Exposure   │ ────────────────> │ Disable Auto-Focus       │
└──────────────────────────┘                   └──────────────────────────┘
      │
      ▼
┌──────────────────────────┐     XNNPACK       ┌──────────────────────────┐
│  Convert BGR to RGB      │ ────────────────> │ Run TFLite Interpreter   │
└──────────────────────────┘                   └──────────────────────────┘
```

### Core Bottlenecks:
1.  **Auto-Exposure and Auto-Focus Jitter:** When an object enters the frame, your webcam automatically adjusts its focus and exposure. This changes the color temperature of the pixels, shifting the input values away from what your model learned during training.
2.  **Single-Threaded Blocking:** Your live script captures frames, runs inference, and renders the output sequentially on a single thread. The camera capture waits for the CPU inference to finish, limiting your framerate to your inference latency.

### Actionable Fixes:
1.  **Hardware Parameter Locking:** Lock your camera parameters at startup. Disable automatic focus, exposure, and white balance, and set them to static values:
    ```python
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)      # Disable autofocus
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0)   # Disable auto exposure
    ```
2.  **Enable XNNPACK Delegation:** TFLite on CPU can be accelerated dramatically using XNNPACK delegates. In your `live_inference_tflite.py`, initialize the interpreter with optimized thread allocations:
    ```python
    # Set thread count to match your CPU's physical cores
    interpreter = tf.lite.Interpreter(
        model_path=str(MODEL_PATH),
        num_threads=4
    )
    ```

---

## 4. Multiple Object Detection

Your current model is an **image classifier** (it maps one global label to an entire image) [2]. If multiple objects (e.g., a plastic cup and a metal can) are placed in the frame simultaneously, the model will output a prediction based on whichever object dominates the geometric feature space, or it will output a highly unstable, low-confidence prediction.

### Architectural Redesign Options:

```
Option A: Single-Stage Object Detection (YOLOv8-Nano)
[ Live Camera Frame ] ──> [ YOLOv8-Nano Model ] ──> [ Multiple Bounding Boxes + Classes ]

Option B: Hybrid OpenCV proposals + TFLite Classification
[ Live Camera Frame ] ──> [ OpenCV Contour Proposed Regions ]
                                   │
                                   ├──> [ Region 1 Crop ] ──> [ TFLite Model ] ──> Class 1
                                   └──> [ Region 2 Crop ] ──> [ TFLite Model ] ──> Class 2
```

#### Option A: Single-Stage Object Detection (YOLOv8-Nano / SSD-MobileNetV2)
This is the modern industry standard. You replace classification with detection. The model directly outputs coordinates of bounding boxes and class names for everything in the frame.
*   **Pros:** Highly robust, handles overlaps, predicts coordinates directly.
*   **Cons:** YOLOv8-Nano requires substantial processing power compared to a quantized TFLite model, which will reduce your framerate on CPU-bound edge devices.

#### Option B: Classical CV Proposed Regions + TFLite Classification (Recommended for Edge)
Before running your AI, use OpenCV to segment the frame into independent objects, crop each object, and pass them sequentially to your TFLite classifier.
*   **Pros:** Highly efficient, maintains your optimized INT8 model [1], requires no training of a complex detection network.
*   **Cons:** Relies on clear physical separation between objects on your sorting belt.

### Actionable Implementation Code (Option B):
```python
# 1. Convert to grayscale and blur to remove noise
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (5, 5), 0)

# 2. Thresholding to segment objects from the background (assumes constant background color)
_, thresh = cv2.threshold(blurred, 50, 255, cv2.THRESH_BINARY_INV)

# 3. Find contours of the isolated items
contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

for contour in contours:
    if cv2.contourArea(contour) < 1000: # Filter out tiny noise particles
        continue
        
    # Get bounding rect
    x, y, w, h = cv2.boundingRect(contour)
    
    # Crop object from the original RGB frame
    cropped_obj = frame_rgb[y:y+h, x:x+w]
    
    # Pad to square and resize to 224x224
    # Run through interpreter.invoke() sequentially
```

---

## 5. Overall System Design & Bottlenecks

A complete review of your pipeline reveals several systemic bottlenecks and design gaps:

```
 ┌───────────────────────────────────────────────────────────┐
 │                  PRODUCER-CONSUMER PATTERN                │
 └───────────────────────────────────────────────────────────┘
                               │
         ┌─────────────────────┴─────────────────────┐
         ▼                                           ▼
┌──────────────────┐                       ┌──────────────────┐
│  Camera/Inference│                       │  Serial Communication│
│  Thread (30 FPS) │ ──> [ Queue Buffer ] ─> │  Thread (Blocking) │
└──────────────────┘                       └──────────────────┘
```

### Identified Architectural Gaps:
1.  **Synchronous Serial/Telemetry Blocking:** If your `live_inference` script communicates directly with the ESP32 (via `pyserial`) or publishes to Azure IoT Hub synchronously, the entire frame loop will freeze while waiting for the physical hardware response. This is a critical latency bottleneck.
2.  **Dataset Integrity:** Your dataset collection script does not record lighting parameters, scale, or camera height. This makes expanding the dataset difficult over time.
3.  **No Anomaly Detection:** If an unknown item (such as a banana peel or battery) is placed in front of the camera, the model *must* classify it as glass, metal, paper, or plastic. This presents a hazard to the sorting hardware.

### Actionable Architectural Upgrades:
1.  **Multi-Threaded Producer-Consumer Architecture:** Separate your Camera/Inference thread, Serial/ESP32 thread, and Telemetry thread using Python's `queue` and `threading` libraries:
    ```python
    import threading
    import queue

    command_queue = queue.Queue(maxsize=1)

    def serial_sender_thread(q):
        import serial
        ser = serial.Serial('COM3', 115200)
        while True:
            cmd = q.get()  # Blocks until a command is available
            ser.write(f"{cmd}\n".encode())
            response = ser.readline()  # Wait for ESP32 confirmation
            q.task_done()

    # Start thread
    threading.Thread(target=serial_sender_thread, args=(command_queue,), daemon=True).start()
    ```
2.  **Softmax Thresholding for Anomaly Detection:** In your inference loop, check the highest confidence value. If it is below a specific threshold (e.g., `< 0.65`), classify the object as `unknown` and route it to a default manual sort bin.

---

## 6. Testing & Evaluation Protocol

For a scientifically valid *Jugend forscht* paper, your evaluation must go beyond standard train/val splits [2]. You must prove the system works under real-world, dynamic constraints.

### The Production Readiness Protocol:

```
  ┌───────────────────────────────────────────────────────┐
  │                 TESTING PROTOCOL                      │
  └───────────────────────────────────────────────────────┘
                              │
       ┌──────────────────────┼──────────────────────┐
       ▼                      ▼                      ▼
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│  OOD Test    │       │ Thermal Run  │       │ Physical Sort│
│  - Shifting  │       │ - Monitor    │       │ - End-to-end │
│    lighting  │       │   CPU thrott-│       │   mechanical │
│  - Target    │       │   ling over  │       │   accuracy   │
│    accuracy  │       │   24 hours   │       │   metric     │
└──────────────┘       └──────────────┘       └──────────────┘
```

1.  **Out-Of-Distribution (OOD) Generalization Test:**
    *   *Execution:* Collect a dedicated test dataset of 100 images captured in a completely different room, using different light sources (e.g., warm LEDs vs. cool fluorescent bulbs). 
    *   *Metric:* Evaluate your FP32 model and INT8 TFLite models on this set [1, 2]. Document the exact percentage drop in accuracy.
2.  **Continuous Operational Thermal Burn-In Test:**
    *   *Execution:* Run your standalone TFLite inference loop continuously on your target hardware (Raspberry Pi/ESP32) for 24 hours in a closed box (to simulate the robot's physical shell). 
    *   *Metric:* Log the CPU temperature, thermal throttling states, and inference latency over time. Plot `Inference Latency vs. Operating Time` to prove your system can run continuously without performance degradation.
3.  **Physical Sorting Throughput vs. Model Accuracy:**
    *   *Execution:* Run 100 physical objects through your sorting system.
    *   *Metric:* Compare your *model's validation accuracy* against the *physical sorting accuracy* (percentage of items that successfully land in the correct physically separated sorting bin). This captures mechanical latency, grip failures, and timing errors, giving you an end-to-end engineering metric.

---

## 7. Future Features Roadmap

To make your project technically outstanding, consider these future features once the basic physical sorting setup is established:

1.  **Edge TPU/NPU Integration:**
    *   *Detail:* Port your INT8 TFLite model to run on a dedicated hardware accelerator, such as a **Google Coral Edge TPU USB Accelerator** [1]. This offloads the vector math from your CPU to dedicated silicon, reducing inference latency below 5 ms.
2.  **On-Device Self-Supervised Learning (Online Learning):**
    *   *Detail:* When MIRA classifies an object with high confidence, it can save that image locally. Overnight, the system can self-train on these new local samples, adapting to new packaging designs in its specific region without manual labeling.
3.  **MQTT-Based Fleet Telemetry & Dashboard:**
    *   *Detail:* Connect multiple MIRA units to a central dashboard. Use MQTT to send data on hourly sorting volume, material distributions (e.g., "55% plastic sorted today"), and error logs to an Azure Web App or Power BI dashboard. This demonstrates industrial IoT scalability.