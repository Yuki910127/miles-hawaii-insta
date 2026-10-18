"""Jinja2 テンプレート → Playwright(Chromium) で PNG 化。"""
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup, escape
from config import TEMPLATES, OUT, BRAND_NAME, BRAND_HANDLE

env = Environment(loader=FileSystemLoader(str(TEMPLATES)), autoescape=True)


def _nl2br(s):
    """改行(実改行・リテラル\\n)を <br> に。本文はエスケープしてから結合。"""
    s = (s or "").replace("\\n", "\n")
    return Markup("<br>".join(str(escape(line)) for line in s.split("\n")))


env.filters["nl2br"] = _nl2br


def _render_html(template: str, ctx: dict) -> str:
    ctx = {"brand": BRAND_NAME, "handle": BRAND_HANDLE, **ctx}
    return env.get_template(template).render(**ctx)


def html_to_png(pages: list[tuple[str, Path]], width: int, height: int):
    """pages: [(html, out_path), ...] を1ブラウザでまとめて撮影。"""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
        for html, out in pages:
            page.set_content(html, wait_until="networkidle")
            page.wait_for_timeout(150)  # フォント描画待ち
            page.screenshot(path=str(out), clip={"x": 0, "y": 0, "width": width, "height": height})
        browser.close()


def render_carousel(post: dict, slug: str) -> list[Path]:
    """表紙 + 本文スライド + CTA の PNG(1080x1350)を返す。"""
    slides = []
    total = len(post["slides"]) + 2
    slides.append(_render_html("carousel.html", {"type": "cover", "post": post, "idx": 1, "total": total}))
    for i, s in enumerate(post["slides"], start=2):
        slides.append(_render_html("carousel.html", {"type": "body", "post": post, "slide": s, "idx": i, "total": total}))
    slides.append(_render_html("carousel.html", {"type": "cta", "post": post, "idx": total, "total": total}))

    outs = []
    jobs = []
    for i, html in enumerate(slides, start=1):
        out = OUT / f"{slug}_{i:02d}.png"
        jobs.append((html, out))
        outs.append(out)
    html_to_png(jobs, 1080, 1350)
    return outs


def render_reel_frames(post: dict, slug: str) -> list[Path]:
    """リール用テキストオーバーレイ(1080x1920・透過背景)を返す。"""
    frames = [("hook", post["hook"])] + [("line", l) for l in post["lines"]] + [("closing", post["closing"])]
    jobs, outs = [], []
    for i, (kind, text) in enumerate(frames, start=1):
        html = _render_html("reel_slide.html", {"kind": kind, "text": text, "idx": i, "total": len(frames)})
        out = OUT / f"{slug}_r{i:02d}.png"
        jobs.append((html, out))
        outs.append(out)
    _html_to_png_transparent(jobs, 1080, 1920)
    return outs


def _html_to_png_transparent(pages, width, height):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
        for html, out in pages:
            page.set_content(html, wait_until="networkidle")
            page.wait_for_timeout(150)
            page.screenshot(path=str(out), omit_background=True)
        browser.close()


def preview_html(template: str, ctx: dict) -> str:
    """検証用: HTML文字列を返す。"""
    return _render_html(template, ctx)
