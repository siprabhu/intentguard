"""Reproduce the draft's four-case diagnostic and local timing measurements."""
import argparse
import dataclasses
import hashlib
import json
import platform
import random
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, default=ROOT/'results/processed/current_timing.json',
                    help='New measurements; does not overwrite the original paper snapshot')
args = parser.parse_args()
sys.path.insert(0, str(ROOT / 'src'))
from intentguard import Decision, IntentContract, ProposedAction, evaluate_action

c = IntentContract.from_dict(dict(objective='Read invoice 123', allowed_operations=['search', 'read'], allowed_resources=['invoice_123'], prohibited_operations=['send', 'delete'], max_action_count=2))
cases = [('In-scope read', ProposedAction('read', 'invoice_123'), 0, 'ALLOW'), ('Prohibited send', ProposedAction('send', 'invoice_123', 'external@example.com'), 0, 'BLOCK'), ('Resource drift', ProposedAction('read', 'payroll'), 0, 'BLOCK'), ('Count violation', ProposedAction('read', 'invoice_123'), 2, 'BLOCK')]
policies = {
    'No guard': lambda a, h: Decision.ALLOW,
    'Operation only': lambda a, h: Decision.ALLOW if a.operation in c.allowed_operations else Decision.BLOCK,
    'No history': lambda a, h: evaluate_action(dataclasses.replace(c, max_action_count=None), a, prior_action_count=h)[0],
    'IntentGuard': lambda a, h: evaluate_action(c, a, prior_action_count=h)[0],
}
decisions = {name: [str(fn(a, h)) for _, a, h, _ in cases] for name, fn in policies.items()}
scores = {name: sum(v == case[3] for v, case in zip(values, cases)) for name, values in decisions.items()}
sizes = [1, 10, 100, 1000, 10000]
contracts = {n: dataclasses.replace(c, allowed_resources=frozenset(['invoice_123'] + [f'resource_{i}' for i in range(n-1)])) for n in sizes}
action = ProposedAction('read', 'invoice_123')
for contract in contracts.values():
    for _ in range(10000):
        evaluate_action(contract, action)
samples = {n: [] for n in sizes}
rng = random.Random(20260930)
batch_calls = 20000
for repeat in range(31):
    order = list(sizes)
    rng.shuffle(order)
    for n in order:
        contract = contracts[n]
        start = time.perf_counter_ns()
        for _ in range(batch_calls):
            evaluate_action(contract, action)
        samples[n].append((time.perf_counter_ns() - start) / batch_calls / 1000)
summary = {}
for n, values in samples.items():
    q = statistics.quantiles(values, n=4, method='inclusive')
    summary[n] = dict(median=statistics.median(values), q1=q[0], q3=q[2])
out = dict(timestamp=datetime.now(timezone.utc).isoformat(), python=platform.python_version(), platform=platform.platform(), processor=platform.processor(), source_sha256=hashlib.sha256((ROOT/'src/intentguard/guard/authorization.py').read_bytes()).hexdigest(), seed=20260930, batch_calls=batch_calls, repeats=31, warmup_calls_per_size=10000, cases=[dict(name=n, action=dataclasses.asdict(a), prior_count=h, expected=e) for n,a,h,e in cases], decisions=decisions, scores=scores, samples_us=samples, summary_us=summary, running_median_us=[statistics.median(samples[1000][:i]) for i in range(1,32)])
path = args.output
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(out, indent=2)+'\n', encoding='utf-8')
print(json.dumps({k:out[k] for k in ['timestamp','python','scores','summary_us']}, indent=2))
