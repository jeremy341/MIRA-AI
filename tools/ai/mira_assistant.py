import os
import re
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

# 1. KONFIGURATION
API_KEY = os.environ.get("HACK_CLUB_API_KEY", "")
API_URL = "https://ai.hackclub.com/proxy/v1/chat/completions"

# Verfügbare Modelle zur Auswahl
MODELS = {
    "1": "google/gemini-2.5-flash",
    "2": "google/gemini-2.5-pro",
    "3": "meta-llama/llama-3.3-70b-instruct"
}


def call_gemini(model, system_prompt, user_content):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.2
    }
    response = requests.post(API_URL, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        raise RuntimeError(f"API Fehler {response.status_code}: {response.text}")


def clean_code_block(text):
    # Holt den reinen Text aus Markdown-Codeblöcken heraus
    match = re.search(r"```.*?\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1)
    return text.strip()


def main():
    if API_KEY == "DEIN_HACK_CLUB_API_KEY_HIER":
        print("[-] Bitte trage zuerst deinen Hack Club API-Key im Skript ein!")
        return

    print("=== MIRA UNIVERSAL ASSISTANT ===")

    # 1. Modell auswählen
    print("\nWähle ein Modell:")
    for key, val in MODELS.items():
        print(f"[{key}] {val}")
    model_choice = input("Auswahl (Standard: 1): ").strip() or "1"
    selected_model = MODELS.get(model_choice, MODELS["1"])
    print(f"[✓] Modell ausgewählt: {selected_model}")

    # 2. Ordner auswählen
    folder_input = input("\nWelchen Ordner soll ich bearbeiten? (z.B. 'latex' oder 'src'): ").strip()
    target_folder = Path(folder_input)

    if not target_folder.exists() or not target_folder.is_dir():
        print(f"[-] Der Ordner '{folder_input}' existiert nicht!")
        return

    # Unterstützte Dateitypen auflisten (z.B. .tex, .py, .md, .txt)
    extensions = [".tex", ".py", ".md", ".txt", ".json"]
    files = [f for f in target_folder.glob("**/*") if f.is_file() and f.suffix in extensions]

    if not files:
        print(f"[-] Keine passenden Dateien (.tex, .py, etc.) in '{folder_input}' gefunden.")
        return

    print(f"\n[+] Folgende Dateien wurden im Ordner '{folder_input}' gefunden:")
    for f in files:
        print(f"  - {f.relative_to(target_folder.parent)}")

    # 3. Prompt eingeben
    print("\nWas soll ich mit diesen Dateien tun?")
    task_prompt = input("Dein Prompt: ").strip()
    if not task_prompt:
        print("[-] Kein Prompt eingegeben. Abbruch.")
        return

    # Bestätigung
    confirm = input(f"\nSollen alle {len(files)} Dateien jetzt überschrieben werden? (y/N): ").strip().lower()
    if confirm != "y":
        print("[-] Abgebrochen. Keine Änderungen vorgenommen.")
        return

    # 4. Dateien verarbeiten
    for file_path in files:
        print(f"\n[*] Verarbeite: {file_path.name}...")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            system_prompt = (
                "You are an expert assistant. Your job is to modify the provided file content based on the user's task. "
                "Keep the format, style, and language exactly as requested. "
                "Return ONLY the updated file content inside a markdown code block. Do not add any conversational text or explanations outside the code block."
            )

            user_content = (
                f"File: {file_path.name}\n"
                f"Content:\n"
                f"```\n{content}\n```\n\n"
                f"Task to perform on this file:\n{task_prompt}"
            )

            response_raw = call_gemini(selected_model, system_prompt, user_content)
            updated_content = clean_code_block(response_raw)

            # Sicherung vor dem Überschreiben
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(updated_content)
            print(f"[✓] {file_path.name} wurde erfolgreich aktualisiert!")

        except Exception as e:
            print(f"[X] Fehler bei {file_path.name}: {e}")

    print("\n==========================================")
    print("Fertig! Alle Dateien im Ordner wurden wunschgemäß angepasst, große Herrscher!")


if __name__ == "__main__":
    main()