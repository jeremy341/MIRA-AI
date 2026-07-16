"""Hack Club AI API client — OpenAI-compatible proxy."""
import os
from pathlib import Path
import requests
from dotenv import load_dotenv
from typing import Generator

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

BASE_URL = "https://ai.hackclub.com/proxy/v1"
DEFAULT_MODEL = "google/gemini-3.1-flash-lite-preview"

def get_api_key() -> str:
    key = os.environ.get("HACK_CLUB_API_KEY")
    if not key:
        raise RuntimeError("Set HACK_CLUB_API_KEY environment variable.")
    return key

def chat(messages: list[dict], model: str = DEFAULT_MODEL,
         temperature: float = 0.7, max_tokens: int = 4096) -> str:
    """Send chat completion request, return assistant response text."""
    headers = {"Authorization": f"Bearer {get_api_key()}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    resp = requests.post(f"{BASE_URL}/chat/completions", headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

def chat_stream(messages: list[dict], model: str = DEFAULT_MODEL,
                temperature: float = 0.7, max_tokens: int = 4096) -> Generator[str, None, None]:
    """Stream chat completion, yield text chunks."""
    headers = {"Authorization": f"Bearer {get_api_key()}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }
    with requests.post(f"{BASE_URL}/chat/completions", headers=headers, json=payload,
                       timeout=120, stream=True) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
            data = line[6:]
            if data == "[DONE]":
                break
            import json
            chunk = json.loads(data)
            delta = chunk["choices"][0].get("delta", {})
            if "content" in delta:
                yield delta["content"]
