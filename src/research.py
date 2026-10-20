"""週次の自動リサーチ(公式サイト限定)。

1. research_targets.yml の各質問を Gemini(Google検索グラウンディング)で調べる
2. 出典ドメインが許可リスト外のものは捨てる
3. 構造化して data/facts_auto.md(事実)と data/news.md(ネタ候補)に書く
4. 前回との差分があれば GitHub Issue で通知。失敗した項目は前回の値を維持
"""
import json
import subprocess
import time
from datetime import date
from urllib.parse import urlparse
import yaml
from config import DATA, REPORTS
from gemini_client import generate_grounded, generate_json

TARGETS = DATA / "research_targets.yml"
STATE = DATA / "research_state.json"
FACTS_AUTO = DATA / "facts_auto.md"
NEWS = DATA / "news.md"
TOPICS = DATA / "topics.yml"

EXTRACT_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "as_of": {"type": "STRING", "description": "情報の時点(YYYY年M月 など)。不明なら空"},
        "confidence": {"type": "STRING", "enum": ["high", "medium", "low"]},
        "items": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
            "label": {"type": "STRING", "description": "項目名(例: ANA エコノミー ロー 往復)"},
            "value": {"type": "STRING", "description": "値(例: 35,000マイル / 40米ドル / 不明)"},
            "note": {"type": "STRING", "description": "条件・補足(30字以内)"},
        }, "required": ["label", "value"]}},
        "news": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
            "date": {"type": "STRING"}, "title": {"type": "STRING", "description": "30字以内"},
            "summary": {"type": "STRING", "description": "60字以内"}, "source": {"type": "STRING", "description": "ドメイン"},
        }, "required": ["title", "summary"]}},
    },
    "required": ["as_of", "confidence", "items", "news"],
}


def _domain(src: dict) -> str:
    t = (src.get("title") or "").lower().strip()
    if "." in t and " " not in t:
        return t
    host = urlparse(src.get("uri", "")).netloc.lower()
    return host


def _allowed(domain: str, allowed: list[str]) -> bool:
    return any(domain == a or domain.endswith("." + a) for a in allowed)


def research_one(target: dict, allowed: list[str]) -> dict | None:
    q = target["question"].strip() + "\n\n必ず出典URLを本文中に示し、公式サイト以外の情報(ブログ・まとめサイト・SNS)は使わないでください。見つからない項目は「不明」と明記してください。"
    text, sources = generate_grounded(q)
    doms = sorted({_domain(s) for s in sources if _domain(s)})
    ok_doms = [d for d in doms if _allowed(d, allowed)]
    print(f"[research] {target['key']}: sources={doms} allowed={ok_doms}")
    if not ok_doms:
        print(f"[research] {target['key']}: 許可ドメインの出典なし → スキップ")
        return None

    system = ("あなたは事実抽出器です。与えられた調査結果テキストから、数値・制度・ニュースを構造化して抜き出します。"
              "テキストに無い数値を補ってはいけません。あいまいな値は『不明』にし、confidence を下げてください。"
              f"出典として信頼できるドメインは {', '.join(ok_doms)} のみです。それ以外のドメインに由来すると思われる情報は除外してください。")
    user = f"<title>{target['title']}</title>\n<type>{target['type']}</type>\n<research_text>\n{text}\n</research_text>"
    data = generate_json(system, user, EXTRACT_SCHEMA, temperature=0.1)
    data["sources"] = ok_doms
    data["fetched"] = date.today().isoformat()
    return data


