from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT/'experiments'))
from intentguard import IntentContract, ProposedAction, GuardedRuntime, ToolSpec, TrajectoryPolicy, TrajectoryState, evaluate_action
from run_benchmark import load_cases, run, run_case
from generate_trajectory_pairs import build_cases


class TrajectoryTests(unittest.TestCase):
    def runtime(self, policy, handler=None, confirmation=False):
        contract=IntentContract('Read and send', ['read','draft','send','copy'], ['invoice','memo'],
            allowed_destinations=['user','accountant'],max_action_count=20,
            confirmation_required=['communication'] if confirmation else [],trajectory=policy)
        handler=handler or (lambda a: None)
        return GuardedRuntime(contract,{'read':ToolSpec(handler),'draft':ToolSpec(handler),
            'send':ToolSpec(handler,True,'communication'),'copy':ToolSpec(handler,True,'disclosure')})

    def test_operation_budget_preserves_other_operations(self):
        r=self.runtime({'operation_limits':{'send':1}})
        self.assertTrue(r.execute(ProposedAction('send','invoice','user')).executed)
        self.assertEqual(r.execute(ProposedAction('send','invoice','user')).decision,'BLOCK')
        self.assertTrue(r.execute(ProposedAction('read','invoice')).executed)
        self.assertEqual(r.charged_count,2)

    def test_resource_budget_covers_multiple_operations(self):
        r=self.runtime({'resource_limits':{'invoice':1}})
        r.execute(ProposedAction('read','invoice'))
        self.assertEqual(r.execute(ProposedAction('copy','invoice','user')).decision,'BLOCK')
        self.assertTrue(r.execute(ProposedAction('read','memo')).executed)

    def test_distinct_destinations_allow_repeated_approved_recipient(self):
        r=self.runtime({'max_distinct_destinations':1})
        for _ in range(2):
            self.assertTrue(r.execute(ProposedAction('send','invoice','user')).executed)
        self.assertEqual(r.execute(ProposedAction('send','invoice','accountant')).decision,'BLOCK')
        self.assertEqual(r.trajectory_state.destinations,frozenset(['user']))

    def test_out_of_order_rejection_does_not_advance_sequence(self):
        r=self.runtime({'operation_sequence':['read','draft','send']})
        self.assertEqual(r.execute(ProposedAction('send','invoice','user')).decision,'BLOCK')
        for action in [ProposedAction('read','invoice'),ProposedAction('draft','invoice'),ProposedAction('send','invoice','user')]:
            self.assertTrue(r.execute(action).executed)
        self.assertEqual(r.execute(ProposedAction('send','invoice','user')).decision,'BLOCK')
        self.assertEqual(r.trajectory_state.sequence_index,3)

    def test_failed_step_charges_budget_without_advancing_sequence(self):
        def fail(a):
            raise RuntimeError('failure')
        r=self.runtime({'operation_sequence':['read','send'],'resource_limits':{'invoice':1}},fail)
        self.assertIsNotNone(r.execute(ProposedAction('read','invoice')).error)
        self.assertEqual(r.trajectory_state.sequence_index,0)
        self.assertEqual(r.execute(ProposedAction('read','invoice')).decision,'BLOCK')
        self.assertEqual(r.execute(ProposedAction('send','memo','user')).decision,'BLOCK')

    def test_confirmation_changes_no_trajectory_state(self):
        r=self.runtime({'operation_sequence':['send'],'operation_limits':{'send':1}},confirmation=True)
        before=r.trajectory_state
        self.assertEqual(r.execute(ProposedAction('send','invoice','user')).decision,'CONFIRM')
        self.assertEqual(r.trajectory_state,before)
        self.assertEqual(r.charged_count,0)

    def test_scoped_budget_is_shared_by_concurrent_callers(self):
        r=self.runtime({'operation_limits':{'send':1}})
        with ThreadPoolExecutor(max_workers=8) as pool:
            results=list(pool.map(lambda _:r.execute(ProposedAction('send','invoice','user')),range(40)))
        self.assertEqual(sum(x.executed for x in results),1)
        self.assertEqual(r.charged_count,1)

    def test_reentrant_handler_cannot_consume_same_sequence_step(self):
        r=None
        def recurse(a):
            return r.execute(a)
        r=self.runtime({'operation_sequence':['read']},recurse)
        result=r.execute(ProposedAction('read','invoice'))
        self.assertIn('cannot reenter',result.error)
        self.assertEqual(r.charged_count,1)
        self.assertEqual(r.trajectory_state.sequence_index,0)

    def test_active_policy_requires_trusted_state_for_direct_predicate(self):
        c=IntentContract('Read', ['read'], ['invoice'],trajectory={'operation_limits':{'read':1}})
        self.assertEqual(evaluate_action(c,ProposedAction('read','invoice'))[0],'BLOCK')
        self.assertEqual(evaluate_action(c,ProposedAction('read','invoice'),trajectory_state=TrajectoryState())[0],'ALLOW')

    def test_policy_is_immutable_and_validated(self):
        original={'read':1}; seq=['read']
        policy=TrajectoryPolicy(operation_limits=original,operation_sequence=seq)
        original['read']=10;seq.append('send')
        self.assertEqual(policy.operation_limits,(('read',1),))
        self.assertEqual(policy.operation_sequence,('read',))
        for value in [{'operation_limits':{'read':True}},{'operation_limits':{'read':-1}},
                      {'resource_limits':{'':1}},{'operation_sequence':'read'},
                      {'max_distinct_destinations':0},{'unknown':1}]:
            with self.subTest(value=value),self.assertRaises(ValueError):
                TrajectoryPolicy.from_dict(value)

    def test_invalid_scope_and_state_rejected(self):
        for policy in [{'operation_limits':{'send':1}},{'resource_limits':{'payroll':1}},
                       {'operation_sequence':['send']}]:
            with self.assertRaises(ValueError):
                IntentContract('Read',['read'],['invoice'],trajectory=policy)
        with self.assertRaises(ValueError):
            TrajectoryState(sequence_index=-1)

    def test_zero_scoped_budget_blocks_first_proposal(self):
        r=self.runtime({'operation_limits':{'send':0}})
        self.assertEqual(r.execute(ProposedAction('send','invoice','user')).decision,'BLOCK')

    def test_trajectory_fixture_and_count_only_ablation(self):
        cases=load_cases([ROOT/'benchmark/deterministic/trajectory_pairs.json'])
        self.assertEqual(cases,build_cases())
        results=run(cases)['summary']
        self.assertEqual(results['intentguard']['unauthorized_executions'],0)
        self.assertEqual(results['count_only']['unauthorized_executions'],6)
        self.assertEqual(results['no_history']['unauthorized_executions'],6)
        self.assertEqual(results['intentguard']['authorized_executions'],results['intentguard']['authorized_actions'])
        for case in cases:
            if case['member']=='drift':
                self.assertLessEqual(len(case['proposed_actions']),case['contract']['max_action_count'])
                self.assertFalse(run_case(case,'count_only')['case_match'])


if __name__=='__main__':
    unittest.main()
