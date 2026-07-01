
***



# MIRA — Machine Intelligence for Recycling Automation

MIRA is the vision and AI "brain" for an autonomous robotic sorting arm designed to classify recyclable materials. The project is structured to transition from offline training to real-time, low-latency edge deployment.

---

## 1. Project Directory Structure

This is the structure of the MIRA-AI repository, with key directories and files explained:

```text
MIRA-AI/
├── .venv/                         # Virtual environment (ignored)
├── data/                          # Raw labeled dataset (ignored)
│   ├── glass/
│   ├── metal/
│   ├── paper/
│   └── plastic/
├── doc/                           # JuFo documentation, timeline, and resources
│   ├── JuFo_Hypothesis_and_Timeline.md
│   ├── JuFo_Report_Template.md
│   └── MIRA_Learning_Resources.md
├── models/                        # Saved neural network binaries (.keras)
│   ├── mira_waste_model.keras     # EXP-001 Baseline
│   ├── mira_transfer_model.keras  # EXP-002 Frozen MobileNetV2
│   └── mira_fine_tuned_model.keras # EXP-003 Fine-Tuned MobileNetV2
├── reference/                     # Sandbox, legacy scripts, and educational files
│   ├── evaluate_reference.py
│   └── tutorial.py
├── results/                       # Generated confusion matrices, curves, and reports
│   ├── EXP-001_Baseline/
│   ├── EXP-002_MobileNetV2/
│   ├── EXP-003_FineTuning/
│   └── experiments_log.md         # Markdown ledger tracking all experiments
├── src/                           # Pure execution source code
│   ├── capture_frame.py           # Keyboard-controlled raw image collection tool
│   ├── evaluate.py                # Parameterized evaluation script (argparse)
│   ├── live_inference.py          # Real-time webcam inference loop
│   ├── train_baseline.py          # Custom 3-layer CNN pipeline
│   ├── train_transfer.py          # Frozen MobileNetV2 pipeline
│   ├── train_fine_tune.py         # MobileNetV2 layer 100+ fine-tuning pipeline
│   └── visualize_dataset.py       # Dataset distribution checking and visualization
├── .gitignore
└── LICENSE
```

---

## 2. Installation & Setup

1. **Activate Virtual Environment:**
   Ensure you are using your configured virtual environment (`.venv`).
   ```bash
   # Windows PowerShell
   .venv\Scripts\Activate.ps1
   ```

2. **Install Dependencies:**
   Install the required core machine learning and visualization packages:
   ```bash
   pip install tensorflow numpy opencv-python matplotlib scikit-learn
   ```

---

## 3. How to Run the Code

### A. Dataset Collection & Inspection
To collect fresh, original datasets or visually inspect class balances:

*   **Capture Labeled Frames:** Runs a live webcam stream. Press `1` (glass), `2` (metal), `3` (paper), or `4` (plastic) to save a timestamped frame directly into `/data/`. Press `q` to quit.
    ```bash
    python src/capture_frame.py
    ```
*   **Visualize the Dataset:** Counts images across your directories, outputs the exact distribution, and renders a random sample grid.
    ```bash
    python src/visualize_dataset.py
    ```

### B. Training Pipelines
To re-train any of the experimental setups, run the corresponding training script. Trained models will automatically save to the central `/models/` directory:

```bash
# EXP-001: Baseline Custom CNN (180x180 resolution)
python src/train_baseline.py

# EXP-002: MobileNetV2 Transfer Learning (224x224, frozen base)
python src/train_transfer.py

# EXP-003: MobileNetV2 Fine-Tuning (224x224, unfrozen layers 100-154, low LR)
python src/train_fine_tune.py
```

### C. Unified Evaluation Pipeline (`evaluate.py`)
Evaluation metrics, confusion matrices, and classification reports are handled by a single, parameterized command-line tool. It dynamically scales image inputs to fit the loaded architecture and calculates **mean CPU inference latency** per image:

```bash
# Format: python src/evaluate.py --model [MODEL_NAME] --exp [EXP_NAME]

# 1. Evaluate Baseline Model (EXP-001)
python src/evaluate.py --model mira_waste_model.keras --exp EXP-001_Baseline

# 2. Evaluate Frozen Transfer Model (EXP-002)
python src/evaluate.py --model mira_transfer_model.keras --exp EXP-002_MobileNetV2

# 3. Evaluate Fine-Tuned Model (EXP-003)
python src/evaluate.py --model mira_fine_tuned_model.keras --exp EXP-003_FineTuning
```
*All reports (`classification_report.txt`) and matrices (`confusion_matrix.png`) are saved directly to `/results/[EXP_NAME]/`.*

### D. Real-Time Live Webcam Inference
To deploy the final fine-tuned model onto your live webcam feed for real-time inference (calculating real-time latency and FPS on-screen):
```bash
python src/live_inference.py
```

---

## 4. Current Experimental Results (Abitur-Prestige Baseline)

We maintain a rigorous comparative ledger of all architectural versions evaluated against our scaled dataset of **796 images** (80/20 train/val split):

| Experiment Metric | EXP-001 (Baseline CNN) | EXP-002 (MobileNetV2 Frozen) | EXP-003 (Two-Stage Fine-Tuning) |
|---|---|---|---|
| **Model Size (MB)** | 15.22 MB | 8.61 MB | 8.63 MB |
| **Validation Accuracy** | 61.00% | 84.28% | **87.42%** |
| **Validation Loss** | 1.0633 | 0.5659 | **0.3148** |
| **Paper Recall** | 0.07 | 0.81 | **0.64 (Precision: 0.96)** |
| **Metal Recall** | 0.80 | 0.76 | **0.98 (Precision: 0.77)** |

---

## 5. Upcoming Milestones
*   **Phase F (Quantization):** Export the baseline FP32 `.keras` network to `.tflite` format, applying post-training INT8 quantization to measure parameter size reduction and evaluate any CPU latency advantages versus accuracy degradation.
*   **Phase G (Embedded Integration):** Connect the live inference output to an ESP32 microcontroller over Serial/PWM to drive physical servo motor routines.
```