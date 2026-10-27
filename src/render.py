"""Jinja2 テンプレート → Playwright(Chromium) で PNG 化。"""
import base64
import random
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup, escape
from config import TEMPLATES, OUT, ASSETS, BRAND_NAME, BRAND_HANDLE

env = Environment(loader=FileSystemLoader(str(TEMPLATES)), autoescape=True)


def _nl2br(s):
    s = (s or "").replace("\\n", "\n")
    return Markup("<br>".join(str(escape(line)) for line in s.split("\n")))


def _em(s):
    """**強調** → 赤字、__下線__ → 赤下線、改行 → <br>。本文はエスケープ済み。"""
    import re
    s = (s or "").replace("\\n", "\n")
    out = []
    for line in s.split("\n"):
        t = str(escape(line))
        t = re.sub(r"\*\*(.+?)\*\*", r'<span class="em">\1</span>', t)
        t = re.sub(r"__(.+?)__", r'<span class="ul">\1</span>', t)
        out.append(t)
    return Markup("<br>".join(out))


env.filters["nl2br"] = _nl2br
env.filters["em"] = _em


def load_deco() -> dict:
    """assets/deco/*.svg を名前ごとに data URI で返す(plane / hibiscus / suitcase / ticket / palm)。"""
    d = ASSETS / "deco"
    out = {}
    if d.exists():
        for p in d.glob("*.svg"):
            for key in ("plane", "hibiscus", "suitcase", "ticket", "palm"):
                if key in p.stem.lower():
                    out[key] = _data_uri(p)
    return out

MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".svg": "image/svg+xml"}


def _data_uri(p: Path) -> str:
    return f"data:{MIME.get(p.suffix.lower(), 'image/png')};base64," + base64.b64encode(p.read_bytes()).decode()


def pick_mascot(prefer: str | None = None) -> str | None:
    """assets/mascot/ からポーズ画像を選ぶ。prefer に一致する名前を優先(happy / surprised / point)。"""
    d = ASSETS / "mascot"
    files = [p for p in d.glob("*") if p.suffix.lower() in MIME] if d.exists() else []
    if not files:
        return None
    if prefer:
        hit = [p for p in files if prefer in p.stem.lower()]
        if hit:
            return _data_uri(random.choice(hit))
    return _data_uri(random.choice(files))


def pick_bg_photo() -> str | None:
    """assets/bg_photos/ からランダム(無ければ None → グラデーション)。"""
    d = ASSETS / "bg_photos"
    files = [p for p in d.glob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")] if d.exists() else []
    return _data_uri(random.choice(files)) if files else None


def pick_illust(key: str | None) -> str | None:
    """assets/illust/<key>.* を data URI で返す。"""
    if not key:
        return None
    d = ASSETS / "illust"
    for p in d.glob(f"{key}.*") if d.exists() else []:
        if p.suffix.lower() in MIME:
            return _data_uri(p)
    return None


def _render_html(template: str, ctx: dict) -> str:
    ctx = {"brand": BRAND_NAME, "handle": BRAND_HANDLE, **ctx}
    return env.get_template(template).render(**ctx)


def _shoot(pages: list[tuple[str, Path]], width: int, height: int, transparent=False):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
        for html, out in pages:
            page.set_content(html, wait_until="networkidle")
            page.wait_for_timeout(200)
            if transparent:
                page.screenshot(path=str(out), omit_background=True)
            else:
                page.screenshot(path=str(out), clip={"x": 0, "y": 0, "width": width, "height": height})
        browser.close()


POSE_BY_FORMAT = {"ranking": "surprised", "table": "point", "checklist": "happy", "editorial": "happy", "points": "happy"}
SLIDE_POSES = ["point", "surprised", "happy"]


def render_carousel(post: dict, slug: str) -> list[Path]:
    """1枚目(編集記事表紙 or インフォグラフィック) + 編集記事スタイルの詳細スライド + CTA。1080x1350。"""
    fmt = post.get("format", "editorial")
    mascot = pick_mascot(POSE_BY_FORMAT.get(fmt))
    deco = load_deco()
    bg = pick_bg_photo()
    total = len(post["slides"]) + 2
    pages = []

    if fmt in ("ranking", "table", "checklist"):
        post = {**post, "title_html": Markup(f"{escape(post['title_top'])}<br><span class=\"hl\">{escape(post['title_hl'])}</span>")}
        pages.append(_render_html("infographic.html", {"post": post, "mascot": mascot, "bg_photo": bg}))
    else:
        pages.append(_render_html("editorial.html", {"type": "cover", "post": post, "idx": 1, "total": total,
                                                     "mascot": mascot, "deco": deco, "bg_photo": bg,
                                                     "illust": pick_illust(post.get("cover_illust"))}))

    for i, s in enumerate(post["slides"], start=2):
        # マスコットは1枚おきに登場(毎回だと情報スペースが減る)
        m = pick_mascot(SLIDE_POSES[i % len(SLIDE_POSES)]) if i % 2 == 0 else None
        pages.append(_render_html("editorial.html", {"type": "body", "post": post, "slide": s, "idx": i, "total": total,
                                                     "mascot": m, "deco": deco, "bg_photo": None,
                                                     "illust": pick_illust(s.get("illust")),
                                                     "from_illust": pick_illust(s.get("example_from_illust")),
                                                     "to_illust": pick_illust(s.get("example_to_illust"))}))
    pages.append(_render_html("editorial.html", {"type": "cta", "post": post, "idx": total, "total": total,
                                                 "mascot": pick_mascot("happy"), "deco": deco, "bg_photo": None}))

    jobs = [(html, OUT / f"{slug}_{i:02d}.png") for i, html in enumerate(pages, start=1)]
    _shoot(jobs, 1080, 1350)
    return [o for _, o in jobs]


def render_reel_frames(post: dict, slug: str) -> list[Path]:
    """リール用テキストオーバーレイ(1080x1920・透過)。frames の kind ごとに描き分け。"""
    deco = load_deco()
    frames = post.get("frames") or ([{"kind": "hook", "text": post["hook"]}] +
                                    [{"kind": "line", "text": l} for l in post["lines"]] +
                                    [{"kind": "closing", "text": post["closing"]}])
    mascot = pick_mascot("point")
    jobs = []
    for i, f in enumerate(frames, start=1):
        kind = f.get("kind", "line")
        html = _render_html("reel_slide.html", {
            "kind": kind, "text": f.get("text", ""), "value": f.get("value", ""),
            "insert": deco.get(f.get("insert") or "", None),
            "mascot": mascot if kind == "closing" else None,
            "idx": i, "total": len(frames)})
        jobs.append((html, OUT / f"{slug}_r{i:02d}.png"))
    _shoot(jobs, 1080, 1920, transparent=True)
    post["_frame_kinds"] = [f.get("kind", "line") for f in frames]
    return [o for _, o in jobs]


def preview_html(template: str, ctx: dict) -> str:
    return _render_html(template, ctx)
