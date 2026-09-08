---
name: fukugyojapanarticle
description: 副業JAPAN向けの新規SEO検証記事を、iHubのtask ID・サイトID・当日の執筆予定または案件資料から作成する。seo-site-skillsの調査・Ahrefs KW選定・執筆・LINE CTA・レビュー・検査を使い、フジ名義のAstro MDX、証拠画像、アイキャッチ、ローカル表示、本番公開確認、iHub articleUrl更新まで扱う。リライトやWordPress投稿には使わない。
---

# 副業JAPAN新規記事制作

副業JAPANの新規検証記事を、同梱した`seo-site-skills`の正本に従って作る統括スキル。

キャラ、アイキャッチ、LINE CTA、作業場所、iHub、公開先は副業JAPANの設定を使う。スキルの設定変更だけでは記事作成・公開・iHub更新を実行しない。

## 正本と変更境界

優先順位は次のとおり。

1. ユーザーの今回の指示
2. `references/character-workflow.md`、`references/eyecatch-rules.md`、`references/line-cta.md`のキャラ・アイキャッチ・CTA表示仕様と、`references/fukugyojapan-editorial-rules.md`の文章・キャプション仕様
3. `references/seo-site-skills/`に同梱した正本
4. `references/fukugyojapan-adapter.md`の副業JAPAN接続仕様
5. `references/publish-workflow.md`の表示・公開仕様

同梱した正本を要約や記憶で置き換えない。副業JAPAN固有処理は、iHub入出力、フジ、CTA画像、アイキャッチ、Astroサイトへの配置、表示・公開、`fukugyojapan-editorial-rules.md`に明記した文章・画像キャプションだけとする。記事の調査・KW・構成・本文・文体・CTA文言・品質基準は、副業JAPAN固有ルールが明示的に上書きする箇所以外、正本に従う。

実行時に`/Users/hirototakada/SEO/seo-site-skills`を参照しない。コピー元の別スキルや他サイトの既存記事の制作ルールも上位ルールとして使わない。

## 実行開始・工程別の必読ルート

最初に今回の依頼範囲を確定する。記事作成では以下を適用する。修正案の提示やスキル設定の修正だけの依頼では、案件取得・記事制作の工程を開始しない。

新規記事ごとに正本を読み直す。会話にこのSKILL.md全文が提供されていても、参照資料は別途全文を読む。省略・切断された出力は分割して残りを取得する。子スキルが対象工程で必読とする参照も追加する。資料の要約や読了記録は原文の代わりにならない。

起動時に`references/workflow-state.md`を読み、次表と`references/workflow-manifest.json`の正確なパスを確認する。相対パスは本スキルルート基準。表は読む期限を示し、原文の読み込みを省略するための要約ではない。

| 工程ID | 開始前に全文を読む資料 | 終了条件 |
|---|---|---|
| intake | 本SKILL、workflow-state、adapter、editorial-rules、character-workflow、personas/fuji | 依頼範囲・対象案件・資料取得者を確定しcase-info.jsonへ保存 |
| research | 同梱research-agent、同references/ad-keywords | 調査根拠・未確認事項・Ahrefs結果・メインKWを保存 |
| cta | 同梱line-cvr、型決定後にclosing-templates、writing-examples | 型番号・判定KW・読者状態をoutlineとreview-reportへ記録 |
| writing | 同梱writing-agent、同referencesのarticle-types・ng-words・mdx-components・human-voice、docs/design-guide、critic、フジのペルソナ、line-cta | 構成と根拠に対応したAstro MDXを作成 |
| images | 同梱article-evidence-image-capture、eyecatch-rules、同資料が指定する専用スキルと画像生成スキル | 証拠画像・出典・配置・alt・アイキャッチを完成 |
| review | 同梱critic・seo-eeat-check・competitor-check、ペルソナ、publish-workflow | 指摘反映・全必須検査・375px表示確認を完了 |
| publish | publish-workflow（本番公開の依頼時のみ工程実行） | 本番・画像・サイトマップ確認後にiHubのarticleUrlだけ更新 |

`critic`はwriting-agentの必読指定に従い、レビュー時まで読み込みを遅らせず執筆前に読む。証拠画像を調査中に取得する場合は、その取得前に画像用資料を読む。フジ設定の初回作成・変更時だけ同梱`character-creator/SKILL.md`も読む。

ローカル表示または本番公開を実行する前に`references/publish-workflow.md`を読む。作成依頼でも工程6の表示検査には同資料を使用するが、公開の許可にはならない。

各工程の開始前・終了時にworkflow Gateを実行する。未読・必須成果物の欠落・必須検査の未実施がある工程を完了にしない。通常の読み込みと工程移行は自律的に行い、承認待ちを追加しない。取得不能は復旧を試み、解消しなければ未完了の工程と理由を報告する。

