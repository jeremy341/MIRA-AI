# MIRA — Quick Start Guide

Get MIRA running in **3 minutes**.

## 1. Install (1 min)

```powershell
git clone https://github.com/jeremy341/MIRA-AI.git
cd MIRA-AI
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2. Verify (1 min)

```powershell
.\mira live
```

Press `q` to quit. If you see a webcam window with bounding boxes, **you're done!**

## 3. Explore (1 min)

```powershell
# Use a different model
.\mira live --model mira_detector_wild_v2.pt

# Try the web dashboard
.\mira dashboard
# Opens browser at localhost:8501

# Collect your own training data
python src/capture_frame.py
```

---

## Common Next Steps

| Goal | Command |
|---|---|
| **Test best model** | `.\mira live --model mira_detector_wild_v2.pt` |
| **Evaluate on validation set** | `.\mira eval-yolo --model mira_detector_wild_v2.pt` |
| **Retrain classifier** | `.\mira train-tune` |
| **Retrain detector** | `.\mira train-detection` |
| **View all options** | `.\mira --help` |

---

## Troubleshooting

**Webcam not detected?**
```powershell
# Try a different camera index
.\mira live --camera 1
```

**Slow inference?**
```powershell
# Use quantized (faster, smaller)
.\mira live --model mira_detector_tabletop_int8_320.tflite

# Or lower resolution
.\mira live --resolution 640x360
```

**Permission denied errors?**
- Make sure Python is installed correctly
- Try running PowerShell as Administrator

See [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) for more issues.

---

For full documentation, see [`README.md`](README.md).
