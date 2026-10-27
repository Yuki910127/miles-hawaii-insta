"""queue_batchXX.py から
  data/queue.yml            … 自動投稿が読む台帳(キャプション・照合用の文言)
  QUEUE_PROMPTS_batchXX.md  … Genspark に貼るプロンプト集
を生成する。使い方: python tools/build_queue.py queue_batch01
"""
import importlib, sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

STYLE = """【サイズ】縦9:16(1080×1920)。上端と下端の約8%には文字を置かない(Instagramの表示で隠れるため)。

【テイスト】日本の人気マイル系インスタアカウントのような、情報量が多く賑やかな「図解ポスター」。背景は青空と雲・空港やハワイの景色を淡く。
パネルは角丸で、パネルごとに色・大きさ・形に強弱をつける(見出し帯を色付きにする、重要な数字は赤枠で大きく、注意は黄色、締めはティールの吹き出し)。
意味が伝わる大きめのイラストアイコン(飛行機、カード、コイン、カレンダー、スーツケース、ヤシの木、ハイビスカスなど)を余白にたくさん散りばめる。
配色はティール(#0E7C86)とコーラル(#F28C28)をメインに、強調は赤(#E2572B)、背景にサンド(#FFF7EA)。
実在の航空会社・ホテル・カード会社のロゴ、機体塗装、カード券面は描かない(社名は文字だけで書く)。人物の顔は描かない。

【キャラクター】添付したウミガメのパイロット(ホヌ)を使う。見た目(ティールの制服・帽子・甲羅・顔)は添付画像と同じにする。
大きめのホヌを1体、パネルの縁に乗っているように重ねて配置。もう1体を小さく別の場所に。表情とポーズは内容に合わせて変える。"""

TAIL = """【注意】上の「文字」に書いた文言を一字一句そのまま使う(数字・記号を変えない、省略しない、言い換えない)。それ以外の文字は入れない。
日本語はくっきり読める太いゴシック体で、文字化けさせない。"""


def build(mod_name: str):
    mod = importlib.import_module(mod_name)
    posts = mod.POSTS
    # --- queue.yml(既存に追記・同じ id は上書き) ---
    qpath = ROOT / "data" / "queue.yml"
    existing = (yaml.safe_load(qpath.read_text(encoding="utf-8")) or {}).get("items", []) if qpath.exists() else []
    by_id = {it["id"]: it for it in existing}
    for p in posts:
        by_id[p["id"]] = {
            "id": p["id"], "file": f"{p['id']:03d}", "category": p["category"], "topic": p["topic"],
            "caption": p["caption"], "tags": p.get("tags", []),
            "expect": [t for _, t in p["texts"]],
        }
    # 冒頭の一言(tools/hooks.py)を全件に付与
    try:
        from hooks import HOOKS
    except ImportError:
        HOOKS = {}
    for k, it in by_id.items():
        if k in HOOKS:
            it["hook"] = HOOKS[k]
    # 2本を1枚にまとめた画像(tools/merges.py)は、キャプション等を結合して吸収側を外す
    try:
        from merges import MERGES
    except ImportError:
        MERGES = {}
    for keep, absorbed in MERGES.items():
        if keep not in by_id:
            continue
        base = by_id[keep]
        for a in absorbed:
            if a not in by_id:
                continue
            src = by_id.pop(a)
            base["topic"] = base["topic"].split(" ＋ ")[0] + " ＋ " + src["topic"] if " ＋ " not in base["topic"] else base["topic"] + " ＋ " + src["topic"]
            base["caption"] = base["caption"].rstrip() + "\n\n――――\n\n" + src["caption"].strip()
            base["tags"] = list(dict.fromkeys(base.get("tags", []) + src.get("tags", [])))[:5]
            base["expect"] = base.get("expect", []) + src.get("expect", [])
    try:
        from priority import PRIORITY
    except ImportError:
        PRIORITY = []
    for k, it in by_id.items():
        it.pop("priority", None)
        if k in PRIORITY:
            it["priority"] = 1
    items = [by_id[k] for k in sorted(by_id)]
    qpath.write_text("# 自動生成(tools/build_queue.py)。画像は assets/queue/<file>.png|jpg|webp\n" +
                     yaml.safe_dump({"items": items}, allow_unicode=True, sort_keys=False, width=1000), encoding="utf-8")

    # --- プロンプト集 ---
    out = [f"# Genspark 画像プロンプト集({mod_name})\n",
           "## 使い方\n",
           "1. Genspark の画像生成を開き、モデルは **GPT Image** を選ぶ(比較で一番きれいだったもの)。",
           "2. **ホヌの画像(ティール制服)を添付**してから、下のプロンプトを1本ずつ丸ごと貼って生成。",
           "3. 文字と数字が「文字」欄のとおりか目で確認(違っていたら作り直し)。",
           "4. 番号の名前で保存(`001.png`、`002.png` …)。jpg / webp でもOK。",
           "5. まとめて GitHub の `assets/queue/` にアップロード → 毎日20時に1本ずつ自動でリール投稿されます。\n",
           "---\n"]
    for p in posts:
        lines = "\n".join(f"・{label}:「{text}」" for label, text in p["texts"])
        prompt = (f"添付したキャラクター(ホヌ)を使って、Instagramリール用の縦長インフォグラフィックを1枚作ってください。\n\n"
                  f"【テーマ】{p['topic']}\n\n{STYLE}\n\n【構成】{p['design']}\n\n【文字(この文言だけを使う)】\n{lines}\n\n{TAIL}")
        out.append(f"## {p['id']:03d} {p['topic']}\n\n保存名: `{p['id']:03d}.png`\n\n```\n{prompt}\n```\n")
    md = ROOT / f"QUEUE_PROMPTS_{mod_name.replace('queue_', '')}.md"
    md.write_text("\n".join(out), encoding="utf-8")
    print(f"queue.yml: {len(items)} items / {md.name}")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "queue_batch01")
