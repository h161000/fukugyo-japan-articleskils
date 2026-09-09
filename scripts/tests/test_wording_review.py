"""ユーザーの修正意図・引用の保全・未確認レビューの納品防止を検証する。"""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'check_fukugyojapan_editorial.py'
spec = importlib.util.spec_from_file_location('wording_editorial', SCRIPT)
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)


def reviewed(text):
    report = e.make_wording_review(text)
    report['full_text_review']['scopes'] = list(e.REVIEW_SCOPES)
    for rule, check in report['full_text_review']['checks'].items():
        check.update(status='pass', detail=f'{rule}: 「{e.wording_blocks(text)[0]["text"]}」を含む本文を照合し、事実の留保と筆者の判断を区別した。')
    return report


class CandidateTests(unittest.TestCase):
    def test_actual_requested_revisions(self):
        cases = [
            ('私なら、報酬の条件と支援に払う総額を比べられない段階では、有料契約を見送ります。',
             '私なら、報酬の条件と支援に払う総額を比べられないので、有料契約を見送ります。', 'judgment'),
            ('払う総額と受けられる支援を比較できるまでは、有料契約を見送ります。',
             '払う総額と受けられる支援を比較できないので、有料契約は見送ります。', 'judgment'),
            ('この記事では、届いた仕事内容やアンケート、料金と口コミ、運営会社、解約の条件を確認します。',
             'この記事では、調べて分かった料金や解約条件をお伝えします。', 'results'),
            ('有料支援は、金額だけでなく期間や対応内容までそろえて比べたいところ。',
             '有料支援は、金額だけでなく、期間や対応内容も含めて比較する必要があります。', 'recommendation'),
            ('案内を受けて迷っている方は、どの説明に不安を感じたのか、私のLINEでも一緒に確認できます。',
             '案内を受けて迷っている方は、どの説明に不安を感じたのか、私のLINEで相談できます。', 'consultation'),
            ('テンプレートを受け取るだけなのか、実際の投稿を見て改善点を教えてくれるのか。',
             'たとえば、投稿文のテンプレートを渡すだけの支援もあれば、投稿の改善点まで教える支援もあります。', 'example-context'),
        ]
        for before, after, rule in cases:
            with self.subTest(rule=rule, before=before):
                self.assertIn(rule, {c['rule'] for c in e.wording_candidates(before)})
                self.assertEqual(e.wording_candidates(after), [])

    def test_synonyms_and_article_wide_occurrences(self):
        body = '''## 結論
私なら、必要な支援と支払額を比べられないうちは、契約せずに説明を持ち帰ります。

## 料金
個々の質問への説明も欲しいところ。

<Balloon name="フジ">
私のLINEでは、あなたの状況から一緒に考えます。
</Balloon>

## まとめ
最後に、契約後にやめたくなった場合の条件を確かめておきます。'''
        self.assertEqual({c['rule'] for c in e.wording_candidates(body)}, {'judgment', 'recommendation', 'consultation', 'results'})

    def test_multiline_markup_context_and_original_line(self):
        body = '''前の説明です。

案内を受けた方は、<span
 style="color: blue;">私のLINEでも<strong>一緒に確認</strong>できます。</span>

どこまで進んだかを教えてください。'''
        c = e.wording_candidates(body)[0]
        self.assertEqual(c['line'], 3)
        self.assertIn('私のLINEでも一緒に確認できます。', c['text'])
        self.assertEqual(c['before'], ['前の説明です。'])
        self.assertEqual(c['after'], ['どこまで進んだかを教えてください。'])

    def test_preserves_uncertainty_reader_wishes_and_questions(self):
        samples = [
            '現在の資料では料金を確認できません。',
            'すべての申込者に同じ案内が届くとまでは言えません。',
            '返金の可否は契約条件によって異なります。',
            '副業を始めたいです。',
            '始めたい気持ちがあっても、その日に決める必要はありません。',
            '「無料説明のあとにいくらかかるの？」',
            '1件800円なら、13件で1万円を超えます。',
            '料金は、契約前に確認してください。',
            '法人番号の指定日は2025年2月10日。',
            '問い合わせる方法を、一緒に確認しましょう。',
        ]
        for text in samples:
            with self.subTest(text=text):
                self.assertEqual(e.wording_candidates(text), [])

    def test_does_not_apply_author_rules_to_quotes_code_or_metadata(self):
        text = '''---
description: "この記事では料金を確認します。"
---

> 「有料支援は比べたいところ」と投稿されています。

<blockquote>
私のLINEでも一緒に確認できます。
</blockquote>

```mdx
この記事では条件を確認します。
```

<!-- 期間も比較したいところ。 -->

広告には「LINEで一緒に確認できます」とあります。

<a title="この記事では確認します。" href="/example/">公式の説明</a>

`私のLINEでも一緒に確認できます。`

![料金は比べたいところ](/images/example.webp)
'''
        self.assertEqual(e.wording_candidates(text), [])

    def test_each_repeated_occurrence_has_its_own_decision(self):
        text = '\n\n'.join(['## 結論', '私のLINEでも一緒に確認できます。', '## まとめ', '私のLINEでも一緒に確認できます。'])
        candidates = e.wording_candidates(text)
        self.assertEqual(len(candidates), 2)
        self.assertNotEqual(candidates[0]['id'], candidates[1]['id'])
        report = reviewed(text)
        report['candidates'][0].update(decision='retain', reason='この段落は相談入口ではなく、利用者と確認する手順の説明。')
        self.assertTrue(e.validate_wording_review(text, report))


