# Genspark 用プロンプト集(最初の1回だけ)

Genspark Plus の **画像生成** / **動画生成** に、以下をそのまま貼ってください。
ブランド配色: 海のティール `#0E7C86`、夕焼けコーラル `#F28C28`、砂浜 `#FFF7EA`

---

## ① プロフィールアイコン(画像生成・正方形)

```
Flat minimal logo icon for an Instagram account about earning airline miles to travel to Hawaii.
A single stylized plumeria flower combined with a small paper-plane silhouette, centered.
Color palette: teal #0E7C86 background, coral #F28C28 and warm sand #FFF7EA for the flower and plane.
Clean vector style, no text, no letters, no gradients, soft rounded shapes, lots of negative space,
looks crisp at small size. Square 1:1, 1024x1024.
```
→ 気に入ったものを Instagram のプロフィール画像に設定。

---

## ② リール用 背景動画(動画生成・縦 9:16・各5〜8秒)

**ポイント**: 文字が上に乗るので「主張しすぎない・人物の顔なし・文字なし・ゆっくりした動き」が条件です。
以下を1本ずつ生成し、5〜10本作ってください。ファイル名は `bg01.mp4` `bg02.mp4`… とし、`assets/reel_bg/` にアップロード。
**25MB以下**にしてください(大きい場合は Genspark で解像度を 1080x1920 または 720x1280 に下げる)。

共通の末尾(全プロンプトに付ける):
```
Vertical 9:16 video, 1080x1920, 6 seconds, slow smooth camera motion, cinematic soft light,
no people, no faces, no text, no logos, no watermark, calm and dreamy mood, slightly muted colors
so that white and dark text overlays remain readable. Seamless loop if possible.
```

バリエーション(先頭に付ける):
1. `Gentle turquoise waves rolling onto a white sand beach in Hawaii, seen from above, slow drone glide.`
2. `Palm tree fronds swaying softly against a warm sunset sky over the Pacific, low angle, golden hour.`
3. `Aerial view of Diamond Head crater and Waikiki coastline at dawn, slow forward drift, soft haze.`
4. `Close-up of plumeria flowers on a branch with soft ocean bokeh behind, light breeze.`
5. `View from an airplane window above fluffy clouds, wing visible, golden sunlight, slow drift.`
6. `Calm lagoon with a single outrigger canoe far away, pastel pink and teal morning sky, slow pan.`
7. `Underwater shot of sun rays filtering through clear turquoise water over a sandy bottom, slow motion.`
8. `Hawaiian green mountain ridges with mist moving slowly, lush valley, soft light.`
9. `Sunset over the ocean with a wide empty beach, long shadows, slow pull back.`
10. `Looping animation of a stylized paper plane flying over a minimal map with dotted route to Hawaii, flat vector style, teal and coral palette.`

---

### 25MBを超える動画は「Releases」に置く(画質を落とさない方法・推奨)

GitHubのブラウザアップロードは1ファイル25MBまでですが、**Releases** なら1ファイル2GBまで置けます。
システムは投稿のたびに Releases の `reel-bg` から動画を取得するので、**1080pや4Kのまま**アップロードできます(720pに落とす必要なし)。

1. リポジトリのトップ右側「**Releases**」→「**Create a new release**」(初回)
2. 「Choose a tag」→ `reel-bg` と入力 → 「Create new tag: reel-bg」をクリック
3. Release title: `reel-bg`(何でも可)
4. 下の「Attach binaries by dropping them here」に動画をまとめてドラッグ(アップロード完了まで待つ)
5. 緑の「**Publish release**」
6. 追加・差し替えは、Releases → `reel-bg` の右の鉛筆(Edit)→ ドラッグ → 「Update release」

`assets/reel_bg/` に入っている動画と Releases の動画は**両方**使われます(ランダム選択)。
720p以下の素材は自動で軽くシャープがかかりますが、1080p以上を推奨します。横動画は上下にぼかし背景を敷いて配置されます。

## ③ BGM(任意)

Genspark に音楽生成がある場合:
```
Instrumental background music for a short travel video about Hawaii. Gentle ukulele and soft acoustic guitar,
light percussion, warm and optimistic, relaxed tempo around 95 BPM, no vocals, loopable, 30 seconds.
```
無い場合は、商用利用可・クレジット表記不要の素材(例: YouTube オーディオライブラリ、Pixabay Music、DOVA-SYNDROME)から
ウクレレ系の30秒前後の曲を2〜3曲ダウンロードして `assets/music/` へ。
※ Instagram のアプリ内音源(人気曲)はAPI投稿では使えません。必ずロイヤリティフリー音源を。

---

## ⑤ マスコット「ホヌのパイロット」(画像生成・3ポーズ)

表紙・最終スライド・リールに毎回登場させるキャラクターです。**3枚とも同じキャラに見えること**が最重要なので、
1枚目で気に入ったものができたら、2・3枚目はそのチャットの続きで「同じキャラクターで、ポーズだけ変えて」と頼んでください
(Gensparkに「参照画像」機能があれば1枚目を添付)。

