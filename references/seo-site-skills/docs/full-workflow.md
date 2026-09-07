# 案件名 → 公開 までの全自動ワークフロー

案件名を受け取ってから本番公開まで、一連の流れ。

---

## 全体フロー

```
案件名を受け取る
    ↓
Phase 1: 調査（research-agent）
    ↓
Phase 2: 画像生成（＋LP証拠スクショの注釈＝必須）
    ↓
Phase 3: 執筆（writing-agent）
    ↓
Phase 3.5: レビュー（critic）
    ↓
Phase 4: デザイン確認（design-guide準拠）
    ↓
Phase 5: Git push → 自動デプロイ
    ↓
Phase 6: 本番確認
```

---

## Phase 1: 調査

**使うスキル:** `skills/research-agent/SKILL.md`

### インプット
- 案件名（例: 「株式会社YASAKAの副業」）
- キャラ指定（例: 「マナブ」）
- タグ指定（任意。なければ案件の内容から自動判断）

### やること

| # | タスク | ツール |
|---|--------|--------|
| 1 | LP・公式サイトを確認、ジャンル判定 | WebFetch |
| 2 | SEO用KW調査（ボリューム・難易度） | Ahrefs keywords-explorer |
| 3 | 競合記事を2〜3本確認（構成・切り口） | WebSearch + WebFetch |
| 4 | 会社情報・特商法を調査 | WebSearch |
| 5 | 口コミ・評判を収集（Yahoo知恵袋、SNS等） | WebSearch |
| 6 | 運営者・責任者の経歴を調査 | WebSearch |
| 7 | 危険度チェックリストを実行 | research-agent SKILL.md参照 |
| 8 | 実際にLINE登録して検証（可能な場合） | 手動 or ブラウザ |

### アウトプット
- 調査ノート（research_notes.json or チャット上のまとめ）
- KWリスト（メインKW + サブKW）
- タグ候補（案件の内容ベース: 「情報商材」「FX自動売買」等）

### 注意
- **NGワード確認**: 「詐欺」「逮捕」「犯罪」「違法」は使わない
- **裏取り必須**: 競合記事の情報を鵜呑みにしない。一次ソースで確認
- **情報不足時**: ユーザーに報告して判断を仰ぐ

---

## Phase 2: 画像生成

### アイキャッチ画像
```bash
# 【重要】IMAGEN_API_KEY は各サイトの .env に自分で設定する。プリセットされていない。
# 横展開した新サイトの .env は IMAGEN_API_KEY が未設定（プレースホルダ）なので、毎回ここで設定する。
#   Google AI Studio (https://aistudio.google.com/apikey) で Generative Language API のキーを発行し、
#   echo 'IMAGEN_API_KEY=AIza...' >> .env  で追記してから source する。
# ※ Imagen 生成は標準機能。「使えない／未設定」と判断する前に、まず .env にキーがあるか確認すること。
source .env

curl -s "https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key=${IMAGEN_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"instances":[{"prompt":"プロンプト"}],"parameters":{"sampleCount":1,"aspectRatio":"16:9"}}' \
  | python3 -c "import sys,json,base64; d=json.load(sys.stdin); open('output.png','wb').write(base64.b64decode(d['predictions'][0]['bytesBase64Encoded']))"

# WebPに変換（リサイズ不要 — GitHub Actionsがデプロイ時に自動リサイズ）
cwebp -q 80 output.png -o public/images/slug名.webp
```

> **注意:** 画像のリサイズはAI側で不要。GitHub Actionsがデプロイ時に自動でリサイズする（アイキャッチ→1200×630、セクション→800×600上限）。cwebpでWebP変換するだけでよい。縦長スクショ（高さが幅の2倍超）は撮らないこと。

### セクション画像
- 各H2セクションに1枚
- `public/images/slug名-section01.webp` 〜 `section09.webp`
- **スクショが撮れない場合:** Google Imagen APIでイメージ画像を生成して代用する（証拠画像のように見せない）

### LP証拠スクショの注釈（必須・例外なし）

**料金・特商法・実績表示・煽り文言のLPスクショには、赤枠＋番号＋注釈を必ず焼き込む。** 素通しのスクショは「で、どこを見ればいい？」が伝わらず一次情報としての価値が落ちる。推奨ではなく**必須ステップ**。

```bash
# skills/scripts/annotate_shot.py を使う（撮影済みスクショに後から焼ける）
# 枠はデフォルト赤で統一・区別は番号／注釈はベタ塗り＋文字色自動コントラスト
python3 skills/scripts/annotate_shot.py \
  public/images/slug名-section03.webp public/images/slug名-section03.webp \
  --title "料金プランが書かれていた箇所" \
  --box 4,46,44,22,1 --note "1 月額9,800円と表示されている" \
  --box 4,70,90,10,2 --note "2 初期費用は「別途」とだけ書かれ金額の記載がない"
```

