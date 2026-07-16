"""Build Mode: File modifications with confirmation."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from api import chat
from context import build_context

SYSTEM_PROMPT = """You are MIRA-AI in BUILD MODE. You can read AND modify code.
You are working on the MIRA project (Machine Intelligence for Recycling Automation) for Jugend Forscht 2027.
The project uses YOLO object detection (5 classes: glass, metal, paper, plastic, trash) on Raspberry Pi.

RULES:
- You can read, write, and modify files
- When suggesting a file change, use this EXACT format:
  FILE: <path>
  ACTION: <create|modify|delete>
  ```<language>
  <content>
  ```
- Always explain what you're changing and why
- Prefer minimal, focused changes
- Follow existing code style"""

def run(user_input: str, messages: list[dict], model: str, context: str) -> str:
    """Process a build mode message."""
    if not messages:
        messages.append({"role": "system", "content": SYSTEM_PROMPT})
        messages.append({"role": "user", "content": f"Project context:\n{context}"})
        messages.append({"role": "assistant", "content": "Understood. I'm in Build Mode — I can read and modify files. What should I build or fix?"})

    messages.append({"role": "user", "content": user_input})
    response = chat(messages, model=model, temperature=0.5)
    messages.append({"role": "assistant", "content": response})
    return response
