"""作り置きリールの「冒頭1秒の一言」フレームを作る。
背景 = 図解をぼかして暗くしたもの。中央に白文字＋黒フチの大きな一言(**〜** は黄色で強調)。
"""
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

W, H = 1080, 1920
FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
]
YELLOW = (255, 214, 10)
WHITE = (255, 255, 255)


def _font(size: int) -> ImageFont.FreeTypeFont:
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            return ImageFont.truetype(p, size, index=0)  # index0 = JP
    return ImageFont.load_default()


def _segments(line: str):
    """'ハワイ往復**何マイル**？' → [('ハワイ往復',False),('何マイル',True),('？',False)]"""
    out, pos = [], 0
    for m in re.finditer(r"\*\*(.+?)\*\*", line):
        if m.start() > pos:
            out.append((line[pos:m.start()], False))
        out.append((m.group(1), True))
        pos = m.end()
    if pos < len(line):
        out.append((line[pos:], False))
    return out


def _cover(img: Image.Image) -> Image.Image:
    r = max(W / img.width, H / img.height)
    img = img.resize((round(img.width * r), round(img.height * r)), Image.LANCZOS)
    x, y = (img.width - W) // 2, (img.height - H) // 2
    return img.crop((x, y, x + W, y + H))


def make_hook_frame(src: Path, text: str, out: Path) -> Path:
    """text は改行 \\n 区切り(2〜3行)。各行は幅に収まるよう自動で文字サイズを調整。"""
    bg = _cover(Image.open(src).convert("RGB")).filter(ImageFilter.GaussianBlur(18))
    bg = ImageEnhance.Brightness(bg).enhance(0.45)
    d = ImageDraw.Draw(bg)
    lines = [l for l in text.replace("\\n", "\n").split("\n") if l.strip()]
    # 行をまたぐ **〜** に備えて、強調の開閉状態を行ごとに引き継ぐ
    fixed, open_em = [], False
    for ln in lines:
        if open_em:
            ln = "**" + ln
        open_em = ln.count("**") % 2 == 1
        fixed.append(ln + ("**" if open_em else ""))
    max_w = W - 120
    segs_list = [_segments(ln) for ln in fixed]
    # 一番長い行が収まるサイズに全行を揃える(行ごとにバラつかせない)
    size = 190
    while size > 70:
        f = _font(size)
        if all(sum(d.textlength(t, font=f) for t, _ in segs) <= max_w for segs in segs_list):
            break
        size -= 6
    rendered = [(segs, f, sum(d.textlength(t, font=f) for t, _ in segs), size) for segs in segs_list]
    gap = 30
    total_h = sum(s for *_, s in rendered) + gap * (len(rendered) - 1)
    y = (H - total_h) // 2 - 40
    for segs, f, width, size in rendered:
        x = (W - width) / 2
        stroke = max(10, size // 9)
        for t, em in segs:
            d.text((x, y), t, font=f, fill=YELLOW if em else WHITE, stroke_width=stroke, stroke_fill=(17, 17, 17))
            x += d.textlength(t, font=f)
        y += size + gap
    # 下部に「保存して見返してね」の小さな帯
    sf = _font(44)
    tag = "▼ 詳しくは図解で"
    tw = d.textlength(tag, font=sf)
    d.rounded_rectangle(((W - tw) / 2 - 36, H - 430, (W + tw) / 2 + 36, H - 350), radius=40, fill=(14, 124, 134))
    d.text(((W - tw) / 2, H - 418), tag, font=sf, fill=WHITE)
    bg.save(out, quality=95)
    return out
