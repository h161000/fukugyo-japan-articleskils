#!/usr/bin/env python3
"""
競合パクリチェックスクリプト

使い方:
    python3 skills/competitor-check/check_competitor.py <記事ファイル> --competitor <競合テキスト> ...

または:
    python3 skills/competitor-check/check_competitor.py <記事ファイル> --competitors-dir <ディレクトリ>

競合テキストは事前に Claude が WebFetch で取得して保存しておく。

出力:
    /tmp/<slug>-competitor-check.md にレポートを書き出し
    20文字以上の完全一致が見つかったら exit 1
"""
import sys
import re
import os
import argparse
from pathlib import Path

# しきい値
ERROR_LEN = 20  # 20文字以上の連続一致 → エラー
WARN_LEN = 15   # 15〜19文字の連続一致 → 警告
H2_OVERLAP_THRESHOLD = 0.8  # H2並び順80%以上 → 警告

# 検出から除外する定型句（固有名詞や定型表記）
NOISE_PATTERNS = [
    r"株式会社[一-龥ァ-ヴA-Za-z0-9]+の?",
    r"合同会社[一-龥ァ-ヴA-Za-z0-9]+の?",
    r"一般社団法人[一-龥ァ-ヴA-Za-z0-9]+の?",
    r"代表取締役[一-龥]+",
    r"https?://[^\s]+",
    r"\d{4}年\d{1,2}月\d{1,2}日",
    r"[A-Z][a-zA-Z]{4,}とは",  # 「VisionCreatorとは」のような固有名詞+とは
    r"[一-龥ァ-ヴ]{2,8}とは[？\?]?",  # 「高速資産形成セミナーとは」
]


def color(s, c):
    codes = {"red": "31", "yellow": "33", "green": "32", "cyan": "36", "gray": "90", "bold": "1"}
    return f"\033[{codes.get(c, '0')}m{s}\033[0m"


def get_article_body(content):
    """frontmatter / import / コードブロック除去"""
    body = re.sub(r"^---.*?---\n", "", content, count=1, flags=re.DOTALL)
    body = re.sub(r"^import .*$", "", body, flags=re.MULTILINE)
    return body


def extract_text_from_html(html):
    """HTMLタグを除去してテキスト化"""
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.I)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"\s+", " ", text)
    return text


def normalize_text(text):
    """比較用にテキストを正規化"""
    text = re.sub(r"\s+", "", text)  # 空白除去
    return text


def find_long_matches(article_text, competitor_text, min_len):
    """
    article_text の中から、competitor_text に min_len 文字以上連続一致する部分を全件抽出。
    返り値: [(自記事内での開始位置, 一致した文字列), ...]
    """
    matches = []
    a = article_text
    c = competitor_text
    n = len(a)
    i = 0
    while i < n - min_len:
        # i から始まる最長一致を探す（greedy）
        # まず min_len 文字一致するか
        snippet = a[i:i + min_len]
        if snippet in c:
            # さらに伸ばせるか
            j = min_len
            while i + j <= n and a[i:i + j + 1] in c:
                j += 1
            matches.append((i, a[i:i + j]))
            i += j  # 一致部分をスキップ
        else:
            i += 1
    return matches


def is_noise(matched_string):
    """固有名詞やURL等のノイズかどうか判定"""
    for pat in NOISE_PATTERNS:
        if re.fullmatch(pat, matched_string):
            return True
    return False


def get_line_number(content, position):
    """正規化前のcontentで、該当する行番号を返す（おおまか）"""
    return content[:position].count("\n") + 1


def extract_h2_list(content):
    """## で始まる行から H2 一覧を取得"""
    return [m.group(1).strip() for m in re.finditer(r"^##\s+(.+)$", content, re.MULTILINE)]


def extract_h2_from_html(text):
    """競合HTMLからH2を抽出（簡易）"""
    h2s = re.findall(r"<h2[^>]*>(.*?)</h2>", text, re.IGNORECASE | re.DOTALL)
    cleaned = []
    for h in h2s:
        h = re.sub(r"<[^>]+>", "", h)
        h = h.strip()
        if h:
            cleaned.append(h)
    return cleaned


