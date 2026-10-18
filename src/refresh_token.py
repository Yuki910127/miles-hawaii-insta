"""トークンの健全性チェック / 更新。

facebook モード : ページトークンは無期限なので更新不要。有効かどうかだけ確認する。
instagram モード: 60日期限の長期トークンを更新し、GitHub Secret を書き換える(GH_PAT が必要)。
"""
import os
import subprocess
import requests
from config import IG_API_MODE, IG_ACCESS_TOKEN
from publish import me

if IG_API_MODE == "facebook":
    acct = me()
    print(f"[token] OK: @{acct.get('username')} followers={acct.get('followers_count')} (ページトークン・無期限)")
    raise SystemExit(0)

r = requests.get(
    "https://graph.instagram.com/refresh_access_token",
    params={"grant_type": "ig_refresh_token", "access_token": IG_ACCESS_TOKEN},
    timeout=60,
)
if r.status_code >= 400:
    raise SystemExit(f"トークン更新失敗: {r.text}")
new_token = r.json()["access_token"]
expires_days = r.json().get("expires_in", 0) // 86400
print(f"[token] 更新成功。有効期限 約{expires_days}日")

if not os.environ.get("GH_PAT"):
    raise SystemExit("GH_PAT が未設定のため Secret を更新できません")
env = {**os.environ, "GH_TOKEN": os.environ["GH_PAT"]}
subprocess.run(["gh", "secret", "set", "IG_ACCESS_TOKEN", "--body", new_token,
                "--repo", os.environ["GITHUB_REPOSITORY"]], check=True, env=env)
print("[token] GitHub Secret を更新しました")
