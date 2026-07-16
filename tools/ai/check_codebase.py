import os
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

# 1. KONFIGURATION
API_KEY = os.environ.get("HACK_CLUB_API_KEY", "")
API_URL = "https://ai.hackclub.com/proxy/v1/chat/completions"
MODEL = "google/gemini-2.5-flash"  # Du kannst auch "gemini-2.5-pro" probieren, falls Claude belegt ist

# Ordner und Dateien, die NICHT eingelesen werden sollen
IGNORE_DIRS = {".git", "venv", "__pycache__", ".ipynb_checkpoints", "node_modules", "build", "dist"}
IGNORE_FILES = {"check_codebase.py", "package-lock.json", "report.pdf", "main.pdf"}
ALLOWED_EXTENSIONS = {".py", ".yaml", ".yml", ".json"} # Erweitern, falls du z. B. .ino für Arduino-Code nutzt

def read_codebase(root_dir):
    codebase_content = []
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Ignoriere versteckte oder irrelevante Ordner
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS and not d.startswith('.')]
        
        for file in filenames:
            if file in IGNORE_FILES or file.startswith('.'):
                continue
                
            _, ext = os.path.splitext(file)
            if ext in ALLOWED_EXTENSIONS:
                full_path = os.path.join(dirpath, file)
                relative_path = os.path.relpath(full_path, root_dir)
                
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        codebase_content.append(f"### FILE: {relative_path}\n```\n{content}\n```\n")
                except Exception as e:
                    print(f"Konnte {relative_path} nicht lesen: {e}")
                    
    return "\n".join(codebase_content)

# 2. Codebase einlesen
print("Gathering codebase files...")
current_directory = os.path.dirname(os.path.abspath(__file__)) if "__file__" in locals() else "."
entire_code = read_codebase(current_directory)

if not entire_code:
    print("Keine passenden Dateien gefunden!")
    exit()

# 3. PROMPT AUF ENGLISCH (Für JUFO und Praktika-Bewertung)
prompt = f"""
You are an expert AI software architect, a Jugend forscht (JUFO) National Jury Member in the Technology category, and a Lead Tech Recruiter at a high-growth robotics/AI startup.

Please analyze the following codebase of my project "MIRA" (Machine Intelligence for Recycling Automation) and provide an in-depth review in English.

Please structure your review into three parts:

### Part 1: JUFO Jury Evaluation (Technical & Scientific Rigor)
- Assess the scientific approach: Does the code reflect robust machine learning principles (e.g., Transfer Learning, Post-Training Quantization)?
- Rate the implementation: Is the model integration (YOLOv8, MobileNetV2, ByteTrack) handled correctly and efficiently?
- Are there any critical bugs, logical flaws (such as RGB/BGR channel issues), or inefficiencies that a jury would call out during the presentation?

### Part 2: Internship Recruiter Rating (Industry Readiness)
- Rate my coding style, modularity, and structure from 1-10 for a high-school level internship candidate.
- Does this codebase show that I am ready to work as a junior/intern developer in a real-world AI/Robotics team?
- What are the "Green Flags" (amazing implementations) and "Red Flags" (bad practices, messy code, or lack of documentation) in this project?

### Part 3: Actionable Bug Report & Fixes
- List any specific bugs, edge-case failures, or performance bottlenecks you found in the code.
- Provide concrete code snippets showing how to fix them.

Here is the entire codebase:

{entire_code}
"""

# 4. API Anfrage senden
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "model": MODEL,
    "messages": [
        {"role": "user", "content": prompt}
    ]
}

print(f"Sending codebase to {MODEL} via Hack Club API... Please wait, this might take a moment.")
response = requests.post(API_URL, headers=headers, json=data)

if response.status_code == 200:
    result = response.json()
    print("\n" + "="*40 + "\nCLAUDE'S ASSESSMENT:\n" + "="*40)
    print(result["choices"][0]["message"]["content"])
else:
    print(f"Error {response.status_code}: {response.text}")