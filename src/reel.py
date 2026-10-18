"""ffmpeg で縦型リール(1080x1920)を合成。
背景: assets/reel_bg/*.mp4 (Genspark等で生成した風景動画) をランダム使用。無ければグラデーション。
音源: assets/music/*.mp3 (ロイヤリティフリー) をランダム使用。無ければ無音トラック。
"""
import random
import subprocess
from pathlib import Path
from config import ASSETS, OUT

HOOK_SEC = 2.5
LINE_SEC = 3.0
CLOSE_SEC = 3.0


def _pick(dir_: Path, exts: tuple[str, ...]) -> Path | None:
    files = [p for p in dir_.glob("*") if p.suffix.lower() in exts]
    return random.choice(files) if files else None


def build_reel(frames: list[Path], slug: str) -> Path:
    out = OUT / f"{slug}.mp4"
    durations = [HOOK_SEC] + [LINE_SEC] * (len(frames) - 2) + [CLOSE_SEC]
    total = sum(durations)

    bg = _pick(ASSETS / "reel_bg", (".mp4", ".mov"))
    music = _pick(ASSETS / "music", (".mp3", ".m4a", ".wav"))

    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    # input 0: 背景
    if bg:
        cmd += ["-stream_loop", "-1", "-i", str(bg)]
        bg_filter = "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,eq=brightness=-0.08:saturation=1.05[bg]"
    else:
        cmd += ["-f", "lavfi", "-i", f"gradients=s=1080x1920:c0=0x0E7C86:c1=0xF28C28:speed=0.02:d={total}"]
        bg_filter = "[0:v]setsar=1[bg]"
    # input 1: 音声
    if music:
        cmd += ["-stream_loop", "-1", "-i", str(music)]
    else:
        cmd += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]
    # input 2..: フレーム
    for f in frames:
        cmd += ["-loop", "1", "-i", str(f)]

    filters = [bg_filter]
    prev = "bg"
    t = 0.0
    for i, d in enumerate(durations):
        idx = i + 2
        start, end = t, t + d
        fade = 0.3
        # 各フレームをフェードイン付きでオーバーレイ
        filters.append(
            f"[{idx}:v]format=rgba,fade=t=in:st={start:.2f}:d={fade}:alpha=1,setpts=PTS-STARTPTS[f{i}]"
        )
        filters.append(f"[{prev}][f{i}]overlay=enable='between(t,{start:.2f},{end:.2f})'[v{i}]")
        prev = f"v{i}"
        t = end
    filters.append(f"[{prev}]format=yuv420p[vout]")

    cmd += [
        "-filter_complex", ";".join(filters),
        "-map", "[vout]", "-map", "1:a",
        "-t", f"{total:.2f}", "-r", "30",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-profile:v", "high", "-level", "4.1",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        "-movflags", "+faststart",
        str(out),
    ]
    print("[reel] ffmpeg", " ".join(cmd[:8]), "...")
    subprocess.run(cmd, check=True)
    return out
