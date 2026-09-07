#!/usr/bin/env python3
"""
LP→セクション画像自動マッチングスクリプト

記事のMDXファイルを解析し、各セクション(H2/H3)のテキストからキーワードを抽出。
LPをPlaywrightで開き、ページ内テキストをスキャンして最も関連性の高い位置を特定。
その位置を中心にスクショを撮影し、WebPに変換して記事に挿入する。

使い方:
  python3 scripts/lp_to_sections.py <LP_URL> <MDX_PATH> [--extra-urls URL1 URL2]

例:
  python3 scripts/lp_to_sections.py "https://example.com/lp" "src/content/articles/slug.mdx"
  python3 scripts/lp_to_sections.py "https://example.com/lp" "src/content/articles/slug.mdx" --extra-urls "https://example.com/tokushoho"
"""

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field

from playwright.sync_api import sync_playwright


@dataclass
class Section:
    """記事の1セクション"""
    heading: str          # H2/H3見出しテキスト
    level: int            # 2 or 3
    line_num: int         # MDXファイル内の行番号
    text_lines: list = field(default_factory=list)  # セクション内の本文行
    keywords: list = field(default_factory=list)     # 抽出されたキーワード
    image_path: str = ""  # 挿入する画像パス


@dataclass
class LPElement:
    """LP上のテキスト要素"""
    text: str
    y: int
    height: int


