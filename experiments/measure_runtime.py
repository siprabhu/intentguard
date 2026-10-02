"""Local three-call workflow timings including runtime creation and mock tools.

These are not LLM-agent or network end-to-end measurements. Contract and action
construction are outside the timed region; runtime initialization, validation,
history bookkeeping, locking, tracing and handlers are inside it.
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import json
import math
import platform
import random
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from intentguard import IntentContract,ProposedAction,GuardedRuntime,ToolSpec
from intentguard.reproducibility import source_digest


def quantile(values, q):
    values=sorted(values)
    pos=(len(values)-1)*q
    low=math.floor(pos);high=math.ceil(pos)
    return values[low]+(values[high]-values[low])*(pos-low)


def measure(samples=2000):
    actions=[ProposedAction('read','invoice'),ProposedAction('draft','invoice'),
             ProposedAction('send','invoice','user')]
    def handler(action):
        return {'synthetic':True,'resource':action.resource}
    tools={'read':ToolSpec(handler),'draft':ToolSpec(handler),
           'send':ToolSpec(handler,True,'external_communication')}
    base=dict(objective='Read, draft, then send once',allowed_operations=['read','draft','send'],
              allowed_resources=['invoice'],allowed_destinations=['user'],max_action_count=6)
    policy=dict(operation_limits={'send':1},resource_limits={'invoice':3},
                operation_sequence=['read','draft','send'],max_distinct_destinations=1)
    contracts={'static_runtime':IntentContract.from_dict(base)}
    for size in [1,10,100,1000,10000]:
        contracts[f'trajectory_{size}']=IntentContract.from_dict(dict(base,
            allowed_resources=['invoice']+[f'resource_{i}' for i in range(size-1)],trajectory=policy))
    conditions=['tools_only',*contracts]
    raw={name:[] for name in conditions}

    def one(name):
        start=time.perf_counter_ns()
        if name=='tools_only':
            results=[handler(a) for a in actions]
        else:
            runtime=GuardedRuntime(contracts[name],tools)
            results=[runtime.execute(a) for a in actions]
        elapsed=(time.perf_counter_ns()-start)/1000
        if name!='tools_only' and any(not r.executed or r.error for r in results):
            raise RuntimeError('timed workflow did not complete correctly')
        return elapsed

    for name in conditions:
        for _ in range(100):one(name)
    rng=random.Random(20261002)
    for _ in range(samples):
        order=list(conditions);rng.shuffle(order)
        for name in order:raw[name].append(one(name))
    summaries={name:{f'p{p}':quantile(values,p/100) for p in [50,95,99]} for name,values in raw.items()}
    tracked=[Path(__file__),*sorted((ROOT/'src/intentguard').rglob('*.py'))]
    return dict(metadata=dict(timestamp=datetime.now(timezone.utc).isoformat(),python=platform.python_version(),
        platform=platform.platform(),processor=platform.processor(),seed=20261002,samples_per_condition=samples,
        warmup_per_condition=100,calls_per_workflow=3,quantiles='linear interpolation over sorted workflow samples',
        scope='local runtime initialization and three mock calls; no LLM or network; prebuilt contracts/actions',
        hash_algorithm='sha256-utf8-lf',sha256={p.relative_to(ROOT).as_posix():source_digest(p) for p in tracked}),
        summary_us=summaries,samples_us=raw)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--samples',type=int,default=2000)
    parser.add_argument('--output',type=Path,default=ROOT/'results/processed/workflow_timing.json')
    args=parser.parse_args()
    if args.samples<100:parser.error('use at least 100 samples per condition')
    result=measure(args.samples)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result['summary_us'],indent=2))
