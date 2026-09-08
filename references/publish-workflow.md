# 副業JAPAN表示・公開手順

ローカル表示・記事作成工程の表示検査・本番公開を実行する前に読む。本番公開工程は公開の明示がある場合だけ実行する。記事作成、構成確認、原稿確認だけではcommit、push、iHub更新を行わない。

## 接続先

- 実行リポジトリ：`/Users/hirototakada/SEO/fukugyojapan`
- origin：`https://github.com/fuji-ai-site/fukugyojapan.git`
- 本番ドメイン：`https://fukugyojapan.com`
- Cloudflare設定：サイトの`wrangler.toml`、Worker名`fukugyojapan`、画像バケット`fukugyojapan-images`

実行時はリポジトリ・origin・現行のデプロイ連携を確認する。別サイトのリポジトリでは実行しない。

## ローカル表示

1. 対象記事がルート生成対象になる公開状態であることを確認する。正本を公開状態にしたくない段階では、隔離コピーを使う。
2. Astroの開発サーバーを起動し、対象記事URLがHTTP 200になることを確認する。
3. 375pxとデスクトップで本文、画像、表、吹き出し、目次、CTAを確認する。
4. ユーザーへ表示URLを返し、終了の明示があるまでサーバーを維持する。

ローカル表示を依頼された記事を、一覧から除外された状態や404のまま案内しない。

## 本番公開

ユーザーが「プッシュ」「本番公開」「本番反映」を明示した場合、非公開またはブランチ限定の指定がない限り、本番で表示する指示として扱う。

1. 対象MDXを公開状態にする。
2. textlint、記事ゲート、LINE CV、画像、E-E-A-T、競合一致、MDX、Astroビルドを再確認する。
3. `dist/client/<slug>/index.html`とサイトマップへの`/<slug>/`掲載を確認する。
4. `git status`と差分を確認し、対象MDXと参照画像だけを明示してstageする。`git add .`を使わない。
5. `origin/main`とのfast-forward可否と、本番へ追加されるcommitを確認する。無関係な変更やcommitを含めない。
6. 通常commitを作り、force pushせず`origin/main`へpushする。現行のCloudflare連携によるデプロイ結果を確認する。画像配信はサイト既存のR2同期・ビルド方式を使い、本番画像の読み込みまで確認する。ローカル検査には`npm run build -- --force`を使い、画像を削除する`cf:build`は日常のローカル検査として実行しない。
7. `https://fukugyojapan.com/<slug>/`のHTTP 200、タイトル、canonical、本文、画像、CTAを確認する。
8. `https://fukugyojapan.com/sitemap.xml`への掲載を確認する。
9. 本番確認後に限り、`fukugyojapan-adapter.md`の手順でiHubの`articleUrl`だけを更新する。

現在ブランチへのpushだけ、本番ビルド成功だけ、または反映待ちの状態を「本番公開済み」と報告しない。
