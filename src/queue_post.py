"""作り置き画像(assets/queue/)を1枚ずつリールにして投稿する。
- data/queue.yml の順に、未投稿 かつ 画像がある最初の1件を選ぶ
- Gemini で画像の文字を読み取り、数字を含む文言が全部入っているか確認(誤った数字の投稿を防ぐ)
- 静止画を軽くズームしながら BGM を付けて 1080x1920 のリールにする
"""
import random
import re
import subprocess
import unicodedata
from pathlib import Path
import yaml
from config import ASSETS, DATA, OUT

QUEUE_DIR = ASSETS / "queue"
EXTS = (".png", ".jpg", ".jpeg", ".webp")
REEL_SEC = 9


def load_queue() -> list[dict]:
    p = DATA / "queue.yml"
    return (yaml.safe_load(p.read_text(encoding="utf-8")) or {}).get("items", []) if p.exists() else []


def image_for(item: dict) -> Path | None:
    for ext in EXTS:
        for cand in (QUEUE_DIR / f"{item['file']}{ext}", QUEUE_DIR / f"{item['file']}{ext.upper()}"):
            if cand.exists():
                return cand
    return None


def next_item(posted: list[dict], skip: set | None = None) -> tuple[dict, Path] | None:
    done = {p.get("queue_id") for p in posted if p.get("queue_id") is not None}
    for it in load_queue():
        if it["id"] in done or (skip and it["id"] in skip):
            continue
        img = image_for(it)
        if img:
            return it, img
    return None


def remaining(posted: list[dict]) -> int:
    done = {p.get("queue_id") for p in posted if p.get("queue_id") is not None}
    return sum(1 for it in load_queue() if it["id"] not in done and image_for(it))


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    return re.sub(r"[\s・、。,.!！?？「」『』()（）〜~ー\-−:：]", "", s)


def verify(item: dict, img: Path) -> list[str]:
    """数字を含む文言のうち、画像から読み取れなかったものを返す(空なら OK)。読み取り失敗時は空(=止めない)。"""
    from gemini_client import read_image_text
    text = read_image_text(img)
    if not text:
        print("[queue] 文字の読み取りに失敗 → 確認をスキップ")
        return []
    got = _norm(text)
    missing = []
    for t in item.get("expect", []):
        if t.startswith("※") or not re.search(r"\d", t):  # 小さな注記は照合しない
            continue
        # 数字だけは厳密に: 文言内の数字列がすべて画像内にあるか
        nums = re.findall(r"\d[\d,]*", unicodedata.normalize("NFKC", t))
        if not all(n.replace(",", "") in got.replace(",", "") for n in nums):
            missing.append(t)
    return missing


def build_still_reel(img: Path, slug: str) -> Path:
    """静止画 → ゆっくりズーム(1.00→1.03)+BGM の 9 秒リール。"""
    out = OUT / f"{slug}.mp4"
    music = [p for p in (ASSETS / "music").glob("*") if p.suffix.lower() in (".mp3", ".m4a", ".wav")]
    fps, frames = 30, REEL_SEC * 30
    vf = ("scale=2160:3840:force_original_aspect_ratio=increase:flags=lanczos,crop=2160:3840,"
          f"zoompan=z='1+0.03*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920:fps={fps},"
          "format=yuv420p")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(img)]
    if music:
        cmd += ["-stream_loop", "-1", "-i", str(random.choice(music))]
    else:
        cmd += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]
    cmd += ["-vf", vf, "-map", "0:v", "-map", "1:a", "-t", str(REEL_SEC),
            "-af", f"afade=t=out:st={REEL_SEC-1.5}:d=1.5",
            "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high", "-level", "4.1",
            "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True)
    return out


def cover_jpg(img: Path, slug: str) -> Path:
    out = OUT / f"{slug}_cover.jpg"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(img),
                    "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920", "-q:v", "2", str(out)], check=True)
    return out
