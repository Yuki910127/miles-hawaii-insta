"""Instagram API でカルーセル / リールを投稿。
IG_API_MODE=facebook  : graph.facebook.com + IG_USER_ID(ページトークン)
IG_API_MODE=instagram : graph.instagram.com + /me(Instagramログイントークン)
"""
import time
import requests
from config import IG_API, IG_API_MODE, IG_USER_ID, IG_ACCESS_TOKEN, DRY_RUN


def _get(path, **params):
    params["access_token"] = IG_ACCESS_TOKEN
    r = requests.get(f"{IG_API}/{path}", params=params, timeout=60)
    _raise(r)
    return r.json()


def _post(path, **params):
    params["access_token"] = IG_ACCESS_TOKEN
    r = requests.post(f"{IG_API}/{path}", data=params, timeout=120)
    _raise(r)
    return r.json()


def _raise(r):
    if r.status_code >= 400:
        raise RuntimeError(f"Instagram API error {r.status_code}: {r.text}")


def me() -> dict:
    """アカウント情報。どちらのモードでも 'user_id' キーで IG ユーザーIDを返す。"""
    if IG_API_MODE == "facebook":
        if not IG_USER_ID:
            raise RuntimeError("IG_USER_ID が未設定です(Variables に Instagram Business Account ID を登録)")
        d = _get(IG_USER_ID, fields="id,username,followers_count,media_count")
        d["user_id"] = d["id"]
        return d
    return _get("me", fields="user_id,username,followers_count,media_count")


def _wait_container(container_id: str, timeout_sec: int = 900):
    """動画などの処理完了を待つ。"""
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        st = _get(container_id, fields="status_code,status")
        code = st.get("status_code")
        if code == "FINISHED":
            return
        if code in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"コンテナ処理失敗: {st}")
        print(f"[ig] container {container_id} status={code} ... waiting")
        time.sleep(15)
    raise TimeoutError("コンテナ処理がタイムアウトしました")


def publish_carousel(image_urls: list[str], caption: str) -> str:
    if DRY_RUN:
        print("[ig] DRY_RUN: carousel\n", caption[:200], "\n", image_urls)
        return "dry-run"
    uid = me()["user_id"]
    children = []
    for url in image_urls:
        c = _post(f"{uid}/media", image_url=url, is_carousel_item="true")
        children.append(c["id"])
    time.sleep(5)
    for cid in children:
        _wait_container(cid, timeout_sec=300)
    container = _post(f"{uid}/media", media_type="CAROUSEL", children=",".join(children), caption=caption)
    _wait_container(container["id"], timeout_sec=300)
    res = _post(f"{uid}/media_publish", creation_id=container["id"])
    print("[ig] published carousel:", res)
    return res["id"]


def publish_reel(video_url: str, caption: str, cover_url: str | None = None) -> str:
    if DRY_RUN:
        print("[ig] DRY_RUN: reel\n", caption[:200], "\n", video_url)
        return "dry-run"
    uid = me()["user_id"]
    params = dict(media_type="REELS", video_url=video_url, caption=caption, share_to_feed="true")
    if cover_url:
        params["cover_url"] = cover_url
    container = _post(f"{uid}/media", **params)
    _wait_container(container["id"])
    res = _post(f"{uid}/media_publish", creation_id=container["id"])
    print("[ig] published reel:", res)
    return res["id"]


def media_insights(media_id: str) -> dict:
    """投稿ごとの指標。取れない指標があっても落ちないように個別取得。"""
    out = {}
    for metric in ("reach", "saved", "likes", "comments", "shares", "views"):
        try:
            d = _get(f"{media_id}/insights", metric=metric)
            out[metric] = d["data"][0]["values"][0]["value"] if d.get("data") else 0
        except Exception:
            out[metric] = None
    return out
