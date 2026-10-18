# 初期設定手順書(1回だけ・約90分)

これを終えると、以後は毎日20:00にカルーセル、火木土12:00にリールが自動投稿され、毎週月曜にレポートがメールで届きます。
(STEP 3 は「Facebookページ経由」方式です。以前の「Instagramログイン方式」で詰まった場合もこちらで進めてください)
順番どおりに進めてください。「→」はクリックする場所です。

---

## STEP 0. 準備するもの
- スマホ(Instagramアプリ)
- PC のブラウザ
- 既存の Instagram アカウントのログイン情報
- Genspark Plus(素材作り用。`GENSPARK_PROMPTS.md` を使います)

---

## STEP 1. 既存の Instagram アカウントを作り変える(15分)

既存アカウント(ほぼ未使用・公開)を使います。新規作成より有利です(アカウント年齢があるため初期の制限を受けにくい)。
すべてスマホの Instagram アプリで行います。

1. **過去の投稿をアーカイブ**(削除ではないので後で戻せます)
   各投稿を開く → 右上 … → **アーカイブ**。投稿が数件なら1分で終わります。
2. **ユーザーネームを変更**
   プロフィール → **プロフィールを編集** → ユーザーネーム → 空いているものに変更。候補:
   `miles_hawaii_bu` / `mile_de_hawaii` / `hawaii_mile_note` / `hawaii_mile_bu`
   ※ 変更したユーザーネームは STEP 5 の `BRAND_HANDLE` に `@付き` で登録します。メモしておいてください。
3. **プロフィールを埋める**(同じ「プロフィールを編集」画面)
   - 名前: `マイルでハワイ部｜マイルでお得にハワイへ`
     (「名前」欄は検索対象なので「マイル」「ハワイ」の両方を入れるのがポイント)
   - 自己紹介(例。そのままコピーでOK):
     ```
     ✈️ マイルを貯めて、ハワイにお得に行く情報を毎日発信
     🌺 初心者向け｜特典航空券｜ポイ活｜ハワイ旅Tips
     📌 保存して旅の計画に使ってね
     ```
   - プロフィール画像: `GENSPARK_PROMPTS.md` の「①アイコン」で生成した画像に差し替え
   - 以前のリンク・ハイライト・固定投稿が残っていれば外す
4. **プロアカウントに切り替え**(必須。APIはプロアカウントでしか使えません)
   プロフィール → 右上 ≡ → **設定とアクティビティ** → **アカウントの種類とツール** → **プロアカウントに切り替える** → **クリエイター**(推奨) → カテゴリ「デジタルクリエイター」 → Facebookページとの連携を聞かれたら **スキップ** でOK
   - 切り替え後、同じ設定画面で **「公開アカウント」のまま**であることを確認(非公開だとAPIも成長も止まります)
5. 以前フォローしていたアカウントが多い場合は、そのままで構いません(フォロー数が極端に多いと「メディアっぽさ」が薄れますが、整理は任意です)。

> 新規作成ではないので「数日置く」待機は不要です。そのまま STEP 2 へ進んでください。

---

## STEP 2. Gemini API キーを取得(5分・無料)

1. https://aistudio.google.com/ にGoogleアカウントでログイン
2. 左メニュー → **Get API key** → **Create API key** → プロジェクトを選択(なければ新規作成)
3. 表示されたキー(`AIza...`)をコピーしてメモ帳に貼る → これが `GEMINI_API_KEY`
   ※ 無料枠(1日あたり数百リクエスト)で十分足ります。1日1〜2回しか呼びません。

---

## STEP 3. Facebookページ経由で Instagram のトークンを取得(25分)

> 方式について: Instagram には2種類の接続方法があります。「Instagramログイン方式」はテスター登録で詰まることがあるため、
> ここでは **Facebookページ経由(Facebookログイン方式)** を使います。あなた自身がアプリ管理者なのでテスター登録が不要で、
> 取得できるトークンは **無期限** です(自動更新の仕組みも不要)。

### 3-A. Facebookページを作る(3分)
1. PC で https://www.facebook.com/pages/create を開く(普段使っているFacebookアカウントでログイン)
2. ページ名: `マイルでハワイ部` / カテゴリ: `ブログ` や `旅行会社` など何でも可 → **ページを作成**
3. プロフィール写真などは飛ばしてOK(このページは裏方で、誰にも見せません)

