# MIRA — Deployment Guide

Deploy MIRA on Raspberry Pi and other edge devices.

---

## Target Hardware

| Device | RAM | CPU | Supported? | Notes |
|---|---|---|---|---|
| **Raspberry Pi Zero 2W** | 512 MB | ARMv7 (4 cores) | ⚠️ Partial | Quantized models only (~9 FPS) |
| **Raspberry Pi 4 (4GB)** | 4 GB | ARMv8 (4 cores) | ✅ Full | PyTorch + TFLite (~10-15 FPS) |
| **Raspberry Pi 5** | 4-8 GB | ARMv8 (8 cores) | ✅ Full | Best performance (~20+ FPS) |
| **Jetson Nano** | 4 GB | ARM64 + GPU | ✅ Full | CUDA-accelerated (~30+ FPS) |
| **Generic x86 Linux** | 2+ GB | Any | ✅ Full | Same as desktop setup |

**Recommendation for sorting robot:** Raspberry Pi 4 (4GB) or Pi 5

---

## Installation on Raspberry Pi 4

### Prerequisites

- Raspberry Pi 4 (4GB RAM) with OS installed (Raspberry Pi OS Bookworm recommended)
- USB Webcam
- 32+ GB microSD card
- Power supply (5V/3A minimum)
- Network access (WiFi or Ethernet)

### Step 1: Update System

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3.11-venv python3-pip git libatlas-base-dev libjasper-dev libopenjp2-7 libtiff5 libjasper1
```

### Step 2: Clone Repository

```bash
cd ~
git clone https://github.com/jeremy341/MIRA-AI.git
cd MIRA-AI
```

### Step 3: Create Virtual Environment

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
```

### Step 4: Install Dependencies

```bash
# Install with specific versions for Pi compatibility
pip install -r requirements.txt

# If issues, install individually:
pip install opencv-python tensorflow tflite-runtime ultralytics streamlit
```

**Note:** On Pi, some packages take 10-30 minutes to compile. Be patient!

### Step 5: Verify Installation

```bash
# Test with default model (uses tabletop quantized)
python src/live_detection.py --model mira_detector_tabletop_int8_320.tflite

# Or use the CLI wrapper
python src/cli.py live --model mira_detector_tabletop_int8_320.tflite
```

Press `q` to exit.

---

## Recommended Deployment Models

### For Raspberry Pi Zero 2W

```bash
# ONLY quantized models will work at acceptable speed
python src/live_detection.py --model mira_detector_tabletop_int8_320.tflite

# Expected performance:
# - FPS: ~9
# - Latency: ~110 ms per frame
# - Memory: ~180 MB
```

### For Raspberry Pi 4 (4GB) — **RECOMMENDED**

```bash
# Best accuracy (PyTorch)
python src/live_detection.py --model mira_detector_wild_v2.pt

# Expected performance:
# - FPS: ~10-12
# - Latency: ~85 ms per frame
# - Memory: ~400 MB
```

### For Raspberry Pi 5 / Jetson

```bash
# Full performance
python src/live_detection.py --model mira_detector_wild_v2.pt

# Expected performance:
# - FPS: ~20+ (Jetson: ~30+)
# - Latency: ~40 ms (Jetson: ~25 ms)
# - Memory: ~400-600 MB
```

---

## Performance Optimization on Pi

### 1. Enable Hardware Acceleration

**For Pi 4/5 (VideoCore GPU):**
```bash
# TensorFlow can use GPU delegation (optional, minimal improvement)
# Already enabled in our TFLite model path

# For faster MJPEG decoding:
# Already optimized in live_detection.py with MJPG codec + DirectShow
```

**For Jetson (CUDA):**
```bash
# Install CUDA-enabled TensorFlow
pip install tensorflow-gpu-jetson
```

### 2. Reduce Inference Resolution

```bash
# Faster inference at lower quality
python src/live_detection.py --model mira_detector_tabletop_int8_320.tflite
# Model runs at 320×320 internally (already optimized)
```

### 3. Lower Camera Capture Resolution

```bash
# Reduces USB bandwidth, faster processing
python src/live_detection.py --resolution 640x360 --model mira_detector_tabletop_int8_320.tflite
```

### 4. Disable Unnecessary Features

In `dashboard.py`, comment out:
- Real-time inventory tracking (line ~77)
- ByteTrack (line ~40, set value=False)

---

## Running as a Service (Autostart)

### Create systemd Service (Pi 4)

```bash
sudo nano /etc/systemd/system/mira.service
```

**Paste:**
```ini
[Unit]
Description=MIRA Sorting Robot
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/MIRA-AI
Environment="PATH=/home/pi/MIRA-AI/.venv/bin"
ExecStart=/home/pi/MIRA-AI/.venv/bin/python src/live_detection.py --model mira_detector_wild_v2.pt
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable mira
sudo systemctl start mira
```

**Monitor:**
```bash
sudo systemctl status mira
sudo journalctl -u mira -f
```

---

## Logging & Monitoring

### Capture Inference Metrics

Modify `live_detection.py` line ~150:

```python
# Add after each inference:
fps = 1.0 / elapsed_time
with open("logs/performance.csv", "a") as f:
    f.write(f"{datetime.now()},{model_name},{fps},{latency_ms}\n")
```

### Monitor Resource Usage

On Pi:
```bash
# Check memory
free -h

# Check CPU temperature
vcgencmd measure_temp

# Monitor live
watch -n 1 free -h
```

---

## Docker Deployment (Optional)

For consistent cross-platform deployment:

```dockerfile
FROM python:3.11-slim-bullseye
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "src/live_detection.py", "--model", "mira_detector_wild_v2.pt"]
```

**Build and run:**
```bash
docker build -t mira:latest .
docker run --privileged -v /dev:/dev mira:latest
```

---

## Troubleshooting Deployment

### ❌ "No module named 'tensorflow'"

```bash
# Reinstall with verbose output
pip install tensorflow -v
```

### ❌ Camera not detected on Pi

```bash
# Check USB devices
lsusb

# Grant permissions
sudo usermod -a -G video $USER
newgrp video
```

### ❌ Very slow on Pi Zero 2W

- Use only quantized models (`*_int8_320.tflite`)
- Lower camera resolution to 320x240
- Disable Streamlit dashboard (too heavy)

### ❌ Out of memory

```bash
# Free up RAM
sudo systemctl stop bluetooth
sudo systemctl stop avahi-daemon

# Or reduce batch processing:
# Edit src/live_detection.py, reduce WARMUP_FRAMES
```

---

## Next Steps

1. Deploy model to Pi
2. Connect sorting arm (GPIO pins)
3. Run inference loop
4. Trigger arm actions based on detected classes

See `README.md` for integration examples.
