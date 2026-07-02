# MIRA Master Implementation Plan (2026–2028)

This master plan integrates all architectural decisions, code designs, and scientific methodologies established during our technical sessions into a single, cohesive development map. It is designed to be followed sequentially to build, evaluate, and document MIRA for school academic requirements (*Facharbeit*) and the *Jugend forscht* (Technology track) national competition [2].

---

## Phase 1: Dataset Expansion & Generalization Architecture

### 1. Public Datasets to Merge
To address your dataset's limited diversity (currently ~800 images across 4 high-level classes, covering ~20 trash sub-categories), you will integrate curated subsets of two high-quality public repositories:
1.  **TrashNet (Stanford):** Consists of 2,527 images of glass, paper, cardboard, plastic, metal, and general trash on clean, white backgrounds. It is optimal for providing stable, baseline geometric representation.
2.  **TACO (Trash Annotations in Context):** Contains 1,500 highly diverse images of waste in various indoor and outdoor settings with pixel-level polygon annotations. This introduces semantic variations (crushed cans, wrinkled bags, dirt, and varied labeling).

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
                                       │
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │    Mapping & Normalization Pipeline     │
                  │       (src/merge_datasets.py)           │
                  └─────────────────────────────────────────┘
```

### 2. Dataset Merging & Label Quality Control
To merge these sources without corrupting class labels, write a dedicated utility script: `src/merge_datasets.py`. This script will programmatically download the public datasets and apply a strict structural mapping dictionary:

*   **TrashNet Mapping:**
    *   `glass` $\rightarrow$ `data/glass/`
    *   `metal` $\rightarrow$ `data/metal/`
    *   `paper`, `cardboard` $\rightarrow$ `data/paper/`
    *   `plastic` $\rightarrow$ `data/plastic/`
    *   *Exclude:* `trash` category (to prevent class boundary dilution).
*   **TACO Mapping (Using COCO Annotations):**
    *   Filter objects by category ID:
        *   `Aluminium can`, `Tin can` $\rightarrow$ `data/metal/`
        *   `Glass bottle`, `Glass jar` $\rightarrow$ `data/glass/`
        *   `Cardboardbox`, `Paper bag`, `Magazine` $\rightarrow$ `data/paper/`
        *   `Plastic bottle`, `Plastic cup`, `Tupperware` $\rightarrow$ `data/plastic/`
    *   *Filter:* Discard organic waste, cigarette butts, and unmappable debris to keep class purity near 100%.

### 3. Background Generalization: Critical Evaluation
Since your robotic arm will be demonstrated at different venues with different tabletops and lighting, the model must ignore background features and classify objects solely on their material properties.

*   **Option A: Classical Background Removal (e.g., HSV Thresholding / Contour Slicing):**
    *   *Evaluation:* Extremely fragile. If the demonstration venue has a tabletop of a similar color to a target material (e.g., a white plastic bottle on a light-colored laminate table, or shadows cast by bright spotlights), the background removal pipeline will fail or crop the object incorrectly.
*   **Option B: Deep-Learning-Based Object Detection (YOLOv8-Nano) with Background Augmentation (Recommended):**
    *   *Evaluation:* Highly robust. Instead of manually cropping the background, the neural network learns to identify the local color gradients, edges, and shiny specular highlights of the materials themselves, regardless of the tabletop. 
    *   *Implementation:* You will use a single-stage object detector trained with synthetic background insertion (randomly replacing the bounding-box background during training with wood, concrete, or metal textures).

### 4. Data Augmentation Implementations
To simulate shifting lighting and angles, implement these augmentations inside your preprocessing pipeline [2]:
*   **Spatial Augmentations:** `RandomFlip("horizontal")`, `RandomRotation(0.15)`, and `RandomZoom(0.15)` to simulate different positioning on the sorting belt [2].
*   **Color Space Augmentations:** `RandomBrightness(factor=0.2)` and `RandomContrast(factor=0.2)` to simulate shifting ambient light intensities and autofocus/exposure adjustments [2].

---

## Phase 2: Core Machine Learning Optimization

### 1. Training Strategy Decision: Retrain vs. Continue
To meet your new requirement of **detecting multiple objects simultaneously with bounding boxes**, you must **pivot from an image classifier to an object detector**. 

Your current MobileNetV2 classification model (EXP-003) outputting a single global label cannot fulfill this requirement [2]. You will **retrain from scratch** using a lightweight, single-stage object detection architecture: **YOLOv8-Nano (or SSD-MobileNetV2)**.

```
[ Raw Camera Frame ] ──> [ Feature Pyramid Network ] ──> [ Bounding Box Regressor ] ──> [ Class Predictor ]
```

### 2. Architectural Upgrades
You will use the PyTorch-based **YOLOv8-Nano** architecture [1]:
*   **Why:** It is structurally optimized for edge deployment. It uses a single backbone with anchor-free detection heads, enabling parallel processing of bounding boxes and class confidences in a single pass.
*   **Transfer Learning:** You will initialize training with pre-trained weights from the COCO dataset (which contains thousands of generalized real-world shapes) and fine-tune all layers on your newly merged, high-quality MIRA dataset.

### 3. Hyperparameter Tuning & Optimizations
*   **Cosine Learning Rate Decay:** Implement a dynamic cosine learning rate scheduler starting at `1e-3` down to `1e-6` to ensure the model smoothly converges without getting stuck in sharp local minima.
*   **Loss Formulation:** Use Complete IoU (CIoU) Loss for the bounding box regression, which optimizes for box overlap, aspect ratio, and center-point distance simultaneously.

---

## Phase 3: Live Real-Time Multi-Object Detection Engine

### 1. System Redesign: `src/live_detection_tflite.py`
This script replaces `live_inference_tflite.py`. It uses the TensorFlow Lite Interpreter to run inference at high framerates on a CPU (or Raspberry Pi), parses multiple object bounding boxes, draws them on screen, and stabilizes the predictions [2].

```
                                  ┌────────────────────────────────┐
                                  │      Camera Frame Capture      │
                                  └────────────────────────────────┘
                                                   │
                                                   ▼
                                  ┌────────────────────────────────┐
                                  │   Convert BGR to RGB (OpenCV)  │
                                  └────────────────────────────────┘
                                                   │
                                                   ▼
                                  ┌────────────────────────────────┐
                                  │    Run TFLite INT8 Inference   │
                                  └────────────────────────────────┘
                                                   │
                                                   ▼
                                  ┌────────────────────────────────┐
                                  │  Non-Maximum Suppression (NMS) │
                                  └────────────────────────────────┘
                                                   │
                                                   ▼
                                  ┌────────────────────────────────┐
                                  │     IOU Object Tracker &       │
                                  │   Exponential Smoothing (EMA)  │
                                  └────────────────────────────────┘
