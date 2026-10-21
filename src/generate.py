"""ネタ選定 → Gemini で投稿内容(JSON)を生成。

カルーセルの1枚目は高密度インフォグラフィック(ranking / table / checklist)。
それが作れないテーマは points(シンプル表紙)にフォールバック。
"""
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
1. 事実(必要マイル数・レート・料金・年会費・制度)は、提供された<facts>の内容だけを根拠にする。facts にない数値は絶対に書かない。facts に無い項目の数値欄は「要確認」とする。
2. 誇大表現・断定的な儲け話・特定カードの過度な推奨・アフィリエイト臭い文言は禁止。
3. 口調は「親しみやすい先輩」。です・ます調。絵文字は1スライドに最大1つ。
4. 詳細スライド(slides)は「編集記事スタイル」。各スライドは heading(14字以内)+ lead(結論1文・40字以内)を必須とし、
   body / big_value(巨大数字) / example(たとえば箱) / cautions(注意点1〜3) / conclusion(結論帯・34字以内) のうち2〜3個を組み合わせる。
   強調したい語句は **二重アスタリスク** で囲む(赤字になる)。1スライドの合計文字数は180字以内。
5. 既出テーマ(<posted>)と重複しない切り口にする。
6. 1枚目(表紙)の format を次から選ぶ:
   - editorial: 標準。title_lines(2〜3行・各10字以内。強調語は **〜**、下線は __〜__)+ subtitle + bottom_box(結論1〜2行。数字を1つ入れる)。
   - ranking  : 「○○で選ぶ最強△△」型(facts に比較できる数値が十分あるときだけ)。3〜5行。
   - table    : 「早見表」型(facts に表にできる数値があるときだけ)。列3〜4、行4〜8。強調セルは値の先頭に *。
   - checklist: 「やること/チェック」型。5〜6項目。
   迷ったら editorial。
7. ranking/table/checklist のときも title_lines と bottom_box は埋める(title_top/title_hl は title_lines から自動生成される)。
8. slides は6〜9枚。slides[0] は「まず目指すゴール」や「結論」から入り、以降は手順・比較・注意・まとめの順。cta_text は24字以内で1文。
9. リール(frames)は「実写のハワイ映像の上に、白文字+黒フチの大きな文字」を1画面1メッセージで出す形式。
   1枚目は hook(疑問・意外性・数字で止める)、最後は closing(保存/フォロー誘導)。途中に bignum(巨大数字)を1枚入れると強い。
   各フレームの文字は2〜3行・各行12字以内。読み上げなしで読める量にする。