- 対象は**料金・特商法・実績・煽り**のスクショ。**1記事あたり2〜4枚**が目安（全部には付けない）
- 座標は画像に対する**％**（詳細ルールとPython例は `skills/writing-agent/SKILL.md` の「画像注釈」節）
- 🚫 **LP上の文字を注釈で覆わない／写ってる事実だけ書く／評価は本文へ／枠がズレたら注釈ごと外す**
- 撮れなかった等で対象スクショが1枚も無い記事は、注釈スキップ可（ただし理由を一言残す）

### 画像ファイル命名規則
```
public/images/
  slug名.webp              ← アイキャッチ
  slug名-section01.webp    ← セクション画像
  slug名-section02.webp
  ...
```

---

## Phase 3: 執筆

**使うスキル:**
- `skills/writing-agent/SKILL.md` — 執筆ルール全般
- `skills/writing-agent/references/personas/manabu.md` — キャラ設定（マナブの場合）
- `skills/writing-agent/references/ng-words.md` — NGワード
- `skills/writing-agent/references/mdx-components.md` — コンポーネント使い方
- `docs/design-guide.md` — デザイン・改行・装飾ルール

### やること

| # | タスク |
|---|--------|
| 1 | キャラファイルを読み込む |
| 2 | design-guide.mdを読み込む |
| 3 | 調査結果をもとにMDX記事を執筆 |
| 4 | frontmatterを設定（title, description, tags等） |
| 5 | 品質チェック（下記参照） |

### frontmatter
```yaml
---
title: "記事タイトル（全角32文字以内・メインKWを先頭20字以内に）"
description: "meta description（120文字以内）"
publishedAt: "2026-03-27"
verdict: "danger"          # danger / warning / safe / unknown
verdictText: "危険"
category: "fukugyo"        # fukugyo / toushi
tags: ["情報商材", "競馬ツール"]  # 案件の内容ベース
image: "/images/slug名.webp"
---
```

### 品質チェック

| チェック項目 | 基準 |
|-------------|------|
| `<br>` | 使ってないこと。「。」後は段落分け |
| モバイル3行以内 | 30文字超えの文は「、」で分割 |
| 吹き出し | 8〜12箇所。2つ連続禁止 |
| LINE誘導 | 3回。毎回文面を変える |
| AlertBox内リスト | 複数理由は `<ul><li>` |
| `<strong>` / `<b>` | 強調 / 目立たせ の使い分け |
| 自分語り | 1記事2回まで、各1〜2文 |
| 箇条書き | 本文中は2箇所まで |
| NGワード | 「逮捕」「犯罪」「違法」なし |
| LINE訴求 | 「稼げる副業教えます」系なし |
| タグ | 案件名ではなく内容ベース |

### 出力先
```
src/content/articles/slug名.mdx
```

---

## Phase 3.5: レビュー（critic）

**使うスキル:** `skills/critic/SKILL.md`

writing-agentが書いた記事ドラフトに対して、読者目線で重大な問題だけを突っ込む。

### やること

| # | タスク |
|---|--------|
| 1 | 記事MDXファイルを読み込む |
| 2 | キャラファイルを読み込む |
| 3 | 5つの観点でレビュー（読者離脱・AI感・根拠不足・キャラブレ・LINE誘導） |
| 4 | 指摘は3〜5個まで。重大な問題だけ |
| 5 | writing-agentが修正したら完了。再チェックはしない |

### ルール
- 問題がなければ「問題なし、このまま出せ」で終わり
- 無理にダメ出ししない
- SEO・画像・誤字脱字は対象外（それぞれ別スキルが担当）
- H2の順番やSKILL.mdの構成ルールには触らない

---

## Phase 4: デザイン確認

**使うファイル:** `docs/design-guide.md`

devサーバーで確認（`npm run dev`）

| チェック | 方法 |
|---------|------|
| フォント（Noto Sans JP 19px） | preview_inspect |
| 段落margin-bottom（2.5em） | preview_inspect |
| H2見出し（紺色背景・白抜き） | preview_screenshot |
| 吹き出し（ボーダー・名前表示） | preview_screenshot |
| LINEボタン（緑一色・白文字・1行） | preview_screenshot |
| マーカー（#ffe95b 細い線） | preview_inspect |
| AlertBox（薄い背景・角丸） | preview_screenshot |
| 目次（LINE誘導①の後） | preview_screenshot |
| モバイル表示（375px） | preview_resize mobile |

---

## Phase 4.5: SEO/E-E-A-T・競合パクリチェック（必須・例外なし）

**push 前に必ず2つのスキルを実行する。** スキップ禁止。

### 1. SEO/E-E-A-T チェック

**使うスキル:** `skills/seo-eeat-check/SKILL.md`

```bash
python3 skills/seo-eeat-check/check_eeat.py src/content/articles/<slug>.mdx
```

エラーが出たら修正して再実行。エラー0件になるまで push しない。
警告と人間判断項目（H1〜H7）も全部目視確認する。

### 2. 競合パクリチェック

**使うスキル:** `skills/competitor-check/SKILL.md`

