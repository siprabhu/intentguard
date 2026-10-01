from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / 'src'))
from intentguard import Decision, GuardedRuntime, IntentContract, ProposedAction, ToolSpec


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.contract = IntentContract('Read invoice', ['read', 'send'], ['invoice'],
            allowed_destinations=['user'], confirmation_required=['external_communication'], max_action_count=2)
        self.tools = {'read': ToolSpec(self.handler),
                      'send': ToolSpec(self.handler, True, 'external_communication')}
        self.runtime = GuardedRuntime(self.contract, self.tools)

    def handler(self, action):
        self.calls.append(action)
        return {'amount': 100}

    def test_execution_returns_output_and_charges_once(self):
        result = self.runtime.execute(ProposedAction('read', 'invoice'))
        self.assertEqual(result.output, {'amount': 100})
        self.assertTrue(result.executed)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.runtime.charged_count, 1)

    def test_blocked_action_never_reaches_tool(self):
        result = self.runtime.execute(ProposedAction('read', 'payroll'))
        self.assertEqual(result.decision, Decision.BLOCK)
        self.assertFalse(result.executed)
        self.assertEqual(self.calls, [])
        self.assertEqual(self.runtime.charged_count, 0)

    def test_omitted_side_effect_cannot_bypass_confirmation(self):
        result = self.runtime.execute(ProposedAction('send', 'invoice', 'user'))
        self.assertEqual(result.decision, Decision.CONFIRM)
        self.assertEqual(result.action.side_effect, 'external_communication')
        self.assertFalse(result.executed)
        self.assertEqual(self.calls, [])
        self.assertEqual(self.runtime.charged_count, 0)

    def test_unapproved_destination_blocks_before_confirmation(self):
        result = self.runtime.execute(ProposedAction('send', 'invoice', 'external'))
        self.assertEqual(result.decision, Decision.BLOCK)
        self.assertEqual(self.calls, [])

    def test_missing_destination_and_metadata_conflicts(self):
        for action in [ProposedAction('send', 'invoice'),
                       ProposedAction('send', 'invoice', 'user', 'harmless'),
                       ProposedAction('read', 'invoice', 'user'),
                       ProposedAction('unknown', 'invoice')]:
            with self.subTest(action=action):
                self.assertEqual(self.runtime.execute(action).decision, Decision.BLOCK)
        self.assertEqual(self.calls, [])

    def test_count_blocks_actual_third_execution(self):
        results = [self.runtime.execute(ProposedAction('read', 'invoice')) for _ in range(3)]
        self.assertEqual([r.decision for r in results], [Decision.ALLOW, Decision.ALLOW, Decision.BLOCK])
        self.assertEqual(len(self.calls), 2)

    def test_concurrent_calls_share_one_limit(self):
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda _: self.runtime.execute(ProposedAction('read', 'invoice')), range(40)))
        self.assertEqual(sum(r.executed for r in results), 2)
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(self.runtime.charged_count, 2)
        self.assertEqual(len(self.runtime.trace), 40)

    def test_failure_consumes_budget_and_is_audited(self):
        def fail(action):
            raise RuntimeError('synthetic failure')
        runtime = GuardedRuntime(self.contract, {'read': ToolSpec(fail)})
        results = [runtime.execute(ProposedAction('read', 'invoice')) for _ in range(3)]
        self.assertTrue(results[0].executed)
        self.assertIn('synthetic failure', results[0].error)
        self.assertEqual(results[-1].decision, Decision.BLOCK)
        self.assertEqual(runtime.charged_count, 2)

    def test_registry_is_copied_and_trace_is_snapshot(self):
        del self.tools['read']
        snapshot = self.runtime.trace
        result = self.runtime.execute(ProposedAction('read', 'invoice'))
        self.assertTrue(result.executed)
        self.assertEqual(snapshot, ())
        self.assertIsInstance(self.runtime.trace, tuple)

    def test_raw_action_dictionary_is_not_trusted(self):
        with self.assertRaises(ValueError):
            self.runtime.execute({'operation': 'read', 'resource': 'invoice'})
        self.assertEqual(self.calls, [])


if __name__ == '__main__':
    unittest.main()
