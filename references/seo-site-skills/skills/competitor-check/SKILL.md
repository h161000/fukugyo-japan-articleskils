---
name: competitor-check
description: Use when finishing any article in src/content/articles/ before commit/push, to detect verbatim string overlap (20+ chars) and structural copying against competitor articles ranked for the article's target keywords.
---

# 競合パクリチェック

## 目的

書いた記事が、競合記事（同じKWで検索上位に来る他社の検証ブログ等）と **20文字以上連続して文字列が一致していないか** を機械的に検出する。
さらに **H2構成の流れが被っていないか** をレポートする。

## 鉄則

1. **文字列の完全一致は罪**。20文字以上連続して同じならその段落は書き直し
2. **同じ意味でも表現を変えればOK**。言い換えは検出対象外
3. **流れ（H2構成）が被るのもよろしくない**。並びの一致率が高ければ順番を変える
4. **競合に送客しない**。チェック中に得た競合URLを記事内には絶対書かない
5. **判断は人間が行う**。スクリプトは検出するだけ、書き換えは人が決める

## いつ使うか

- 記事執筆完了後、seo-eeat-check の後、git push 前
- リライト後の記事も同様に実行

**例外なし。**

## チェックフロー

```
1. ユーザーから受け取った主要KW（または記事のメインKW）を引数に渡す
2. python3 skills/competitor-check/check_competitor.py <記事ファイル> "KW1" "KW2" "KW3" ...
3. レポート（/tmp/<slug>-competitor-check.md）を確認
4. 20文字以上の完全一致が検出されたら → その段落を書き換え
5. H2構成の一致率が高ければ → 順番や見出し表現を変える
6. カバー漏れ（参考情報）→ 必要なら追記を検討
7. 修正後、再度スクリプトを実行して 0 件になることを確認
```

## スクリプトの動作

### 入力

- 記事ファイルパス（必須）
- 主要KW（最低1個、複数可）

```bash
python3 skills/competitor-check/check_competitor.py \
  src/content/articles/xxx.mdx \
  "高速資産形成セミナー" \
  "武藤孝幸 評判" \
  "高速資産形成セミナー 怪しい"
```

### 処理ステップ

1. **WebSearch を各KWで実行**（外部スクリプトでは Python から WebSearch 直接呼べないため、結果URLは Claude が会話内で WebSearch して渡す or キャッシュ機構を使う方式を採用）
2. **ヒットしたURLを集約 → 重複除外**
3. **除外フィルタ適用**（自社・PR系・動画サイト・SNSなど）
4. **上位5記事を WebFetch で取得**
5. **各記事をプレーンテキストに変換**（HTMLタグ除去）
6. **自記事の本文を文単位に分割**
7. **20文字以上の連続一致を検出**（自記事の各部分文字列を競合本文に検索）
8. **H2構成を抽出して並びの一致率を計算**
9. **競合に出てくる固有名詞で自記事に無いものを抽出**（カバー漏れ参考）
10. **レポートを `/tmp/<slug>-competitor-check.md` に出力**

### 除外ドメイン

```
自社:
  - yakkei.jp
  - fukugyo-blog.yekouxiuxiong75.workers.dev

プレスリリース系:
  - prtimes.jp
  - atpress.ne.jp
  - valuepress.com
  - pr-times.com

非競合（チェック対象外）:
  - youtube.com / youtu.be
  - twitter.com / x.com
  - facebook.com
  - instagram.com
  - tiktok.com
  - amazon.co.jp / rakuten.co.jp（書籍販売）
```

これら以外は **すべて競合チェック対象**。

### 一致しきい値

| しきい値 | 動作 |
|---|---|
| **20文字以上連続一致** | エラー（書き換え必須） |
| **15〜19文字連続一致** | 警告（人間が見て判断） |
| **H2並び順 80%以上一致** | 警告（順番を変える検討） |

参考: 「ありがとうございます」(11文字) → スルー
参考: 「おすすめできない」(8文字) → スルー
参考: 「無料セミナーから高額講座への動線」(16文字) → 警告
参考: 「米国株オプション取引は仕組みを正しく理解しないと」(24文字) → エラー

## レポートフォーマット

