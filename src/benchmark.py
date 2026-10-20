"""ベンチマーク分析(週次)。

Instagram 公式 API の Business Discovery で対象アカウントの公開投稿を取得し、
エンゲージメント上位の「テーマ・切り口・形式・フック」を Gemini で分析して
  - data/trends.md       … 分析レポート(人が読む用)
  - data/style_hints.md  … 生成時に参照する作り方のヒント(文言は流用しない)
  - data/topics.yml      … 「トレンド」カテゴリにネタ候補を差し替え
を更新する。文章・画像の流用は一切しない(構成とテーマだけを学ぶ)。
"""
import base64
import json
import statistics
import subprocess
from datetime import date
import requests
import yaml
from config import DATA, REPORTS, IG_API, IG_API_MODE, IG_USER_ID, IG_ACCESS_TOKEN
from gemini_client import generate_json, candidate_models, BASE, GEMINI_API_KEY

CFG = DATA / "benchmark_accounts.yml"
TRENDS = DATA / "trends.md"
HINTS = DATA / "style_hints.md"
TOPICS = DATA / "topics.yml"

ANALYSIS_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "summary": {"type": "STRING", "description": "伸びている投稿の共通点を200字以内で"},
        "winning_formats": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "伸びている形式(例: ランキング型 / 比較表 / 失敗談 / Q&A)。最大5"},
        "hook_patterns": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "表紙やフックの作り方のパターン(抽象化して。元の文言は書かない)。最大6"},
        "topic_ideas": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
            "idea": {"type": "STRING", "description": "自分のアカウント(マイル×ハワイ)向けに言い換えたネタ。30字以内"},
            "angle": {"type": "STRING", "description": "元投稿と違う切り口にする指示。30字以内"},
            "why": {"type": "STRING", "description": "なぜ伸びると考えるか。30字以内"},
        }, "required": ["idea", "angle"]}, "description": "最大10"},
        "style_hints": {"type": "ARRAY", "items": {"type": "STRING"},
                         "description": "自分の投稿生成に使える作り方のルール(例: 表紙に具体的な数字を1つ入れる / 2枚目で結論を先に言う)。文言のコピーではなく方法論。最大8"},
        "design_notes": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "画像から読み取れるデザイン上の特徴(文字量・配色・レイアウト・キャラの使い方など)。最大8。画像が無ければ空"},
    },
    "required": ["summary", "winning_formats", "hook_patterns", "topic_ideas", "style_hints", "design_notes"],
}


def fetch_account(username: str, limit: int) -> dict | None:
    if IG_API_MODE != "facebook":
        print("[bench] Business Discovery は facebook モードでのみ利用可")
        return None
    fields = (f"business_discovery.username({username})"
              "{username,followers_count,media_count,"
              f"media.limit({limit}){{id,caption,like_count,comments_count,media_type,media_product_type,permalink,timestamp,media_url,thumbnail_url}}}}")
    r = requests.get(f"{IG_API}/{IG_USER_ID}", params={"fields": fields, "access_token": IG_ACCESS_TOKEN}, timeout=60)
    if r.status_code >= 400:
        print(f"[bench] {username}: API error {r.status_code}: {r.text[:200]}")
        return None
    return r.json().get("business_discovery")


def rank_media(acct: dict, top_n: int) -> list[dict]:
    media = acct.get("media", {}).get("data", [])
    for m in media:
        m["score"] = (m.get("like_count") or 0) + 3 * (m.get("comments_count") or 0)
    if not media:
        return []
    med = statistics.median([m["score"] for m in media]) or 1
    for m in media:
        m["rel"] = round(m["score"] / med, 2)  # そのアカウント内での相対的な伸び
    return sorted(media, key=lambda m: m["score"], reverse=True)[:top_n]


def _fetch_image_b64(url: str) -> str | None:
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200 and len(r.content) < 4_000_000:
            return base64.b64encode(r.content).decode()
    except requests.RequestException:
        pass
    return None


def analyze_with_images(prompt_text: str, images_b64: list[str]) -> dict:
    """表紙画像(最大6枚)も渡して分析。画像付きは JSON モードで直接呼ぶ。"""
    parts = [{"text": prompt_text}]
    for b in images_b64[:6]:
        parts.append({"inline_data": {"mime_type": "image/jpeg", "data": b}})
    body = {
        "system_instruction": {"parts": [{"text":
            "あなたはSNSコンテンツ戦略のアナリストです。他アカウントの投稿データから『何が伸びているか』を抽象化して学びます。"
            "元投稿の文言・固有の表現・デザインをそのまま写す提案は禁止。方法論・切り口・構成パターンに言い換えること。"
            "自分のアカウントは『マイルを貯めてハワイに行く』がテーマの日本語メディアで、マスコットはウミガメのパイロット、配色はティール×コーラル×サンド。"}]},
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {"temperature": 0.4, "response_mime_type": "application/json", "response_schema": ANALYSIS_SCHEMA},
    }
    last = None
    for model in candidate_models()[:4]:
        r = requests.post(f"{BASE}/models/{model}:generateContent", params={"key": GEMINI_API_KEY}, json=body, timeout=180)
        if r.status_code == 404:
            continue
        if r.status_code >= 400:
            last = r.text[:300]
            print(f"[bench] {model}: {r.status_code} {last}")
            # 画像で失敗したらテキストのみで再試行
            body["contents"][0]["parts"] = parts[:1]
            continue
        return json.loads(r.json()["candidates"][0]["content"]["parts"][0]["text"])
    raise RuntimeError(f"分析に失敗: {last}")


