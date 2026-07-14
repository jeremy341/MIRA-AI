
***

# MIRA — Jugend forscht 2027 Scientific Report Writing Context
**Project Title:** MIRA (Machine Intelligence for Recycling Automation)  
**Sponsoring Category:** Technik (Technology) / Informatik (Computer Science) [2]  
**Author:** Jeremy Darko, Oberstufe, Gymnasium Mülheim an der Ruhr, Germany [2]  
**Submission Date:** January 15, 2027  
**Code Repository:** https://github.com/jeremy341/MIRA-AI  

---

## 1. Executive Summary & Core Objective
MIRA is an autonomous, edge-AI-optimized mechatronic sorting system designed to classify and physically separate five waste categories: Glass, Metal, Paper, Plastic, and Trash (Reject) [2]. The system's "brain" transitions from a single-object image classifier (Stage A) to a real-time, multi-object spatial detector with tracking (Stage B), running locally on a low-cost, low-power single-board computer (Raspberry Pi) [2]. The mechatronic "body" is a custom 3-DOF robotic arm controlled in C++ via an ESP32 microcontroller [2].

---

## 2. Research Questions & Hypotheses
The scientific inquiry is structured around four measurable hypotheses [2]:
*   **Hypothese 1 (Transfer Learning):** A pre-trained MobileNetV2 architecture with selective fine-tuning (EXP-003) will outperform a custom shallow Convolutional Neural Network (EXP-001) trained from scratch by at least 15 percentage points in validation accuracy on a small, domain-specific dataset.
*   **Hypothese 2 (Model Compression):** Post-training 8-bit integer quantization (INT8) will compress the model binary size by at least 75% (4x) and reduce CPU execution latency by over 40% [2], with an accuracy loss of less than 2 percentage points compared to the baseline FP32 model [2].
*   **Hypothese 3 (Spatial Tracking):** Transitioning from global image classification to single-stage object detection (YOLOv8-Nano) enables simultaneous tracking of multiple overlapping objects at a real-time frame rate of $>15$ FPS on a standard CPU [2].
*   **Hypothese 4 (Temporal Damping):** An Exponential Moving Average (EMA) filter applied to the raw class probabilities with a smoothing factor of $\alpha = 0.15$ will stabilize the output signal, preventing physical jitter of the robotic arm's servo motors without introducing critical mechanical lag [2].

---

## 3. The Dataset Evolution
To construct MIRA's dataset, several iterations and data-engineering pivots were performed [2]:

### A. Custom Raw Dataset
Initially, 796 custom images were captured via a 720p webcam under controlled laboratory conditions, split into four classes (glass, metal, paper, plastic).

