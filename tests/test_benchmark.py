import copy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'experiments'))
from run_benchmark import load_cases, run, run_case, validate_case, main
from generate_deterministic_pairs import build_cases


class BenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.cases=load_cases([ROOT/'benchmark/deterministic/pairs.json',
            ROOT/'benchmark/benign/IG-BEN-001.json',ROOT/'benchmark/indirect_injection/IG-INJ-001.json'])

    def test_materialized_pairs_match_declared_design(self):
        self.assertEqual(self.cases[:30],build_cases())
        self.assertEqual(len({c['pair_id'] for c in self.cases[:30]}),15)
        self.assertTrue(all(not c['independent_review'] for c in self.cases[:30]))

    def test_full_guard_matches_all_cases_and_never_executes_nonallow(self):
        result=run(self.cases)
        full=result['summary']['intentguard']
        self.assertEqual(full['matched_cases'],32)
        self.assertEqual(full['matched_decisions'],36)
        self.assertEqual(full['unauthorized_executions'],0)
        self.assertEqual(full['authorized_executions'],20)
        self.assertEqual(full['confirmations'],2)
        for row in result['runs']:
            if row['policy']=='intentguard':
                self.assertEqual(len(row['tool_effects']),sum(t['expected']=='ALLOW' for t in row['trace']))

    def test_history_ablation_changes_only_exhausted_trajectory(self):
        for case in self.cases:
            full=run_case(case,'intentguard')
            ablated=run_case(case,'no_history')
            if case['id']=='P15-drift':
                self.assertEqual(full['trace'][-1]['decision'],'BLOCK')
                self.assertEqual(ablated['trace'][-1]['decision'],'ALLOW')
            else:
                self.assertEqual([t['decision'] for t in full['trace']],
                                 [t['decision'] for t in ablated['trace']])

    def test_runner_rejects_missing_labels_and_unknown_tools(self):
        for field,value in [('expected_decisions',[]),('expected_decisions',['WRONG']),
                            ('proposed_actions',[{'operation':'unknown','resource':'invoice_123'}])]:
            case=copy.deepcopy(self.cases[0]);case[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):
                validate_case(case)

    def test_duplicate_ids_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'duplicate.json'
            path.write_text(json.dumps([self.cases[0],self.cases[0]]))
            with self.assertRaisesRegex(ValueError,'duplicate'):
                load_cases([path])

    def test_cli_writes_trace_and_fails_when_labels_disagree(self):
        case=copy.deepcopy(self.cases[0]);case['expected_decisions']=['BLOCK']
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'case.json';output=Path(folder)/'result.json'
            path.write_text(json.dumps(case))
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(['--cases',str(path),'--output',str(output)]),1)
            result=json.loads(output.read_text())
            self.assertEqual(result['summary']['intentguard']['matched_decisions'],0)
            self.assertTrue(result['metadata']['sha256'])


if __name__=='__main__':
    unittest.main()
