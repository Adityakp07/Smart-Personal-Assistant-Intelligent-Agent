"""Small, inspectable forward-chaining rule engine used by the assistant."""
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Rule:
    name: str
    premises: tuple[str, ...]
    conclusion: str
    explanation: str


RULES = (
    Rule(
        "early_meeting_reminder",
        ("Meeting(?x)", 'StartsBefore(?x, "10:00")'),
        "Remind(?x, 30)",
        "Meetings starting before 10:00 receive a 30-minute advance reminder.",
    ),
    Rule(
        "due_today_priority",
        ("Task(?x)", "DueToday(?x)"),
        'Priority(?x, "high")',
        "A task due today is marked high priority.",
    ),
)


def _parse(fact):
    match = re.fullmatch(r"([A-Za-z][A-Za-z0-9_]*)\((.*)\)", fact.strip())
    if not match:
        return None, ()
    args = tuple(part.strip().strip('"') for part in match.group(2).split(","))
    return match.group(1), args


def _match(pattern, fact, bindings):
    pred, args = _parse(pattern)
    fact_pred, fact_args = _parse(fact)
    if pred != fact_pred or len(args) != len(fact_args):
        return None
    result = dict(bindings)
    for expected, actual in zip(args, fact_args):
        if expected.startswith("?"):
            if expected in result and result[expected] != actual:
                return None
            result[expected] = actual
        elif expected != actual:
            return None
    return result


def forward_chain(initial_facts):
    """Return all known facts and a human-readable proof trace."""
    facts = list(dict.fromkeys(initial_facts))
    trace = []
    changed = True
    while changed:
        changed = False
        known = set(facts)
        for rule in RULES:
            bindings_list = [({}, [])]
            for premise in rule.premises:
                next_bindings = []
                for bindings, evidence in bindings_list:
                    for fact in sorted(known):
                        matched = _match(premise, fact, bindings)
                        if matched is not None:
                            next_bindings.append((matched, evidence + [fact]))
                bindings_list = next_bindings
            for bindings, evidence in bindings_list:
                conclusion = rule.conclusion
                for variable, value in bindings.items():
                    conclusion = conclusion.replace(variable, f'"{value}"')
                if conclusion not in known:
                    facts.append(conclusion)
                    known.add(conclusion)
                    trace.append({"rule": rule.name, "premises": evidence,
                                  "conclusion": conclusion,
                                  "explanation": rule.explanation})
                    changed = True
    return facts, trace


def task_facts(tasks):
    facts = []
    for task in tasks:
        get = task.get if isinstance(task, dict) else lambda key, default=None: getattr(task, key, default)
        name = get("title", "").replace('"', "'")
        kind = get("kind", "reminder")
        facts.append(f'{"Meeting" if kind == "meeting" else "Task"}("{name}")')
        if get("due_today", False):
            facts.append(f'DueToday("{name}")')
        start = get("fixed_start")
        if start and start < "10:00":
            facts.append(f'StartsBefore("{name}", "10:00")')
    return facts