def main():
    cfg = yaml.safe_load(CFG.read_text(encoding="utf-8"))
    accounts = cfg["accounts"]
    limit = int(cfg.get("media_limit", 40))
    top_n = int(cfg.get("top_n", 12))

    today = date.today().isoformat()
    report = [f"# ベンチマーク分析 {today}", ""]
    all_top = []
    for a in accounts:
        acct = fetch_account(a["username"], limit)
        if not acct:
            report.append(f"## @{a['username']}: 取得できませんでした(プロアカウントでない/非公開/一時的エラー)\n")
            continue
        top = rank_media(acct, top_n)
        report.append(f"## @{acct['username']}(フォロワー {acct.get('followers_count'):,} / 投稿 {acct.get('media_count')})")
        report.append("")
        report.append("| 相対スコア | いいね | コメント | 種別 | 日付 | 冒頭 |")
        report.append("|---|---|---|---|---|---|")
        for m in top[:8]:
            cap = (m.get("caption") or "").replace("\n", " ")[:40]
            report.append(f"| x{m['rel']} | {m.get('like_count',0)} | {m.get('comments_count',0)} | {m.get('media_product_type','')} | {m.get('timestamp','')[:10]} | {cap}… |")
        report.append("")
        for m in top:
            m["_account"] = acct["username"]
        all_top += top

    if not all_top:
        TRENDS.write_text("\n".join(report), encoding="utf-8")
        print("\n".join(report))
        return

    # Gemini に渡す要約(キャプションは分析用に最大300字。生成側には渡さない)
    lines = []
    for m in sorted(all_top, key=lambda m: m["rel"], reverse=True):
        cap = (m.get("caption") or "").replace("\n", " ")[:300]
        lines.append(f"- [@{m['_account']}] 相対スコア x{m['rel']} / {m.get('media_product_type','')} / {m.get('timestamp','')[:10]}\n  caption: {cap}")
    prompt = ("以下は参考アカウントの『伸びた投稿』一覧(相対スコア=そのアカウント内の中央値比)と、上位投稿の表紙画像です。\n"
              "伸びている理由を『形式・切り口・フックの作り方・デザインの特徴』として抽象化し、"
              "自分のアカウント(マイル×ハワイ)向けのネタ案と、作り方のヒントをJSONで出してください。\n\n" + "\n".join(lines))
    imgs = []
    for m in sorted(all_top, key=lambda m: m["rel"], reverse=True)[:6]:
        url = m.get("thumbnail_url") or m.get("media_url")
        if url:
            b = _fetch_image_b64(url)
            if b:
                imgs.append(b)
    try:
        res = analyze_with_images(prompt, imgs)
    except Exception as e:
        print(f"[bench] 分析失敗: {e}")
        TRENDS.write_text("\n".join(report), encoding="utf-8")
        return

    report += ["## 伸びている投稿の共通点", "", res["summary"], "",
               "## 伸びている形式", ""] + [f"- {x}" for x in res["winning_formats"]] + ["",
               "## フックの作り方(抽象化)", ""] + [f"- {x}" for x in res["hook_patterns"]] + ["",
               "## デザインの特徴(画像から)", ""] + ([f"- {x}" for x in res["design_notes"]] or ["(画像なし)"]) + ["",
               "## 自分向けネタ案", ""] + [f"- {t['idea']} … 切り口: {t['angle']}" + (f"(理由: {t.get('why','')})" if t.get('why') else "") for t in res["topic_ideas"]]
    TRENDS.write_text("\n".join(report), encoding="utf-8")

    HINTS.write_text(f"# 作り方のヒント(ベンチマーク分析から・{today})\n※ 方法論のみ。他アカウントの文言・デザインは写さない。\n\n" +
                     "\n".join(f"- {h}" for h in res["style_hints"]), encoding="utf-8")

    topics = yaml.safe_load(TOPICS.read_text(encoding="utf-8"))
    cats = topics["categories"]
    cat = next((c for c in cats if c["key"] == "trend"), None)
    ideas = [f"【トレンド】{t['idea']}(切り口: {t['angle']}。文言は写さず自分のfactsの数字で)" for t in res["topic_ideas"]][:10]
    if ideas:
        if not cat:
            cat = {"key": "trend", "name": "トレンド(ベンチマーク由来)", "weight": 1.4, "ideas": []}
            cats.insert(0, cat)
        cat["ideas"] = ideas
    TOPICS.write_text(yaml.safe_dump(topics, allow_unicode=True, sort_keys=False), encoding="utf-8")

    print("\n".join(report))
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / f"benchmark-{today}.md").write_text("\n".join(report), encoding="utf-8")
    subprocess.run(["git", "config", "user.name", "insta-bot"], check=True)
    subprocess.run(["git", "config", "user.email", "insta-bot@users.noreply.github.com"], check=True)
    subprocess.run(["git", "add", "data/", "reports/"], check=True)
    subprocess.run(["git", "commit", "-m", f"benchmark: {today}"], check=False)
    subprocess.run(["git", "pull", "--rebase", "--autostash", "origin", "HEAD"], check=True)
    subprocess.run(["git", "push", "origin", "HEAD"], check=True)


if __name__ == "__main__":
    main()