def write_outputs(state: dict, targets: list[dict]):
    today = date.today().isoformat()
    facts_lines = [f"> 自動リサーチ(公式サイト限定)。各項目に取得日と出典ドメインを併記。confidence が low の項目は『目安』として扱うこと。最終更新 {today}", ""]
    news_lines = [f"# 最新ニュース候補(自動収集・最終更新 {today})", ""]
    news_ideas = []
    for t in targets:
        d = state.get(t["key"])
        if not d:
            continue
        if t["type"] == "facts" and d.get("items"):
            facts_lines.append(f"## {t['title']}(取得日 {d['fetched']} / 時点 {d.get('as_of') or '不明'} / 出典 {', '.join(d['sources'])} / 信頼度 {d.get('confidence')})")
            for it in d["items"]:
                note = f"({it['note']})" if it.get("note") else ""
                facts_lines.append(f"- {it['label']}: {it['value']} {note}".rstrip())
            facts_lines.append("")
        if t["type"] == "news" and d.get("news"):
            news_lines.append(f"## {t['title']}(取得日 {d['fetched']})")
            for n in d["news"][:5]:
                news_lines.append(f"- {n.get('date','')} {n['title']} — {n['summary']} [{n.get('source','')}]")
                news_ideas.append(f"[NEWS {n.get('date','')}] {n['title']}: {n['summary']}")
            news_lines.append("")
    FACTS_AUTO.write_text("\n".join(facts_lines), encoding="utf-8")
    NEWS.write_text("\n".join(news_lines), encoding="utf-8")

    # ネタ帳の「最新情報」カテゴリを差し替え(古いNEWSは消す)
    topics = yaml.safe_load(TOPICS.read_text(encoding="utf-8"))
    cats = topics["categories"]
    news_cat = next((c for c in cats if c["key"] == "news"), None)
    if news_ideas:
        if not news_cat:
            news_cat = {"key": "news", "name": "最新情報・キャンペーン", "weight": 1.4, "ideas": []}
            cats.insert(0, news_cat)
        news_cat["ideas"] = news_ideas[:10]
    elif news_cat:
        cats.remove(news_cat)
    TOPICS.write_text(yaml.safe_dump(topics, allow_unicode=True, sort_keys=False), encoding="utf-8")


def diff_summary(old: dict, new: dict, targets: list[dict]) -> list[str]:
    lines = []
    for t in targets:
        if t["type"] != "facts":
            continue
        o = {i["label"]: i["value"] for i in (old.get(t["key"]) or {}).get("items", [])}
        n = {i["label"]: i["value"] for i in (new.get(t["key"]) or {}).get("items", [])}
        for k, v in n.items():
            if k in o and o[k] != v:
                lines.append(f"- 🔄 {t['title']} / {k}: {o[k]} → **{v}**")
            elif k not in o:
                lines.append(f"- 🆕 {t['title']} / {k}: {v}")
    return lines


def main():
    cfg = yaml.safe_load(TARGETS.read_text(encoding="utf-8"))
    allowed = [d.lower() for d in cfg["allowed_domains"]]
    targets = cfg["targets"]
    old = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    new = dict(old)
    failed = []
    for t in targets:
        try:
            r = research_one(t, allowed)
            if r:
                new[t["key"]] = r
            else:
                failed.append(t["title"])
        except Exception as e:
            print(f"[research] {t['key']} failed: {e}")
            failed.append(t["title"])
        time.sleep(8)  # 無料枠のレート対策

    STATE.write_text(json.dumps(new, ensure_ascii=False, indent=2), encoding="utf-8")
    write_outputs(new, targets)

    changes = diff_summary(old, new, targets)
    body = [f"# 自動リサーチ {date.today().isoformat()}", ""]
    body += ["## 変更があった項目", ""] + (changes or ["(変更なし)"]) + [""]
    if failed:
        body += ["## 取得できなかった項目(前回の値を維持)", ""] + [f"- {f}" for f in failed] + [""]
    body += ["詳細: `data/facts_auto.md` / `data/news.md`"]
    text = "\n".join(body)
    print(text)
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / f"research-{date.today().isoformat()}.md").write_text(text, encoding="utf-8")

    subprocess.run(["git", "config", "user.name", "insta-bot"], check=True)
    subprocess.run(["git", "config", "user.email", "insta-bot@users.noreply.github.com"], check=True)
    subprocess.run(["git", "add", "data/", "reports/"], check=True)
    subprocess.run(["git", "commit", "-m", f"research: {date.today().isoformat()}"], check=False)
    subprocess.run(["git", "pull", "--rebase", "--autostash", "origin", "HEAD"], check=True)
    subprocess.run(["git", "push", "origin", "HEAD"], check=True)
    if changes or failed:
        subprocess.run(["gh", "issue", "create", "--title", f"🔎 自動リサーチ {date.today().isoformat()}: 変更{len(changes)}件 / 失敗{len(failed)}件",
                        "--body", text], check=False)


if __name__ == "__main__":
    main()
