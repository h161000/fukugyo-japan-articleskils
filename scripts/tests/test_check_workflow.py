import copy
from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('workflow', Path(__file__).resolve().parents[1] / 'check_workflow.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

class WorkflowGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        work = Path(self.tmp.name) / 'sample'
        work.mkdir()
        now = datetime.now(timezone.utc)
        def ago(n): return (now - timedelta(seconds=n)).isoformat()
        self.state = dict(schema_version=1, scope='create', request='記事を作成',
            site_id='kn79v569bym1h9xbfjy1hfv0px8bh122', case_id='test-case', slug='sample',
            articlework=str(work), created_at=ago(60), stages={})
        for name, item in gate.MANIFEST.items():
            for rel in item['outputs']:
                p = work / rel.format(slug='sample')
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text('test evidence')
            proof = work / (name + '.log')
            proof.write_text('test execution evidence')
            self.state['stages'][name] = dict(status='complete', started_at=ago(30), completed_at=ago(10),
                reads=[dict(path=str(gate.absolute(p)), sha256=gate.digest(gate.absolute(p)),
                            read_at=ago(40), applied_rule='対象工程の具体的規定') for p in item['reads']],
                checks={c:dict(status='pass', detail='対象根拠の照合結果', evidence=str(proof), sha256=gate.digest(proof)) for c in item['checks']},
                unresolved=[], exceptions=[])

    def test_complete_and_publish_scope(self):
        self.assertEqual(gate.validate(self.state, 'review', 'complete'), [])
        self.assertTrue(gate.validate(self.state, 'publish', 'complete'))
        self.state['scope'] = 'publish'
        self.assertEqual(gate.validate(self.state, 'publish', 'complete'), [])

    def test_missing_read(self):
        self.state['stages']['writing']['reads'].pop()
        self.assertTrue(gate.validate(self.state, 'writing', 'ready'))

    def test_unfinished_previous_stage(self):
        self.state['stages']['research']['status'] = 'in_progress'
        self.assertTrue(gate.validate(self.state, 'writing', 'ready'))

    def test_missing_output(self):
        (Path(self.state['articlework']) / 'facts.md').unlink()
        self.assertTrue(gate.validate(self.state, 'research', 'complete'))

    def test_stale_evidence(self):
        (Path(self.state['articlework']) / 'research.log').write_text('changed')
        self.assertTrue(gate.validate(self.state, 'review', 'complete'))

    def test_read_after_start(self):
        self.state['stages']['writing']['reads'][0]['read_at'] = datetime.now(timezone.utc).isoformat()
        self.assertTrue(gate.validate(self.state, 'writing', 'complete'))

    def test_failed_check_and_unresolved(self):
        self.state['stages']['review']['checks']['critic']['status'] = 'fail'
        self.state['stages']['review']['unresolved'] = ['未対応']
        self.assertTrue(gate.validate(self.state, 'review', 'complete'))

    def test_exception_needs_replacement(self):
        self.state['stages']['review']['exceptions'] = [dict(rule_source='rule', reason='reason', replacement_check='missing')]
        self.assertTrue(gate.validate(self.state, 'review', 'complete'))

if __name__ == '__main__':
    unittest.main()
