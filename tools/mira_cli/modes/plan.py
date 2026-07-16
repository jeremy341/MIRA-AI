"""Plan Mode: Read-only code analysis and suggestions."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from api import chat
from context import build_context

SYSTEM_PROMPT = """You are MIRA-AI in PLAN MODE. You can ONLY read and analyze code.
You are working on the MIRA project (Machine Intelligence for Recycling Automation) for Jugend Forscht 2027.
The project uses YOLO object detection (5 classes: glass, metal, paper, plastic, trash) on Raspberry Pi.

RULES:
- You can read, search, and analyze code
- You CANNOT modify, write, or delete any files
- Provide structured plans with file paths and line numbers
- Suggest changes but do NOT implement them
- Be concise and actionable"""

def run(user_input: str, messages: list[dict], model: str, context: str) -> str:
    """Process a plan mode message."""
    if not messages:
        messages.append({"role": "system", "content": SYSTEM_PROMPT})
        messages.append({"role": "user", "content": f"Project context:\n{context}"})
        messages.append({"role": "assistant", "content": "Understood. I'm in Plan Mode — read-only analysis. What would you like me to analyze?"})

    messages.append({"role": "user", "content": user_input})
    response = chat(messages, model=model, temperature=0.5)
    messages.append({"role": "assistant", "content": response})
    return response
