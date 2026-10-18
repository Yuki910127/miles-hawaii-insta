"""ネタ選定 → Gemini で投稿内容(JSON)を生成。"""
import json
import random
from datetime import date
import yaml
from config import DATA, BRAND_NAME, BRAND_HANDLE
from gemini_client import generate_json

POSTED = DATA / "posted.json"

SYSTEM = f"""あなたは日本語のInstagramメディア「{BRAND_NAME}」({BRAND_HANDLE})の編集長です。
テーマ:「マイルを貯めて、ハワイにお得に行く」。読者は20〜40代の日本在住で、ハワイ旅行に憧れ、クレカ・ポイ活・マイルに興味がある初心者〜中級者。

執筆ルール(厳守):
1. 事実(必要マイル数・レート・料金・制度)は、提供された<facts>の内容だけを根拠にする。facts にない数値は書かない。断定が必要なら「〜の目安」「〜時点」と添える。
2. 誇大表現・断定的な儲け話・特定カードの過度な推奨・アフィリエイト臭い文言は禁止。
3. 口調は「親しみやすい先輩」。です・ます調。絵文字は1スライドに最大1つ。
4. 1スライドの文字量は見出し18文字以内、本文は改行込みで80文字以内。スマホで一瞬で読める密度にする。
5. 保存したくなる「まとめ・早見表・手順・チェックリスト」型を優先する。
6. 既出テーマ(<posted>)と重複しない切り口にする。
7. 出力は指定JSONのみ。
"""

CAROUSEL_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "topic": {"type": "STRING", "description": "この投稿のテーマを20字以内で"},
        "cover_title": {"type": "STRING", "description": "表紙の大見出し(22字以内・改行は\\n)"},
        "cover_sub": {"type": "STRING", "description": "表紙の補足(25字以内)"},
        "slides": {
            "type": "ARRAY", "minItems": 5, "maxItems": 7,
            "items": {"type": "OBJECT", "properties": {
                "heading": {"type": "STRING"},
                "body": {"type": "STRING"},
                "emphasis": {"type": "STRING", "description": "数字や一言など強調表示する短い語(任意・10字以内)"},
            }, "required": ["heading", "body"]},
        },
        "cta_text": {"type": "STRING", "description": "最終スライドの一言(保存・フォローを促す。30字以内)"},
        "caption": {"type": "STRING", "description": "キャプション本文。冒頭1行で結論、続けて要点を3〜5行、最後に『保存して後で見返してね』系の一言。ハッシュタグは含めない。400字以内"},
        "extra_hashtags": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "この投稿固有のハッシュタグを5個(#付き・日本語可)"},
    },
    "required": ["topic", "cover_title", "cover_sub", "slides", "cta_text", "caption", "extra_hashtags"],
}

REEL_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "topic": {"type": "STRING"},
        "hook": {"type": "STRING", "description": "冒頭0〜2秒で止めるフック。20字以内。例:『ハワイ往復、実は3.5万マイル』"},
        "lines": {"type": "ARRAY", "minItems": 5, "maxItems": 8,
                   "items": {"type": "STRING", "description": "1画面1メッセージ。各22字以内"}},
        "closing": {"type": "STRING", "description": "締めの一言(フォロー誘導)。20字以内"},
        "caption": {"type": "STRING", "description": "250字以内。ハッシュタグ含めない"},
        "extra_hashtags": {"type": "ARRAY", "items": {"type": "STRING"}},
    },
    "required": ["topic", "hook", "lines", "closing", "caption", "extra_hashtags"],
}


def load_yaml(name):
    with open(DATA / name, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_posted() -> list[dict]:
    if POSTED.exists():
        return json.loads(POSTED.read_text(encoding="utf-8"))
    return []


def save_posted(entry: dict):
    items = load_posted()
    items.append(entry)
    POSTED.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def pick_category(topics: dict) -> dict:
    cats = topics["categories"]
    weights = [c.get("weight", 1.0) for c in cats]
    return random.choices(cats, weights=weights, k=1)[0]


def build_hashtags(hashtags: dict, category_key: str, extra: list[str]) -> list[str]:
    """固定タグ(ブランド+ビッグワード)+カテゴリ別+投稿固有。最大25個。"""
    tags = list(hashtags["always"])
    tags += random.sample(hashtags["big"], k=min(6, len(hashtags["big"])))
    tags += hashtags["by_category"].get(category_key, [])[:6]
    tags += [t if t.startswith("#") else f"#{t}" for t in extra][:5]
    seen, out = set(), []
    for t in tags:
        t = t.replace(" ", "").replace("＃", "#")
        if t.lower() not in seen:
            seen.add(t.lower())
            out.append(t)
    return out[:25]


def recent_topics(n=40) -> str:
    return "\n".join(f"- {p['topic']}" for p in load_posted()[-n:]) or "(なし)"


def generate_post(kind: str) -> dict:
    """kind: 'carousel' | 'reel'"""
    topics = load_yaml("topics.yml")
    hashtags = load_yaml("hashtags.yml")
    facts = (DATA / "facts.md").read_text(encoding="utf-8")
    cat = pick_category(topics)
    seed = random.choice(cat["ideas"])
    today = date.today().strftime("%Y年%m月")

    user_prompt = f"""今日は {today} です。
<category>{cat['name']}</category>
<seed_idea>{seed}</seed_idea>
<posted>
{recent_topics()}
</posted>
<facts>
{facts}
</facts>

seed_idea を出発点に、カテゴリ「{cat['name']}」で{'カルーセル(画像複数枚)' if kind=='carousel' else 'リール(縦型・テキスト動画)'}投稿を1本作ってください。
既出テーマと切り口が被るなら、別の角度(初心者向け/比較/失敗談/チェックリスト/数字で見る等)に変えてください。"""

    schema = CAROUSEL_SCHEMA if kind == "carousel" else REEL_SCHEMA
    data = generate_json(SYSTEM, user_prompt, schema)
    data["kind"] = kind
    data["category"] = cat["key"]
    data["hashtags"] = build_hashtags(hashtags, cat["key"], data.get("extra_hashtags", []))
    data["full_caption"] = data["caption"].strip() + "\n.\n.\n.\n" + " ".join(data["hashtags"])
    return data


if __name__ == "__main__":
    import sys
    kind = sys.argv[1] if len(sys.argv) > 1 else "carousel"
    print(json.dumps(generate_post(kind), ensure_ascii=False, indent=2))