同梱research-agent・writing-agent等は、主担当が指示書として実行する。criticレビューは独立したサブエージェント1名へ委譲する。入力は対象MDX、facts、outline、フジのペルソナ、本スキルの優先ルール、critic原文。出力をcritic-review.mdへ保存し、主担当が指摘を反映してreview-report.mdへ対応を記録する。1周で終える。委譲機能が使えない場合は自己レビューを独立レビュー済みと扱わず、未完了として報告する。

サイト側のAGENTS.mdや検査と本スキルの適用規則に不整合があれば、双方の該当箇所・適用根拠・代替検査をreview-reportへ記録する。検査全体を黙って無効化しない。上位指示に従い、明示された適用除外以外のFAILは修正する。

## 作業場所と成果物

サイトルート`<SITE_ROOT>`は`/Users/hirototakada/SEO/fukugyojapan`、作業場所`<ARTICLEWORK>`は`/Users/hirototakada/SEO/seo-articlework/hukugyojapan/<slug>/`、スキルルート`<SKILL_ROOT>`は`/Users/hirototakada/.codex/skills/fukugyojapanarticle`とする。コピー元スキルへ処理を委ねず、上記スキルルートの同梱ファイルを使う。

```text
/Users/hirototakada/SEO/seo-articlework/hukugyojapan/<slug>/
├── workflow-state.json
├── case-info.json
├── facts.md
├── research_notes.json
├── outline.md
├── article-draft.mdx
├── images/
├── assets/eyecatch/
└── review-report.md

src/content/articles/<slug>.mdx
public/images/<slug>*.webp
```

`article-draft.mdx`も最初からAstro MDXで書く。確認後の最終MDXと本文、見出し、CTA、画像配置を一致させる。

## ワークフロー

### 0. フジのキャラ設定を作成・確認する

`references/character-workflow.md`に従い、同梱`character-creator`でフジの設定を作る。確定したペルソナがあれば読み込み、記事ごとに作り直さない。

### 1. iHub・案件情報を取得する

task ID、サイトID、本日の執筆予定、またはユーザー提供資料から案件を確定する。取得・選定・クエリの対応は`references/fukugyojapan-adapter.md`に従う。

### 2. 調査とKW選定

同梱`research-agent`の新規作成モードまたは新規案件モードをそのまま実行する。LP、特商法、登録後、会社・人物、公的機関、口コミ、競合を調べ、AhrefsでSEO用KWを選定する。結果を`facts.md`と`research_notes.json`へ保存する。

iHub資料は一次資料・調査の起点として使う。競合記事の評価や文面を事実として流用せず、正本の裏取りルールを守る。

LP・LINE資料の取得者と制作担当への提供経路は、`references/fukugyojapan-editorial-rules.md`の「LP・LINE資料の取得者と本文での書き方」に従って記録する。ユーザーが確認したフジの登録後情報を、制作担当の未登録と混同しない。

### 3. CTA型を決める

- iHubに指定クエリがある場合、その値をGSC実クエリとして扱い、`line-cvr`の表からCTA型を決める。
- 指定クエリがない場合、KW選定工程で最終決定したメインKWから読者状態を判定してCTA型を決める。
- iHub指定クエリはKW調査の優先候補にするが、SEOのメインKWへ無条件採用しない。
- 1記事につきCTA型は1つにする。各CTAの文面は配置箇所の文脈に合わせて変える。

型番号、判定に使ったクエリまたはメインKW、読者状態を`outline.md`と`review-report.md`へ記録する。

### 4. 構成とAstro MDXを作る

`writing-agent`に従って構成と本文を作る。記事タイプは通常`kensho`とし、`outline.md`に記録する。公開frontmatterは副業JAPANの`src/content.config.ts`に合わせ、必須の`title`、`description`、`publishedAt`と、`systemTag`など必要な対応フィールドを設定する。構成を機械的に固定せず、KW、検索意図、一次情報、競合との差を基準に決める。`systemTag`は`src/lib/systemTags.ts`の17種から案件内容に合う値を必ず1つ選ぶ。

フジのペルソナを読み、本文と吹き出しへ反映する。見出しはSEO用の標準表現とし、キャラ口調を入れない。

### 5. CTA・画像・アイキャッチを完成させる

CTA文言は`line-cvr`へ従い、表示には現在の副業JAPANの共通画像と自動挿入コンポーネントを使う。`references/line-cta.md`を必読とする。記事固有性はCTA前後の文章、読者状態、記事内の根拠で作る。

CTAは`ArticleLayout.astro`と`Balloon.astro`に自動表示を任せる。記事MDXには`LineButton`やCTA画像・リンクを手書きしない。最後のH2内は記事内容に合わせたフジの締めを作り、その後の画像CTAは既存の`ArticleBottomLine`で表示する。導入後・最初のH2末尾・吹き出し後の条件と検査は`references/line-cta.md`に従う。

画像は同梱正本の優先順位、証拠性、注釈、alt、寸法と`fukugyojapan-editorial-rules.md`の公開キャプション仕様に従う。

