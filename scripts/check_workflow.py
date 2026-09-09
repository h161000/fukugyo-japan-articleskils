#!/usr/bin/env python3
"""Validate recorded workflow evidence; does not attest model comprehension."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / 'references/workflow-manifest.json').read_text())
EDITORIAL_SPEC = importlib.util.spec_from_file_location('workflow_editorial', ROOT / 'scripts/check_fukugyojapan_editorial.py')
EDITORIAL = importlib.util.module_from_spec(EDITORIAL_SPEC)
EDITORIAL_SPEC.loader.exec_module(EDITORIAL)

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def absolute(path):
    p = Path(path)
    return p if p.is_absolute() else ROOT / p

def timestamp(value):
    t = datetime.fromisoformat(value)
    if t.tzinfo is None:
        raise ValueError('日時にはタイムゾーンが必要です')
    return t

def validate(state, stage, mode):
    errors = []
    def require(ok, message):
        if not ok:
            errors.append(message)
    require(state['schema_version'] == 1, 'schema_versionが不正')
    require(state['scope'] in ('create', 'publish'), 'scopeが不正')
    require(bool(state['request'].strip()), '依頼原文が空')
    require(state['site_id'] == 'kn79v569bym1h9xbfjy1hfv0px8bh122', 'サイトID不一致')
    created = timestamp(state['created_at'])
    now = datetime.now(timezone.utc)
    require(created <= now, '作成日時が未来')
    order = list(MANIFEST)
    require(stage != 'publish' or state['scope'] == 'publish', '公開が依頼範囲外')
    work = Path(state['articlework'])
    require(work.is_absolute() and work.name == state['slug'], '作業場所とslugが不一致')
    require(bool(state['case_id']), 'case_idが未確定')
    for name in order[:order.index(stage) + 1]:
        spec, item = MANIFEST[name], state['stages'][name]
        finished = name != stage or mode == 'complete'
        start = timestamp(item['started_at']) if item.get('started_at') else now
        if finished:
            require(item['status'] == 'complete', f'{name}: 未完了')
            require(bool(item.get('started_at')), f'{name}: 開始日時なし')
            end = timestamp(item['completed_at'])
            require(created <= start <= end <= now, f'{name}: 日時の順序不正')
        require(not item['unresolved'], f'{name}: 未解決事項あり')
        records = item['reads']
        paths = [x['path'] for x in records]
        for path in spec['reads']:
            require(str(absolute(path)) in paths, f'{name}: 必読資料未登録 {path}')
        for rec in records:
            p = Path(rec['path'])
            require(p.is_absolute() and p.is_file(), f'{name}: 資料なし {p}')
            if p.is_file():
                require(rec['sha256'] == digest(p), f'{name}: 資料変更/未読 {p}')
            require(bool(rec['applied_rule'].strip()), f'{name}: 適用要件なし {p}')
            read_at = timestamp(rec['read_at'])
            require(created <= read_at <= start, f'{name}: 工程開始前の読了記録なし {p}')
        if not finished:
            continue
        for rel in spec['outputs']:
            p = work / rel.format(slug=state['slug'])
            require(p.is_file() and p.stat().st_size > 0, f'{name}: 成果物なし {p}')
        for check in spec['checks']:
            rec = item['checks'].get(check, {})
            require(rec.get('status') == 'pass', f'{name}/{check}: 検査未完了')
            require(bool(rec.get('detail', '').strip()), f'{name}/{check}: 判断理由なし')
            p = Path(rec.get('evidence', ''))
            require(p.is_absolute() and p.is_file(), f'{name}/{check}: 証跡ファイルなし')
            if p.is_file():
                require(p.stat().st_size > 0 and rec.get('sha256') == digest(p), f'{name}/{check}: 証跡空/更新後の再確認なし')
        if name == 'review':
            review_path = work / 'editorial-review.json'
            rec = item['checks'].get('wording-review', {})
            require(rec.get('evidence') == str(review_path), 'review/wording-review: 専用JSONを証跡にしてください')
            try:
                article_text = (work / 'article-draft.mdx').read_bytes().decode('utf-8')
                wording_review = json.loads(review_path.read_text())
                errors.extend('review/wording-review: ' + message for message in EDITORIAL.validate_wording_review(article_text, wording_review))
            except (OSError, ValueError, TypeError, KeyError) as exc:
                errors.append(f'review/wording-review: 証跡を検証できません: {exc}')
        for ex in item.get('exceptions', []):
            require(all(ex.get(k) for k in ('rule_source', 'reason', 'replacement_check')), f'{name}: 適用除外の根拠不足')
            require(item['checks'].get(ex.get('replacement_check'), {}).get('status') == 'pass', f'{name}: 代替検査未完了')
    return errors

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['init', 'ready', 'complete'])
    parser.add_argument('state', type=Path)
    parser.add_argument('--stage', choices=list(MANIFEST))
    parser.add_argument('--slug')
    parser.add_argument('--case-id', default='pending')
    parser.add_argument('--scope', choices=['create', 'publish'], default='create')
    parser.add_argument('--request', default='')
    args = parser.parse_args()
    try:
        if args.mode == 'init':
            if not args.slug or not args.request or args.state.parent.name != args.slug:
                raise ValueError('initには作業フォルダ名と一致する--slugと--requestが必要')
            data = dict(schema_version=1, slug=args.slug, case_id=args.case_id,
                        site_id='kn79v569bym1h9xbfjy1hfv0px8bh122', scope=args.scope,
                        request=args.request, created_at=datetime.now(timezone.utc).isoformat(),
                        articlework=str(args.state.parent.resolve()), stages={})
            for name, spec in MANIFEST.items():
                data['stages'][name] = dict(status='pending', started_at=None, completed_at=None,
                    reads=[dict(path=str(absolute(p)), sha256='', read_at='', applied_rule='') for p in spec['reads']],
                    checks={}, unresolved=[], exceptions=[])
            args.state.parent.mkdir(parents=True, exist_ok=True)
            with args.state.open('x') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.write('\n')
            print('INITIALIZED: 読了・実施記録は未入力です')
            return 0
        if not args.stage:
            raise ValueError('--stageが必要')
        data = json.loads(args.state.read_text())
        if args.stage != 'intake' or args.mode == 'complete':
            if data.get('case_id') == 'pending':
                raise ValueError('案件が未確定です')
        errors = validate(data, args.stage, args.mode)
        for err in errors:
            print('FAIL:', err)
        if not errors:
            print('PASS: 記録と実ファイルの整合を確認。理解・内容品質の保証ではありません。')
        return int(bool(errors))
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        print('FAIL:', exc)
        return 1

if __name__ == '__main__':
    sys.exit(main())
