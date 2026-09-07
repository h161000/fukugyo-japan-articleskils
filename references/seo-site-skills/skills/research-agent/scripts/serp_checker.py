#!/usr/bin/env python3
"""
SERP順位チェッカー
指定したキーワードでGoogle検索し、ターゲットドメインの順位を返す。

使い方:
    python3 serp_checker.py "キーワード1" "キーワード2" ...

設定:
    同じディレクトリの serp_config.json で以下を設定:
    - target_domains: チェック対象のドメインリスト
    - serper_api_key: Serper API のAPIキー
    - country: 検索対象の国（デフォルト: jp）
    - language: 検索言語（デフォルト: ja）
"""

import json
import sys
import os
import urllib.request
import urllib.error
import urllib.parse


def load_config():
    """serp_config.json を読み込む"""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "serp_config.json")

    if not os.path.exists(config_path):
        print(f"エラー: 設定ファイルが見つかりません: {config_path}", file=sys.stderr)
        print("serp_config.json を作成してください。", file=sys.stderr)
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    if not config.get("serper_api_key"):
        print("エラー: serper_api_key が設定されていません。", file=sys.stderr)
        print("https://serper.dev/ でAPIキーを取得してください。", file=sys.stderr)
        sys.exit(1)

    return config


def search_google(keyword, api_key, country="jp", language="ja"):
    """Serper API でGoogle検索を実行"""
    url = "https://google.serper.dev/search"

    payload = json.dumps({
        "q": keyword,
        "gl": country,
        "hl": language,
        "num": 10
    }).encode("utf-8")

    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}"}
    except urllib.error.URLError as e:
        return {"error": f"接続エラー: {e.reason}"}
    except Exception as e:
        return {"error": str(e)}


def check_serp(keyword, config):
    """キーワードのSERP順位をチェック"""
    target_domains = config.get("target_domains", [])
    api_key = config["serper_api_key"]
    country = config.get("country", "jp")
    language = config.get("language", "ja")

    result = search_google(keyword, api_key, country, language)

    if "error" in result:
        return {
            "キーワード": keyword,
            "エラー": result["error"],
            "ターゲット順位": [],
            "採用判定": "要確認"
        }

    # オーガニック検索結果からターゲットドメインの順位を抽出
    target_positions = []
    organic_results = result.get("organic", [])

    for i, item in enumerate(organic_results, 1):
        link = item.get("link", "")
        for domain in target_domains:
            if domain in link:
                target_positions.append(i)
                break

    # 採用判定: 1〜3位にターゲットが2つ以上あれば不採用
    top3_count = sum(1 for pos in target_positions if pos <= 3)

    if top3_count >= 2:
        judgment = "不採用"
    elif top3_count <= 1:
        judgment = "採用"
    else:
        judgment = "要確認"

    return {
        "キーワード": keyword,
        "SERP順位": target_positions if target_positions else ["圏外"],
        "採用判定": judgment,
        "上位3件": [
            {"順位": i + 1, "タイトル": item.get("title", ""), "URL": item.get("link", "")}
            for i, item in enumerate(organic_results[:3])
        ]
    }


def main():
    if len(sys.argv) < 2:
        print("使い方: python3 serp_checker.py \"キーワード1\" \"キーワード2\" ...")
        print("例: python3 serp_checker.py \"マネーキャッチ 詐欺\" \"マネーキャッチ 口コミ\"")
        sys.exit(1)

    config = load_config()
    keywords = sys.argv[1:]

    results = []
    for kw in keywords:
        print(f"検索中: {kw}", file=sys.stderr)
        result = check_serp(kw, config)
        results.append(result)

    # 結果をJSON形式で出力
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
