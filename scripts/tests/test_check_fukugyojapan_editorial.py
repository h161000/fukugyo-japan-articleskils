import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "check_fukugyojapan_editorial.py"
SPEC = importlib.util.spec_from_file_location("check_fukugyojapan_editorial", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


CAPTION = (
    '<p style="font-size: 0.75em; color: #666; text-align: center; '
    'line-height: 1.5; margin-top: 6px;">確認できる事実です。</p>'
)


class CheckFukugyojapanEditorialTests(unittest.TestCase):
    def test_accepts_preferred_wording_and_caption(self):
        text = "\n".join(
            [
                "そこで、口コミを次の3つの観点から確認します。",
                "実際の案内を時系列で並べると、次のとおりです。",
                "副業情報をLINEで共有しています。",
                "![確認画面](/images/example.webp)",
                "",
                CAPTION,
            ]
        )

        self.assertEqual(MODULE.check_text(text), [])

    def test_rejects_previous_wording(self):
        old_phrases = [
            "一緒に整理できます",
            "口コミは次の3種類に分けて見ます",
            "流れを整理すると、次の順番です",
            "LINEで流しています",
            "実際に続けている副業の話をそのまま流しています",
        ]

        for phrase in old_phrases:
            with self.subTest(phrase=phrase):
                self.assertTrue(MODULE.check_text(phrase))

    def test_rejects_missing_or_large_caption(self):
        missing = "![確認画面](/images/example.webp)"
        large = "\n".join(
            [
                "![確認画面](/images/example.webp)",
                '<p style="font-size: 0.9em; color: #666;">説明です。</p>',
            ]
        )

        self.assertTrue(MODULE.check_text(missing))
        self.assertTrue(MODULE.check_text(large))

    def test_rejects_public_provenance_and_confirmation_date(self):
        captions = [
            CAPTION.replace(
                "確認できる事実です。", "確認できる事実です。（ユーザー提供画像、2026-09-04確認）"
            ),
            CAPTION.replace("確認できる事実です。", "確認できる事実です。（2026-09-04確認）"),
        ]

        for caption in captions:
            with self.subTest(caption=caption):
                text = "\n".join(
                    ["![確認画面](/images/example.webp)", "", caption]
                )
                self.assertTrue(MODULE.check_text(text))


if __name__ == "__main__":
    unittest.main()
