"""共通設定。環境変数(GitHub Secrets / Variables)から読み込む。"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
TEMPLATES = ROOT / "templates"
ASSETS = ROOT / "assets"
DOCS = ROOT / "docs"            # GitHub Pages 公開ディレクトリ
MEDIA = DOCS / "media"          # 生成画像・動画の置き場
REPORTS = ROOT / "reports"
OUT = ROOT / "out"              # 一時出力

# --- Secrets ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
IG_ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN", "")
PAGES_BASE_URL = os.environ.get("PAGES_BASE_URL", "").rstrip("/")  # 例: https://user.github.io/miles-hawaii-insta

# --- Instagram API の接続方式 ---
#   facebook : Facebookログイン経由(Facebookページに紐づけたIGアカウント。ページトークンは無期限)← 推奨・既定
#   instagram: Instagramログイン経由(Instagramテスター登録が必要。トークン60日で要更新)
IG_API_MODE = os.environ.get("IG_API_MODE", "facebook").lower()
IG_USER_ID = os.environ.get("IG_USER_ID", "")  # facebook モードで必須(Instagram Business Account ID)
IG_API = "https://graph.facebook.com/v21.0" if IG_API_MODE == "facebook" else "https://graph.instagram.com/v21.0"

# --- 挙動 ---
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

# --- ブランド ---
BRAND_NAME = os.environ.get("BRAND_NAME", "マイルでハワイ部")
BRAND_HANDLE = os.environ.get("BRAND_HANDLE", "@miles_hawaii_bu")

# --- メディア保持日数(docs/media の肥大化防止) ---
MEDIA_KEEP_DAYS = 14

for d in (MEDIA, REPORTS, OUT):
    d.mkdir(parents=True, exist_ok=True)