```markdown
# 競合チェックレポート: <記事タイトル>

実行日時: 2026-04-07 15:30
対象記事: src/content/articles/<slug>.mdx
主要KW: ["KW1", "KW2", "KW3"]

## 競合候補（5件）

1. https://example1.com/article
2. https://example2.com/article
...

## 完全一致検出

### ❌ エラー（20文字以上）

- L137 「2時間のセミナーで全部教えてもらえるなら、誰も苦労しません」
  ↑ example1.com の本文と 21文字一致
- L221 「米国株オプション取引は仕組みを正しく理解しないと一回」
  ↑ example2.com の本文と 26文字一致

### ⚠️ 警告（15〜19文字）

- L88 「無料セミナーから高額講座への動線」
  ↑ example3.com と 16文字一致

## H2構成の比較

自記事:
  1. 結論
  2. とは
  3. 実績
  4. 登録
  5. 料金
  6. 口コミ
  7. 運営情報
  8. まとめ

competitor1.com:
  1. 概要
  2. 料金
  3. 口コミ
  4. 運営
  5. まとめ
  並び順一致率: 50%

competitor2.com:
  1. とは
  2. 料金
  3. 講師
  4. 口コミ
  5. まとめ
  並び順一致率: 60%

## カバー漏れ（参考情報）

- competitor1 で言及されているが自記事に無い:
  - 「投資助言業」
  - 「金融商品取引業者」
- competitor2 で言及されているが自記事に無い:
  - 「累計受講者の業種」
```

## 違反時の対応

| 違反種別 | 対応 |
|---|---|
| 20文字以上の完全一致 | 該当段落を別の表現で書き直し。同義語・語順変更・主語変更で対応 |
| 15〜19文字一致 | 書き換え推奨。ただし固有名詞や定型句は許容（例：「株式会社○○」は社名なので一致して当然） |
| H2並び順80%以上一致 | 順番を入れ替えるか、見出し文言を独自のものに変更 |
| カバー漏れ | 必須ではない。情報として価値があれば追記、なければスルー |

## ループ穴対策

| 言い訳 | 反論 |
|---|---|
| 「20文字一致だけど業界の常識的な指摘だから」 | 常識でも文字列が一致してはダメ。表現を変える |
| 「固有名詞だけだから検出されても無視していい」 | 「株式会社○○の代表取締役○○氏は」のような長い固有名詞並びは一致して当然。ただし周辺の修飾語は変える |
| 「競合が少ないから5記事集まらない」 | 集まる分だけでチェック。0件は OK としない（KWを変えて再検索） |
| 「H2構成は業界標準だから被っても仕方ない」 | 並び順80%超えたら順番を変える。見出し文言を独自にする |
| 「忙しいからこのチェックはスキップ」 | スキップ禁止。push前必須 |
| 「前回チェックしたから今回はスキップ」 | 修正のたびに再実行 |

## Red Flags - STOP and Re-check

- check_competitor.py を実行していない
- レポートを開かずに「OK」と判断している
- 20文字一致が出ているのに「常識的だから」と書き換えていない
- 競合のURLを「出典」として記事に書こうとしている
- WebSearch をスキップして「競合がいない」ことにしている

**全部 NG。push 前にやり直し。**

## スクリプトの実行モード

このスクリプトは Python 単体では WebSearch / WebFetch を実行できないため、2モードで動かす：

### Mode A: 競合URL外部入力モード（推奨）

事前に Claude が WebSearch で取得した URL を、テキストファイルとして渡す方式。

```bash
# 1. Claude が WebSearch で URL を集めて /tmp/competitors.txt に1行1URLで保存
# 2. Claude が WebFetch で各URLの本文を取得して /tmp/competitor_<n>.txt に保存
# 3. スクリプト実行
python3 skills/competitor-check/check_competitor.py \
  src/content/articles/xxx.mdx \
  --competitors-dir /tmp/competitors/
```

### Mode B: テキスト直接比較モード

Claude が WebFetch した結果を持っているなら、直接テキストファイルとして比較できる。

```bash
python3 skills/competitor-check/check_competitor.py \
  src/content/articles/xxx.mdx \
  --competitor /tmp/comp1.txt \
  --competitor /tmp/comp2.txt \
  --competitor /tmp/comp3.txt
```

## ワークフロー（Claude側の動き）

```
1. ユーザーから記事のメインKWを取得
2. WebSearch を各KWで実行（最大3〜5回）
3. 結果URLを集約・除外フィルタ・上位5件を選択
4. 各URLを WebFetch して本文を取得 → /tmp/competitor_<n>.txt に保存
5. python3 skills/competitor-check/check_competitor.py <記事> /tmp/competitor_*.txt
6. レポートを Read で確認
7. 違反箇所を Edit で修正
8. 再度スクリプト実行 → 0件確認
9. seo-eeat-check に進む or git push へ
```