```bash
# 1. WebSearch で主要KW（ユーザー指定の上位3個程度）の上位5記事URLを取得
# 2. 各URLを WebFetch で本文取得 → /tmp/competitors/comp1.txt 〜 comp5.txt に保存
# 3. スクリプト実行
python3 skills/competitor-check/check_competitor.py \
  src/content/articles/<slug>.mdx \
  --competitors-dir /tmp/competitors/
```

**しきい値:**
- 20文字以上の連続一致 → エラー（書き換え必須）
- 15〜19文字の連続一致 → 警告（人間判断、固有名詞ならOK）

検出された段落は、別の表現に書き換えて再実行。エラー0件になるまで push しない。

### 鉄則

- **両スキルともpush前に必ず実行**
- **片方だけスキップは禁止**
- **「軽い修正だから」「時間がないから」は通らない**
- **エラーが出たまま push しない**

---

## Phase 5: Git push → 自動デプロイ

### 手順
```bash
cd /path/to/project  # プロジェクトルートに移動

# 変更を確認
git status
git diff

# コミット（記事＋画像）
git add src/content/articles/slug名.mdx
git add public/images/slug名*.webp
git commit -m "記事追加: slug名"

# push → GitHub Actions が自動デプロイ
git push origin main
```

### GitHub Actionsの自動処理（deploy.yml）
```
1. public/images/* → R2にアップロード（--remote付き）
2. public/images/* を削除（ビルドマシン上のみ）
3. npm run build（画像なしの軽いdist）
4. wrangler deploy → Cloudflare Workersにデプロイ
5. IndexNow → Bing/Yandexに新規・更新記事を自動通知
```

> **補足:** 管理画面に記事エディタ（`/admin/editor/`）があり、簡単なテキスト修正はブラウザからGitHub API経由で直接保存できる。ただしMDXの構造的な変更やスキルチェックが必要な修正はローカルで行うこと。

### 必要なシークレット（GitHub Secrets）
- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`

---

## Phase 6: 本番確認

デプロイ完了後、本番URLで確認。

**重要: 記事のパーマリンクはルート直下（`/<slug>/`）。`/articles/<slug>/` ではない。** 動的ルーティングは `src/pages/[id].astro` で実装されており、`/articles/` 配下は記事一覧ページ（`src/pages/articles/[...page].astro`）になる。混同しないこと。

```
https://yakkei.jp/<slug>/
```

| チェック | 内容 |
|---------|------|
| ページ表示 | 404にならないこと |
| 画像表示 | R2から配信されていること |
| OGP | SNSシェア時の画像・タイトル |
| 構造化データ | Article + BreadcrumbList |
| モバイル表示 | 実機 or DevToolsで確認 |

---

## スキルファイル一覧（参照順）

| Phase | ファイル | 役割 |
|-------|---------|------|
| 調査 | `skills/research-agent/SKILL.md` | 調査手順・チェックリスト |
| 調査 | `skills/research-agent/references/ad-keywords.md` | 広告KWリスト |
| 執筆 | `skills/writing-agent/SKILL.md` | 執筆ルール・品質基準 |
| 執筆 | `skills/writing-agent/references/personas/manabu.md` | マナブのキャラ設定 |
| 執筆 | `skills/writing-agent/references/ng-words.md` | NGワード一覧 |
| 執筆 | `skills/writing-agent/references/mdx-components.md` | コンポーネント使い方 |
| レビュー | `skills/critic/SKILL.md` | 記事ドラフトの重大問題チェック |
| リライト | `skills/rewrite-agent/SKILL.md` | リライト手順・チェックリスト |
| デザイン | `docs/design-guide.md` | デザイン・改行・装飾ルール |
| SEO | `docs/seo-requirements.md` | SEO要件 |
| デプロイ | `.github/workflows/deploy.yml` | CI/CD設定 |
| 画像 | Google Imagen API | 画像生成（cwebpでWebP変換） |

---

## ユーザーが渡す情報

### 最低限
- 案件名（例: 「株式会社YASAKAの副業」）
- キャラ（例: 「マナブ」）

### あると助かる
- 案件のURL（LP・公式サイト）
- タグ指定（例: 「情報商材」）
- 参考にしたい競合記事URL
- 特に書いてほしいポイント

---

## トラブルシューティング

| 問題 | 対処 |
|------|------|
| 画像がR2に上がらない | deploy.ymlの `--remote` フラグを確認 |
| 記事ページが404 | content.config.tsのスキーマ、ファイル名を確認 |
| フォントが適用されない | BaseLayout.astroのGoogle Fonts読み込みを確認 |
| LINEボタン文字が青 | `color: #fff !important` がLineButtonにあるか確認 |
| 吹き出し内の余白が大きい | `.balloon-bubble p { margin-bottom: 0 }` を確認 |
| 目次が表示されない | ArticleLayoutのJS挿入スクリプトを確認 |
| デプロイが失敗 | GitHub SecretsのAPI TOKEN・ACCOUNT IDを確認 |
