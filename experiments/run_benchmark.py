"""Run fixed proposals through safe in-memory tools; no model or external I/O."""
import argparse
from dataclasses import asdict, replace
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from intentguard import IntentContract, ProposedAction, GuardedRuntime, ToolSpec, TrajectoryPolicy
from intentguard.intent.contract import identifier
from intentguard.reproducibility import source_digest

POLICIES = ('none', 'operation_only', 'no_history', 'count_only', 'intentguard')
# Trusted tool metadata, independent of action proposals and expected labels.
TOOL_METADATA = {
    'read': (False, None), 'search': (False, None),
    'get_balance': (False, None), 'get_transactions': (False, None),
    'draft': (False, None), 'prepare_transfer': (False, None),
    'delete': (False, 'deletion'), 'update': (False, 'modification'),
    'send': (True, 'external_communication'), 'export': (True, 'disclosure'),
    'copy': (True, 'disclosure'), 'transfer': (True, 'financial_transfer'),
}


def validate_case(case):
    """Validate the executable case model, including cross-field label length."""
    if not isinstance(case, dict):
        raise ValueError('case must be an object')
    required = {'id','category','user_task','contract','proposed_actions','expected_decisions','rationale'}
    if not required <= case.keys():
        raise ValueError(f'missing case fields: {sorted(required - case.keys())}')
    for name in ('id','category','user_task','rationale'):
        identifier(case[name], name)
    optional={'pair_id','member','domain','contract_version','untrusted_content',
              'prohibited_outcome','provenance','independent_review'}
    if case.keys() - required - optional:
        raise ValueError('unknown case fields')
    for name in ('pair_id','domain','contract_version'):
        if name in case:
            identifier(case[name],name)
    if 'member' in case and case['member'] not in ('benign','drift'):
        raise ValueError('invalid pair member')
    if 'independent_review' in case and type(case['independent_review']) is not bool:
        raise ValueError('independent_review must be a boolean')
    if 'provenance' in case:
        if not isinstance(case['provenance'],dict):
            raise ValueError('provenance must be an object')
        for name,value in case['provenance'].items():
            identifier(name,'provenance key')
            identifier(value,'provenance value')
    contract = IntentContract.from_dict(case['contract'])
    actions = case['proposed_actions']
    labels = case['expected_decisions']
    if not isinstance(actions,list) or not actions or not isinstance(labels,list) or len(actions)!=len(labels):
        raise ValueError('nonempty action and label arrays must have equal lengths')
    for label in labels:
        if label not in ('ALLOW','CONFIRM','BLOCK'):
            raise ValueError('invalid decision label')
    parsed = [ProposedAction.from_dict(a) for a in actions]
    if any(a.operation not in TOOL_METADATA for a in parsed):
        raise ValueError('case references an unregistered mock operation')
    for name in ('untrusted_content','prohibited_outcome'):
        if case.get(name) is not None and not isinstance(case[name],str):
            raise ValueError(f'{name} must be text or null')
    return contract, parsed


def load_cases(paths):
    cases=[]
    for path in paths:
        value=json.loads(Path(path).read_text(encoding='utf-8'))
        for case in value if isinstance(value,list) else [value]:
            validate_case(case)
            cases.append(case)
    ids=[case['id'] for case in cases]
    if len(ids)!=len(set(ids)):
        raise ValueError('duplicate benchmark IDs')
    if not cases:
        raise ValueError('benchmark contains no cases')
    return cases


def run_case(case, policy):
    contract, actions = validate_case(case)
    if policy not in POLICIES:
        raise ValueError(f'unknown policy: {policy}')
    if policy == 'no_history':
        contract=replace(contract,max_action_count=None,trajectory=TrajectoryPolicy())
    elif policy == 'count_only':
        contract=replace(contract,trajectory=TrajectoryPolicy())
    elif policy in ('none','operation_only'):
        contract=IntentContract(
            objective=contract.objective,
            allowed_operations=frozenset(TOOL_METADATA) if policy=='none' else contract.allowed_operations,
            allowed_resources=frozenset(a.resource for a in actions),
            allowed_destinations=frozenset(a.destination for a in actions if a.destination is not None),
        )
    effects=[]
    def mock_handler(action):
        effect=asdict(action)
        effects.append(effect)
        return {'synthetic': True, 'resource': action.resource}
    registry={op:ToolSpec(mock_handler,required,effect) for op,(required,effect) in TOOL_METADATA.items()}
    runtime=GuardedRuntime(contract,registry)
    trace=[]
    for action,expected in zip(actions,case['expected_decisions']):
        result=runtime.execute(action)
        trace.append(dict(asdict(result),expected=expected,match=result.decision==expected))
    return dict(case_id=case['id'],policy=policy,matched=sum(t['match'] for t in trace),
                action_count=len(trace),case_match=all(t['match'] for t in trace),
                trace=trace,tool_effects=effects)


def run(cases):
    rows=[run_case(case,policy) for policy in POLICIES for case in cases]
    summary={}
    for policy in POLICIES:
        selected=[r for r in rows if r['policy']==policy]
        traces=[t for r in selected for t in r['trace']]
        summary[policy]=dict(cases=len(selected),matched_cases=sum(r['case_match'] for r in selected),
            actions=len(traces),matched_decisions=sum(t['match'] for t in traces),
            unauthorized_executions=sum(t['executed'] and t['expected']!='ALLOW' for t in traces),
            authorized_actions=sum(t['expected']=='ALLOW' for t in traces),
            authorized_executions=sum(t['executed'] and t['expected']=='ALLOW' for t in traces),
            confirmations=sum(t['decision']=='CONFIRM' for t in traces),
            tool_errors=sum(t['error'] is not None for t in traces))
    return dict(summary=summary,runs=rows)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases',type=Path,nargs='+',default=[ROOT/'benchmark/deterministic/pairs.json',ROOT/'benchmark/benign/IG-BEN-001.json',ROOT/'benchmark/indirect_injection/IG-INJ-001.json',ROOT/'benchmark/deterministic/trajectory_pairs.json'])
    parser.add_argument('--output',type=Path,default=ROOT/'results/processed/deterministic.json')
    args=parser.parse_args(argv)
    try:
        cases=load_cases(args.cases)
        result=run(cases)
    except (ValueError,OSError,TypeError) as exc:
        parser.exit(2,f'Invalid benchmark: {exc}\n')
    tracked=[*args.cases,Path(__file__),*sorted((ROOT/'src/intentguard').rglob('*.py'))]
    result['metadata']=dict(timestamp=datetime.now(timezone.utc).isoformat(),python=platform.python_version(),
        platform=platform.platform(),evaluation='fixed synthetic proposals; no LLM',
        hash_algorithm='sha256-utf8-lf',
        sha256={(p.relative_to(ROOT) if p.is_relative_to(ROOT) else p).as_posix():source_digest(p) for p in tracked})
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result['summary'],indent=2))
    print(f'Traces: {args.output}')
    full=result['summary']['intentguard']
    return 0 if full['matched_cases']==full['cases'] and full['tool_errors']==0 else 1


if __name__=='__main__':
    sys.exit(main())