共通のキャラ設定(毎回プロンプトの先頭に付ける):
```
A cute cartoon mascot: a friendly Hawaiian green sea turtle (honu) wearing a navy airline pilot cap with a gold emblem
and a small plumeria flower tucked behind the cap. Big round sparkling eyes, soft rounded shapes, thick clean outlines,
flat vector illustration with subtle cel shading, warm friendly expression. Colors: teal-green shell, sand-colored belly,
navy cap, coral #F28C28 accents. Full body visible, centered, isolated on a plain white background, no text, no logo, no shadow on ground.
```

ポーズ(末尾に付ける。ファイル名も指定どおりに):
1. `Pose: happy, smiling with one flipper raised in a cheerful wave.` → 保存名 **`honu_happy.png`**
2. `Pose: surprised, both flippers on cheeks, mouth open in a cute "oh!" expression, small sparkle marks around the head.` → **`honu_surprised.png`**
3. `Pose: pointing to the left with one flipper, confident grin, as if presenting information.` → **`honu_point.png`**
4. (任意)`Pose: thinking, one flipper on chin, eyes looking up, small question mark above head.` → **`honu_think.png`**
5. (任意)`Pose: excited, both flippers up, eyes sparkling, small coins or stars floating around.` → **`honu_excited.png`**

キャラの雰囲気の指定(日本語で付け足してもOK): 「柴犬キャラのような親しみやすい2〜3頭身、目が大きい、線は太め、
Instagramの小さなサムネイルでも表情が分かる」

**背景を透明にする**(重要):
- Gensparkに「背景を透過(transparent background / remove background)」オプションがあれば使う
- 無ければ、生成したPNGを https://www.remove.bg/ja にドラッグ → 無料でダウンロード(1枚ずつ・低解像度版でOK)
- 透過していないと白い四角のまま表示されます

できた3枚を GitHub の `assets/mascot/` にアップロード:
https://github.com/Yuki910127/miles-hawaii-insta/upload/main/assets/mascot
ファイル名に `happy` / `surprised` / `point` が含まれていれば、投稿の種類に応じて自動で使い分けられます。

---

## ⑥ 表紙の背景写真(任意・実写推奨)

インフォグラフィック型の表紙は、背景にハワイの写真をぼかして敷きます。**ご自身で撮ったハワイの写真**が最適です
(海・空・ヤシ・街並み。人の顔が大きく写っていないもの)。5〜10枚を `assets/bg_photos/` にアップロード:
https://github.com/Yuki910127/miles-hawaii-insta/upload/main/assets/bg_photos
- 横でも縦でも可(中央でトリミングされます)。1枚あたり 25MB 以下・できれば 2MB 程度に縮小(iPhoneなら共有 → 「サイズ: 中」で送ると縮小されます)
- 無い場合は Genspark の画像生成で: `Photorealistic wide shot of Waikiki beach with turquoise water and palm trees, soft morning light, no people, no text, 4:5 vertical` などを数枚

---

## ④ ハイライト用アイコン(任意・5枚)

```
Set of 5 minimal line icons in one consistent style for Instagram story highlight covers,
each centered on a solid sand-colored background #FFF7EA, coral #F28C28 line color, 1:1 square:
1) airplane ticket  2) credit card  3) plumeria flower  4) hotel building with palm  5) checklist.
```

---

## ⑦ 挿絵ライブラリ(画像生成・37枚・最初の1回だけ)

カルーセルの中面で「内容に合う挿絵」として使います。参考アカウントの「日本地図と飛行ルート」「東京タワーと富士山」のような絵をあらかじめ用意しておき、Geminiが毎回その中から選びます。
**全部同じ画風にすること**が最重要なので、1つのチャットで続けて生成するか、毎回「共通の画風」を先頭に付けてください。

共通の画風(毎回先頭に付ける):
```
Flat vector illustration, clean thick outlines, soft cel shading, friendly and bright. Color palette: teal #0E7C86, deep teal #0A5C64, coral #F28C28, sand #FFF7EA, light sky blue. Plain pure white background (#FFFFFF), no text, no letters, no logos, no people, no shadow on the ground, subject centered with margin, 4:3 landscape, 1024x768.
```

モチーフ(1枚ずつ末尾に付ける。**保存ファイル名**はそのまま使ってください):

