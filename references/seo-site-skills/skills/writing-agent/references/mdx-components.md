# MDXコンポーネント・装飾リファレンス

記事（`.mdx`）で使う書き方の一覧。WordPress Gutenbergブロックは使わない。

---

## インポート（全記事共通・frontmatterの直後に書く）

```mdx
import AlertBox from "../../components/AlertBox.astro";
import Balloon from "../../components/Balloon.astro";
```

---

## 基本要素

**段落:**
```mdx
テキスト

テキスト
```
※ 空行で段落を区切る。1段落に「。」は1つまで。

**見出しH2:**
```mdx
## 見出しテキスト
```

**見出しH3:**
```mdx
### 見出しテキスト
```

**画像:**
```mdx
![alt text](/images/slug-section01.webp)
```

**リスト:**
```mdx
- 項目1
- 項目2
- 項目3
```

**テーブル:**
```mdx
| ラベル | 値 |
|--------|-----|
| 会社名 | 株式会社〇〇 |
| 代表者 | 〇〇太郎 |
```

**テーブルのモバイル対策（必須）:**
- **列は3列まで。** 4列以上はモバイルで潰れて読めなくなる
- **セル内は短く。** 長い名称は省略する（「KS会員（サービス受領者）」→「KS会員」）
- **金額は短く書く。** 「10,000円」→「1万円」。ただし正確さが必要な場面では省略しない
- **列が多いなら表を分割する。** 1つの表を無理に詰め込まず、2つに分けて本文で補足する
- **特商法テーブルは2列（ラベル+値）で統一。** これなら崩れない

**引用（口コミ等）:**
```mdx
> 引用テキスト
>
> <cite>LINE相談者さんより</cite>
```
⚠️ **本文と`<cite>`の間は必ず「>」だけの行**にする（上記の通り）。**完全な空行（>のない空行）を入れると別々のblockquoteに割れて、引用とciteが2つの箱に分断表示される。** 納品ゲート(check-article.sh)でも検出する。

---

## Astroコンポーネント

**吹き出し（Balloon）:**
```mdx
<Balloon name="タカシ" image="/images/prof.webp">
  吹き出しの本文（1文だけ。複数文を入れない）
</Balloon>
```
- `name`: キャラ名（必須）
- `image`: アバター画像パス（任意。なければ名前の頭文字が表示される）
- `position`: `"left"`（デフォルト）or `"right"`

**警告・注意ボックス（AlertBox）:**
```mdx
<AlertBox type="danger" title="要注意ポイント">
  ボックスの内容テキスト
</AlertBox>
```
- `type`: `"danger"` / `"warning"` / `"info"`
- `title`: ボックスのタイトル

**~~FAQ構造化データ（FaqSchema）~~ — 廃止。使わない。**
GoogleがFAQリッチリザルトを2026年5月に完全廃止したため不要。

---

## 装飾（HTMLタグで直接書く）

装飾ルールはSKILL.mdを参照。

---

## LINE誘導（画像バナー）

```mdx
<a href="https://line.me/xxx" target="_blank" rel="noopener nofollow">
  <img src="/images/line-banner.webp" alt="LINEで無料相談する" width="600" height="200" loading="lazy" />
</a>
```

※ バナー画像URL・LINE URLはキャラファイル（`personas/*.md`）を参照すること。

---

