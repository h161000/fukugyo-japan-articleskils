# 副業検証サイト — セットアップガイド

このskillsディレクトリをコピーすれば、誰でも同じ品質で副業検証記事を書けます。

---

## 前提条件

- Node.js 22以上
- GitHub アカウント
- Cloudflare アカウント

---

## 1. サイト構築（初回のみ）

### 1-1. Astroプロジェクト作成

```bash
npm create astro@latest my-site
cd my-site
npm install @astrojs/mdx @astrojs/sitemap @astrojs/cloudflare
```

### 1-2. skillsディレクトリをコピー

```bash
cp -r /path/to/skills ./skills
```

### 1-3. textlint セットアップ

```bash
# パッケージインストール
npm install --save-dev \
  textlint \
  textlint-plugin-html \
  textlint-rule-preset-japanese \
  textlint-rule-no-double-negative-ja \
  textlint-rule-no-dropping-the-ra \
  textlint-rule-sentence-length \
  textlint-rule-no-doubled-joshi \
  textlint-rule-max-ten \
  textlint-rule-no-mix-dearu-desumasu

# 設定ファイルをコピー
cp skills/_setup/.textlintrc.json ./.textlintrc.json
mkdir -p textlint-rules
cp skills/_setup/textlint-rules/*.js ./textlint-rules/

# カスタムルールをnode_modulesに配置
mkdir -p node_modules/textlint-rule-ng-words node_modules/textlint-rule-no-consecutive-same-endings
cp textlint-rules/ng-words.js node_modules/textlint-rule-ng-words/index.js
cp textlint-rules/no-consecutive-same-endings.js node_modules/textlint-rule-no-consecutive-same-endings/index.js
```

### 1-4. package.jsonにスクリプト追加

```json
{
  "scripts": {
    "lint:text": "textlint 'src/content/articles/**/*.mdx'",
    "lint:text:fix": "textlint --fix 'src/content/articles/**/*.mdx'",
    "postinstall": "cp textlint-rules/ng-words.js node_modules/textlint-rule-ng-words/index.js 2>/dev/null; cp textlint-rules/no-consecutive-same-endings.js node_modules/textlint-rule-no-consecutive-same-endings/index.js 2>/dev/null; true"
  }
}
```

### 1-5. 動作確認

```bash
npm run lint:text
```

---

## 2. Cloudflare リソース作成（初回のみ）

### 2-1. Workers + D1 + R2 を作成

```bash
# Wranglerにログイン
npx wrangler login

# D1データベース作成
npx wrangler d1 create <サイト名>-db

# R2バケット作成
npx wrangler r2 bucket create <サイト名>-images
```

### 2-2. wrangler.toml 設定

```toml
name = "<サイト名>"
compatibility_date = "2024-12-01"

[[d1_databases]]
binding = "DB"
database_name = "<サイト名>-db"
database_id = "<作成時に表示されたID>"

[[r2_buckets]]
binding = "R2"
bucket_name = "<サイト名>-images"
```

### 2-3. 管理画面パスワード設定

```bash
npx wrangler secret put ADMIN_PASSWORD --name <サイト名>
```

---

## 3. GitHub リポジトリ + 自動デプロイ（初回のみ）

### 3-1. リポジトリ作成 & push

```bash
git init
git add .
git commit -m "初期コミット"
git remote add origin https://github.com/<user>/<repo>.git
git push -u origin main
```

### 3-2. GitHub Secrets 登録

リポジトリ > Settings > Secrets and variables > Actions に以下を追加:

| Secret名 | 値 |
|----------|-----|
| `CLOUDFLARE_API_TOKEN` | Cloudflareダッシュボードで発行（Workers編集権限 + R2読み書き権限） |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflareダッシュボード > 概要 > アカウントID |

### 3-3. GitHub Actions 設定

`.github/workflows/deploy.yml` を作成:

```yaml
name: Deploy to Cloudflare Workers

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 22

      - name: Install dependencies
        run: npm ci

      - name: Upload images to R2
        run: |
          for file in public/images/*; do
            if [ -f "$file" ]; then
              key=$(basename "$file")
              npx wrangler r2 object put "<サイト名>-images/$key" --file="$file" --remote
              echo "Uploaded: $key"
            fi
          done
        env:
          CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          CLOUDFLARE_ACCOUNT_ID: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}

      - name: Remove images from build
        run: rm -rf public/images/*

      - name: Build
        run: npm run build

      - name: Deploy to Workers
        run: npx wrangler deploy
        env:
          CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          CLOUDFLARE_ACCOUNT_ID: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
```

---

## 4. サイト共通インフラ（初回のみ）

