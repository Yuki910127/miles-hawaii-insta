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

## ④ ハイライト用アイコン(任意・5枚)

```
Set of 5 minimal line icons in one consistent style for Instagram story highlight covers,
each centered on a solid sand-colored background #FFF7EA, coral #F28C28 line color, 1:1 square:
1) airplane ticket  2) credit card  3) plumeria flower  4) hotel building with palm  5) checklist.
```
