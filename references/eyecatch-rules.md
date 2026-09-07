# 副業JAPANのアイキャッチ工程

ユーザー指定の`seo-article-to-mdx`と同じアイキャッチ工程を使う。

## 参照順

1. `/Users/hirototakada/.codex/skills/seo-article-to-mdx/SKILL.md`のアイキャッチ工程を確認する。
2. 同工程が指定する`/Users/hirototakada/.agents/skills/create-seo-fuji-eyecatch/SKILL.md`を全文読む。
3. 専用スキルの`references/eyecatch-rules.md`と、利用可能な画像生成スキルを読む。

デザインは専用スキルの生成り×朱赤×チャコール、1672×941pxを適用する。同梱正本のアイキャッチ規定より本工程を優先する。コピー時に残した`assets/navy-gold-reference.webp`と`scripts/finalize_eyecatch.sh`はこのスキルから使用しない。

## 原稿と保存先の接続

本文制作の正本は本スキルの`article-draft.mdx`を維持する。アイキャッチ工程のためだけに`seo-article-to-mdx`の調査・本文制作を開始しない。

- 専用スキルの作業先は`/Users/hirototakada/SEO/seo-articlework/hukugyojapan/<slug>/`。本スキルと同じ作業先を使い、確定稿`article-draft.mdx`からアイキャッチ工程用の`article-draft.md`を同期する。`facts.md`、`outline.md`、画像素材・出典記録は同じ案件フォルダ内のものを参照する。既存の別案件ファイルを上書きしない。
- 専用スキルの保存スクリプトを使用する。公開画像は`/Users/hirototakada/SEO/fukugyojapan/public/images/<slug>-eyecatch.webp`へ置く。
- 専用スキルの原稿更新後、画像frontmatterを本スキルの`article-draft.mdx`と公開MDXへ同期する。本文を変更する必要が出た場合は本スキルの正本を先に更新する。
- `image: "/images/<slug>-eyecatch.webp"`が各原稿・公開MDXで一致し、公開画像が存在することを確認する。
- 目視確認、画像寸法、ビルド、記録は専用スキルに従う。MDX形式の正本には本スキルのAstro MDX検査を使い、アイキャッチのために本文を別の変換器で書き換えない。

画像frontmatterの反映先は副業JAPANの公開MDXとする。
