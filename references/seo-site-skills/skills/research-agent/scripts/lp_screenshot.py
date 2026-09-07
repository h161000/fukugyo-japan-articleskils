#!/usr/bin/env python3
"""
LP スクリーンショット自動撮影ツール

LPのURLを渡すと、自動的に以下のスクショを撮影して保存する:
1. ページ全体の長いスクショ（フルページ）
2. ファーストビュー（最初に見える画面）
3. ページをスクロールしながらセクションごとのスクショ
4. 特商法ページが見つかれば自動的にそちらもスクショ

使い方:
    python3 lp_screenshot.py <URL> [保存先フォルダ]

例:
    python3 lp_screenshot.py "https://example.com/lp" ./screenshots
    python3 lp_screenshot.py "https://example.com/lp"  ← カレントディレクトリに保存

初回セットアップ（1回だけ）:
    pip install playwright
    playwright install chromium
"""

import sys
import os
import re
import json
import asyncio
from datetime import datetime
from urllib.parse import urljoin, urlparse

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("エラー: playwright がインストールされていません。")
    print("")
    print("以下のコマンドでセットアップしてください（初回のみ）:")
    print("  pip install playwright")
    print("  playwright install chromium")
    sys.exit(1)


async def find_tokushoho_link(page):
    """ページ内から特商法ページへのリンクを探す"""
    keywords = [
        "特定商取引", "特商法", "tokushoho", "tokutei",
        "特定商取引法に基づく表記", "特定商取引法に基づく表示",
        "特定商", "特商"
    ]

    links = await page.query_selector_all("a")
    for link in links:
        try:
            text = await link.text_content()
            href = await link.get_attribute("href")
            if text and href:
                text_lower = text.lower().strip()
                for kw in keywords:
                    if kw in text_lower or kw in text:
                        full_url = urljoin(page.url, href)
                        return full_url
        except Exception:
            continue
    return None