10. 出力は指定JSONのみ。該当しない format の項目は空配列でよい。
"""

CAROUSEL_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "topic": {"type": "STRING", "description": "この投稿のテーマを20字以内で"},
        "format": {"type": "STRING", "enum": ["ranking", "table", "checklist", "points"]},
        "ribbon": {"type": "STRING", "description": "表紙左上の赤帯(10字以内。例: 年間利用額で選ぶ / 保存版 / 出発前チェック)"},
        "title_lines": {"type": "ARRAY", "minItems": 2, "maxItems": 3, "items": {"type": "STRING"}, "description": "表紙見出し。各10字以内。強調は **〜**、下線は __〜__"},
        "subtitle": {"type": "STRING", "description": "表紙の補足(20字以内)"},
        "bottom_box": {"type": "STRING", "description": "表紙下部の結論(2行・各16字以内・改行\\n・数字を**で強調)"},
        "bubble": {"type": "STRING", "description": "マスコットの一言(16字以内)"},
        "rows": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
            "rank": {"type": "STRING"}, "condition": {"type": "STRING", "description": "ランクの条件(10字以内・改行\\n可)"},
            "name": {"type": "STRING", "description": "14字以内"}, "name_sub": {"type": "STRING"},
            "bullets": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "各14字以内。注意点は先頭に ! を付ける"},
            "stats": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
                "label": {"type": "STRING"}, "value": {"type": "STRING"}, "unit": {"type": "STRING"}}, "required": ["label", "value"]}},
        }, "required": ["rank", "name", "bullets", "stats"]}},
        "columns": {"type": "ARRAY", "items": {"type": "STRING"}},
        "table_rows": {"type": "ARRAY", "items": {"type": "ARRAY", "items": {"type": "STRING"}}},
        "takeaway": {"type": "STRING", "description": "table のとき、表の下に出す結論1〜2行(各18字以内・改行\\n)"},
        "table_note": {"type": "STRING", "description": "注記(40字以内。時点・条件など)"},
        "check_items": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
            "title": {"type": "STRING"}, "desc": {"type": "STRING"}}, "required": ["title"]}},
        "footer": {"type": "STRING", "description": "表紙下部の一言(28字以内)"},
        "slides": {"type": "ARRAY", "minItems": 6, "maxItems": 9,
                   "items": {"type": "OBJECT", "properties": {
                       "heading": {"type": "STRING", "description": "14字以内。強調は**。big_value があるスライドでは heading は結論語(例: ハワイ往復)、pre_heading に前置き(例: まず目指したいのは)"},
                       "pre_heading": {"type": "STRING", "description": "big_value スライド用の前置き(12字以内・任意)"},
                       "lead": {"type": "STRING", "description": "結論1文・40字以内"},
                       "body": {"type": "STRING", "description": "補足・60字以内(任意)"},
                       "big_label": {"type": "STRING"}, "big_value": {"type": "STRING", "description": "巨大数字(例: 35,000)"}, "big_unit": {"type": "STRING"},
                       "example_title": {"type": "STRING", "description": "既定は『たとえば』"}, "example_text": {"type": "STRING", "description": "30字以内"},
                       "example_value": {"type": "STRING"}, "example_value_note": {"type": "STRING"},
                       "cautions": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "各24字以内・最大3"},
                       "conclusion": {"type": "STRING", "description": "結論帯・34字以内"},
                       "illust": {"type": "STRING", "description": "<illusts> の key から内容に最も合う挿絵を1つ(無ければ空)"}},
                       "required": ["heading", "lead"]}},
        "cover_illust": {"type": "STRING", "description": "表紙用の挿絵 key(任意)"},
        "cta_text": {"type": "STRING", "description": "最終スライドの一言。24字以内・1文"},
        "caption": {"type": "STRING", "description": "キャプション。冒頭1行で結論、要点3〜5行、最後に保存を促す一言。ハッシュタグは含めない。400字以内"},
        "extra_hashtags": {"type": "ARRAY", "items": {"type": "STRING"}},
    },
    "required": ["topic", "format", "title_lines", "subtitle", "bottom_box", "footer", "slides", "cta_text", "caption", "extra_hashtags"],
}

REEL_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "topic": {"type": "STRING"},
        "frames": {"type": "ARRAY", "minItems": 6, "maxItems": 10, "items": {"type": "OBJECT", "properties": {
            "kind": {"type": "STRING", "enum": ["hook", "line", "bignum", "vertical", "closing"],
                     "description": "hook=冒頭(1枚目必須) / line=通常 / bignum=巨大数字 / vertical=縦書き(1本に1枚まで) / closing=締め(最後必須)"},
            "text": {"type": "STRING", "description": "1画面1メッセージ。改行\\nで2〜3行、各行12字以内。強調語は **〜**(1〜2語)"},
            "value": {"type": "STRING", "description": "bignum のときの数字(例: 70% / 35,000)。他は空"},
            "insert": {"type": "STRING", "enum": ["", "plane", "ticket", "suitcase", "hibiscus", "palm"], "description": "差し込み小物(任意)"},
        }, "required": ["kind", "text"]}},
        "caption": {"type": "STRING", "description": "250字以内。ハッシュタグ含めない"},
        "extra_hashtags": {"type": "ARRAY", "items": {"type": "STRING"}},
    },
    "required": ["topic", "frames", "caption", "extra_hashtags"],
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


def load_facts() -> str:
    """手入力の facts.md + 自動リサーチの facts_auto.md(あれば)を結合。"""
    parts = [(DATA / "facts.md").read_text(encoding="utf-8")]
    auto = DATA / "facts_auto.md"
    if auto.exists():
        parts.append("\n\n# 自動リサーチで取得した最新情報(出典・取得日付き)\n" + auto.read_text(encoding="utf-8"))
    return "\n".join(parts)


def load_illust_catalog() -> dict:
    p = DATA / "illust_catalog.yml"
    return (yaml.safe_load(p.read_text(encoding="utf-8")) or {}).get("illusts", {}) if p.exists() else {}


def available_illusts() -> dict:
    """assets/illust に実在するものだけ(無いものを選ばせない)。"""
    from config import ASSETS
    cat = load_illust_catalog()
    d = ASSETS / "illust"
    have = {p.stem for p in d.glob("*") if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")} if d.exists() else set()
    return {k: v for k, v in cat.items() if k in have}


def load_style_hints() -> str:
    """ベンチマーク分析由来の『作り方のヒント』(あれば)。"""
    p = DATA / "style_hints.md"
    return p.read_text(encoding="utf-8") if p.exists() else ""


def pick_category(topics: dict) -> dict:
    cats = topics["categories"]
    weights = [c.get("weight", 1.0) for c in cats]
    return random.choices(cats, weights=weights, k=1)[0]


def build_hashtags(hashtags: dict, category_key: str, extra: list[str]) -> list[str]:
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


def _sanitize_carousel(d: dict) -> dict:
    """format ごとの必須データが欠けていたら points にフォールバック。"""
    f = d.get("format", "editorial")
    if f == "ranking" and len(d.get("rows") or []) < 3:
        f = "editorial"
    if f == "table" and (len(d.get("columns") or []) < 2 or len(d.get("table_rows") or []) < 3):
        f = "editorial"
    if f == "checklist" and len(d.get("check_items") or []) < 4:
        f = "editorial"
    d["format"] = f
    import re
    plain = [re.sub(r"[*_]", "", x) for x in (d.get("title_lines") or ["", ""])]
    d["title_lines"] = (d.get("title_lines") or [])[:3]
    d["title_top"] = plain[0] if plain else ""
    d["title_hl"] = "".join(plain[1:3])
    d["slides"] = (d.get("slides") or [])[:9]
    ok = set(available_illusts().keys())
    for sl in d["slides"]:
        sl["cautions"] = (sl.get("cautions") or [])[:3]
        if sl.get("illust") not in ok:
            sl["illust"] = ""
    if d.get("cover_illust") not in ok:
        d["cover_illust"] = ""
    d["rows"] = (d.get("rows") or [])[:5]
    for r in d["rows"]:
        r["bullets"] = (r.get("bullets") or [])[:4]
        r["stats"] = (r.get("stats") or [])[:2]
    d["table_rows"] = (d.get("table_rows") or [])[:8]
    d["check_items"] = (d.get("check_items") or [])[:6]
    d["as_of"] = date.today().strftime("%Y年%m月")
    # 旧テンプレ互換
    d["cover_title"] = "\n".join(plain)
    d["cover_sub"] = d.get("subtitle", "")
    return d


def generate_post(kind: str) -> dict:
    """kind: 'carousel' | 'reel'"""
    topics = load_yaml("topics.yml")
    hashtags = load_yaml("hashtags.yml")
    facts = load_facts()
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
<style_hints>
{load_style_hints() or "(なし)"}
</style_hints>
<illusts>
{chr(10).join(f"- {k}: {v}" for k, v in available_illusts().items()) or "(なし)"}
</illusts>

style_hints は「作り方」の参考です(他アカウントの文言を写すためのものではありません)。
illusts は使える挿絵の一覧です。各スライドの illust には、この一覧の key だけを使い、同じ key を連続で使わないでください。
seed_idea を出発点に、カテゴリ「{cat['name']}」で{'カルーセル(1枚目=保存される高密度の表紙 + 詳細スライド)' if kind=='carousel' else 'リール(縦型・テキスト動画)'}投稿を1本作ってください。
既出テーマと切り口が被るなら、別の角度(初心者向け/比較/失敗談/チェックリスト/数字で見る等)に変えてください。"""

    schema = CAROUSEL_SCHEMA if kind == "carousel" else REEL_SCHEMA
    required = ["topic", "slides", "caption"] if kind == "carousel" else ["topic", "frames", "caption"]

    # モデルがスキーマを一部無視して返すことがあるので、必須キーが欠けていたら最大3回まで作り直す
    data = None
    for attempt in range(3):
        d = generate_json(SYSTEM, user_prompt + ("" if attempt == 0 else
                          f"\n\n※前回の出力には {', '.join(k for k in required if k not in (d or {}))} が欠けていました。必ず全ての必須キーを含めてください。"),
                          schema)
        print(f"[gen] keys={sorted(d.keys())}")
        if all(d.get(k) for k in required):
            data = d
            break
        print(f"[gen] 必須キー不足 → 再生成 ({attempt+1}/3)")
    if data is None:
        raise RuntimeError(f"Gemini の出力に必須キーが揃いませんでした: {required}")
    data.setdefault("topic", seed)

    if kind == "carousel":
        data = _sanitize_carousel(data)
    else:
        fr = [f for f in (data.get("frames") or []) if isinstance(f, dict) and f.get("text")]
        for f in fr:
            f["kind"] = f.get("kind") or "line"
        if not fr:
            raise RuntimeError("リールのフレームが生成されませんでした")
        if fr[0]["kind"] != "hook":
            fr[0]["kind"] = "hook"
        if fr[-1]["kind"] != "closing":
            fr.append({"kind": "closing", "text": "保存して\\nあとで見返してね"})
        data["frames"] = fr[:10]
        data["hook"], data["closing"] = fr[0]["text"], fr[-1]["text"]
        data["lines"] = [f["text"] for f in fr[1:-1]]
    data["kind"] = kind
    data["category"] = cat["key"]
    data["hashtags"] = build_hashtags(hashtags, cat["key"], data.get("extra_hashtags", []))
    data["full_caption"] = data["caption"].strip() + "\n.\n.\n.\n" + " ".join(data["hashtags"])
    return data


if __name__ == "__main__":
    import sys
    kind = sys.argv[1] if len(sys.argv) > 1 else "carousel"
    print(json.dumps(generate_post(kind), ensure_ascii=False, indent=2))