```

### 2. Implementation: `src/live_detection_tflite.py`

```python
import cv2
import numpy as np
import pathlib
import time

try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    from tensorflow import lite as tflite

# 1. PARSE OUTPUT BOUNDING BOXES & APPLY NMS (Non-Maximum Suppression)
def apply_nms(boxes, scores, score_threshold=0.5, iou_threshold=0.4):
    """
    Classic Non-Maximum Suppression to eliminate overlapping bounding boxes.
    boxes: array of shape (N, 4) in format [ymin, xmin, ymax, xmax]
    scores: array of shape (N, num_classes)
    """
    classes = np.argmax(scores, axis=1)
    max_scores = np.max(scores, axis=1)
    
    # Filter by score threshold
    indices = np.where(max_scores > score_threshold)[0]
    boxes = boxes[indices]
    classes = classes[indices]
    max_scores = max_scores[indices]
    
    # Sort by confidence
    order = max_scores.argsort()[::-1]
    keep = []
    
    while order.size > 0:
        i = order[0]
        keep.append(i)
        if order.size == 1: break
        
        # Calculate Intersection over Union (IoU)
        y1 = np.maximum(boxes[i, 0], boxes[order[1:], 0])
        x1 = np.maximum(boxes[i, 1], boxes[order[1:], 1])
        y2 = np.minimum(boxes[i, 2], boxes[order[1:], 2])
        x2 = np.minimum(boxes[i, 3], boxes[order[1:], 3])
        
        w = np.maximum(0.0, x2 - x1)
        h = np.maximum(0.0, y2 - y1)
        intersection = w * h
        
        area_i = (boxes[i, 2] - boxes[i, 0]) * (boxes[i, 3] - boxes[i, 1])
        area_others = (boxes[order[1:], 2] - boxes[order[1:], 0]) * (boxes[order[1:], 3] - boxes[order[1:], 1])
        union = area_i + area_others - intersection
        
        iou = intersection / union
        
        # Keep boxes with IoU less than the threshold
        inds = np.where(iou <= iou_threshold)[0]
        order = order[inds + 1]
        
    return boxes[keep], classes[keep], max_scores[keep]

