#!/usr/bin/env python3
"""
アイキャッチ画像自動生成スクリプト

使い方:
  python3 scripts/generate-eyecatch.py <slug> <title> <subtitle> <fv_image_path> [--category toushi]

例:
  python3 scripts/generate-eyecatch.py sns-partners-mocchi "合同会社mocchi" "「SNSPartners」の実態を調査" /tmp/mocchi-fv-mobile.png
  python3 scripts/generate-eyecatch.py kabu-24 "カブ24" "「月利20%」の実態を調査" /tmp/kabu24-fv.png --category toushi

出力:
  public/images/<slug>.webp
"""

import argparse
import os
import subprocess
import sys
import tempfile

TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&display=swap');
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    width: 1200px;
    height: 630px;
    font-family: 'Noto Sans JP', 'Hiragino Kaku Gothic ProN', sans-serif;
    overflow: hidden;
  }}
  .card {{
    width: 1200px;
    height: 630px;
    position: relative;
    overflow: hidden;
    background: #fff8e8;
  }}
  .frame {{
    position: absolute;
    top: 12px; left: 12px; right: 12px; bottom: 12px;
    border: 5px solid #f59e0b;
    border-radius: 12px;
    z-index: 5;
    pointer-events: none;
  }}
  .text-area {{
    position: absolute;
    top: 0; left: 0;
    width: 65%;
    height: 100%;
    padding: 45px 50px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    z-index: 3;
  }}
  .category-label {{
    display: inline-block;
    background: #ef4444;
    color: #fff;
    font-size: 24px;
    font-weight: 900;
    padding: 8px 26px;
    border-radius: 6px;
    margin-bottom: 24px;
    letter-spacing: 0.12em;
    width: fit-content;
  }}
  .main-title {{
    font-size: {title_font_size}px;
    font-weight: 900;
    color: #1a1a1a;
    line-height: 1.2;
    margin-bottom: 22px;
  }}
  .main-title .accent {{
    color: #ef4444;
  }}
  .sub-title {{
    font-size: {subtitle_font_size}px;
    color: #444;
    font-weight: 700;
    line-height: 1.5;
  }}
  .sub-title .quote {{
    color: #ef4444;
    font-weight: 900;
  }}
  .phone-area {{
    position: absolute;
    right: 40px;
    top: 50%;
    transform: translateY(-50%);
    z-index: 4;
  }}
  .phone-frame {{
    width: 240px;
    height: 480px;
    background: #111;
    border-radius: 36px;
    padding: 10px;
    box-shadow: -10px 10px 40px rgba(0,0,0,0.18);
  }}
  .phone-screen {{
    width: 100%;
    height: 100%;
    border-radius: 28px;
    overflow: hidden;
    background: #fff;
  }}
  .phone-screen img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: top center;
    display: block;
  }}
  .lp-label {{
    position: absolute;
    bottom: -32px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(0,0,0,0.6);
    color: #fff;
    font-size: 13px;
    font-weight: 700;
    padding: 4px 14px;
    border-radius: 4px;
    white-space: nowrap;
    z-index: 6;
  }}
  .dot-pattern {{
    position: absolute;
    top: 20px;
    right: 20px;
    width: 400px;
    height: 400px;
    background-image: radial-gradient(circle, #f59e0b 1.5px, transparent 1.5px);
    background-size: 18px 18px;
    opacity: 0.12;
    z-index: 1;
  }}
  .top-line {{
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 6px;
    background: #ef4444;
    z-index: 10;
  }}
</style>
</head>
<body>
  <div class="card">
    <div class="top-line"></div>
    <div class="frame"></div>
    <div class="dot-pattern"></div>
    <div class="text-area">
      <div class="category-label">{category_label}</div>
      <div class="main-title"><span class="accent">{title}</span>の<br>{category_suffix}</div>
      <div class="sub-title"><span class="quote">{subtitle}</span><br>の実態を調査</div>
    </div>
    <div class="phone-area">
      <div class="phone-frame">
        <div class="phone-screen">
          <img src="{fv_image}" alt="LP">
        </div>
      </div>
      <div class="lp-label">{lp_label}</div>
    </div>
  </div>
</body>
</html>"""


def auto_font_size(text: str) -> int:
    """テキスト長に応じてフォントサイズを自動調整"""
    length = len(text)
    if length <= 6:
        return 76
    elif length <= 10:
        return 68
    elif length <= 14:
        return 58
    else:
        return 48


def main():
    parser = argparse.ArgumentParser(description="アイキャッチ画像自動生成")
    parser.add_argument("slug", help="記事のslug")
    parser.add_argument("title", help="商材名・会社名（赤文字部分）")
    parser.add_argument("subtitle", help="サブタイトル（謳い文句、「」で囲む）")
    parser.add_argument("fv_image", help="モバイルFVスクショのパス")
    parser.add_argument("--category", default="fukugyo", choices=["fukugyo", "toushi"],
                        help="カテゴリ（fukugyo or toushi）")
    parser.add_argument("--lp-label", default="▲ 実際の広告ページ",
                        help="スマホ下のラベル文言")
    parser.add_argument("--output-dir", default="public/images",
                        help="出力ディレクトリ")
    args = parser.parse_args()

    # FV画像の存在確認
    fv_path = os.path.abspath(args.fv_image)
    if not os.path.exists(fv_path):
        print(f"ERROR: FV画像が見つかりません: {fv_path}")
        sys.exit(1)

    # カテゴリに応じたテキスト
    if args.category == "fukugyo":
        category_label = "副業検証"
        category_suffix = "副業は安全？"
    else:
        category_label = "投資検証"
        category_suffix = "投資は安全？"

    # フォントサイズ自動調整
    title_font_size = auto_font_size(args.title)
    subtitle_font_size = min(34, 38 - max(0, len(args.subtitle) - 15))

    # HTML生成
    html = TEMPLATE.format(
        title=args.title,
        subtitle=args.subtitle,
        fv_image=fv_path,
        category_label=category_label,
        category_suffix=category_suffix,
        lp_label=args.lp_label,
        title_font_size=title_font_size,
        subtitle_font_size=subtitle_font_size,
    )

    # 一時HTMLファイル
    html_path = os.path.join(tempfile.gettempdir(), f"eyecatch-{args.slug}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    # Playwrightでスクショ
    png_path = os.path.join(tempfile.gettempdir(), f"eyecatch-{args.slug}.png")
    webp_path = os.path.join(args.output_dir, f"{args.slug}.webp")

    print(f"HTML: {html_path}")
    print(f"FV:   {fv_path}")
    print(f"出力: {webp_path}")

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1200, "height": 630})
            page.goto(f"file://{html_path}")
            page.wait_for_timeout(2000)
            page.screenshot(path=png_path)
            browser.close()
    except Exception as e:
        print(f"ERROR: Playwright失敗: {e}")
        sys.exit(1)

    # WebP変換
    result = subprocess.run(
        ["cwebp", "-q", "80", png_path, "-o", webp_path],
        capture_output=True
    )
    if result.returncode != 0:
        print(f"ERROR: cwebp失敗: {result.stderr.decode()}")
        sys.exit(1)

    # サイズ確認
    from PIL import Image
    img = Image.open(webp_path)
    size_kb = os.path.getsize(webp_path) / 1024
    print(f"完了: {img.width}x{img.height} ({size_kb:.0f}KB)")

    # クリーンアップ
    os.remove(png_path)


if __name__ == "__main__":
    main()