### 4-1. GTM（Google Tag Manager）

`src/layouts/BaseLayout.astro` の `</head>` 直前と `<body>` 直後にスニペットを追加。
初回はコメントアウトで枠だけ取っておき、コンテナIDが決まったら `GTM-XXXXXX` を置換してコメント解除。

**`</head>` 直前:**

```html
{/* Google Tag Manager - IDが決まったら GTM-XXXXXX を置換してコメント解除 */}
{/* <script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','GTM-XXXXXX');</script> */}
```

**`<body>` 直後:**

```html
{/* Google Tag Manager (noscript) - IDが決まったら GTM-XXXXXX を置換してコメント解除 */}
{/* <noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-XXXXXX"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript> */}
```

### 4-2. LINE登録リダイレクト（/add-line/）

WPの `functions.php` にあったLINE登録リダイレクト機能を、AstroのSSRエンドポイントで再現する。

**`src/pages/add-line.ts` を作成:**

```typescript
import type { APIRoute } from "astro";

export const prerender = false;

// --- 本番URLが決まったら差し替え ---
const REDIRECT_URLS = [
  "https://example.line-chat.jp/add-line/",
];

function isLineChatJpUrl(url: string): boolean {
  return /^https:\/\/[^/]+\.line-chat\.jp\/add-line\//i.test(url);
}

export const GET: APIRoute = ({ request }) => {
  const randomUrl = REDIRECT_URLS[Math.floor(Math.random() * REDIRECT_URLS.length)];
  const url = new URL(randomUrl);

  if (isLineChatJpUrl(randomUrl)) {
    const referer = request.headers.get("referer") || "";
    if (referer) {
      try {
        const refUrl = new URL(referer);
        const pathMatch = refUrl.pathname.match(/\/articles\/([^/]+)/);
        url.searchParams.set("referer", refUrl.pathname);
        if (pathMatch?.[1]) {
          url.searchParams.set("category", pathMatch[1]);
        }
      } catch {}
    }
  }

  return new Response(null, {
    status: 307,
    headers: { Location: url.toString() },
  });
};
```

**全LINEリンクのhrefを `/add-line/` に統一:**
- `LineButton.astro` — デフォルトURLを `/add-line/` に
- `StickyLine.astro` — hrefを `/add-line/` に
- `Sidebar.astro` — 全LINE系hrefを `/add-line/` に

これにより：
- LINEボタンクリック → `/add-line/` → 307リダイレクト → LINE登録画面
- リファラーから記事slug・パスを自動取得してパラメータ付与
- 複数URLで分散可能（A/Bテスト等）
- URL変更時は `add-line.ts` の1箇所だけ修正すればOK

### 4-3. 構造化データ（Organization JSON-LD + SNS sameAs）

SWELLの「構造化データ > 組織情報」に相当する機能。Googleナレッジパネルやリッチリザルトに組織情報・SNSリンクが出る可能性がある。

**BaseLayout.astro に Organization JSON-LD を追加（全ページ出力）:**

```html
<script type="application/ld+json" set:html={JSON.stringify({
  "@context": "https://schema.org",
  "@type": "Organization",
  name: "サイト名",
  url: siteUrl,
  logo: `${siteUrl}/favicon.svg`,
  description: "サイトの説明文",
  sameAs: [
    "https://x.com/XXXXXX",
    "https://www.instagram.com/XXXXXX/",
    "https://www.facebook.com/XXXXXX",
    "https://www.wantedly.com/id/XXXXXX",
  ],
  contactPoint: {
    "@type": "ContactPoint",
    contactType: "customer support",
    url: `${siteUrl}/add-line/`,
    availableLanguage: "Japanese",
  },
})} />
```

**やること:**
- `BaseLayout.astro`: Organization JSON-LD を全ページに出力 + WebSiteに `publisher` 追加
- `ArticleLayout.astro`: `publisher.sameAs` と `author.sameAs` にSNS URL追加
- SNSアカウント作成後に `XXXXXX` を実際のURLに差し替え

### 4-4. Google Search Console

`BaseLayout.astro` にサイト所有権確認用メタタグを追加。コメントアウトで枠を取り、確認コード取得後に差し替え。

```html
{/* <meta name="google-site-verification" content="XXXXXX" /> */}
```

### 4-5. ページネーション

記事一覧ページ（`/articles/`）にページネーションを実装。Astroの `paginate()` を使用。

- `src/pages/articles/index.astro` → `src/pages/articles/[...page].astro` に変更
- `getStaticPaths` で `paginate(articles, { pageSize: 10 })` を返す
- `/articles/` = 1ページ目、`/articles/2/` = 2ページ目〜
- 10件以下の間はページネーションUI非表示
- タイトルに「（2ページ目）」等を自動付与