アイキャッチは`references/eyecatch-rules.md`に従い、`seo-article-to-mdx`と同じ専用スキル`create-seo-fuji-eyecatch`で作成する。生成り×朱赤×チャコールのデザイン、素材選定、保存、frontmatter、検査を同スキルへ委ねる。本文制作はこのスキルのフローを維持し、アイキャッチの入出力は参照ファイルの接続手順で同期する。

### 6. 準拠Gateと検査

次をすべて通す。違反があれば本文または成果物を直し、該当検査を再実行する。

工程の必読資料・成果物・検査証跡は`references/workflow-state.md`のGateでも確認する。読了・問題なしという自己申告だけでは合格にしない。調査根拠、CTA型の理由、critic指摘と対応、導入レビューの実内容を照合する。workflow Gateは既存の品質検査を置き換えない。

1. フジペルソナ、`writing-agent`、`human-voice`、`line-cvr`への文体・CTA準拠確認
2. `critic`の1周レビューと指摘反映
3. textlint
4. `python3 /Users/hirototakada/.codex/skills/fukugyojapanarticle/scripts/check_fukugyojapan_editorial.py src/content/articles/<slug>.mdx`
5. 同梱`references/seo-site-skills/check-article.sh`（副業JAPANのサイトルートから実行）
6. 同梱`references/seo-site-skills/skills/scripts/check-line-cv.sh`
7. 同梱`references/seo-site-skills/skills/scripts/check-images.sh`
8. E-E-A-Tチェック
9. 競合文章一致チェック
10. Astro MDXコンパイルとローカルビルド
11. 375pxでH1、本文、表、画像、吹き出し、CTA、目次、コンソールを確認

CTA検査は`references/line-cta.md`に従い、レンダリング後の表示数、配置、画像、リンク、重複を確認する。同梱`check-article.sh`の`LineButton`記述数・直前段落を前提とした項目は自動CTAに適用せず、表示後の検査へ置き換える。他項目のFAILは修正する。

`kensho`では、正本の型別基準である画像10枚以上・各H2に画像・吹き出し8個以上・LINE誘導3個以上を満たす。LINE誘導の数はMDXのタグ数ではなく、自動表示後の記事本文内で確認する。

記事全体の判断文の語順と、資料取得者・本文の一人称の一致も、`references/fukugyojapan-editorial-rules.md`の納品前Gateに従って確認し、`review-report.md`へ記録する。

#### 導入の内容レビュー

同梱`writing-agent`の「導入の完成条件」「導入の情報量と前後のつながり」に照らし、次の各項目について、原稿の該当文・判定・判断理由を`review-report.md`へ記録する。装飾についてはMDXの指定と表示確認結果を示す。

- 読者の疑問が、この案件に即して具体的か
- 広告の特徴、サービス内容、判断理由、本文で分かること、相談内容が、導入だけで無理なく理解できるか。短くするために必要な説明を削っていないか
- 結論の理由が導入だけでも理解できるか
- 本文で何を確かめられるか分かるか
- LINEで確認できる内容が具体的か
- 吹き出しが1文で、前後と重複していないか
- 通常段落同士と吹き出しも含め、同じ訴求や説明を言い換えて繰り返していないか。隣接する文が加える情報の違いを確認する
- 部分修正した場合、前後2段落（端では存在する範囲）と関連する吹き出し、導入全体を読み直し、指示語・意味の重複・話題の飛躍がないか
- 必要な装飾が原稿と表示の両方に反映されているか

「問題なし」「共感あり」「CTAあり」「文字数内」だけの報告は禁止。重複やつながりの判定には比較した文を併記し、新しく加わる情報や自然につながる理由を示す。導入を修正した場合は、修正前の判定を流用せず、この内容レビューを更新する。情報不足・重複・つながりの不自然さがあれば、文字数や機械検査が通っていてもGateを合格にせず修正する。相談実績・体験・対応能力は、導入を充実させる目的で創作しない。

### 7. 表示・公開・完了記録

ローカル表示または本番公開は`references/publish-workflow.md`に従う。作成だけの依頼ではcommit、push、公開、iHub更新を行わない。

本番URLの表示とサイトマップ掲載を確認し、対象タスクのサイトIDが副業JAPANと一致することを再確認した後、iHubは`articleUrl`だけ更新する。`writeDoneDate`やメモなど他のフィールドは変更しない。

## 完了条件

- 必須成果物と公開用MDX・画像があり、依頼範囲のworkflow Gateが合格している。
- Ahrefsを含む調査、CTA型判定、準拠Gate、機械検査、表示確認が完了している。
- 未確認情報を事実として書いていない。
- ローカル表示依頼では記事がHTTP 200で表示され、サーバーが稼働中である。
- 本番公開依頼では本番URLがHTTP 200で、サイトマップへ掲載されている。
- iHub更新を行った場合、変更フィールドが`articleUrl`だけである。

完了時は、成果物の絶対パス、検査結果、表示URL、公開を行った場合はcommitと本番確認結果を報告する。
