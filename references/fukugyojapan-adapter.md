# 副業JAPAN接続仕様

同梱した`seo-site-skills`の内容を、副業JAPANのiHub入力、サイト資産、Astroリポジトリへ接続する。ここに記事の構成・本文・文体ルールを追加しない。

- サイトルート：`/Users/hirototakada/SEO/fukugyojapan`
- 案件作業先：`/Users/hirototakada/SEO/seo-articlework/hukugyojapan/<slug>/`
- 公開記事：`/Users/hirototakada/SEO/fukugyojapan/src/content/articles/<slug>.mdx`
- 公開画像：`/Users/hirototakada/SEO/fukugyojapan/public/images/`
- 本番URL：`https://fukugyojapan.com/<slug>/`

## iHubの対象

- サイトID：`kn79v569bym1h9xbfjy1hfv0px8bh122`
- サイト名：副業JAPAN(富士)
- タイムゾーン：`Asia/Tokyo`

task IDが指定された場合は、`case-info-fetcher`でそのタスクを取得し、返却タスクの`siteId`が上記IDと一致することを確認する。サイト名は`副業JAPAN(富士)`または`副業JAPAN`。別サイトのタスクは選定・制作・更新しない。資料のサイト名を付け替えて別サイトのタスクを流用しない。

```bash
python3 /Users/hirototakada/SEO/case-info-fetcher/case_info_fetcher.py list \
  --task-id <TASK_ID> --format raw-json \
  --output <ARTICLEWORK>/case-info.json
```

サイトIDだけ、または本日の執筆予定を指定された場合は、候補を全件取得して同梱スクリプトで1件選ぶ。

```bash
python3 /Users/hirototakada/SEO/case-info-fetcher/case_info_fetcher.py list \
  --site-id kn79v569bym1h9xbfjy1hfv0px8bh122 \
  --format raw-json --output /Users/hirototakada/SEO/seo-articlework/hukugyojapan/_queue/incomplete-tasks.json

python3 /Users/hirototakada/.codex/skills/fukugyojapanarticle/scripts/select_write_plan_task.py \
  --input /Users/hirototakada/SEO/seo-articlework/hukugyojapan/_queue/incomplete-tasks.json \
  --date YYYY-MM-DD \
  --output /Users/hirototakada/SEO/seo-articlework/hukugyojapan/_queue/selected-task.json
```

選定規則は、上記サイトIDに一致し、対象日の`writePlanDate`が一致し、`articleUrl`と`writeDoneDate`が空のタスクのうち、API順の先頭1件。別日や予定日未設定のタスクへ勝手に切り替えない。

選定後はtask IDで再取得し、案件用`case-info.json`を作る。案件名、task ID、メモ、`project.memo`、`project.addMemos`、LP URL、画像、カテゴリ、既存URLを確認する。

## 指定クエリ

iHubのtask memo、project memo、addMemosのいずれかに検索クエリとして明示された語句を「iHub指定クエリ」とする。この指定クエリはGSCで実際に確認されたクエリという前提で扱う。

- 明示されたクエリを勝手に言い換えない。
- 指定クエリはAhrefs調査の優先候補へ含める。
- 検索ボリューム、案件との一致、関連KW、カニバリを確認し、SEOのメインKWは正本の手順で決定する。
- 指定クエリがあれば、CTA型はそのクエリから決定する。
- 指定クエリがなければ、最終決定したメインKWからCTA型を決定する。

## 副業JAPAN固有資産

- ペルソナ：`/Users/hirototakada/.codex/skills/fukugyojapanarticle/references/personas/fuji.md`（確定済み）
- キャラ作成工程：`references/character-workflow.md`と同梱`character-creator`
- CTAコンポーネント：副業JAPANの`ArticleInlineLine.astro`、`ArticleConclusionLine.astro`、`ArticleBottomLine.astro`。接続は`references/line-cta.md`に従う。
- CTA画像：`/images/line-cta-banner-unified-v1.webp`。副業JAPANの`src/lib/article-cta-image.ts`を正本とする。
- CTAリンク：`https://fukugyojapan.com/add-line/`（既存コンポーネントが出力）
- アイキャッチ入口：`seo-article-to-mdx`のアイキャッチ工程 → `create-seo-fuji-eyecatch`
- アイキャッチ作成仕様：`/Users/hirototakada/.codex/skills/fukugyojapanarticle/references/eyecatch-rules.md`
- 公開記事：`src/content/articles/<slug>.mdx`
- 公開画像：`public/images/<slug>*.webp`

CTAは現在の副業JAPANと同じ自動表示方式を使う。MDXに画像・ボタン・リンクを重複記述しない。画像内の共通文言を記事固有の事実や相談実績として再審査しない。CTA前後の本文は、`line-cvr`で決めた読者状態と各配置箇所の内容に合わせて記事ごとに書く。

アイキャッチの構図、表示文言、素材選定、imagegenプロンプト、目視検査、保存、frontmatterは`references/eyecatch-rules.md`に従う。表示文言と素材は`facts.md`、`outline.md`、Gate通過済み本文にある確認済み情報だけを使う。

## iHub完了記録

本番記事URLとサイトマップを確認し、task IDで再取得した`siteId`が副業JAPANと一致することを確認した後だけ、次のように`articleUrl`を更新する。

```bash
python3 /Users/hirototakada/SEO/case-info-fetcher/case_info_fetcher.py complete \
  <TASK_ID> --article-url "https://fukugyojapan.com/<slug>/" \
  --output <ARTICLEWORK>/ihub-article-url-update.json
```

`--write-done-date`と`--clear-write-done-date`は指定しない。更新後の応答で`articleUrl`以外が変わっていないことを確認する。