### 4-6. ProfilePage JSON-LD（著者E-E-A-T）

`/profile/` の著者構造化データ。GoogleのE-E-A-T（経験・専門性・権威性・信頼性）評価に寄与。

`profile.astro` のJSON-LDを `ProfilePage > mainEntity > Person` に設定：
- `jobTitle` — 職種
- `knowsAbout` — 専門分野
- `worksFor` — 所属組織（サイト）
- `sameAs` — SNS URL

### 4-7. チェックリスト

新しいサイトを立ち上げたら以下を確認：

| 項目 | ファイル | 状態 |
|------|---------|------|
| GTMスニペット（枠） | `BaseLayout.astro` | コメントアウトで配置 |
| GTMコンテナID | `BaseLayout.astro` | ID決定後に置換 |
| LINEリダイレクト | `src/pages/add-line.ts` | ダミーURLで配置 |
| LINE本番URL | `src/pages/add-line.ts` | URL決定後に差し替え |
| 全LINEリンク | `LineButton/StickyLine/Sidebar` | `/add-line/` に統一 |
| Organization JSON-LD | `BaseLayout.astro` | sameAs にSNS URL |
| Article publisher/author sameAs | `ArticleLayout.astro` | SNS URL差し替え |
| Search Console メタタグ | `BaseLayout.astro` | 確認コード差し替え |
| ページネーション | `src/pages/articles/[...page].astro` | pageSize調整 |
| ProfilePage JSON-LD | `profile.astro` | 著者E-E-A-T構造化データ |

---

## 5. キャラ作成

`skills/writing-agent/references/personas/_template.md` をコピーして自分のキャラを作る。

```bash
cp skills/writing-agent/references/personas/_template.md \
   skills/writing-agent/references/personas/<キャラ名>.md
```

編集する項目:
- ペンネーム・年齢・経歴
- 文体・トーン
- LINE URL・バナー画像
- サイト名・URL
- 締めの言い回し

---

## 6. 日常運用（記事追加のフロー）

```
案件名を受け取る
    |
    v
[1] 調査（skills/research-agent/SKILL.md）
    - LP・特商法を確認
    - 口コミ・会社情報を調査
    - KW調査
    |
    v
[2] 画像生成（Google Imagen API or 手動）
    - アイキャッチ: 1200px幅 WebP
    - セクション画像: 800px幅 WebP x 10枚以上
    - public/images/ に配置
    |
    v
[3] 執筆（skills/writing-agent/SKILL.md）
    - キャラファイル読み込み
    - SKILL.mdの①〜⑫の構成で執筆
    - MDXファイルを src/content/articles/<slug>.mdx に出力
    |
    v
[4] 品質チェック
    - npm run lint:text（textlint）
    - SKILL.mdの品質チェックリスト18項目
    - npm run dev でプレビュー確認
    |
    v
[5] デプロイ
    - git add / commit / push origin main
    - GitHub Actionsが自動で: 画像→R2 → ビルド → Workers
    |
    v
[6] 本番確認
    - https://<サイト名>.workers.dev/articles/<slug>/
    - 画像表示、OGP、モバイル表示を確認
```

---

## トラブルシューティング

| 問題 | 対処 |
|------|------|
| textlintが動かない | `npm run postinstall` でカスタムルールを再配置 |
| 画像がR2に上がらない | deploy.ymlの `--remote` フラグとバケット名を確認 |
| 記事ページが404 | content.config.tsのスキーマ、ファイル名（.mdx）を確認 |
| デプロイ失敗 | GitHub SecretsのAPI TOKEN・ACCOUNT IDを確認 |
| 管理画面に入れない | `wrangler secret put ADMIN_PASSWORD` で再設定 |

---

## ファイル構成

```
skills/
  writing-agent/
    SKILL.md                 ← 執筆ワークフロー（司令塔）
    references/
      personas/
        _template.md         ← 新規キャラ用テンプレート
        manabu.md            ← サンプルキャラ
      ng-words.md            ← NGワード一覧
      mdx-components.md      ← コンポーネント仕様
  research-agent/
    SKILL.md                 ← 調査ワークフロー
    references/
      ad-keywords.md         ← KWパターン
  rewrite-agent/
    SKILL.md                 ← リライトワークフロー
  _setup/
    README.md                ← このファイル
    .textlintrc.json         ← textlint設定
    textlint-rules/
      ng-words.js            ← カスタムルール
      no-consecutive-same-endings.js
```