### 3-B. Instagramアカウントをそのページに紐づける(3分)
1. 作ったページを開く → 左メニュー(または「…」)から **設定** → **リンク済みのアカウント**(*Linked accounts*)→ **Instagram** → **アカウントをリンク**
2. Instagram のログイン画面が出るので、作り変えたアカウント(`mile_de_hawaii`)でログイン → 許可
   - 「Instagramのメッセージをアクセス許可する」のような確認はどちらでもOK
   - ※ 見つからない場合はスマホの Instagram から: 設定とアクティビティ → **アカウントセンター** → **アカウント** → **アカウントを追加** → Facebook でログイン → 追加後、Instagram の **プロフィールを編集** → **ページ** → 作ったページを選択
3. ページ設定の「リンク済みのアカウント」に Instagram のユーザーネームが表示されれば完了

### 3-C. Meta アプリを用意する(5分)
すでに `miles-hawaii-bot` アプリがあればそれを使います(新しく作り直す必要はありません)。
1. https://developers.facebook.com/ → **マイアプリ** → `miles-hawaii-bot` を開く
2. ダッシュボード右上 **ユースケースを追加** → **「Facebookログインでビジネスを管理」**(*Manage your business with Facebook Login*)に近い名前のものを選ぶ → 追加
   - 名前が見つからない場合は、「Facebookログイン」を含むユースケースを選べばOK
3. 追加したユースケース → **カスタマイズ** → **アクセス許可と機能** で、次の権限が「追加済み/準備完了」になっているか確認。無ければ **追加** を押す
   - `pages_show_list`
   - `pages_read_engagement`
   - `instagram_basic`
   - `instagram_content_publish`
   - `instagram_manage_insights`
   - `business_management`(あれば)
   ※ 審査申請(アプリレビュー)は不要です。管理者である自分だけが使うので開発モードのまま動きます。

### 3-D. 無期限トークンと Instagram ID を取得(10分)
**グラフAPIエクスプローラ** という Meta の公式ツールを使います。
1. https://developers.facebook.com/tools/explorer/ を開く
2. 右上の **Metaアプリ** で `miles-hawaii-bot` を選択
3. 右側 **アクセス許可** の欄に、3-C の権限を1つずつ入力して追加(`pages_show_list`, `pages_read_engagement`, `instagram_basic`, `instagram_content_publish`, `instagram_manage_insights`, `business_management`)
4. **Generate Access Token**(アクセストークンを生成)→ Facebookのログイン/確認画面 → 「マイルでハワイ部」のページと Instagram アカウントにチェックが入っていることを確認 → **続行/許可**
5. 上部の「アクセストークン」欄に短いトークンが入ります。これを **無期限トークンに変換** します:
   - トークン欄の右の **ⓘ(情報)アイコン** → **アクセストークンツールで開く** → 下の **アクセストークンを延長**(*Extend Access Token*)→ 表示された延長済みトークンを **コピー**
   - グラフAPIエクスプローラに戻り、トークン欄の中身を消して、コピーした延長済みトークンを **貼り付け**
6. 上部の入力欄(`me?fields=id,name` と入っている所)を次に書き換えて **送信**:
   ```
   me/accounts?fields=name,access_token,instagram_business_account
   ```
7. 下に出る結果の中から、`"name": "マイルでハワイ部"` のブロックを見て、
   - `"access_token": "EAA..."` → この長い文字列をコピー → メモアプリに `IG_ACCESS_TOKEN = ` として保存(**これが無期限のページトークン**)
   - `"instagram_business_account": { "id": "1784..." }` → この数字をコピー → `IG_USER_ID = ` として保存
   - ※ `instagram_business_account` が出てこない場合は 3-B の紐づけができていません。3-B をやり直してください
8. 念のため確認: 入力欄を `(IG_USER_IDの数字)?fields=username,followers_count` にして送信し、トークン欄に **手順7のページトークン** を貼って送信 → `username` に自分のアカウント名が出れば成功

## STEP 4. GitHub にリポジトリを作り、ファイルを置く(15分)

1. https://github.com/ でアカウント作成(無料)
2. 右上 **+** → **New repository**
   - Repository name: `miles-hawaii-insta`
   - **Public** を選択(無料で GitHub Pages を使うために Public が必要。公開されるのは投稿画像とネタ帳だけで、鍵類は公開されません)
   - **Create repository**
3. このフォルダ(`miles-hawaii-insta`)の中身を丸ごとアップロード
   - リポジトリ画面 → **uploading an existing file** → フォルダの中身を全部ドラッグ&ドロップ → **Commit changes**
   - ※ `.github` フォルダ(隠しフォルダ)が漏れやすいので注意。Mac は Finder で `Cmd+Shift+.` で表示。漏れた場合はもう一度 `.github/workflows/` の2ファイルだけアップ。
   - ※ ブラウザからのアップロードは1ファイル25MBまで。Genspark の動画は25MB以下にしてください(STEP 6)。
