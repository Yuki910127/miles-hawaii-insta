"""週次レポート: フォロワー推移・投稿別成績を集計し、カテゴリ重みを自動調整。
GitHub Issue として作成 → メール通知で届く(手作業なし)。
"""
import json
import subprocess
from datetime import date, datetime
import yaml
from config import DATA, REPORTS
from generate import load_posted
from publish import me, media_insights

GOAL = 500
DEADLINE = date(2026, 12, 20)
STATS = DATA / "stats.json"


def main():
    acct = me()
    followers = acct.get("followers_count", 0)
    today = date.today()

    # フォロワー履歴
    hist = json.loads(STATS.read_text(encoding="utf-8")) if STATS.exists() else []
    hist.append({"date": today.isoformat(), "followers": followers})
    STATS.write_text(json.dumps(hist, ensure_ascii=False, indent=2), encoding="utf-8")
    prev = hist[-2]["followers"] if len(hist) >= 2 else followers
    delta = followers - prev
    days_left = (DEADLINE - today).days
    need_per_day = max(GOAL - followers, 0) / max(days_left, 1)

    # 直近14日の投稿の成績
    posted = [p for p in load_posted() if p.get("media_id") and p["media_id"] != "dry-run"]
    recent = posted[-14:]
    rows, cat_scores = [], {}
    for p in recent:
        ins = media_insights(p["media_id"])
        reach = ins.get("reach") or 0
        saved = ins.get("saved") or 0
        score = reach + saved * 20  # 保存を重視
        rows.append((p["date"], p["kind"], p["category"], p["topic"], reach, saved, ins.get("likes") or 0))
        cat_scores.setdefault(p["category"], []).append(score)

    # カテゴリ重みの自動調整(平均スコアに応じて 0.5〜2.0 の範囲で緩やかに)
    topics = yaml.safe_load((DATA / "topics.yml").read_text(encoding="utf-8"))
    if cat_scores:
        avg_all = sum(sum(v) for v in cat_scores.values()) / sum(len(v) for v in cat_scores.values()) or 1
        for c in topics["categories"]:
            if c["key"] in cat_scores:
                ratio = (sum(cat_scores[c["key"]]) / len(cat_scores[c["key"]])) / avg_all
                new_w = c.get("weight", 1.0) * (0.7 + 0.3 * ratio)
                c["weight"] = round(min(2.0, max(0.5, new_w)), 2)
        (DATA / "topics.yml").write_text(yaml.safe_dump(topics, allow_unicode=True, sort_keys=False), encoding="utf-8")

    # レポート本文
    rows.sort(key=lambda r: (r[5], r[4]), reverse=True)
    lines = [
        f"# 週次レポート {today.isoformat()}",
        "",
        f"- フォロワー: **{followers}** (前回比 {delta:+d})",
        f"- 目標 {GOAL} まで残り **{max(GOAL-followers,0)}** / 残り {days_left} 日 → 必要ペース {need_per_day:.1f} 人/日",
        f"- 直近投稿数: {len(recent)}",
        "",
        "## 直近投稿 TOP(保存数順)",
        "",
        "| 日付 | 種別 | カテゴリ | テーマ | リーチ | 保存 | いいね |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows[:10]:
        lines.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} | {r[6]} |")
    lines += ["", "## カテゴリ重み(自動調整後)", ""]
    for c in topics["categories"]:
        lines.append(f"- {c['name']}: {c.get('weight', 1.0)}")
    if need_per_day > 10:
        lines += ["", "> ⚠️ 必要ペースが高めです。残り予算を広告(プロフィール訪問目的)に回す検討をおすすめします。"]

    body = "\n".join(lines)
    REPORTS.mkdir(exist_ok=True)
    path = REPORTS / f"{today.isoformat()}.md"
    path.write_text(body, encoding="utf-8")
    print(body)

    # commit & issue
    subprocess.run(["git", "config", "user.name", "insta-bot"], check=True)
    subprocess.run(["git", "config", "user.email", "insta-bot@users.noreply.github.com"], check=True)
    subprocess.run(["git", "add", "data/stats.json", "data/topics.yml", str(path)], check=True)
    subprocess.run(["git", "commit", "-m", f"report: {today.isoformat()}"], check=False)
    subprocess.run(["git", "pull", "--rebase", "--autostash", "origin", "HEAD"], check=True)
    subprocess.run(["git", "push", "origin", "HEAD"], check=True)
    subprocess.run(["gh", "issue", "create", "--title", f"📊 週次レポート {today.isoformat()} / フォロワー {followers}",
                    "--body", body], check=False)


if __name__ == "__main__":
    main()
