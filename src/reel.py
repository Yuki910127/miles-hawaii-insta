"""ffmpeg で縦型リール(1080x1920)を合成。
背景: assets/reel_bg/*.mp4 (Genspark等で生成した風景動画) をランダム使用。無ければグラデーション。
音源: assets/music/*.mp3 (ロイヤリティフリー) をランダム使用。無ければ無音トラック。
"""
import random
import subprocess
from pathlib import Path
from config import ASSETS, OUT

HOOK_SEC = 2.2
LINE_SEC = 2.6
CLOSE_SEC = 3.0
SEC_BY_KIND = {"hook": 2.2, "line": 2.6, "bignum": 2.4, "vertical": 2.8, "closing": 3.0}


def _pick(dir_: Path, exts: tuple[str, ...]) -> Path | None:
    files = [p for p in dir_.glob("*") if p.suffix.lower() in exts]
    return random.choice(files) if files else None


def pick_music() -> Path | None:
    """BGM を選ぶ。アップロードされた曲(合成した uke_*.mp3 以外)があればそちらを優先。"""
    files = [p for p in (ASSETS / "music").glob("*") if p.suffix.lower() in (".mp3", ".m4a", ".wav", ".aac")]
    own = [p for p in files if not p.name.startswith("uke_")]
    pool = own or files
    pick = random.choice(pool) if pool else None
    print(f"[music] {pick.name if pick else 'なし(無音)'}")
    return pick


def _video_size(path: Path) -> tuple[int, int]:
    """ffprobe で幅・高さ(回転メタデータを考慮)を返す。失敗時は (0, 0)。"""
    import json
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_streams", "-of", "json", str(path)],
            capture_output=True, text=True, check=True).stdout
        st = json.loads(out)["streams"][0]
        w, h = int(st.get("width", 0)), int(st.get("height", 0))
        rot = int(float((st.get("tags") or {}).get("rotate", 0) or 0))
        for sd in st.get("side_data_list", []) or []:
            if "rotation" in sd:
                rot = int(float(sd["rotation"]))
        if abs(rot) % 180 == 90:
            w, h = h, w
        return w, h
    except Exception as e:
        print(f"[reel] ffprobe failed: {e}")
        return 0, 0


def _bg_filter(bg: Path) -> str:
    """背景動画を 1080x1920 に整える。
    縦動画(9:16付近) → 拡大/切り抜きのみ。
    横動画          → 横幅いっぱいに収め、上下の余白には同じ動画をぼかして敷く(解像度を落とさない)。
    """
    w, h = _video_size(bg)
    portrait = (h > 0 and w / h <= 0.75)
    if portrait or w == 0:
        # 低解像度(幅1080未満)の素材を拡大する場合は軽くシャープをかけて眠さを抑える
        sharpen = ",unsharp=5:5:0.6:5:5:0.0" if 0 < w < 1080 else ""
        return ("[0:v]scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,setsar=1,"
                f"eq=brightness=-0.08:saturation=1.05{sharpen}[bg]")
    return ("[0:v]split=2[a][b];"
            "[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:8,eq=brightness=-0.25[blur];"
            "[b]scale=1080:-2:flags=lanczos[fg];"
            "[blur][fg]overlay=(W-w)/2:(H-h)/2,setsar=1,eq=brightness=-0.05:saturation=1.05[bg]")


def build_reel(frames: list[Path], slug: str, kinds: list[str] | None = None) -> Path:
    out = OUT / f"{slug}.mp4"
    if kinds and len(kinds) == len(frames):
        durations = [SEC_BY_KIND.get(k, LINE_SEC) for k in kinds]
    else:
        durations = [HOOK_SEC] + [LINE_SEC] * (len(frames) - 2) + [CLOSE_SEC]
    total = sum(durations)

    bg = _pick(ASSETS / "reel_bg", (".mp4", ".mov"))
    music = pick_music()

    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    # input 0: 背景
    if bg:
        cmd += ["-stream_loop", "-1", "-i", str(bg)]
        bg_filter = _bg_filter(bg)
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
        "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high", "-level", "4.1",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        "-movflags", "+faststart",
        str(out),
    ]
    print("[reel] ffmpeg", " ".join(cmd[:8]), "...")
    subprocess.run(cmd, check=True)
    return out