4. **GitHub Pages を有効化**
   - リポジトリ → **Settings** → 左 **Pages** → *Build and deployment* → Source: **Deploy from a branch** → Branch: **main** / フォルダ: **/docs** → **Save**
   - 1〜2分後、同じ画面上部に `Your site is live at https://ユーザー名.github.io/miles-hawaii-insta/` と出る → この URL をメモ → `PAGES_BASE_URL`(末尾の `/` は不要)

---

## STEP 5. 鍵と設定値を登録(10分)

リポジトリ → **Settings** → 左 **Secrets and variables** → **Actions**

### Secrets タブ → New repository secret(2つ)
| Name | Value |
|---|---|
| `GEMINI_API_KEY` | STEP 2 のキー |
| `IG_ACCESS_TOKEN` | STEP 3-D-7 のページトークン(`EAA...`) |

※ Facebookページ経由のトークンは無期限なので、以前の手順にあった `GH_PAT` は不要です。

### Variables タブ → New repository variable(4つ)
| Name | Value |
|---|---|
| `IG_USER_ID` | STEP 3-D-7 の `instagram_business_account` の数字 |
| `PAGES_BASE_URL` | `https://ユーザー名.github.io/miles-hawaii-insta` |
| `BRAND_NAME` | `マイルでハワイ部`(変える場合はここ) |
| `BRAND_HANDLE` | `@` + Instagramのユーザーネーム |

### Actions の書き込み許可
Settings → **Actions** → **General** → 一番下 *Workflow permissions* → **Read and write permissions** にチェック → Save

---

## STEP 6. Genspark で素材を作って入れる(20分)

`GENSPARK_PROMPTS.md` の手順どおりに生成し、
- アイコン画像 → Instagram のプロフィール画像に設定
- 縦型背景動画(5〜10本、各25MB以下) → リポジトリの `assets/reel_bg/` に **Add file → Upload files**
- BGM(任意) → `assets/music/`

無くても動きます(グラデーション背景・無音になります)が、あった方が見栄えが大きく上がります。

---

## STEP 7. テスト実行(5分)

1. リポジトリ → **Actions** タブ → 左 **Auto Post** → 右の **Run workflow**
   - kind: `carousel` / dry_run: **✅(チェックのまま)** → Run workflow
2. 2〜4分で完了。実行をクリック → 一番下 **Artifacts** → `output-carousel-1` をダウンロード → 画像と `.json`(キャプション)を確認
3. 気になれば `data/facts.md` / `data/topics.yml` を編集(GitHub上で鉛筆アイコンから直接編集できます)
4. もう一度 Run workflow、今度は kind: `reel`、dry_run ✅ で動画も確認
5. 問題なければ **dry_run のチェックを外して** `carousel` を1回実行 → Instagram に投稿されれば完成 🎉

以後は自動です。**Actions タブの左「Weekly Report & Token Check」も1回 Run workflow** しておくと、初回レポートとトークン延長が動作確認できます。

---

## 運用中にすること(基本ゼロ)

- 毎週月曜、GitHub から「📊 週次レポート」というメール(Issue通知)が届きます。読むだけでOK。
- 投稿内容の方向性を変えたいとき: `data/topics.yml` の `ideas` を書き換える / `data/facts.md` を更新する。コードは触らなくて大丈夫です。
- 失敗したときは GitHub から「Run failed」メールが届きます。多いのは「Facebookのパスワード変更などでトークンが無効化された」ケース(STEP 3-D をやり直して `IG_ACCESS_TOKEN` を更新)。

## うまくいかないとき

| 症状 | 対処 |
|---|---|
| Actions が `Pages に公開されませんでした` で失敗 | STEP 4-4 の Pages 設定が main / docs になっているか確認。初回は反映に最大10分かかることがある |
| `Instagram API error 190` | トークン無効(パスワード変更・セキュリティ操作で失効)。STEP 3-D で再発行 |
| `IG_USER_ID が未設定` | Variables に `IG_USER_ID` を登録(STEP 5) |
| `Instagram API error 400 ... media type` | 画像/動画の仕様エラー。Artifacts の生成物を確認。リールは背景動画が壊れている可能性 → `assets/reel_bg` の該当ファイルを削除 |
| `GEMINI ... 429` | 無料枠の一時制限。自動リトライされる。頻発するなら `GEMINI_MODEL` 変数に `gemini-2.0-flash` を設定 |
| 投稿はされるがフォロワーが増えない | 2週間は様子見。レポートで保存数が多いカテゴリの weight を上げる(自動調整もされる)。それでも伸びなければ広告の検討を |