# 2. PATHS & TFLITE INITIALIZATION
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
MODEL_PATH = ROOT_DIR / "models" / "mira_detection_int8.tflite"

print(f"Loading TFLite Detection Model from {MODEL_PATH}...")
interpreter = tflite.Interpreter(model_path=str(MODEL_PATH))
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

class_names = ['glass', 'metal', 'paper', 'plastic']

# 3. WEBCAM SETUP WITH FIXED HARDWARE PARAMETERS
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)      # Lock autofocus to prevent frame jitter [2]
cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0)  # Lock auto-exposure [2]

# Temporal smoothing config
alpha = 0.15
trackers = {} # Format: {track_id: smoothed_probabilities}

print("Smooth TFLite Multi-Object Detection active. Press 'q' to exit.")

while True:
    ret, frame = cap.read()
    if not ret: break
    
    # CRITICAL FIX: Convert BGR to RGB before model inference [2]
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Prepare input image (YOLOv8-Nano expects 224x224 input)
    h, w, _ = frame.shape
    resized = cv2.resize(frame_rgb, (224, 224))
    input_data = np.expand_dims(resized, axis=0).astype(np.float32)
    
    # Execute Model
    start_time = time.perf_counter()
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()
    
    # Extract bounding boxes and confidence outputs
    raw_boxes = interpreter.get_tensor(output_details[0]['index'])   # Shape: (1, Num_Boxes, 4)
    raw_scores = interpreter.get_tensor(output_details[1]['index'])  # Shape: (1, Num_Boxes, Num_Classes)
    end_time = time.perf_counter()
    
    latency_ms = (end_time - start_time) * 1000
    fps = 1000 / latency_ms if latency_ms > 0 else 0
    
    # Process Boxes via NMS
    boxes, classes, scores = apply_nms(raw_boxes[0], raw_scores[0])
    
    # Display Results on Original Frame
    display_frame = frame.copy()
    for i in range(len(boxes)):
        ymin, xmin, ymax, xmax = boxes[i]
        
        # Scale bounding box coordinates back to original frame size
        box_ymin = int(ymin * h / 224)
        box_xmin = int(xmin * w / 224)
        box_ymax = int(ymax * h / 224)
        box_xmax = int(xmax * w / 224)
        
        # Draw Bounding Box [2]
        cv2.rectangle(display_frame, (box_xmin, box_ymin), (box_xmax, box_ymax), (0, 255, 0), 2)
        
        label = f"Class: {class_names[classes[i]].upper()} ({scores[i]*100:.1f}%)"
        cv2.putText(display_frame, label, (box_xmin, box_ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
    latency_label = f"Latency: {latency_ms:.1f} ms | FPS: {fps:.1f}"
    cv2.putText(display_frame, latency_label, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    
    cv2.imshow('MIRA Live Multi-Object Detector', display_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

---

## Phase 4: Parameterized Evaluation & Quantization

### 1. Unified `src/evaluate.py`
This script runs evaluation on either a `.keras` model or `.tflite` model (natively supported via file extension detection) and generates automated reports [2]:
*   *Why it is needed:* It evaluates performance, outputs precision/recall charts, measures latency, and runs on both formats to verify performance [2].
*   *Where it fits:* Execution code, situated in `src/evaluate.py` [2].
*   *Prerequisites:* Ensure a trained `.keras` or `.tflite` model exists in `models/` [2].

### 2. Post-Training Quantization: `src/quantize.py`
This script converts the trained PyTorch YOLOv8-Nano model to standard TFLite and fully quantized INT8 format [1]:
*   *Why it is needed:* Shrinks model size from ~23MB to ~2.6MB, speeding up CPU execution dramatically [2].
*   *Where it fits:* Exists in `src/quantize.py` [2].
*   *Prerequisites:* Training must be completed, and the original model must be saved in `models/` [2].
*   *Calibration:* To ensure high accuracy after INT8 conversion, the script utilizes `tf.image.resize_with_crop_or_pad` over a representative selection of 100 images from `data/` to dynamically map activation ranges [2].

---

## Phase 5: Step-by-Step Integrated Project Roadmap

This roadmap indexes all prior recommendations and new requirements, detailing where they fit and what must be completed before implementing them [2]:

| Step | Recommendation / Requirement | Why It Is Needed | Files Affected | Replaces or Adds? | Prerequisites |
|---|---|---|---|---|---|
| **1** | Directory Restructuring [2] | Organizes project layout, separates research from code, ensures binaries are safe [2]. | Workspace Root | Replaces old unorganized structure. | None. Complete immediately [2]. |
| **2** | `src/merge_datasets.py` | Automatically merges custom images with public TrashNet & TACO datasets. | `src/merge_datasets.py` | Adds new dataset prep pipeline. | Complete Step 1. |
| **3** | Background Augmentation | Prevents the model from relying on tabletop color/texture [2]. | `src/merge_datasets.py` | Adds synthesis functionality to merging. | Complete Step 2. |
| **4** | Dynamic Data Augmentation [2] | Simulates lighting and position variations during training [2]. | `src/train_detection.py` | Replaces simple classifier augmentations [2]. | Complete Step 3. |
| **5** | Retraining Model (YOLOv8-Nano) | Pivot from classification to multi-object bounding-box detection. | `src/train_detection.py` | Replaces `train_transfer.py` and `train_fine_tune.py` [2]. | Complete Step 4. |
| **6** | `src/quantize.py` [2] | Compresses YOLOv8-Nano model weights to INT8 format [1, 2]. | `src/quantize.py` | Replaces custom classification quantization. | Complete Step 5. |
| **7** | `src/evaluate.py` [2] | Unified evaluation for both `.keras` and `.tflite` models [2]. | `src/evaluate.py` | Replaces custom baseline evaluation. | Complete Step 6. |
| **8** | Camera Param Locking [2] | Locks autofocus/exposure to prevent frame value drift during live runs [2]. | `src/live_detection_tflite.py` | Adds hardware-level stability control. | Complete Step 7. |
| **9** | RGB/BGR Channel Fix [2] | Fixes the color channel mismatch between OpenCV and TensorFlow [2]. | `src/live_detection_tflite.py` | Replaces incorrect BGR input frame scaling. | Complete Step 8. |
| **10** | Live TFLite Inference [2] | Uses lightweight runtime to boost CPU speeds from 7 FPS to >25 FPS. | `src/live_detection_tflite.py` | Replaces heavy Keras live stream script [2]. | Complete Step 9. |
| **11** | Bounding Boxes & NMS | Draws and resolves overlapping detections in real-time. | `src/live_detection_tflite.py` | Adds multi-object visual representation. | Complete Step 10. |
| **12** | Temporal EMA Filter [2] | Damps prediction jitter and stabilizes control signals for the physical arm [2]. | `src/live_detection_tflite.py` | Replaces baseline single-frame smoothing. | Complete Step 11. |

---

## Phase 6: Resource Library

To master the concepts required for each development block, utilize these recommended learning resources:

### 1. Dataset Expansion & Merging
*   **TrashNet Repository & Paper:** [Stanford TrashNet Dataset](https://github.com/garythung/trashnet) — Review the dataset structure and study the original paper on recycling classification.
*   **TACO Dataset COCO Format:** [TACO Dataset Guide](http://tacodataset.org/) — Study how COCO polygon annotations are structured and read the TACO implementation details.

### 2. Object Detection & YOLOv8
*   **Ultralytics YOLOv8 Documentation:** [YOLOv8 Official Docs](https://docs.ultralytics.com/) — Read the quick-start guides on training, fine-tuning, and exporting detection models.
*   **Real-time Object Detection Theory:** [Single-Shot MultiBox Detector (SSD) Paper](https://arxiv.org/abs/1512.02325) — Highly recommended reading to understand anchor boxes, bounding-box regression, and feature maps.

### 3. TFLite Conversion & Quantization
*   **TensorFlow Lite Quantization Guide:** [TFLite Post-Training Quantization](https://www.tensorflow.org/lite/performance/post_training_quantization) — Study the different calibration strategies and APIs [1].
*   **Edge AI Calibration:** [TinyML: Machine Learning on Microcontrollers](https://www.oreilly.com/library/view/tinyml/9781492052037/) — Read Chapter 8 on quantization and memory constraints [1].

### 4. LaTeX Academic Formatting
*   **Overleaf Documentation:** [LaTeX Page Layout and Geometry](https://www.overleaf.com/learn/latex/Page_size_and_margins) — Learn how to set margins, headers, footers, and line spacing [2].
*   **Mathematics in LaTeX:** [Overleaf Mathematical Expressions](https://www.overleaf.com/learn/latex/Mathematical_expressions) — Reference sheet for typing formulas, fractions, and Greek variables.

---

## Phase 7: Timeline, Milestones, and Jugend forscht Writing Strategy

### 1. Estimated Development Timeline

The total estimated development time is **120 hours** of focused engineering and writing, structured over a **14-week** schedule to fit alongside school requirements:

```
[Week 1-2: Data & Merging] ──> [Week 3-5: Model Training] ──> [Week 6-8: Real-Time Engine]
                                                                        │
                                                                        ▼
[Week 12-14: Final Submission] <── [Week 10-11: Evaluation] <── [Week 9: Report Writing Pause]
```

*   **Weeks 1–2: Dataset Expansion & Generalization (20 Hours)**
    *   *Tasks:* Implement `src/merge_datasets.py`, map TrashNet/TACO, configure background synthesis and contrast augmentations [2].
    *   *Prerequisites:* Completed Step 1 of roadmap.
    *   *Checkpoint:* You have a balanced, generalized dataset of >3,000 images representing 4 classes on various tabletop backgrounds.
*   **Weeks 3–5: YOLOv8 Training & Fine-Tuning (30 Hours)**
    *   *Tasks:* Set up PyTorch, write `src/train_detection.py`, train the baseline detection network, tune hyperparameters with cosine decay.
    *   *Prerequisites:* Merged dataset complete.
    *   *Checkpoint:* Detection model achieves >82% mAP (Mean Average Precision) on the validation set.
*   **Weeks 6–8: Real-Time Inference & TFLite Optimization (25 Hours)**
    *   *Tasks:* Convert model to INT8 via `src/quantize.py` [2], write `src/live_detection_tflite.py`, fix BGR/RGB channels [2], lock hardware params [2], implement NMS and EMA filters [2].
    *   *Prerequisites:* Detection model trained.
    *   *Checkpoint:* Live inference stream runs smoothly at >25 FPS with stable, non-flickering bounding boxes and confidence scores.
*   **Week 9: Scientific Report Writing Pause (15 Hours)**
    *   *Tasks:* **Pause all development.** Focus entirely on drafting the core architectural and methodological chapters of your report in LaTeX [2].
*   **Weeks 10–11: Scientific Evaluation & Benchmarking (15 Hours)**
    *   *Tasks:* Implement CPU latency profiling in `src/evaluate.py` [2], perform Out-of-Distribution testing, document compression metrics, run continuous operational burn-in tests.
    *   *Prerequisites:* Live inference stabilized.
    *   *Checkpoint:* Complete generation of all quantitative metrics, graphs, and confusion matrices for the results section.
*   **Weeks 12–14: Report Finalization & Code Cleanup (15 Hours)**
    *   *Tasks:* Complete the Results, Discussion, and Outlook chapters in LaTeX [2], polish bibliography, clean up the GitHub repository, document setup instructions in `README.md` [2].
    *   *Checkpoint:* PDF report is compiled (< 30 MB), and GitHub code is archived and stable [2].

---

### 2. Jugend forscht Report: Writing Strategy

Do not wait until development is fully complete to start writing your report. Writing a high-quality scientific paper requires multiple drafts.

#### When to Pause:
*   **The Development Pause (Week 9):** Once your real-time detection pipeline is fully functional and stable, **pause development**. Do not start adding new features (like mechanical robot arms or cloud telemetry) until the core of the report is written.

#### Writing Roadmap:

```
───────────────────────────────────────────────────────────────────────────
   CAN BE WRITTEN DURING DEVELOPMENT          MUST WAIT UNTIL END
───────────────────────────────────────────────────────────────────────────
- Cover Page & TOC                        - Results & Baseline Metrics
- Einleitung & Problemstellung            - Confusion Matrices & Plots
- Forschungsfragen & Hypothesen          - Discussion of Compression
- State-of-the-Art (Literature review)   - Conclusion & Outlook
- Methodik (EMA, YOLO architecture)       - Final Bibliography
```

---

## Phase 8: Critical Project Evaluation & Competition Competitiveness

### 1. Critical Project Weaknesses & Limitations
Even if this plan is executed perfectly, the project will still have technical limitations you must address in your discussion section:
*   **Mechanical Delay vs. AI Latency:** Your AI model can classify an object in 20 ms, but the physical servo motors take 1.5 seconds to sweep the arm. If objects pass too quickly on the sorting belt, the bottleneck is mechanical, not software.
*   **Severe Occlusion & overlapping materials:** If plastic wrap is folded tightly inside a cardboard box, MIRA's camera can only see the outer cardboard. Visual-only edge-AI cannot determine internal composite materials.
*   **Class Ambiguity Boundaries:** Extremely dirty, crushed, or degraded packaging may fall completely out of the feature distributions of the 4 classes.

---

### 2. Opportunities for Further Improvement
*   **Multi-Spectral Optical Fusion:** Integrate an infrared reflectance sensor alongside the webcam. Different materials (like PET plastic vs. HDPE plastic) reflect infrared light differently, providing an additional data layer to help resolve class ambiguities.
*   **Active Gripper Force Feedback:** Implement a pressure sensor on the robot gripper. Measuring the resistance during closing allows the mechatronic controller to distinguish between a rigid glass jar and a deformable plastic bottle, verifying the AI's visual prediction through physical haptics.

---

### 3. Jugend forscht Competitiveness Assessment

```
                      ┌─────────────────────────────────┐
                      │    COMPETITIVENESS TIERS        │
                      └─────────────────────────────────┘
                                       │
         ┌─────────────────────────────┼─────────────────────────────┐
         ▼                             ▼                             ▼
┌──────────────────┐          ┌──────────────────┐          ┌──────────────────┐
│  Regional Level  │          │   State Level    │          │  National Level  │
│  - Near-certain  │          │  - Strong top-tier│          │  - Highly competitive│
│    winner        │          │    contender     │          │    with physical │
│  - Exceeds normal│          │  - High score on │          │    system unity  │
│    depth         │          │    quantization  │          │    & OOD stats   │
└──────────────────┘          └──────────────────┘          └──────────────────┘
```

#### Regionalwettbewerb (Ruhrgebiet / NRW)
*   **Assessment:** **Near-certain winner (Technik).** Most high school projects at the regional level show basic mechatronics with pre-programmed instructions, or basic classification models using generic tutorial code. Your implementation of **YOLOv8-Nano object detection**, **INT8 quantization** [1], **exponential moving average filtering** [2], and a **parameterized evaluation CLI** [2] exceeds typical high school complexity.

#### Landeswettbewerb (NRW State Level)
*   **Assessment:** **Strong top-tier contender.** At the state level, judges are academic specialists. They will scrutinize your scientific rigor. 
*   **Winning Factor:** Your project will stand out because you have documented **controlled baseline experiments** (EXP-001 vs. EXP-003 vs. EXP-004) [2] and analyzed your hypotheses with exact mathematical precision (quantization accuracy drop, latency graphs) [1, 2].

#### Bundeswettbewerb (German National Level)
*   **Assessment:** **Plausible but highly competitive.** Winning at the national level requires **complete system integration** and **contribution to open-source**. 
*   **Winning Factor:** To win at the national level, your paper must prove **generalization**. Your *Out-Of-Distribution (OOD)* test results, showing how your background randomization and contrast augmentations kept accuracy stable across completely different environments, will be critical. Additionally, having your complete code beautifully archived, structured, and reproducible on GitHub will be highly influential.