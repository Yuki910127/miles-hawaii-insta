"""Gemini API (無料枠) を REST で呼び出し、JSON を返す。"""
import json
import time
import requests
from config import GEMINI_API_KEY, GEMINI_MODEL

ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def generate_json(system_prompt: str, user_prompt: str, schema: dict | None = None,
                  retries: int = 4, temperature: float = 0.9) -> dict:
    """JSON モードで生成し dict を返す。失敗時はリトライ。"""
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY が未設定です")

    gen_cfg = {"temperature": temperature, "response_mime_type": "application/json"}
    if schema:
        gen_cfg["response_schema"] = schema

    body = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": gen_cfg,
    }
    url = ENDPOINT.format(model=GEMINI_MODEL)
    last_err = None
    for attempt in range(retries):
        try:
            r = requests.post(url, params={"key": GEMINI_API_KEY}, json=body, timeout=120)
            if r.status_code == 429:
                wait = 20 * (attempt + 1)
                print(f"[gemini] rate limited, waiting {wait}s")
                time.sleep(wait)
                continue
            r.raise_for_status()
            text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text)
        except (requests.RequestException, KeyError, json.JSONDecodeError, IndexError) as e:
            last_err = e
            print(f"[gemini] attempt {attempt+1} failed: {e}")
            time.sleep(5)
    raise RuntimeError(f"Gemini 生成に失敗: {last_err}")
