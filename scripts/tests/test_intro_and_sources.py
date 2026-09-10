"""今回の導入修正と第三者サイト表記を再確認するための回帰検査。"""
import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('editorial_new', Path(__file__).resolve().parents[1] / 'check_fukugyojapan_editorial.py')
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)

BEFORE = '「無料体験で資金が増えたなら、月額費用を払っても続ける価値があるのかな？」'
AFTER = '「AIFAって、<strong>どんな仕組みでお金が増えるの？</strong>　始めるのに費用はかかるのかな？」'
FOLLOWING = 'AIFAは、競馬の自動売買を案内するサービスです。利用には月額費用がかかります。'


def completed(text):
    report = e.make_wording_review(text)
    report['full_text_review']['scopes'] = list(e.REVIEW_SCOPES)
    for key, value in report['full_text_review']['checks'].items():
        value.update(status='pass', detail=f'{key}: 疑問「どんな仕組みでお金が増えるの？」に、後続文「競馬の自動売買を案内するサービス」が仕組みを説明する。体験済みの前提はない。')
    return report


class IntroAndSourcesTests(unittest.TestCase):
    def test_both_actual_questions_are_recorded_with_following_paragraph(self):
        for question in (BEFORE, AFTER):
            text = question + '\n\n' + FOLLOWING + '\n\n## 結論\n\n結論の本文。'
            with self.subTest(question=question):
                report = e.make_wording_review(text)
                self.assertEqual([b['text'] for b in report['intro_context']], [e.visible_text(question), FOLLOWING])
                # 正規表現の候補0件でも、導入の意味確認は未完了。
                self.assertEqual(report['candidates'], [])
                self.assertTrue(e.validate_wording_review(text, report))

    def test_missing_added_checks_blocks_completion(self):
        text = AFTER + '\n\n' + FOLLOWING
        for key in ('intro-premise', 'intro-connection', 'source-naming'):
            report = completed(text)
            del report['full_text_review']['checks'][key]
            self.assertTrue(e.validate_wording_review(text, report), key)

    def test_cannot_remove_question_or_change_recorded_following_text(self):
        text = AFTER + '\n\n' + FOLLOWING
        report = completed(text)
        self.assertEqual(e.validate_wording_review(text, report), [])
        for mode in ('remove', 'replace'):
            altered = copy.deepcopy(report)
            if mode == 'remove': altered['intro_context'].pop(0)
            else: altered['intro_context'][1]['text'] = '原稿と異なる後続文。'
            self.assertTrue(e.validate_wording_review(text, altered))

    def test_intro_revision_invalidates_previous_review(self):
        self.assertTrue(e.validate_wording_review(AFTER + '\n\n' + FOLLOWING, completed(BEFORE + '\n\n' + FOLLOWING)))

    def test_actual_quotation_is_preserved_for_review_without_style_rewrite(self):
        text = '> 広告には「LINEで一緒に確認できます」とあります。\n\n' + FOLLOWING
        self.assertEqual(e.wording_candidates(text), [])
        self.assertIn('LINEで一緒に確認できます', e.intro_context(text)[0]['text'])

    def test_intro_boundary_ignores_metadata_code_and_comments(self):
        text = '---\ntitle: 記事\n---\n\n```mdx\n## コードの見出し\n```\n\n<!--\n## コメント\n-->\n\n' + AFTER + '\n\n' + FOLLOWING + '\n## 本文\n本文です。'
        self.assertEqual([b['text'] for b in e.intro_context(text)], [e.visible_text(AFTER), FOLLOWING])

    def test_site_names_fail_in_public_text_cite_alt_and_caption(self):
        for name in e.THIRD_PARTY_SITE_NAMES:
            samples = [f'レビューサイト「{name}」には、購入者と名乗る投稿もありました。',
                       f'<cite>出典：{name}に掲載されたコメントの要旨</cite>',
                       f'![{name}の投稿](/images/proof.webp)',
                       f'<p>{name}に掲載された画面です。</p>',
                       f'<blockquote>{name}の投稿</blockquote>']
            for text in samples:
                with self.subTest(text=text):
                    self.assertTrue(e.check_source_names(text))
                    # レビューをpassと書いても、公開名の残存を許さない。
                    self.assertTrue(e.validate_wording_review(text, completed(text)))

    def test_formatted_name_is_detected(self):
        self.assertTrue(e.check_source_names('第三者の<strong>副</strong>レポに掲載されています。'))

    def test_generic_names_and_primary_source_names_are_accepted(self):
        text = '第三者サイトには、購入者と名乗る投稿もありました。\n\n同じ内容は、別の第三者サイトの記事にも転載されていました。\n\n国民生活センターの資料とAIFAの運営会社であるElegance合同会社の案内を確認しました。'
        self.assertEqual(e.check_source_names(text), [])

    def test_internal_comments_code_and_link_destinations_are_not_public_names(self):
        text = '<!-- 調査元：副レポ -->\n\n```text\nジョブネットワークセンター\n```\n\n[第三者サイト](https://example.test/副レポ)'
        self.assertEqual(e.check_source_names(text), [])

    def test_old_review_schema_requires_recheck(self):
        report = completed(AFTER)
        report['schema_version'] = 1
        self.assertTrue(e.validate_wording_review(AFTER, report))


if __name__ == '__main__':
    unittest.main()
