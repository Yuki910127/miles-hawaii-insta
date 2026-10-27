"""エントリポイント: python src/main.py carousel | reel | queue"""
import json
import subprocess
import sys
from datetime import datetime
from config import OUT, DRY_RUN
from generate import generate_post, save_posted, load_posted, load_yaml, build_hashtags
from render import render_carousel, render_reel_frames
from reel import build_reel
from pages import publish_files
from publish import publish_carousel, publish_reel


def _git_commit_posted(slug: str):
    if not DRY_RUN:
        subprocess.run(["git", "add", "data/posted.json"], check=True)
        subprocess.run(["git", "commit", "-m", f"posted: {slug}"], check=False)
        subprocess.run(["git", "pull", "--rebase", "--autostash", "origin", "HEAD"], check=True)
        subprocess.run(["git", "push", "origin", "HEAD"], check=True)


def _issue(title: str, body: str):
    try:
        subprocess.run(["gh", "issue", "create", "--title", title, "--body", body], check=False)
    except Exception as e:
        print("[issue] failed:", e)


def run_queue():
    """作り置き画像を1本リール投稿。在庫が無ければ通常のカルーセルにフォールバック。"""
    import queue_post as q
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    posted = load_posted()
    skip, bad = set(), []
    for _ in range(3):
        nxt = q.next_item(posted, skip)
        if not nxt:
            break
        item, img = nxt
        miss = q.verify(item, img)
        if not miss:
            break
        print(f"[queue] {item['file']} の数字が画像と一致しません: {miss} → スキップ")
        bad.append((item, miss)); skip.add(item["id"]); nxt = None
    for item, miss in (bad if not DRY_RUN else []):
        _issue(f"⚠ 作り置き画像 {item['file']} の数字を確認してください",
               "画像から次の文言(数字)が読み取れませんでした。画像を作り直して上書きアップロードしてください。\n\n" +
               "\n".join(f"- {m}" for m in miss))
    if not nxt:
        print("[queue] 投稿できる作り置き画像がありません → カルーセルで代替")
        if not bad and not DRY_RUN:
            _issue("📦 作り置き画像の在庫切れ", "assets/queue/ の画像がなくなりました。次のバッチを作成してください(今日はテンプレート投稿で代替)。")
        return run("carousel")

    slug = f"{stamp}-q{item['file']}"
    print(f"=== {slug} (DRY_RUN={DRY_RUN}) topic={item['topic']} ===")
    hashtags = build_hashtags(load_yaml("hashtags.yml"), item.get("category", ""), item.get("tags", []))
    caption = item["caption"].strip() + "\n.\n.\n.\n" + " ".join(hashtags)
    video = q.build_still_reel(img, slug)
    cover = q.cover_jpg(img, slug)
    urls = publish_files([video, cover], f"media: {slug}")
    media_id = publish_reel(urls[0], caption, cover_url=urls[1])
    save_posted({"date": datetime.now().strftime("%Y-%m-%d"), "kind": "queue", "queue_id": item["id"],
                 "category": item.get("category", ""), "topic": item["topic"], "media_id": media_id, "slug": slug})
    _git_commit_posted(slug)
    left = q.remaining(load_posted())
    print(f"=== done (残り在庫 {left} 本) ===")
    if left in (5, 1) and not DRY_RUN:
        _issue(f"📦 作り置き画像の残りが {left} 本です", "次のバッチのプロンプトを作成して、画像を補充してください。")


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
        video = build_reel(frames, slug, post.get("_frame_kinds"))
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
    _git_commit_posted(slug)
    print("=== done ===")


if __name__ == "__main__":
    kind = sys.argv[1] if len(sys.argv) > 1 else "carousel"
    assert kind in ("carousel", "reel", "queue")
    run_queue() if kind == "queue" else run(kind)
