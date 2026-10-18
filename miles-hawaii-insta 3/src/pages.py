"""生成メディアを docs/media に置き、git push → GitHub Pages で公開 URL を得る。
Instagram API は公開 URL からしかメディアを取得できないため必須。
"""
import shutil
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
import requests
from config import MEDIA, PAGES_BASE_URL, MEDIA_KEEP_DAYS, DRY_RUN


def _git(*args):
    subprocess.run(["git", *args], check=True)


def prune_old_media():
    cutoff = datetime.now() - timedelta(days=MEDIA_KEEP_DAYS)
    for p in MEDIA.glob("*"):
        if p.is_file() and datetime.fromtimestamp(p.stat().st_mtime) < cutoff:
            p.unlink()


def publish_files(files: list[Path], message: str) -> list[str]:
    """ファイルを docs/media にコピーして commit/push し、公開URLリストを返す。"""
    if not PAGES_BASE_URL:
        raise RuntimeError("PAGES_BASE_URL が未設定です")
    prune_old_media()
    urls = []
    for f in files:
        dst = MEDIA / f.name
        shutil.copy2(f, dst)
        urls.append(f"{PAGES_BASE_URL}/media/{f.name}")

    if DRY_RUN:
        print("[pages] DRY_RUN: push をスキップ")
        return urls

    _git("config", "user.name", "insta-bot")
    _git("config", "user.email", "insta-bot@users.noreply.github.com")
    _git("add", "-A", str(MEDIA))
    # 変更が無ければ commit は失敗するので許容
    subprocess.run(["git", "commit", "-m", message], check=False)
    _git("pull", "--rebase", "--autostash", "origin", "HEAD")
    _git("push", "origin", "HEAD")
    wait_until_live(urls)
    return urls


def wait_until_live(urls: list[str], timeout_sec: int = 600):
    """Pages のデプロイ完了を URL の 200 応答で待つ。"""
    deadline = time.time() + timeout_sec
    pending = list(urls)
    while pending and time.time() < deadline:
        still = []
        for u in pending:
            try:
                r = requests.head(u, timeout=20, allow_redirects=True)
                if r.status_code != 200:
                    still.append(u)
            except requests.RequestException:
                still.append(u)
        pending = still
        if pending:
            print(f"[pages] {len(pending)} 件のデプロイ待ち...")
            time.sleep(20)
    if pending:
        raise TimeoutError(f"Pages に公開されませんでした: {pending}")
    time.sleep(10)  # CDN 伝播の余裕