def parse_mdx(mdx_path: str) -> list[Section]:
    """MDXファイルからセクションを抽出"""
    with open(mdx_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    sections = []
    current = None
    in_frontmatter = False

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # frontmatterスキップ
        if stripped == "---":
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter:
            continue

        # importスキップ
        if stripped.startswith("import "):
            continue

        # H2/H3検出
        m = re.match(r'^(#{2,3})\s+(.+)$', stripped)
        if m:
            level = len(m.group(1))
            heading = m.group(2).strip()
            current = Section(heading=heading, level=level, line_num=i)
            sections.append(current)
            continue

        # 本文をセクションに追加（コンポーネント行やMarkdown画像行は除外）
        if current and stripped and not stripped.startswith("<") and not stripped.startswith("!") and not stripped.startswith(">") and not stripped.startswith("-"):
            current.text_lines.append(stripped)

    return sections


def extract_keywords(section: Section) -> list[str]:
    """セクションからLP検索用のキーワードを抽出"""
    keywords = []

    # 見出しからキーワード抽出
    heading = section.heading
    # ｜以降を削除
    heading = re.split(r'[｜|]', heading)[0].strip()
    # 「？」等を削除
    heading = re.sub(r'[？?！!]', '', heading)
    keywords.append(heading)

    # 本文から「」で囲まれた固有名詞を抽出
    for line in section.text_lines[:10]:
        quotes = re.findall(r'「([^」]+)」', line)
        for q in quotes:
            if len(q) >= 3 and q not in keywords:
                keywords.append(q)

    # 本文から太字<b>タグの中身を抽出
    for line in section.text_lines[:10]:
        bolds = re.findall(r'<b>([^<]+)</b>', line)
        for b in bolds:
            if b not in keywords:
                keywords.append(b)

    return keywords


def scan_lp_elements(page) -> list[LPElement]:
    """LP上の全テキスト要素をスキャンして位置を取得"""
    raw = page.evaluate("""() => {
        const results = [];
        const all = document.querySelectorAll('*');
        for (const el of all) {
            // テキストノードのみ（子要素を含まない直接テキスト）
            const text = Array.from(el.childNodes)
                .filter(n => n.nodeType === 3)
                .map(n => n.textContent.trim())
                .join(' ')
                .trim();
            if (text.length >= 3) {
                const rect = el.getBoundingClientRect();
                if (rect.top > 0 && rect.height > 0 && rect.height < 800) {
                    results.push({
                        text: text.substring(0, 200),
                        y: Math.round(rect.top + window.scrollY),
                        height: Math.round(rect.height)
                    });
                }
            }
        }
        // 重複除去（同じy座標のものは1つに）
        const seen = new Set();
        return results.filter(r => {
            const key = r.y + ':' + r.text.substring(0, 20);
            if (seen.has(key)) return false;
            seen.add(key);
            return true;
        }).sort((a, b) => a.y - b.y);
    }""")

    return [LPElement(text=r["text"], y=r["y"], height=r["height"]) for r in raw]


def find_best_match(keywords: list[str], elements: list[LPElement], used_ys: set = None) -> int | None:
    """キーワードに最もマッチするLP上の位置(y座標)を返す"""
    if used_ys is None:
        used_ys = set()

    best_score = 0
    best_y = None

    for el in elements:
        # 既に使ったy座標の近辺(±200px)は避ける
        if any(abs(el.y - uy) < 200 for uy in used_ys):
            continue

        score = 0
        for kw in keywords:
            # 完全一致
            if kw in el.text:
                score += len(kw) * 2
            else:
                # キーワードの各単語で部分一致
                words = re.split(r'[のはをがにで・、\s]+', kw)
                for word in words:
                    if len(word) >= 2 and word in el.text:
                        score += len(word)

        if score > best_score:
            best_score = score
            best_y = el.y

    return best_y if best_score > 0 else None


def hide_sticky_headers(page):
    """追従ヘッダー（fixed/sticky）を非表示にする"""
    page.evaluate("""() => {
        document.querySelectorAll('*').forEach(el => {
            const style = getComputedStyle(el);
            if (style.position === 'fixed' || style.position === 'sticky') {
                el.dataset.originalDisplay = el.style.display;
                el.style.display = 'none';
            }
        });
    }""")


def take_screenshot(page, y: int, output_path: str, viewport_height: int = 600):
    """指定Y座標を中心にスクリーンショットを撮影（追従ヘッダー非表示）"""
    hide_sticky_headers(page)
    # 対象要素がビューポートの上部1/3に来るようにスクロール
    scroll_to = max(0, y - viewport_height // 3)
    page.evaluate(f"window.scrollTo(0, {scroll_to})")
    page.wait_for_timeout(300)
    page.screenshot(path=output_path, full_page=False)


def convert_to_webp(png_path: str, webp_path: str, max_width: int = 800):
    """PNG→WebP変換（縦長チェック付き）"""
    from PIL import Image as PILImage
    img = PILImage.open(png_path)
    w, h = img.size

    # 縦長すぎる場合は上部からクロップ
    if h > w * 2:
        old_h = h
        h = w * 2
        img = img.crop((0, 0, w, h))
        img.save(png_path)
        print(f"    ⚠ 縦長クロップ: {w}x{old_h} → {w}x{h}")

    subprocess.run(
        ["cwebp", "-q", "80", png_path, "-o", webp_path],
        capture_output=True
    )

    # サイズチェック
    result_size = os.path.getsize(webp_path) / 1024
    if result_size > 150:
        print(f"    ⚠ {result_size:.0f}KB（150KB推奨）")

    os.remove(png_path)


def insert_images_into_mdx(mdx_path: str, sections: list[Section]):
    """セクションの画像パスをMDXファイルに挿入"""
    with open(mdx_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 挿入位置を逆順で処理（行番号がずれないように）
    insertions = []
    for sec in sections:
        if sec.image_path:
            # H2/H3の直後に画像を挿入
            alt = sec.heading.replace("｜", " ").replace("|", " ")
            img_line = f"\n![{alt}]({sec.image_path})\n\n"
            insertions.append((sec.line_num, img_line))

    # 逆順で挿入
    for line_num, img_line in sorted(insertions, reverse=True):
        lines.insert(line_num, img_line)

    with open(mdx_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def main():
    parser = argparse.ArgumentParser(description="LP→セクション画像自動マッチング")
    parser.add_argument("lp_url", help="メインLPのURL")
    parser.add_argument("mdx_path", help="MDXファイルのパス")
    parser.add_argument("--extra-urls", nargs="*", default=[], help="追加URL（特商法ページ等）")
    parser.add_argument("--output-dir", default="public/images", help="画像出力ディレクトリ")
    parser.add_argument("--dry-run", action="store_true", help="スクショを撮らずにマッチング結果だけ表示")
    args = parser.parse_args()

    # slugをMDXパスから取得
    slug = os.path.splitext(os.path.basename(args.mdx_path))[0]
    os.makedirs(args.output_dir, exist_ok=True)

    # 1. MDX解析
    print("=== MDX解析 ===")
    sections = parse_mdx(args.mdx_path)
    for sec in sections:
        sec.keywords = extract_keywords(sec)
        print(f"  H{sec.level} L{sec.line_num}: {sec.heading}")
        print(f"       KW: {sec.keywords}")

    if args.dry_run:
        return

    # 2. LP読み込み＆テキストスキャン
    print("\n=== LPスキャン ===")
    all_urls = [args.lp_url] + args.extra_urls

    with sync_playwright() as p:
        browser = p.chromium.launch()

        for url_idx, url in enumerate(all_urls):
            print(f"\n--- URL {url_idx+1}: {url[:80]} ---")
            # まず仮のビューポートでLP幅を測定
            ctx = browser.new_context(viewport={"width": 1400, "height": 600}, device_scale_factor=2)
            page = ctx.new_page()

            try:
                page.goto(url, timeout=30000)
                page.wait_for_timeout(4000)
            except Exception as e:
                print(f"  ERROR: {e}")
                ctx.close()
                continue

            # LPのコンテンツ幅を取得してビューポートを合わせる
            content_width = page.evaluate("() => document.querySelector('body').scrollWidth")
            if content_width and content_width != 1400:
                ctx.close()
                vp_width = min(max(content_width, 375), 1400)
                print(f"  コンテンツ幅: {content_width}px → ビューポート: {vp_width}px")
                ctx = browser.new_context(viewport={"width": vp_width, "height": 600}, device_scale_factor=2)
                page = ctx.new_page()
                page.goto(url, timeout=30000)
                page.wait_for_timeout(4000)
            else:
                print(f"  ビューポート: {content_width}px")

            elements = scan_lp_elements(page)
            print(f"  テキスト要素: {len(elements)}個")

            # 3. マッチング＆スクショ
            img_num = len([s for s in sections if s.image_path]) + 1
            used_ys = set()
            for sec in sections:
                if sec.image_path:
                    continue  # 既に別URLでマッチ済み

                best_y = find_best_match(sec.keywords, elements, used_ys)
                if best_y is not None:
                    used_ys.add(best_y)
                    png_path = os.path.join(args.output_dir, f"{slug}-sec{img_num:02d}.png")
                    webp_path = os.path.join(args.output_dir, f"{slug}-sec{img_num:02d}.webp")

                    take_screenshot(page, best_y, png_path)
                    convert_to_webp(png_path, webp_path)

                    sec.image_path = f"/images/{slug}-sec{img_num:02d}.webp"
                    print(f"  ✓ H{sec.level} '{sec.heading[:30]}' → y={best_y} → {sec.image_path}")
                    img_num += 1
                else:
                    print(f"  ✗ H{sec.level} '{sec.heading[:30]}' → マッチなし")

            ctx.close()

        browser.close()

    # 4. MDXに画像挿入
    print("\n=== MDXに画像挿入 ===")
    matched = [s for s in sections if s.image_path]
    unmatched = [s for s in sections if not s.image_path]

    print(f"  マッチ: {len(matched)}/{len(sections)}")
    if unmatched:
        print(f"  未マッチ: {[s.heading[:20] for s in unmatched]}")

    insert_images_into_mdx(args.mdx_path, sections)
    print(f"  画像{len(matched)}枚を挿入しました")

    # 結果をJSONで保存
    result = {
        "slug": slug,
        "sections": [
            {
                "heading": s.heading,
                "level": s.level,
                "keywords": s.keywords,
                "image": s.image_path or None,
            }
            for s in sections
        ]
    }
    result_path = os.path.join(args.output_dir, f"{slug}-mapping.json")
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"  マッピング結果: {result_path}")


if __name__ == "__main__":
    main()
