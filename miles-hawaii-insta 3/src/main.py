"""エントリポイント: python src/main.py carousel | reel"""
import json
import subprocess
import sys
from datetime import datetime
from config import OUT, DRY_RUN
from generate import generate_post, save_posted
from render import render_carousel, render_reel_frames
from reel import build_reel
from pages import publish_files
from publish import publish_carousel, publish_reel


def run(kind: str):
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    slug = f"{stamp}-{kind}"
    print(f"=== {slug} (DRY_RUN={DRY_RUN}) ===")

    post = generate_post(kind)
    (OUT / f"{slug}.json").write_text(json.dumps(post, ensure_ascii=False, indent=2), encoding="utf-8")
    print("[gen] topic:", post["topic"])

    if kind == "carousel":
        pngs = render_carousel(post, slug)
        urls = publish_files(pngs, f"media: {slug}")
        media_id = publish_carousel(urls, post["full_caption"])
    else:
        frames = render_reel_frames(post, slug)
        video = build_reel(frames, slug)
        urls = publish_files([video], f"media: {slug}")
        media_id = publish_reel(urls[0], post["full_caption"])

    save_posted({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "kind": kind,
        "category": post["category"],
        "topic": post["topic"],
        "media_id": media_id,
        "slug": slug,
    })
    if not DRY_RUN:
        subprocess.run(["git", "add", "data/posted.json"], check=True)
        subprocess.run(["git", "commit", "-m", f"posted: {slug}"], check=False)
        subprocess.run(["git", "pull", "--rebase", "--autostash", "origin", "HEAD"], check=True)
        subprocess.run(["git", "push", "origin", "HEAD"], check=True)
    print("=== done ===")


if __name__ == "__main__":
    kind = sys.argv[1] if len(sys.argv) > 1 else "carousel"
    assert kind in ("carousel", "reel")
    run(kind)
