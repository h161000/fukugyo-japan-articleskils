#!/usr/bin/env python3
"""iHub raw-jsonから指定日の未着手執筆予定タスクを選ぶ。"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


DEFAULT_TIMEZONE = "Asia/Tokyo"
TARGET_SITE_ID = "kn79v569bym1h9xbfjy1hfv0px8bh122"


def is_empty(value: object) -> bool:
    return value is None or value == ""


def plan_date_in_timezone(value: object, timezone: ZoneInfo):
    if value is None or value == "":
        return None
    try:
        milliseconds = float(value)
    except (TypeError, ValueError):
        return None
    return datetime.fromtimestamp(milliseconds / 1000, timezone).date()


def select_tasks(data: object, target_date, timezone: ZoneInfo):
    tasks = data.get("tasks", []) if isinstance(data, dict) else []
    matches = []
    for task in tasks:
        if not isinstance(task, dict):
            continue
        if task.get("siteId") != TARGET_SITE_ID:
            continue
        if plan_date_in_timezone(task.get("writePlanDate"), timezone) != target_date:
            continue
        if not is_empty(task.get("articleUrl")):
            continue
        if not is_empty(task.get("writeDoneDate")):
            continue
        matches.append(task)
    return matches


def parse_args():
    parser = argparse.ArgumentParser(
        description="iHub raw-jsonから執筆予定日が一致する未着手タスクを選びます。"
    )
    parser.add_argument("--input", required=True, help="case-info-fetcherのraw-json")
    parser.add_argument("--date", help="対象日 YYYY-MM-DD。省略時は指定TZの当日")
    parser.add_argument("--timezone", default=DEFAULT_TIMEZONE, help="IANAタイムゾーン")
    parser.add_argument("--output", help="結果JSONの保存先。省略時は標準出力")
    parser.add_argument("--all", action="store_true", help="一致した候補を全件出力")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        timezone = ZoneInfo(args.timezone)
    except Exception as exc:
        print(f"エラー: 不正なタイムゾーンです: {args.timezone}: {exc}", file=sys.stderr)
        return 2

    try:
        target_date = (
            datetime.strptime(args.date, "%Y-%m-%d").date()
            if args.date
            else datetime.now(timezone).date()
        )
    except ValueError:
        print("エラー: --dateはYYYY-MM-DDで指定してください", file=sys.stderr)
        return 2

    input_path = Path(args.input)
    try:
        data = json.loads(input_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"エラー: 入力JSONを読めません: {exc}", file=sys.stderr)
        return 2

    matches = select_tasks(data, target_date, timezone)
    if not matches:
        print(
            f"対象なし: {target_date.isoformat()} ({args.timezone}) の未着手タスクはありません",
            file=sys.stderr,
        )
        return 3

    selected = matches if args.all else matches[:1]
    result = {
        "targetDate": target_date.isoformat(),
        "timezone": args.timezone,
        "matchedCount": len(matches),
        "siteId": TARGET_SITE_ID,
        "selectionRule": "副業JAPAN siteId一致・writePlanDate一致・articleUrl空・writeDoneDate空・API順",
        "tasks": selected,
    }
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
