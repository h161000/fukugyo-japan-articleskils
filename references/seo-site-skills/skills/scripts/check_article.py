#!/usr/bin/env python3
"""記事のスキル遵守チェッカー。textlintでは検出できないルールを検査する。"""

import sys
import re
from pathlib import Path


def check(filepath: str) -> list[str]:
    text = Path(filepath).read_text(encoding="utf-8")
    errors = []

    # --- frontmatter を除いた本文 ---
    parts = text.split("---", 2)
    if len(parts) >= 3:
        body = parts[2]
    else:
        body = text

    # 1. Balloon（吹き出し）の数
    balloon_count = len(re.findall(r"<Balloon\s", body))
    if balloon_count < 8:
        errors.append(f"❌ 吹き出しが{balloon_count}箇所（8箇所以上必要）")

    # 2. Balloon の import があるか
    if balloon_count > 0 and "import Balloon" not in text:
        errors.append("❌ Balloonを使っているがimportがない")
    if balloon_count == 0 and "import Balloon" not in text:
        errors.append("❌ Balloonのimportがない（吹き出し0箇所）")

    # 3. 画像の数
    img_count = len(re.findall(r"!\[.*?\]\(.*?\)", body))
    if img_count < 10:
        errors.append(f"❌ 画像が{img_count}箇所（10箇所以上必要）")

    # 4. LineButton の数
    line_count = len(re.findall(r"<LineButton", body))
    if line_count < 3:
        errors.append(f"❌ LineButtonが{line_count}箇所（3箇所以上必要）")

    # 5. 禁止フレーズ
    forbidden = [
        ("本気で副業で稼ぎたい意志がある方のみ", "間口を狭める表現"),
        ("消費者ホットライン", "外部に誘導しない"),
        ("188に電話", "外部に誘導しない"),
        ("188に相談", "外部に誘導しない"),
        ("お金は一切受け取りません", "禁止フレーズ"),
        ("お金など一切受け取りません", "禁止フレーズ"),
    ]
    for phrase, reason in forbidden:
        if phrase in body:
            errors.append(f"❌ 禁止フレーズ「{phrase}」が含まれている（{reason}）")

    # 6. 冒頭の段落数（最初のH2までに5段落以内）
    first_h2 = re.search(r"^## ", body, re.MULTILINE)
    if first_h2:
        intro = body[: first_h2.start()]
        # 空行で区切られた段落をカウント（import行、コンポーネント行を除く）
        paragraphs = [
            p.strip()
            for p in re.split(r"\n\n+", intro)
            if p.strip()
            and not p.strip().startswith("import ")
            and not p.strip().startswith("<LineButton")
        ]
        if len(paragraphs) > 7:
            errors.append(
                f"❌ 冒頭が{len(paragraphs)}段落（書きすぎ。5段落程度に抑える）"
            )

    # 7. 語尾の連続チェック（です。/ます。/た。が3連続）
    # 段落を抽出（Balloon、AlertBox、コンポーネント行を除く）
    lines = []
    for line in body.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(("<Balloon", "<AlertBox", "<LineButton", "<FaqSchema", "import ", "##", "![", "|", "<div", "</div", "<a ", "</a", "<nav", "---", ">")):
            continue
        if stripped.startswith(("<p", "<strong", "<b>", "<mark", "<span")):
            # HTMLタグ内のテキストも対象
            clean = re.sub(r"<[^>]+>", "", stripped)
            if clean.strip():
                lines.append(clean.strip())
        elif not stripped.startswith("<"):
            lines.append(stripped)

    consecutive = 0
    prev_ending = ""
    for line in lines:
        # 文末の語尾を取得
        match = re.search(r"(です|ます|でした|ました)。\s*$", line)
        if match:
            ending = match.group(1)
            if ending in ("です", "でした") and prev_ending in ("です", "でした"):
                consecutive += 1
            elif ending in ("ます", "ました") and prev_ending in ("ます", "ました"):
                consecutive += 1
            else:
                consecutive = 1
            prev_ending = ending
        else:
            consecutive = 0
            prev_ending = ""

        if consecutive >= 3:
            errors.append(
                f"⚠️ 語尾「〜{ending}。」が3文以上連続（AI感が出る）: ...{line[-30:]}"
            )
            consecutive = 0  # 1回報告したらリセット

    # 8. emダッシュチェック
    if "——" in body or "—" in body:
        errors.append("❌ emダッシュ（——/—）が含まれている")

    # 9. Markdown太字チェック（**text**）
    md_bold = re.findall(r"(?<!\*)\*\*(?!\*)[^*]+\*\*(?!\*)", body)
    # import行やfrontmatterのものを除外
    real_bold = [b for b in md_bold if "import" not in b and "SKILL" not in b]
    if real_bold:
        errors.append(
            f"❌ Markdown太字（**）を{len(real_bold)}箇所使用（<strong>に変更）"
        )

    # 10. <br> チェック
    if "<br>" in body or "<br/>" in body or "<br />" in body:
        errors.append("❌ <br>が含まれている（段落で分ける）")

    return errors


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 check_article.py <article.mdx> [article2.mdx ...]")
        sys.exit(1)

    total_errors = 0
    for filepath in sys.argv[1:]:
        errors = check(filepath)
        name = Path(filepath).name
        if errors:
            print(f"\n📄 {name}")
            for e in errors:
                print(f"  {e}")
            total_errors += len(errors)
        else:
            print(f"\n📄 {name} ✅ 問題なし")

    print(f"\n{'='*40}")
    if total_errors > 0:
        print(f"❌ {total_errors}件のエラー")
        sys.exit(1)
    else:
        print("✅ 全チェック通過")
        sys.exit(0)


if __name__ == "__main__":
    main()
