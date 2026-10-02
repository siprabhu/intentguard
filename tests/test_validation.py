import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / 'src'))
from intentguard import IntentContract, ProposedAction, Decision, evaluate_action


def valid_contract(**updates):
    fields = dict(objective='Read an invoice', allowed_operations=['read'],
                  allowed_resources=['invoice'], allowed_destinations=['user'])
    fields.update(updates)
    return IntentContract.from_dict(fields)


class ValidationTests(unittest.TestCase):
    def test_contract_rejects_unknown_and_missing_fields(self):
        for value in [{}, {'objective': 'x', 'allowed_operations': []},
                      dict(objective='x', allowed_operations=[], allowed_resources=[], typo=[]), None]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                IntentContract.from_dict(value)

    def test_invalid_contract_values(self):
        for name, value in [('objective', ''), ('objective', ' x'),
                            ('allowed_operations', 'read'), ('allowed_resources', [None]),
                            ('allowed_resources', ['x', 'x']), ('allowed_destinations', ['']),
                            ('max_action_count', 0), ('max_action_count', -1),
                            ('max_action_count', True), ('max_action_count', 1.5)]:
            with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                valid_contract(**{name: value})

    def test_direct_construction_freezes_collections(self):
        values = ['invoice']
        contract = IntentContract('Read', ['read'], values)
        values.append('payroll')
        self.assertEqual(contract.allowed_resources, frozenset(['invoice']))

    def test_action_rejects_malformed_fields(self):
        for values in [{}, {'operation': 'read'}, {'operation': 'read', 'resource': ''},
                       {'operation': ' read', 'resource': 'invoice'},
                       {'operation': 'read', 'resource': 'invoice', 'destination': ''},
                       {'operation': 'read', 'resource': 'invoice', 'side_effect': 3},
                       {'operation': 'read', 'resource': 'invoice', 'approved': True}]:
            with self.subTest(values=values), self.assertRaises(ValueError):
                ProposedAction.from_dict(values)

    def test_invalid_history_rejected(self):
        for count in [-1, True, 1.2, '0', None]:
            with self.subTest(count=count), self.assertRaises(ValueError):
                evaluate_action(valid_contract(), ProposedAction('read', 'invoice'), prior_action_count=count)

    def test_destination_membership(self):
        for destination, expected in [('user', Decision.ALLOW), ('external', Decision.BLOCK)]:
            with self.subTest(destination=destination):
                self.assertEqual(evaluate_action(valid_contract(), ProposedAction('read', 'invoice', destination))[0], expected)

    def test_confirmation_and_hard_block_precedence(self):
        c = valid_contract(confirmation_required=['disclosure'])
        self.assertEqual(evaluate_action(c, ProposedAction('read', 'invoice', 'user', 'disclosure'))[0], Decision.CONFIRM)
        self.assertEqual(evaluate_action(c, ProposedAction('read', 'invoice', 'external', 'disclosure'))[0], Decision.BLOCK)
        c = valid_contract(prohibited_operations=['read'], confirmation_required=['disclosure'])
        self.assertEqual(evaluate_action(c, ProposedAction('read', 'invoice', 'user', 'disclosure'))[0], Decision.BLOCK)

    def test_operation_allowlist_and_count_boundaries(self):
        c = valid_contract(max_action_count=2)
        self.assertEqual(evaluate_action(c, ProposedAction('delete', 'invoice'))[0], Decision.BLOCK)
        for count, expected in [(0, Decision.ALLOW), (1, Decision.ALLOW), (2, Decision.BLOCK), (3, Decision.BLOCK)]:
            self.assertEqual(evaluate_action(c, ProposedAction('read', 'invoice'), prior_action_count=count)[0], expected)


if __name__ == '__main__':
    unittest.main()