async def take_screenshots(url, output_dir):
    """LPのスクリーンショットを撮影する"""

    # 保存先フォルダの作成
    os.makedirs(output_dir, exist_ok=True)

    # 撮影結果の記録
    results = {
        "url": url,
        "撮影日時": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "保存先": os.path.abspath(output_dir),
        "撮影した画像": []
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            locale="ja-JP",
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        print(f"📸 ページを読み込み中: {url}")

        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
        except Exception as e:
            print(f"⚠️  ページの読み込みに時間がかかっています: {e}")
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            except Exception:
                print(f"❌ ページを開けませんでした: {url}")
                await browser.close()
                return results

        # 少し待ってから撮影（画像の遅延読み込み対策）
        await page.wait_for_timeout(2000)

        # ===== 1. フルページスクショ =====
        fullpage_path = os.path.join(output_dir, "01_fullpage.png")
        try:
            await page.screenshot(path=fullpage_path, full_page=True)
            results["撮影した画像"].append({
                "ファイル名": "01_fullpage.png",
                "説明": "LP全体のフルページスクリーンショット",
                "用途": "全体把握用"
            })
            print(f"  ✅ フルページ: {fullpage_path}")
        except Exception as e:
            print(f"  ⚠️  フルページスクショ失敗: {e}")

        # ===== 2. ファーストビュー =====
        firstview_path = os.path.join(output_dir, "02_firstview.png")
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(500)
        await page.screenshot(path=firstview_path)
        results["撮影した画像"].append({
            "ファイル名": "02_firstview.png",
            "説明": "ファーストビュー（最初に見える画面）",
            "用途": "記事の導入部分に使用"
        })
        print(f"  ✅ ファーストビュー: {firstview_path}")

        # ===== 3. スクロールしながらセクションごとのスクショ =====
        page_height = await page.evaluate("document.body.scrollHeight")
        viewport_height = 800
        scroll_positions = []

        # スクロール位置を計算（70%ずつスクロール = 少し重複させる）
        current = 0
        while current < page_height:
            scroll_positions.append(current)
            current += int(viewport_height * 0.7)

        print(f"  📜 ページの高さ: {page_height}px → {len(scroll_positions)}セクションに分割")

        for i, pos in enumerate(scroll_positions):
            section_path = os.path.join(output_dir, f"03_section_{i+1:02d}.png")
            await page.evaluate(f"window.scrollTo(0, {pos})")
            await page.wait_for_timeout(500)
            await page.screenshot(path=section_path)
            results["撮影した画像"].append({
                "ファイル名": f"03_section_{i+1:02d}.png",
                "説明": f"セクション {i+1}（上から {pos}px〜{pos+viewport_height}px）",
                "用途": "記事内の各ポイント解説に使用"
            })

        print(f"  ✅ セクション別: {len(scroll_positions)}枚撮影完了")

        # ===== 4. 特商法ページの撮影 =====
        tokushoho_url = await find_tokushoho_link(page)

        if tokushoho_url:
            print(f"  🔍 特商法ページ発見: {tokushoho_url}")
            try:
                await page.goto(tokushoho_url, wait_until="networkidle", timeout=15000)
                await page.wait_for_timeout(1000)

                # 特商法ページのフルスクショ
                toku_fullpage_path = os.path.join(output_dir, "04_tokushoho_full.png")
                await page.screenshot(path=toku_fullpage_path, full_page=True)
                results["撮影した画像"].append({
                    "ファイル名": "04_tokushoho_full.png",
                    "説明": "特定商取引法に基づく表記（フルページ）",
                    "用途": "特商法の検証に使用"
                })

                # 特商法ページのファーストビュー
                await page.evaluate("window.scrollTo(0, 0)")
                toku_view_path = os.path.join(output_dir, "04_tokushoho_view.png")
                await page.screenshot(path=toku_view_path)
                results["撮影した画像"].append({
                    "ファイル名": "04_tokushoho_view.png",
                    "説明": "特定商取引法に基づく表記（上部）",
                    "用途": "特商法の検証に使用"
                })
                results["特商法ページURL"] = tokushoho_url

                print(f"  ✅ 特商法ページ: 2枚撮影完了")
            except Exception as e:
                print(f"  ⚠️  特商法ページの撮影失敗: {e}")
        else:
            print("  ℹ️  特商法ページへのリンクが見つかりませんでした")
            results["特商法ページURL"] = None

        # ===== 5. スマホ版のスクショ =====
        print("  📱 スマホ版を撮影中...")
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.set_viewport_size({"width": 375, "height": 812})
        await page.wait_for_timeout(1000)

        # スマホ版ファーストビュー
        await page.evaluate("window.scrollTo(0, 0)")
        mobile_path = os.path.join(output_dir, "05_mobile_firstview.png")
        await page.screenshot(path=mobile_path)
        results["撮影した画像"].append({
            "ファイル名": "05_mobile_firstview.png",
            "説明": "スマホ版のファーストビュー（375px幅）",
            "用途": "スマホでの見え方の参考"
        })

        # スマホ版フルページ
        mobile_full_path = os.path.join(output_dir, "05_mobile_fullpage.png")
        await page.screenshot(path=mobile_full_path, full_page=True)
        results["撮影した画像"].append({
            "ファイル名": "05_mobile_fullpage.png",
            "説明": "スマホ版のフルページ",
            "用途": "スマホでの見え方の参考"
        })
        print(f"  ✅ スマホ版: 2枚撮影完了")

        await browser.close()

    # ===== 結果をJSONで保存 =====
    results_path = os.path.join(output_dir, "screenshot_info.json")
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    total = len(results["撮影した画像"])
    print(f"\n🎉 撮影完了！合計 {total} 枚")
    print(f"📁 保存先: {os.path.abspath(output_dir)}")
    print(f"📋 撮影情報: {results_path}")

    return results


def main():
    if len(sys.argv) < 2:
        print("LP スクリーンショット自動撮影ツール")
        print("")
        print("使い方:")
        print('  python3 lp_screenshot.py <URL> [保存先フォルダ]')
        print("")
        print("例:")
        print('  python3 lp_screenshot.py "https://example.com/lp" ./screenshots')
        print('  python3 lp_screenshot.py "https://example.com/lp"')
        print("")
        print("初回セットアップ:")
        print("  pip install playwright")
        print("  playwright install chromium")
        sys.exit(1)

    url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./screenshots"

    # URLにプロトコルがなければ追加
    if not url.startswith("http"):
        url = "https://" + url

    # フォルダ名をURLから生成（指定がない場合）
    if output_dir == "./screenshots":
        domain = urlparse(url).netloc.replace(".", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"./screenshots/{domain}_{timestamp}"

    asyncio.run(take_screenshots(url, output_dir))


if __name__ == "__main__":
    main()
