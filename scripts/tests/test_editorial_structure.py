"""結論・締め・顔画像の抜けを再発させないための回帰検査。"""
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('editorial', Path(__file__).resolve().parents[1] / 'check_fukugyojapan_editorial.py')
editorial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(editorial)

VALID = '''## 結論
<AlertBox><ul><li>認可の番号を照合できない</li></ul></AlertBox>
<Balloon name="フジ" image="/images/fuji.webp" lineCta={false}>確認しましょう。</Balloon>
## まとめ
- 認可の番号を照合できない
'''

class StructureTests(unittest.TestCase):
    def test_valid_and_single_quotes_multiline(self):
        self.assertEqual(editorial.check_structure(VALID), [])
        self.assertEqual(editorial.check_structure(VALID.replace('name="フジ" image="/images/fuji.webp"', "name='フジ'\n image='/images/fuji.webp'")), [])

    def test_missing_avatar(self):
        self.assertTrue(any('Balloon' in e for e in editorial.check_structure(VALID.replace(' image="/images/fuji.webp"', ''))))

    def test_wrong_avatar(self):
        self.assertTrue(any('Balloon' in e for e in editorial.check_structure(VALID.replace('/images/fuji.webp', '/images/other.webp'))))

    def test_missing_image_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertTrue(any('存在しません' in e for e in editorial.check_structure(VALID, root)))
            (root / 'public/images').mkdir(parents=True)
            (root / 'public/images/fuji.webp').write_bytes(b'fixture')
            self.assertEqual(editorial.check_structure(VALID, root), [])

    def test_missing_first_reasons(self):
        text = VALID.replace('<AlertBox><ul><li>認可の番号を照合できない</li></ul></AlertBox>', 'おすすめしません。')
        self.assertTrue(any('最初の結論' in e for e in editorial.check_structure(text)))

    def test_missing_closing_reasons(self):
        self.assertTrue(any('最後のまとめ' in e for e in editorial.check_structure(VALID.replace('- 認可の番号を照合できない', '相談してください。'))))

    def test_code_example_cannot_replace_reasons(self):
        self.assertTrue(any('最後のまとめ' in e for e in editorial.check_structure(VALID.replace('- 認可の番号を照合できない', '```md\n- コード例\n```'))))

if __name__ == '__main__':
    unittest.main()