def calc_h2_overlap(my_h2s, comp_h2s):
    """H2並び順の一致率（共通要素の割合）"""
    if not my_h2s or not comp_h2s:
        return 0.0
    # 簡易: 各H2を「キーワード」として包含チェック
    keywords = ["とは", "結論", "料金", "費用", "口コミ", "評判", "登録", "運営", "会社", "まとめ", "詐欺", "怪しい", "実態", "返金"]
    my_keys = set()
    for h in my_h2s:
        for k in keywords:
            if k in h:
                my_keys.add(k)
    comp_keys = set()
    for h in comp_h2s:
        for k in keywords:
            if k in h:
                comp_keys.add(k)
    if not my_keys or not comp_keys:
        return 0.0
    common = my_keys & comp_keys
    return len(common) / max(len(my_keys), len(comp_keys))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("article", help="自記事のmdxファイルパス")
    parser.add_argument("--competitor", action="append", default=[], help="競合本文ファイル（複数指定可）")
    parser.add_argument("--competitors-dir", help="競合本文ファイルのディレクトリ")
    parser.add_argument("--report", help="レポート出力先（デフォルト: /tmp/<slug>-competitor-check.md）")
    args = parser.parse_args()

    if not os.path.exists(args.article):
        print(f"記事ファイルが見つかりません: {args.article}")
        sys.exit(1)

    competitor_files = list(args.competitor)
    if args.competitors_dir:
        d = Path(args.competitors_dir)
        if d.exists():
            competitor_files += sorted(str(p) for p in d.iterdir() if p.is_file() and p.suffix in (".txt", ".html", ".md"))

    if not competitor_files:
        print(color("⚠️  競合ファイルが指定されていません。", "yellow"))
        print("使い方:")
        print("  --competitor <ファイル> （複数指定可）")
        print("  --competitors-dir <ディレクトリ>")
        sys.exit(1)

    with open(args.article) as f:
        article_content = f.read()
    article_body = get_article_body(article_content)
    article_normalized = normalize_text(article_body)
    article_h2s = extract_h2_list(article_content)

    slug = Path(args.article).stem
    report_path = args.report or f"/tmp/{slug}-competitor-check.md"

    report = []
    report.append(f"# 競合パクリチェックレポート: {slug}")
    report.append("")
    report.append(f"対象記事: `{args.article}`")
    report.append(f"競合数: {len(competitor_files)}")
    report.append("")

    total_errors = 0
    total_warnings = 0

    report.append("## 完全一致検出")
    report.append("")

    for cf in competitor_files:
        with open(cf) as f:
            comp_content = f.read()
        comp_text = extract_text_from_html(comp_content) if "<" in comp_content else comp_content
        comp_normalized = normalize_text(comp_text)
        comp_h2s = extract_h2_from_html(comp_content)
        if not comp_h2s:
            # markdown形式の場合
            comp_h2s = [m.group(1).strip() for m in re.finditer(r"^##\s+(.+)$", comp_content, re.MULTILINE)]

        cf_label = Path(cf).name
        report.append(f"### vs `{cf_label}`")
        report.append("")

        matches = find_long_matches(article_normalized, comp_normalized, WARN_LEN)
        # フィルタ
        filtered = [(p, m) for p, m in matches if not is_noise(m)]

        if not filtered:
            report.append("- 一致なし ✓")
            report.append("")
            continue

        for pos, m in filtered:
            length = len(m)
            level = "❌ ERROR" if length >= ERROR_LEN else "⚠️ WARN"
            if length >= ERROR_LEN:
                total_errors += 1
            else:
                total_warnings += 1
            display = m[:60] + ("..." if len(m) > 60 else "")
            report.append(f"- {level} ({length}文字): 「{display}」")
        report.append("")

        # H2比較
        if comp_h2s:
            overlap = calc_h2_overlap(article_h2s, comp_h2s)
            mark = "⚠️" if overlap >= H2_OVERLAP_THRESHOLD else "✓"
            report.append(f"- H2並び順一致率: {overlap:.0%} {mark}")
            report.append(f"  - 競合H2: {comp_h2s}")
            report.append("")
            if overlap >= H2_OVERLAP_THRESHOLD:
                total_warnings += 1

    report.append("## 自記事のH2構成")
    report.append("")
    for i, h in enumerate(article_h2s, 1):
        report.append(f"{i}. {h}")
    report.append("")

    report.append("## サマリ")
    report.append("")
    report.append(f"- エラー（20文字以上一致）: {total_errors} 件")
    report.append(f"- 警告（15〜19文字一致 / H2被り）: {total_warnings} 件")
    report.append("")
    if total_errors == 0:
        report.append("✓ 完全一致のエラーはありません")
    else:
        report.append("❌ 書き換えが必要です。エラー箇所を別の表現に変えてください")
    report.append("")

    with open(report_path, "w") as f:
        f.write("\n".join(report))

    print("=" * 60)
    print(color(f"競合チェックレポート: {report_path}", "cyan"))
    print("=" * 60)
    for line in report:
        print(line)
    print()
    if total_errors:
        print(color(f"❌ {total_errors}件のエラー（書き換え必須）", "red"))
        sys.exit(1)
    elif total_warnings:
        print(color(f"⚠️  {total_warnings}件の警告（人間判断）", "yellow"))
    else:
        print(color("✓ 全てクリア", "green"))


if __name__ == "__main__":
    main()