### B. The Otsu Thresholding / Auto-Labeling Failure (The GIGO Effect)
An attempt was made to automate bounding-box annotations for YOLOv8 using classical computer vision (Canny Edge Detection + Otsu's Thresholding) [2]. 
*   **Failure Mode:** Harsh lighting and specular highlights (glare) on the white tabletop caused the algorithm to detect the entire table edge and shadows as the largest contour.
*   **Consequence:** The resulting bounding boxes wrapped around the entire frame instead of the target object. During training, the YOLOv8 model learned that the table itself was "plastic" or "paper" (Garbage In, Garbage Out).
*   **Scientific Pivot:** The corrupted custom annotations were completely purged.

### C. Public Dataset Integration & Class Remapping
To bypass manual annotation, the original Stanford TrashNet dataset (clean objects on solid white backgrounds) was combined with a highly diverse, hand-labeled "wild" packaging dataset from Roboflow (TACO-based, containing packaging in grass, dirt, and cluttered environments) [2].
*   **The 64-to-5 Class Mapping:** The public dataset contained 64 highly specific classes. A Python script (`prepare_super_dataset.py`) was written to programmatically map these 64 categories into MIRA's 5 target classes [2]:
    *   *Glass (ID 0):* Broken glass, glass bottles, jars [2].
    *   *Metal (ID 1):* Aerosols, foil, drink cans, food cans, metal lids, pop tabs [2].
    *   *Paper (ID 2):* Corrugated cartons, drink cartons, egg cartons, paper bags, tissues, wrapping paper [2].
    *   *Plastic (ID 3):* Clear plastic bottles, crisp packets, foam cups, garbage bags, plastic wrapping [2].
    *   *Trash (ID 4):* Batteries, carded blister packs, cigarettes, food waste, unlabeled litter [2].

---

## 4. Quantitative Results & Benchmarks Ledger

This data constitutes the core of your scientific evaluation. Every table in the results section must reference these numbers [2]:

| Experiment | Task | Model Architecture | Dataset Size | Training Platform | Size (Disk) | Accuracy / mAP50 | CPU Latency |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **EXP-001** | Classif. | Custom CNN (from scratch) | 126 images | Local CPU | 15.22 MB | 61.00% | ~45.00 ms |
| **EXP-002** | Classif. | MobileNetV2 (Frozen Base) | 796 images | Local CPU | 8.49 MB | 84.28% | 38.00 ms |
| **EXP-003** | Classif. | MobileNetV2 (Fine-Tuned 100+) | 796 images | Local CPU | 23.48 MB | **87.42%** | 40.00 ms |
| **EXP-004** | Classif. | Quantized INT8 TFLite (320px) | 100 Calib. | Colab T4 GPU [1] | **2.61 MB** | **87.35%** | **10.32 ms** |
| **EXP-006** | Detection | YOLOv8-Nano (Wild Dataset) | 3,300 images | Colab T4 GPU [1] | 6.20 MB | 39.40% | 40.40 ms |
| **EXP-008** | Detection | YOLOv8-Nano (Pristine Tabletop) | 2,527 images | Kaggle T4 GPU [1] | 6.20 MB | **72.80%** | 40.40 ms |
| **EXP-009** | Detection | Quantized YOLOv8-Nano (320px) | 100 Calib. | Kaggle T4 GPU [1] | **3.18 MB** | **72.80%** | **10.32 ms** |
| **EXP-010** | Detection | YOLOv8-Nano (Wild V2) | 3,365 images | Kaggle T4 GPU [1] | 6.20 MB | 35.00% | 40.40 ms |
| **EXP-011** | Detection | Quantized Wild V2 (320px) | 100 Calib. | Kaggle T4 GPU [1] | **3.16 MB** | **35.00%** | **10.32 ms** |

---

## 5. Key Scientific Discoveries & Problem Solving

### A. The "Silent" RGB/BGR Color Channel Mismatch
During live webcam deployments, the classification accuracy of our trained MobileNetV2 model dropped from 87% to under 40% without throwing any syntax errors [2].
*   **The Cause:** TensorFlow/Keras trains on images in **RGB** format (Red, Green, Blue). OpenCV's webcam capture (`cv2.VideoCapture`), however, outputs frames in **BGR** format (Blue, Green, Red) [2]. The swapped color channels inverted the spectral features (e.g., rendering warm cardboard colors as blue), causing severe classification failures.
*   **The Fix:** Implemented `cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB)` [2] right before the inference step, completely restoring real-time accuracy to match the validation baseline [2].

### B. Data-Centric AI: EXP-006 vs. EXP-008
*   **EXP-006 (Wild Data):** Trained on highly diverse, cluttered backgrounds (forests, beaches) for 100 epochs (3.3 hours) [2]. mAP50: **39.4%** [2].
*   **EXP-008 (Pristine Tabletop):** Trained on clean, white-background TrashNet images for 50 epochs (18.5 minutes) [1, 2]. mAP50: **72.8%** [1, 2].
*   **Scientific Insight:** Because our target environment is a structured sorting tabletop, training on outdoor background noise is inefficient. Purging "wild" background noise and focusing on high-quality, clean images nearly doubled the model's accuracy on the target domain while halving the training time.

### C. Static TFLite Tensor Dimension Mismatch
During live Streamlit testing with a $320 \times 320$ inference resolution, a `ValueError: Dimension mismatch` was thrown by the TFLite Interpreter [2].
*   **The Cause:** Unlike standard PyTorch models, fully quantized TFLite models are compiled with **static tensor dimensions** [2]. A model quantized at $640 \times 640$ in Colab cannot accept a $320 \times 320$ input tensor [2].
*   **The Fix:** Re-quantized the model in the cloud under explicit $320 \times 320$ parameters (`imgsz=320`), reducing floating-point operations by exactly 75% on the local CPU [2].

---

## 6. System Architecture & Mechatronics Integration

```text
               [ Real-Time 720p Webcam Feed ]
                             │
                             ▼
               [ 16:9 to 4:3 Crop & Scale (640x360) ]
                             │
                             ▼
         [ PyTorch / TFLite INT8 Object Detection ]
         - Bounding Box & Centroid Coordinates (X, Y)
         - Probability Filtering (conf=0.35, iou=0.45)
                             │
                             ▼
         [ Queue-Based Multithreaded Serial Sender ]
                             │ (USB COM Port, 115200 Baud)
                             ▼
         [ ESP32 Microcontroller (C++ Firmware) ]
         - Receives Serial Packet
         - Calculates Inverse Kinematics
         - Sweeps Servos (PWM, GPIO 18)
         - Sends 'done' Handshake to release inference lock
```

### Mechatronic Handshake Protocol
To synchronize the high-speed AI (21.8 FPS / 46.0 ms) with the slow physical movement of the 3-DOF robot arm (which takes ~1.5s to sweep and return), an **Inference Lock & Handshake** was designed [2]:
1.  Python detects a target recycling item, locks the camera loop, and transmits the command (e.g., `metal 120\n`) to the ESP32 [2].
2.  The ESP32 sweeps the servo to 120 degrees, drops the item, returns the arm to center, and prints `done\n` back over the serial interface [2].
3.  Python receives `done\n`, releases the inference lock, and begins scanning for the next item [2].

---

## 7. Official Jugend forscht LaTeX Formatting Requirements
To compile the document locally via VS Code & MiKTeX without errors [2]:
*   **Page Limit:** Maximum of 15 DIN-A4 pages [2]. Title page, Project Overview, Table of Contents, Bibliography, and Acknowledgments are **excluded** from this limit [2].
*   **Page Numbering:** Use Roman numerals (`I, II, III...`) for the excluded front-matter, and switch to Arabic numerals (`1, 2, 3...`) starting on Page 1 of your introduction [2].
*   **Margins:** Left: $\ge$ 2.5 cm, Right: $\ge$ 2.5 cm, Top: $\ge$ 2.5 cm, Bottom: $\ge$ 2.0 cm [2].
*   **Line Spacing:** Exactly 1.5 spacing [2].
*   **Font:** Times New Roman, minimum size 10pt (We use 11pt) [2].
*   **Appendix:** No separate Appendix is permitted under national rules [2]. Important code listings must be integrated directly into the report chapters [2].

---

## Instructions for the AI:
You are now fully initialized with the entire context of MIRA, including its development history, raw metrics, and structural requirements [2]. Use this dense context to write scientifically rigorous LaTeX files or explain any algorithmic transitions of the project [2]. Do not invent results, maintain an objective academic tone, and never use emojis.
```

