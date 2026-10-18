# マイルでハワイ部 — Instagram 全自動運用システム

「マイルを貯めてハワイにお得に行く」をテーマにした匿名メディア型アカウントを、
GitHub Actions 上で **生成 → 画像/動画化 → 投稿 → 分析 → 自動調整** まで無人運用します。

```
GitHub Actions(毎日 20:00 JST / 火木土 12:00 JST)
 ├─ Gemini API(無料枠)      … ネタ帳+事実集から本文・キャプション・タグを生成
 ├─ Playwright + HTMLテンプレ … 1080x1350 カルーセル画像 / リール用テキスト画像
 ├─ ffmpeg                   … 背景動画+テキストで 1080x1920 リール合成
 ├─ GitHub Pages             … 画像/動画を公開URL化(Instagram API の要件)
 └─ Instagram Graph API      … カルーセル / リール投稿
毎週月曜
 ├─ トークン有効性チェック(Facebookページ経由のトークンは無期限)
 └─ 週次レポート(フォロワー推移・保存数TOP・カテゴリ重み自動調整)→ Issue でメール通知
```

## まず読むもの
1. `SETUP.md` — 初期設定手順(1回・約90分)
2. `GENSPARK_PROMPTS.md` — 素材生成用プロンプト

## 構成
| パス | 役割 |
|---|---|
| `data/topics.yml` | ネタ帳。カテゴリ×アイデア。weight は自動調整 |
| `data/facts.md` | 数値・制度の根拠。**ここにない数字は書かない**ルールで幻覚を抑制 |
| `data/hashtags.yml` | ハッシュタグ設計(常設+ビッグ+カテゴリ+固有=最大25) |
| `data/posted.json` | 投稿済み台帳(重複防止・分析用) |
| `templates/` | カルーセル/リールのデザイン(HTML+CSS) |
| `assets/reel_bg/`, `assets/music/` | リール背景動画・BGM(任意) |
| `src/` | 実行コード |
| `.github/workflows/post.yml` | 自動投稿 |
| `.github/workflows/weekly.yml` | レポート+トークン延長 |
| `docs/media/` | Pages 公開用メディア(14日で自動削除) |

## 月額コスト
- GitHub Actions / Pages: 無料(Public リポジトリ)
- Gemini API: 無料枠内(1日1〜2回)
- Instagram API: 無料
- → **実質0円**

## やらないこと(規約・凍結リスク)
- 自動フォロー / 自動いいね / 自動コメント / 自動DM はしません(Instagram 規約違反で凍結対象)
- 自動化しているのは「自分のアカウントへの投稿」と「自分の投稿の分析」のみ。公式 API の正規利用です。