class ReviewTests(unittest.TestCase):
    def test_no_candidates_does_not_mean_review_complete(self):
        text = '現在の料金は確認できません。'
        self.assertTrue(e.validate_wording_review(text, e.make_wording_review(text)))
        self.assertEqual(e.validate_wording_review(text, reviewed(text)), [])

    def test_legitimate_condition_can_be_retained_with_reason(self):
        text = '私なら、契約条件を確認できるまでは契約しません。'
        report = reviewed(text)
        self.assertTrue(e.validate_wording_review(text, report))
        report['candidates'][0].update(decision='retain', reason='今後受け取る契約書の確認前には同意しないという行動条件を説明しており、調査済みの結論を先送りする文ではない。')
        self.assertEqual(e.validate_wording_review(text, report), [])

    def test_unresolved_candidate_cannot_be_deleted_or_marked_fixed(self):
        text = '私のLINEでも一緒に確認できます。'
        original = reviewed(text)
        for mutation in ('delete', 'fixed', 'generic', 'duplicate'):
            with self.subTest(mutation=mutation):
                report = copy.deepcopy(original)
                if mutation == 'delete': report['candidates'] = []
                elif mutation == 'fixed': report['candidates'][0].update(decision='revised', reason='修正しました')
                elif mutation == 'generic': report['candidates'][0].update(decision='retain', reason='問題なし')
                else: report['candidates'] *= 2
                self.assertTrue(e.validate_wording_review(text, report))

    def test_review_is_invalidated_by_article_or_rule_changes(self):
        text = '料金は公開されていません。'
        report = reviewed(text)
        self.assertTrue(e.validate_wording_review(text + '\n新しい説明です。', report))
        report['rules_sha256'] = 'old rules'
        self.assertTrue(e.validate_wording_review(text, report))

    def test_before_after_must_match_current_article(self):
        text = '有料支援は、期間や内容も含めて比較する必要があります。'
        report = reviewed(text)
        report['changes'] = [{'before': '有料支援は、期間や内容も比べたいところ。', 'after': text, 'reason': '必要な比較を希望形で終えず、必要性を伝える。'}]
        self.assertEqual(e.validate_wording_review(text, report), [])
        report['changes'][0]['after'] = '原稿にない修正結果です。'
        self.assertTrue(e.validate_wording_review(text, report))

    def test_missing_full_text_scope_or_empty_reason_blocks_completion(self):
        text = '料金は公開されていません。'
        report = reviewed(text)
        report['full_text_review']['scopes'].remove('balloons')
        self.assertTrue(e.validate_wording_review(text, report))
        report = reviewed(text)
        report['full_text_review']['checks']['results']['detail'] = '問題なし'
        self.assertTrue(e.validate_wording_review(text, report))

    def test_cli_review_round_trip_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            article = root / 'sample.mdx'
            report = root / 'editorial-review.json'
            text = '## 結論\n- 総額が不明\n\n費用が不明なので契約は見送ります。\n\n## まとめ\n- 総額が不明\n'
            article.write_text(text)
            command = [sys.executable, str(SCRIPT), str(article), str(root)]
            initial = subprocess.run(command + ['--review-output', str(report)], capture_output=True, text=True)
            self.assertEqual(initial.returncode, 1)
            self.assertTrue(report.exists())
            report.write_text(json.dumps(reviewed(text), ensure_ascii=False))
            good = subprocess.run(command + ['--review', str(report)], capture_output=True, text=True)
            self.assertEqual(good.returncode, 0, good.stdout + good.stderr)
            saved = report.read_bytes()
            overwrite = subprocess.run(command + ['--review-output', str(report)], capture_output=True, text=True)
            self.assertEqual(overwrite.returncode, 1)
            self.assertEqual(report.read_bytes(), saved)
            article.write_text(text + '\n補足しました。\n')
            stale = subprocess.run(command + ['--review', str(report)], capture_output=True, text=True)
            self.assertEqual(stale.returncode, 1)


if __name__ == '__main__':
    unittest.main()