| 保存ファイル名 | モチーフ(英語プロンプト) | 内容 |
|---|---|---|
| `plane_takeoff.png` | `a passenger airplane taking off into a blue sky with soft clouds` | 離陸する旅客機(青空・雲) |
| `plane_window.png` | `view from an airplane window showing the wing above a sea of clouds` | 飛行機の窓から見える翼と雲海 |
| `airport_terminal.png` | `an airport terminal with a boarding gate and large windows` | 空港ターミナルと搭乗ゲート |
| `boarding_pass.png` | `a boarding pass labeled TOKYO to HONOLULU next to a passport` | 搭乗券(TOKYO→HONOLULU)とパスポート |
| `business_seat.png` | `a business class lie-flat seat` | ビジネスクラスのフルフラット座席 |
| `lounge.png` | `an airport lounge sofa with a drink and a small table` | 空港ラウンジのソファとドリンク |
| `japan_map_route.png` | `a simplified map of Japan with a dotted flight route and two location pins` | 日本地図と飛行ルートの点線(東京→沖縄など国内線) |
| `pacific_route.png` | `a globe-style map showing a dotted route from Japan across the Pacific to Hawaii` | 日本からハワイへの太平洋横断ルート(地球儀風) |
| `hawaii_islands.png` | `a simple map of the Hawaiian islands with Oahu highlighted` | ハワイ諸島の地図(オアフ島が強調) |
| `waikiki_beach.png` | `Waikiki beach with turquoise water, palm trees and Diamond Head in the background` | ワイキキビーチとダイヤモンドヘッド |
| `palm_sunset.png` | `palm trees against an orange sunset sky` | 夕焼けとヤシの木 |
| `hibiscus_lei.png` | `red hibiscus flowers and a flower lei` | ハイビスカスとレイ |
| `hotel_pool.png` | `a resort hotel pool with parasols and lounge chairs` | リゾートホテルのプールとパラソル |
| `hotel_room.png` | `a hotel room with an ocean view balcony` | オーシャンビューのホテル客室 |
| `shave_ice_food.png` | `a colorful shave ice and a Hawaiian plate lunch` | シェイブアイスとプレートランチ |
| `rental_car.png` | `an open-top car driving along a coastal road` | オープンカーで海沿いをドライブ |
| `credit_card_gold.png` | `a single gold credit card with a chip, no brand logo, generic design` | ゴールドのクレジットカード1枚(ロゴなし) |
| `credit_cards_stack.png` | `three generic credit cards fanned out, no brand logos` | 複数のクレジットカードが重なっている(ロゴなし) |
| `coins_points.png` | `a stack of coins marked with the letter P` | ポイントコイン(Pマーク)が積み上がる |
| `smartphone_app.png` | `a smartphone showing a points app with a rising number, no real brand` | スマホのポイントアプリ画面(数字が増える) |
| `piggy_bank.png` | `a piggy bank with coins going in` | 貯金箱とコイン |
| `calculator_budget.png` | `a calculator and a household budget notebook` | 電卓と家計簿 |
| `yen_dollar.png` | `yen and dollar symbols with exchange arrows` | 円とドルの両替イメージ |
| `shopping_bags.png` | `shopping bags and a receipt` | 買い物袋とレシート |
| `convenience_store.png` | `a cashless card payment at a store counter, hands only` | コンビニ・スーパーでのカード決済 |
| `calendar_check.png` | `a wall calendar with a red check mark on a date` | カレンダーにチェック(予約日・有効期限) |
| `clock_deadline.png` | `a clock and an hourglass` | 時計と砂時計(期限・タイミング) |
| `checklist.png` | `a clipboard with a checklist and check marks` | クリップボードのチェックリスト |
| `warning_sign.png` | `a triangular warning sign with an exclamation mark` | 三角の注意マーク |
| `lightbulb.png` | `a glowing light bulb idea icon` | ひらめきの電球 |
| `trophy_goal.png` | `a trophy and a goal flag` | トロフィーとゴールの旗 |
| `rising_graph.png` | `a bar chart with an upward arrow` | 右肩上がりのグラフ(マイルが増える) |
| `gift_box.png` | `a gift box with a ribbon` | ギフトボックス(特典・キャンペーン) |
| `family_luggage.png` | `four suitcases of different sizes lined up, no people` | 家族分のスーツケース4つ(人物なし) |
| `esta_document.png` | `a passport, a travel authorization document and a smartphone` | パスポートと渡航認証の書類・スマホ |
| `tokyo_tower_fuji.png` | `Tokyo Tower with Mount Fuji in the background` | 東京タワーと富士山(日本の出発地) |

**注意**: 背景は**真っ白のまま**でOK(透過処理は不要。システム側で白を透かします)。グラデーションや影の付いた背景は透けないので、「plain pure white background」を必ず入れてください。
クレジットカードは**実在のロゴ・ブランド名を入れない**こと(商標回避)。

できた画像を `assets/illust/` にアップロード: https://github.com/Yuki910127/miles-hawaii-insta/upload/main/assets/illust
全部揃わなくても動きます(あるものだけが選ばれます)。まず「plane_takeoff / boarding_pass / japan_map_route / pacific_route / waikiki_beach / credit_card_gold / coins_points / calendar_check / checklist / warning_sign / trophy_goal / tokyo_tower_fuji」の12枚を先に作ると効果が大きいです。
