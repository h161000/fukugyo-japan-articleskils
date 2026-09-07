#!/usr/bin/env python3
"""副業JAPAN固有の文章表現と公開画像キャプションを検査する。"""

from __future__ import annotations

import re
import sys
from pathlib import Path


CAPTION_OPEN = (
    '<p style="font-size: 0.75em; color: #666; text-align: center; '
    'line-height: 1.5; margin-top: 6px;">'
)

BANNED_PHRASES = {
    "一緒に整理できます": "一緒に確認できます",
    "口コミは次の3種類に分けて見ます": "口コミを次の3つの観点から確認します",
    "流れを整理すると、次の順番です": "実際の案内を時系列で並べると、次のとおりです",
    "LINEで流しています": "LINEで共有しています",
}

LINE_DELIVERY_PATTERN = re.compile(
    r"(?:副業情報|副業の話)[^。\n]{0,80}(?:そのまま)?流しています"
)
PUBLIC_PROVENANCE_PATTERN = re.compile(
    r"（[^）]*(?:ユーザー提供画像|\d{4}-\d{2}-\d{2}確認)[^）]*）"
)
MARKDOWN_IMAGE_PATTERN = re.compile(r"^\s*!\[[^\]]*\]\([^)]*\)\s*$")


def check_text(text: str) -> list[str]:
    """検査違反を人が修正できるメッセージとして返す。"""
    errors: list[str] = []
    lines = text.splitlines()

    for old, new in BANNED_PHRASES.items():
        for line_number, line in enumerate(lines, 1):
            if old in line:
                errors.append(
                    f"L{line_number}: 使用しない表現「{old}」があります。"
                    f"「{new}」を基準に文脈へ合わせて修正してください"
                )

    for line_number, line in enumerate(lines, 1):
        if LINE_DELIVERY_PATTERN.search(line) and "LINEで流しています" not in line:
            errors.append(
                f"L{line_number}: LINEで届ける内容を「流しています」と表現しています。"
                "「共有しています」を基準に修正してください"
            )

    for index, line in enumerate(lines):
        if not MARKDOWN_IMAGE_PATTERN.match(line):
            continue

        next_index = index + 1
        while next_index < len(lines) and not lines[next_index].strip():
            next_index += 1

        if next_index >= len(lines) or not lines[next_index].startswith(CAPTION_OPEN):
            errors.append(
                f"L{index + 1}: Markdown画像直後のキャプションがないか、"
                "副業JAPAN指定の小さめ・中央寄せスタイルではありません"
            )
            continue

        caption = lines[next_index]
        provenance = PUBLIC_PROVENANCE_PATTERN.search(caption)
        if provenance:
            errors.append(
                f"L{next_index + 1}: 公開キャプションに出典種別または確認日"
                f"「{provenance.group(0)}」が残っています"
            )

    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"使い方: python3 {Path(argv[0]).name} <記事.mdx>", file=sys.stderr)
        return 2

    article_path = Path(argv[1])
    if not article_path.is_file():
        print(f"記事ファイルがありません: {article_path}", file=sys.stderr)
        return 2

    errors = check_text(article_path.read_text(encoding="utf-8"))
    print(f"=== 副業JAPAN文章・キャプションチェック: {article_path} ===")
    if errors:
        for error in errors:
            print(f"  ❌ {error}")
        print(f"FAIL: {len(errors)}件の修正が必要です")
        return 1

    print("  ✅ 指定外の文章表現なし")
    print("  ✅ 本文画像のキャプション書式・公開文言OK")
    print("PASS: 副業JAPAN固有ルールに適合しています")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
