# 副業JAPANの既存LINE CTAを使う

ユーザー指定により、現在の副業JAPANの画像・ボタン・自動表示を使う。この表示仕様を同梱スキルの手動CTA配置規則より優先する。CTA前後の本文はフジのペルソナと`line-cvr`に従い、記事ごとに書く。

## 実装の正本

サイト：`/Users/hirototakada/SEO/fukugyojapan`

- 画像切替：`src/lib/article-cta-image.ts`
- 本文配置：`src/layouts/ArticleLayout.astro`
- 吹き出し：`src/components/Balloon.astro`
- 画像CTA：`src/components/ArticleInlineLine.astro`、`ArticleConclusionLine.astro`、`ArticleBottomLine.astro`

2026-09-07確認時は`USE_UNIFIED_ARTICLE_CTA = true`。記事内の共通画像は`/images/line-cta-banner-unified-v1.webp`（2121×741px）、リンク先は`https://fukugyojapan.com/add-line/`。将来画像が変更された場合は実装を読み直して追従し、この記事制作スキルからサイトの画像切替を変更しない。

## MDXの作り方と表示位置

- `LineButton`、`ArticleInlineLine`、`ArticleConclusionLine`、`ArticleBottomLine`を記事からimport・手書きしない。共通CTA画像や`/add-line/`リンクも記事MDXに重複挿入しない。
- 最初のH2がレンダリング後に`id="section-1"`となる構造にする（現行Astro設定はH2/H3へ連番IDを自動付与するため、最初のH2より前にH3を置かない）。レイアウトはこのIDを基準に導入文と最初のセクションを分ける。
- 導入文があれば、その後・目次の前に`ArticleInlineLine placement="intro"`が表示される。
- 最初のH2のセクション末尾に`ArticleConclusionLine`が表示される。
- 最終H2より前の`Balloon`では、本文が`一緒に[^。！？]*ましょう`に一致すると画像CTAが表示される。`lineCta`属性による明示指定があればそちらが優先される。文面を機械的に揃えず、CTAを出したい箇所で必要に応じて`lineCta={true}`を使う。
- 最後のH2以降では吹き出し由来の画像CTAがレイアウトにより除外される。フジの締めは記事の内容に合わせて変え、本文末尾の`ArticleBottomLine`へつなぐ。
- ヘッダーや追従CTAは既存サイト側の表示を維持し、記事へ複製しない。

## 検査

MDXソースの`LineButton`数はCTA数ではない。同梱`check-article.sh`の手動ボタン数・手動ボタン直前文の検査は、本ファイルの表示後検査へ置き換え、適用対象外の理由をレポートに残す。その他の品質検査は維持する。

ビルドとローカル375px表示で次を確認する。

- 最初のH2のIDと導入文により、導入後・最初のセクション末尾・本文末尾の画像CTAが表示される。
- 記事本文内のLINE誘導が3個以上あり、意図した吹き出し後の表示も確認できる。
- 同じ箇所でCTAが二重表示されず、最終H2内の吹き出し由来CTAが除外されている。
- 共通画像の読み込みが成功し、リンクが副業JAPANの`/add-line/`を指す。
- 画像のはみ出しや切れがなく、クリック領域とCTA前後の文脈が自然である。

サイトルート・iHub・公開先は`fukugyojapan-adapter.md`の副業JAPAN設定を使う。


## 結論・締めからの接続

最初の結論では具体的な理由一覧と判断への説明、最後のH2では本文の主要な理由の振り返りと読者の判断を済ませてから、共感・相談案内へ進む。CTA型を満たす目的で記事の理由説明を削らない。詳しい完成条件は`fukugyojapan-editorial-rules.md`を参照する。


## 相談案内の文言

相談できる内容と相談先を直接伝え、「LINEで相談できます」を文脈に合わせて使う。「一緒に確認できます」「一緒に考えます」だけで相談への案内を代替しない。実際の共同確認の説明や、解決を保証しないための範囲の限定は保持する。詳しい適用範囲と横断レビューは`fukugyojapan-editorial-rules.md`を正本とする。CTAの自動挿入条件・画像・リンクはこの文言方針で変更しない。
