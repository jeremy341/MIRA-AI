# MIRA — Troubleshooting Guide

Common issues and solutions.

---

## Camera & Hardware

### ❌ "Failed to open video capture device"

**Cause:** Webcam not connected or in use by another application.

**Solutions:**
```powershell
# Try a different camera index
.\mira live --camera 1
.\mira live --camera 2

# Check if another app is using the camera (Teams, Zoom, etc.)
# Close those apps and retry
```

### ❌ Black/blank video feed

**Cause:** Camera needs warmup or exposure correction needed.

**Solution:**
- The application discards 10 warmup frames automatically
- If still black, check camera lens for obstructions
- Try adjusting lighting in your environment

### ❌ Very low FPS (~1-2 FPS)

**Cause:** Model too heavy, or inference running on CPU.

**Solutions:**
```powershell
# Use quantized model (smaller, faster)
.\mira live --model mira_detector_tabletop_int8_320.tflite

# Lower resolution (doesn't affect detection accuracy, only display)
.\mira live --resolution 640x360

# Close other CPU-intensive applications
```

**Note:** On CPU, expect:
- `mira_detector_wild_v2.pt` → ~7-10 FPS
- `mira_detector_tabletop_int8_320.tflite` → ~9 FPS
- Classification only → ~97 FPS

---

## Model & Inference

### ❌ Model not found error

```
FileNotFoundError: Model 'my_model.pt' not found in C:\...\models\
```

**Solution:**
```powershell
# List available models
.\mira live --help

# Or check the directory
Get-ChildItem models/ -File
```

### ❌ "Failed to infer" or inference crashes

**Cause:** Wrong input size, corrupted model, or missing dependencies.

**Solutions:**
```powershell
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check TensorFlow/PyTorch installation
python -c "import tensorflow; print(tensorflow.__version__)"
python -c "import torch; print(torch.__version__)"
```

### ❌ Poor detection accuracy / missed objects

**Possible causes:**
1. **Model overfitting** — trained on clean tabletop, your environment is messy
2. **Wrong model for your use case** — tabletop model vs wild model mismatch
3. **Lighting issues** — too dark, shadows, reflections confuse the detector
4. **Scale mismatch** — objects too small or too large for training data

**Solutions:**
```powershell
# Try different models
.\mira live --model mira_detector_wild_v2.pt          # Better for messy backgrounds
.\mira live --model mira_detector_tabletop_int8_320.tflite  # Better for clean tabletop

# Check detection confidence
.\mira dashboard
# Adjust "Confidence Threshold" slider to see how it affects detections
```

### ❌ Trash class not detected (0% detection)

**Reason:** Trash is the weakest class (63.9% mAP50). The training data was too diverse — all residual waste mixes together.

**Workaround:**
- Lower confidence threshold in dashboard to catch weak detections
- Retrain on cleaner trash category data if this is critical

---

## Dashboard Issues

### ❌ Dashboard crashes or won't load

```
StreamlitError: ...
```

**Solution:**
```powershell
# Reinstall Streamlit
pip install streamlit==1.58.0 --force-reinstall

# Try launching again
.\mira dashboard
```

### ❌ Dashboard runs but camera feed is stuck

**Cause:** Model inference taking too long, or old frames buffering.

**Solutions:**
```powershell
# Use faster model
# In dashboard sidebar, select mira_detector_tabletop_int8_320.tflite

# Lower inference resolution
# In sidebar: set "Inference Resolution (imgsz)" to 320
```

---

## Training & Retraining

### ❌ "No such file or dataset" when training

**Cause:** Dataset not found or not in expected location.

**Solutions:**
```powershell
# Build dataset first
.\mira data-build

# Or manually check paths
Get-ChildItem yolo_data/
```

### ❌ Out of memory (OOM) during training

**Cause:** Batch size too large for your GPU/CPU.

**Solution:** Edit the training script and reduce batch size (line in reference/train_detection.py):
```python
batch = 8  # Try 4 or 2 if OOM
```

---

## Installation Issues

### ❌ "Python not found"

**Cause:** Python not in PATH.

**Solution:**
```powershell
# Check if Python is installed
python --version

# If not, download from python.org and add to PATH during install
```

### ❌ "ModuleNotFoundError: No module named 'xyz'"

**Cause:** Dependency not installed.

**Solution:**
```powershell
# Reinstall all dependencies
pip install -r requirements.txt

# Or install specific package
pip install ultralytics
```

---

## Raspberry Pi Deployment

See [`DEPLOYMENT.md`](DEPLOYMENT.md) for edge device setup.

---

## Still stuck?

1. Check if your issue is in the [Known Limitations](README.md#9-known-limitations) section
2. Look at the full [README.md](README.md)
3. Check internet/camera connection
4. Restart the script

If you find a new issue, consider creating a GitHub issue!
