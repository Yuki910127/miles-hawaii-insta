"""Gemini API (無料枠) を REST で呼び出し、JSON を返す。
モデル名は決め打ちせず、ListModels で「今使える Flash 系」を自動選択する
(GEMINI_MODEL 環境変数で明示指定も可)。404 なら次の候補へフォールバック。
"""
import json
import re
import time
import requests
from config import GEMINI_API_KEY, GEMINI_MODEL

BASE = "https://generativelanguage.googleapis.com/v1beta"
_model_cache: list[str] | None = None


def _version_key(name: str) -> tuple:
    m = re.search(r"(\d+)(?:\.(\d+))?", name)
    return (int(m.group(1)), int(m.group(2) or 0)) if m else (0, 0)


def candidate_models() -> list[str]:
    """利用可能モデルを取得し、優先順に並べる。
    優先: generateContent 対応 / 名前に flash を含む / lite・preview・image・tts・live などを含まない / バージョンが新しい
    """
    global _model_cache
    if _model_cache is not None:
        return _model_cache
    names: list[str] = []
    try:
        page = None
        while True:
            params = {"key": GEMINI_API_KEY, "pageSize": 200}
            if page:
                params["pageToken"] = page
            r = requests.get(f"{BASE}/models", params=params, timeout=60)
            r.raise_for_status()
            d = r.json()
            for m in d.get("models", []):
                if "generateContent" in m.get("supportedGenerationMethods", []):
                    names.append(m["name"].replace("models/", ""))
            page = d.get("nextPageToken")
            if not page:
                break
    except Exception as e:
        print(f"[gemini] モデル一覧の取得に失敗: {e}")

    bad = ("image", "tts", "live", "audio", "embedding", "aqa", "exp", "thinking", "robotics", "computer")
    def ok(n): return "flash" in n and not any(b in n for b in bad)
    tier1 = sorted([n for n in names if ok(n) and "lite" not in n and "preview" not in n], key=_version_key, reverse=True)
    tier2 = sorted([n for n in names if ok(n) and "lite" in n and "preview" not in n], key=_version_key, reverse=True)
    tier3 = sorted([n for n in names if ok(n) and "preview" in n], key=_version_key, reverse=True)
    tier4 = sorted([n for n in names if "gemma" in n and not any(b in n for b in bad)], key=_version_key, reverse=True)

    ordered: list[str] = []
    if GEMINI_MODEL:
        ordered.append(GEMINI_MODEL)
    for n in tier1 + tier2 + tier3 + tier4:
        if n not in ordered:
            ordered.append(n)
    if not ordered:
        ordered = ["gemini-2.5-flash", "gemini-2.0-flash"]
    print(f"[gemini] 候補モデル: {ordered[:5]}")
    _model_cache = ordered
    return ordered


def generate_json(system_prompt: str, user_prompt: str, schema: dict | None = None,
                  retries: int = 3, temperature: float = 0.9) -> dict:
    """JSON モードで生成し dict を返す。モデル 404 は次候補へ、429 は待って再試行。"""
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

    last_err = None
    for model in candidate_models()[:6]:
        url = f"{BASE}/models/{model}:generateContent"
        for attempt in range(retries):
            try:
                r = requests.post(url, params={"key": GEMINI_API_KEY}, json=body, timeout=90)
                if r.status_code == 404:
                    print(f"[gemini] {model} は利用不可(404)。次の候補へ")
                    last_err = f"404 for {model}"
                    break
                if r.status_code in (500, 502, 503, 504):
                    # 混雑・障害: 同じモデルで粘らず次の候補へ
                    print(f"[gemini] {model} が混雑中({r.status_code})。次の候補へ")
                    last_err = f"{r.status_code} for {model}"
                    break
                if r.status_code == 429:
                    wait = 20 * (attempt + 1)
                    print(f"[gemini] {model} rate limited, waiting {wait}s")
                    time.sleep(wait)
                    continue
                if r.status_code == 400 and "response_schema" in r.text:
                    # スキーマ非対応モデル: スキーマ無しで再試行
                    body["generationConfig"].pop("response_schema", None)
                    continue
                r.raise_for_status()
                text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                print(f"[gemini] model={model}")
                return json.loads(text)
            except requests.Timeout as e:
                # 応答が遅いモデルは見切って次の候補へ
                print(f"[gemini] {model} タイムアウト。次の候補へ")
                last_err = e
                break
            except (requests.RequestException, KeyError, json.JSONDecodeError, IndexError) as e:
                last_err = e
                print(f"[gemini] {model} attempt {attempt+1} failed: {e}")
                time.sleep(5)
    raise RuntimeError(f"Gemini 生成に失敗: {last_err}")


def generate_grounded(prompt: str, retries: int = 2) -> tuple[str, list[dict]]:
    """Google検索グラウンディング付きで回答テキストと出典一覧を返す。
    返り値: (text, [{"title": "ana.co.jp", "uri": "..."}])
    """
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY が未設定です")
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "tools": [{"google_search": {}}],
        "generationConfig": {"temperature": 0.2},
    }
    last_err = None
    for model in candidate_models()[:4]:
        url = f"{BASE}/models/{model}:generateContent"
        for attempt in range(retries):
            try:
                r = requests.post(url, params={"key": GEMINI_API_KEY}, json=body, timeout=180)
                if r.status_code == 404:
                    break
                if r.status_code == 429:
                    time.sleep(30 * (attempt + 1))
                    continue
                if r.status_code == 400 and "google_search" in r.text:
                    # 旧モデル向けツール名で再試行
                    body["tools"] = [{"google_search_retrieval": {}}]
                    continue
                r.raise_for_status()
                cand = r.json()["candidates"][0]
                text = "".join(p.get("text", "") for p in cand["content"]["parts"])
                chunks = cand.get("groundingMetadata", {}).get("groundingChunks", [])
                sources = [{"title": c["web"].get("title", ""), "uri": c["web"].get("uri", "")} for c in chunks if "web" in c]
                print(f"[gemini] grounded model={model} sources={len(sources)}")
                return text, sources
            except (requests.RequestException, KeyError, IndexError) as e:
                last_err = e
                print(f"[gemini] grounded {model} attempt {attempt+1} failed: {e}")
                time.sleep(5)
    raise RuntimeError(f"グラウンディング生成に失敗: {last_err}")


def read_image_text(image_path, retries: int = 2) -> str:
    """画像内の文字を Gemini(無料枠)で書き起こす。失敗時は空文字。"""
    import base64, mimetypes
    if not GEMINI_API_KEY:
        return ""
    mime = mimetypes.guess_type(str(image_path))[0] or "image/png"
    data = base64.b64encode(open(image_path, "rb").read()).decode()
    body = {"contents": [{"role": "user", "parts": [
        {"inline_data": {"mime_type": mime, "data": data}},
        {"text": "この画像に書かれている日本語・英数字の文字をすべて、見えるとおりに書き起こしてください。説明は不要で、文字だけを改行区切りで出力してください。"}]}],
        "generationConfig": {"temperature": 0}}
    for model in candidate_models()[:4]:
        for attempt in range(retries):
            try:
                r = requests.post(f"{BASE}/models/{model}:generateContent", params={"key": GEMINI_API_KEY}, json=body, timeout=120)
                if r.status_code == 404:
                    break
                if r.status_code == 429:
                    time.sleep(20 * (attempt + 1)); continue
                r.raise_for_status()
                return "".join(p.get("text", "") for p in r.json()["candidates"][0]["content"]["parts"])
            except Exception as e:
                print(f"[gemini] OCR {model} failed: {e}")
                time.sleep(5)
    return ""
