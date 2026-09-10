#!/usr/bin/env python3
"""副業JAPAN固有の文章表現と公開画像キャプションを検査する。"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from pathlib import Path


CAPTION_OPEN = (
    '<p style="font-size: 0.75em; color: #666; text-align: center; '
    'line-height: 1.5; margin-top: 6px;">'
)

BANNED_PHRASES = {
    "一緒に整理できます": "相談案内では『相談できます』。実際の共同確認は文脈に合わせて具体化",
    "口コミは次の3種類に分けて見ます": "調査済みの口コミについて分かったことを伝える表現",
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


def check_structure(text: str, site_root: Path | None = None) -> list[str]:
    """構造上の抜けだけを検出。理由の内容・顔の正しさは別途レビューする。"""
    errors = []
    # コード例のタグ・見出しは本文と数えない。
    body = re.sub(r"^(```|~~~).*?^\1[^\n]*$", "", text, flags=re.M | re.S)
    for match in re.finditer(r"<Balloon\b([^>]*?)>", body, re.S):
        attrs = match.group(1)
        if not re.search(r"\bname\s*=\s*(['\"])フジ\1", attrs):
            continue
        line = body[:match.start()].count("\n") + 1
        if not re.search(r"\bimage\s*=\s*(['\"])/images/fuji\.webp\1", attrs):
            errors.append(f"L{line}: フジのBalloonに image=\"/images/fuji.webp\" を明示してください")
        elif site_root is not None and not (site_root / 'public/images/fuji.webp').is_file():
            errors.append(f"L{line}: フジの顔画像が存在しません: {site_root / 'public/images/fuji.webp'}")
    heads = list(re.finditer(r"^##[ \t]+.+$", body, re.M))
    if len(heads) < 2:
        errors.append("最初の結論と最後のまとめのH2を確認できません")
        return errors
    sections = [body[heads[0].end():heads[1].start()], body[heads[-1].end():]]
    for label, section in zip(['最初の結論', '最後のまとめ'], sections):
        has_list = re.search(r"^\s*(?:[-*+] |\d+[.)] )\S", section, re.M) or re.search(r"<(?:ul|ol)\b[^>]*>.*?<li\b", section, re.S)
        if not has_list:
            errors.append(f"{label}: 判断理由の一覧がありません。根拠に対応するリストを追加し、内容レビューも実施してください")
    return errors


THIRD_PARTY_SITE_NAMES = ("ジョブネットワークセンター", "副レポ")


def check_source_names(text: str) -> list[str]:
    """公開文章の既知名を検出。調査記録やリンク先URLは変更しない。"""
    def blank(match):
        return re.sub(r"[^\n]", " ", match.group(0))
    source = re.sub(r"^[ \t]*(`{3,}|~{3,})[^\n]*\n.*?^[ \t]*\1[^\n]*(?:\n|$)", blank, text, flags=re.M | re.S)
    source = re.sub(r"<!--.*?-->|\{/\*.*?\*/\}", blank, source, flags=re.S)
    errors = []
    for match in re.finditer(r"\S[\s\S]*?(?=\n[ \t]*\n|\Z)", source):
        if match.group(0).startswith(("import ", "export ")):
            continue
        plain = visible_text(match.group(0))
        for name in THIRD_PARTY_SITE_NAMES:
            if name in plain:
                line = source[:match.start()].count("\n") + 1
                errors.append(f"L{line}: 第三者レビューサイト名「{name}」が公開文に残っています。「第三者サイト」等で表記し、実名とURLは調査記録に保持してください")
    return errors


def check_text(text: str) -> list[str]:
    """検査違反を人が修正できるメッセージとして返す。"""
    errors: list[str] = check_source_names(text)
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


# 候補は文脈レビュー用。該当語を自動置換したり、事実の留保を削除したりしない。
WORDING_RULES = {
    "judgment": (
        re.compile(r"(?:段階では|(?:できる|分かる|わかる|納得する|確認する|比較する|比べる)までは|(?:できない|分からない|わからない|比べられない)うちは)[^。！？]{0,120}(?:見送|契約しません|契約せず|おすすめしません|勧めません)"),
        "確認した事実を理由に現在の判断を伝えているか。必要な条件・未確認範囲は残す。",
    ),
    "results": (
        re.compile(r"(?:この記事では|今回は|ここからは|次は|次に|最後に|では)[^。！？]{0,160}(?:確認します|確認していきます|調べます|調べていきます|検証します|検証していきます|確かめておきます|見ていきます|見ておきます)(?:[。！？]|$)"),
        "調査済みなら、これから調べる予告ではなく結果を届ける文にする。読者への確認手順は区別する。",
    ),
    "recommendation": (
        re.compile(r"(?:(?:比べ|比較し|確認し|確かめ|見|考え|判断し|説明してもらい|受け|受けておき|確かめておき|確認しておき|知っておき|避け|見送り|聞いておき)たい(?:ところ(?:です)?|です|ですね)|(?:欲しい|ほしい)ところ(?:です)?|ほしいと思います|よいと思います)[。！？]?$"),
        "筆者の提案・判断を希望形だけで終えず、必要性や行動を明確にする。読者の気持ちは書き換えない。",
    ),
    "consultation": (
        re.compile(r"LINE[^。！？]{0,120}一緒に(?:確認できます|確認します|考えます|整理できます)"),
        "相談できる内容と相談先を直接伝える。実際の共同確認を説明しているなら、その役割を確認する。",
    ),
    "example-context": (
        re.compile(r"なのか[、，][^。！？]{1,140}(?:のか)[。]?$"),
        "比較例を読者が理解できる文として完結させ、後続の説明につなぐ。実際の質問は一律に禁止しない。",
    ),
}
REVIEW_CHECKS = (*WORDING_RULES, "intro-premise", "intro-connection", "source-naming")
REVIEW_SCOPES = ("intro", "headings", "body", "balloons", "consultation", "closing")
GENERIC_REVIEW_NOTES = {"問題なし", "確認済み", "対象外", "なし", "候補なし", "OK", "PASS"}


def wording_fingerprint() -> str:
    """候補検出と正本ルールの変更後は旧判定を使わない。パス自体はハッシュに含めない。"""
    rules = Path(__file__).resolve().parents[1] / "references/fukugyojapan-editorial-rules.md"
    return hashlib.sha256(Path(__file__).read_bytes() + b"\0" + rules.read_bytes()).hexdigest()


def visible_text(raw: str) -> str:
    text = re.sub(r"<[^>]*>", "", raw)
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[*_~]", "", text)
    return html.unescape("".join(line.strip() for line in text.splitlines())).strip()


def wording_blocks(text: str, *, include_quotes: bool = False) -> list[dict]:
    """行番号を維持し、本文・見出し・吹き出しから表示文を抽出する。"""
    def blank(match):
        return re.sub(r"[^\n]", " ", match.group(0))

    source = re.sub(r"\A---[^\n]*\n.*?^---[^\n]*(?:\n|$)", blank, text, flags=re.M | re.S)
    source = re.sub(r"^[ \t]*(`{3,}|~{3,})[^\n]*\n.*?^[ \t]*\1[^\n]*(?:\n|$)", blank, source, flags=re.M | re.S)
    source = re.sub(r"<!--.*?-->|\{/\*.*?\*/\}", blank, source, flags=re.S)
    if not include_quotes:
        source = re.sub(r"<blockquote\b[^>]*>.*?</blockquote>", blank, source, flags=re.S | re.I)
        source = re.sub(r"^[ \t]*>[^\n]*(?:\n|$)", blank, source, flags=re.M)
    source = re.sub(r"`+[^`\n]*`+", blank, source)
    blocks = []
    for match in re.finditer(r"\S[\s\S]*?(?=\n[ \t]*\n|\Z)", source):
        raw = match.group(0)
        if raw.startswith(("import ", "export ", "![")):
            continue
        if re.match(r'<p\b[^>]*font-size:\s*0\.75em', raw):
            continue  # 証拠画像の短い説明は筆者の判断・相談案内ではない。
        plain = visible_text(raw)
        if plain:
            blocks.append({"line": source[:match.start()].count("\n") + 1, "text": plain})
    return blocks


def wording_candidates(text: str) -> list[dict]:
    blocks = wording_blocks(text)
    candidates = []
    for index, block in enumerate(blocks):
        # 引用された広告・読者の発言自体には筆者の文体規則を適用しない。
        scan = re.sub(r"「[^」]*」|『[^』]*』", "", block["text"]).strip()
        for rule, (pattern, advice) in WORDING_RULES.items():
            if not pattern.search(scan):
                continue
            key = f"{rule}\0{block['line']}\0{block['text']}"
            candidates.append({
                "id": hashlib.sha256(key.encode()).hexdigest()[:16],
                "rule": rule, **block, "advice": advice,
                "before": [b["text"] for b in blocks[max(0, index - 2):index]],
                "after": [b["text"] for b in blocks[index + 1:index + 3]],
            })
    return candidates


def intro_context(text: str) -> list[dict]:
    """導入を引用符で除外せず収録。前提・後続文の意味は担当者が判断する。"""
    def blank(match):
        return re.sub(r"[^\n]", " ", match.group(0))
    # 除外部分も文字位置を保持し、本文最初のH2だけで区切る。
    source = re.sub(r"\A---[^\n]*\n.*?^---[^\n]*(?:\n|$)", blank, text, flags=re.M | re.S)
    source = re.sub(r"^[ \t]*(`{3,}|~{3,})[^\n]*\n.*?^[ \t]*\1[^\n]*(?:\n|$)", blank, source, flags=re.M | re.S)
    source = re.sub(r"<!--.*?-->|\{/\*.*?\*/\}", blank, source, flags=re.S)
    heading = re.search(r"^##[ \t]+", source, flags=re.M)
    return wording_blocks(text[:heading.start()] if heading else text, include_quotes=True)


def make_wording_review(text: str) -> dict:
    """未判定の雛形だけを生成する。候補0件でも全文の意味確認は別途必要。"""
    return {
        "schema_version": 2,
        "intro_context": intro_context(text),
        "article_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "rules_sha256": wording_fingerprint(),
        "candidates": [dict(c, decision="pending", reason="") for c in wording_candidates(text)],
        "changes": [],
        "full_text_review": {
            "scopes": [],
            "checks": {rule: {"status": "pending", "detail": ""} for rule in REVIEW_CHECKS},
        },
    }


def validate_wording_review(text: str, review: dict) -> list[str]:
    errors = check_source_names(text)
    if not isinstance(review, dict) or review.get("schema_version") != 2:
        return errors + ["文章表現レビューのschema_versionが不正です。現行の雛形で再確認してください"]
    if review.get("intro_context") != intro_context(text):
        errors.append("導入全文の記録が現行原稿と一致しません。カギ括弧内も含めて再確認してください")
    if review.get("article_sha256") != hashlib.sha256(text.encode()).hexdigest():
        errors.append("原稿がレビュー後に変更されています。最新原稿を再確認してください")
    if review.get("rules_sha256") != wording_fingerprint():
        errors.append("文章ルールまたは検出器が変更されています。現行ルールで再確認してください")
    actual = {c["id"]: c for c in wording_candidates(text)}
    records = review.get("candidates")
    if not isinstance(records, list) or not all(isinstance(c, dict) for c in records):
        return errors + ["candidatesは候補ごとの判定を含む配列にしてください"]
    ids = [c.get("id") for c in records]
    if len(set(str(i) for i in ids)) != len(ids) or set(str(i) for i in ids) != set(actual):
        errors.append("最新原稿の候補と判定記録が一致しません（候補の削除・重複・旧記録を確認）")
    for record in records:
        candidate = actual.get(str(record.get("id")))
        if candidate is None:
            continue
        if any(record.get(k) != candidate[k] for k in ("rule", "line", "text")):
            errors.append(f"{candidate['id']}: 候補の本文・位置が一致しません")
        reason = record.get("reason")
        if record.get("decision") != "retain" or not isinstance(reason, str) or not reason.strip() or reason.strip() in GENERIC_REVIEW_NOTES:
            errors.append(f"L{candidate['line']}: 未判断の候補です。修正するか、残す具体的な理由を記録してください")
    full = review.get("full_text_review", {})
    if not isinstance(full, dict):
        return errors + ["full_text_reviewがありません"]
    scopes = full.get("scopes", [])
    if not isinstance(scopes, list) or set(str(v) for v in scopes) != set(REVIEW_SCOPES):
        errors.append("導入・見出し・本文・吹き出し・相談案内・締めの全文確認が未完了です")
    checks = full.get("checks", {})
    if not isinstance(checks, dict):
        return errors + ["全文確認のchecksがありません"]
    for rule in REVIEW_CHECKS:
        check = checks.get(rule, {})
        if not isinstance(check, dict):
            errors.append(f"{rule}: 全文確認の記録が不正です")
            continue
        detail = check.get("detail")
        if check.get("status") != "pass" or not isinstance(detail, str) or not detail.strip() or detail.strip() in GENERIC_REVIEW_NOTES:
            errors.append(f"{rule}: 具体的な該当文と判断理由を含む全文確認が必要です")
    changes = review.get("changes", [])
    if not isinstance(changes, list):
        return errors + ["changesは修正前後と理由の配列にしてください"]
    rendered = "\n".join(b["text"] for b in wording_blocks(text))
    for change in changes:
        if not isinstance(change, dict) or not all(isinstance(change.get(k), str) and change[k].strip() for k in ("before", "after", "reason")):
            errors.append("修正した候補にはbefore・after・reasonを記録してください")
        elif change["before"] == change["after"] or visible_text(change["after"]) not in rendered:
            errors.append("修正後の文が現行原稿と一致しません")
    return errors


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("article", type=Path)
    parser.add_argument("site_root", nargs="?", type=Path, default=Path("/Users/hirototakada/SEO/fukugyojapan"))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--review-output", type=Path, help="未判定の文章レビューJSONを新規作成（既存ファイルは上書きしない）")
    mode.add_argument("--review", type=Path, help="現行原稿に対応した文章レビューJSONを検証する")
    args = parser.parse_args(argv[1:])
    try:
        text = args.article.read_bytes().decode("utf-8")
        errors = check_text(text) + check_structure(text, args.site_root)
        candidates = wording_candidates(text)
        print(f"=== 副業JAPAN文章・キャプションチェック: {args.article} ===")
        for c in candidates:
            print(f"  REVIEW L{c['line']} [{c['rule']}] {c['text']}")
            print("    前: " + " / ".join(c["before"]))
            print("    後: " + " / ".join(c["after"]))
            print("    判断点: " + c["advice"])
        if args.review_output:
            args.review_output.parent.mkdir(parents=True, exist_ok=True)
            with args.review_output.open("x", encoding="utf-8") as target:
                json.dump(make_wording_review(text), target, ensure_ascii=False, indent=2)
                target.write("\n")
            print(f"未判定のレビュー雛形を作成: {args.review_output}")
            errors.append("文章表現の横断レビューは未実施です。判定を記録して --review で再確認してください")
        elif args.review:
            errors.extend(validate_wording_review(text, json.loads(args.review.read_text(encoding="utf-8"))))
        elif candidates:
            errors.append(f"文章表現の見直し候補が{len(candidates)}件あります。修正または --review による文脈判定が必要です")
        for error in errors:
            print(f"  ❌ {error}")
        if errors:
            print(f"FAIL: {len(errors)}件の修正・確認が必要です")
            return 1
        print("PASS: 機械検査に適合。意味判断の正しさを保証するものではありません。")
        if not args.review:
            print("NOTE: 候補0件でも、納品前に文章表現の横断レビューを別途記録してください。")
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
