import os
import re
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

# 1. KONFIGURATION
API_KEY = os.environ.get("HACK_CLUB_API_KEY", "")
API_URL = "https://ai.hackclub.com/proxy/v1/chat/completions"
MODEL = "google/gemini-2.5-flash"

# Absolute Pfade zu deinen Projektdateien ermitteln
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILES_TO_FIX = {
    "config.py": "Add a utility function 'setup_camera_properties(cap, width, height, fps=30)' that configures standard camera properties. Also, define the constant 'BYTE_TRACK_CONFIG_PATH = ROOT_DIR / \"bytetrack.yaml\"'. Make sure to import cv2 inside config.py.",
    
    "debug_detector.py": "Fix 1: Add a '--resolution' CLI argument (choices: 640x360, 1280x720, 1920x1080; default 1280x720), parse it, and pass the resulting CAM_W and CAM_H to the InferenceEngine instead of hardcoding 1280x720. Fix 2: Set the default of '--track' to False so tracking is off by default, and can be toggled on.",
    
    "capture_classifier_frames.py": "Import 'setup_camera_properties' from config and replace the redundant cap.set() property lines with 'setup_camera_properties(cap, CAM_W, CAM_H)'. Ensure captured frames are handled cleanly.",
    
    "dashboard.py": "Fix 1: Import 'setup_camera_properties' and 'BYTE_TRACK_CONFIG_PATH' from config. Fix 2: Replace redundant cap.set() lines with 'setup_camera_properties(cap, 640, 360)'. Fix 3: Use 'BYTE_TRACK_CONFIG_PATH' instead of the hardcoded \"bytetrack.yaml\".",
    
    "inference_engine.py": "Fix 1: Import 'setup_camera_properties' and 'BYTE_TRACK_CONFIG_PATH' from config. Fix 2: In CameraStream.__init__, replace redundant cap.set() lines with 'setup_camera_properties(self.cap, width, height)'. Fix 3: In InferenceEngine, use 'BYTE_TRACK_CONFIG_PATH' instead of the hardcoded \"bytetrack.yaml\". Replace critical prints with the logger from logger.py where appropriate."
}

def query_gemini(system_prompt, user_content):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.1  # Niedrige Temperatur für maximal präzisen Code
    }
    response = requests.post(API_URL, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        raise RuntimeError(f"API Error {response.status_code}: {response.text}")

def extract_code(text):
    # Extrahiert nur den reinen Python-Code aus der Markdown-Antwort der KI
    match = re.search(r"```python\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1)
    match_any = re.search(r"```\n(.*?)```", text, re.DOTALL)
    if match_any:
        return match_any.group(1)
    return text.strip()

print("Starte automatische Code-Korrektur, große Herrscher...")

for filename, instructions in FILES_TO_FIX.items():
    file_path = os.path.join(BASE_DIR, filename)
    
    if not os.path.exists(file_path):
        print(f"[-] Datei nicht gefunden: {filename} (Überspringe)")
        continue
        
    print(f"[+] Lese {filename}...")
    with open(file_path, "r", encoding="utf-8") as f:
        current_code = f.read()
        
    system_prompt = (
        "You are an expert Python developer. Your task is to refactor the provided code file based on the user's instructions. "
        "Apply the fixes surgically, keeping all other logic, comments, and structure intact. "
        "Return ONLY the complete, updated, ready-to-run Python code inside a single ```python code block. No explanations, no introduction."
    )
    
    user_content = f"Here is the current content of my file '{filename}':\n\n```python\n{current_code}\n```\n\nInstructions to apply:\n{instructions}"
    
    print(f"[>] Sende {filename} an Gemini für Fixes...")
    try:
        raw_response = query_gemini(system_prompt, user_content)
        updated_code = extract_code(raw_response)
        
        # Sicherheits-Check: Falls die KI leeren Code liefert, brechen wir ab
        if len(updated_code) < 50:
            print(f"[!] Warnung: Antwort für {filename} war fehlerhaft oder zu kurz. Keine Änderungen vorgenommen.")
            continue
            
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(updated_code)
        print(f"[✓] {filename} erfolgreich aktualisiert!")
        
    except Exception as e:
        print(f"[X] Fehler bei {filename}: {e}")

print("\nAlle Anpassungen wurden direkt in deine Dateien geschrieben!")