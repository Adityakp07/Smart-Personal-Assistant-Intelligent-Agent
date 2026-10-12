"""Day-planning CSP: interval variables, backtracking, forward checking and AC-3."""
from dataclasses import dataclass
from time import perf_counter

DAY_START = 9 * 60
DAY_END = 17 * 60
BREAK_START = 12 * 60
BREAK_END = 13 * 60
SLOT_MINUTES = 30


@dataclass(frozen=True)
class Task:
    title: str
    duration: int = 30
    earliest: str = "09:00"
    deadline: str = "17:00"
    fixed_start: str | None = None
    kind: str = "reminder"
    due_today: bool = False


def to_minutes(value):
    hour, minute = map(int, value.split(":"))
    return hour * 60 + minute


def to_clock(value):
    return f"{value // 60:02d}:{value % 60:02d}"


def _fits(start, task):
    end = start + task.duration
    return (start >= to_minutes(task.earliest) and end <= to_minutes(task.deadline)
            and start >= DAY_START and end <= DAY_END
            and not (start < BREAK_END and end > BREAK_START))


def _overlap(start_a, task_a, start_b, task_b):
    return start_a < start_b + task_b.duration and start_b < start_a + task_a.duration


def _domains(tasks):
    domains = {}
    for i, task in enumerate(tasks):
        if task.duration <= 0 or task.duration % SLOT_MINUTES:
            domains[i] = []
            continue
        candidates = [to_minutes(task.fixed_start)] if task.fixed_start else range(
            DAY_START, DAY_END, SLOT_MINUTES)
        domains[i] = [slot for slot in candidates if _fits(slot, task)]
    return domains


def _ac3(domains, tasks):
    """Enforce binary no-overlap arcs; return success and the revised domains."""
    queue = [(i, j) for i in domains for j in domains if i != j]
    while queue:
        i, j = queue.pop(0)
        revised = [a for a in domains[i] if any(
            not _overlap(a, tasks[i], b, tasks[j]) for b in domains[j])]
        if len(revised) != len(domains[i]):
            domains[i] = revised
            if not revised:
                return False, domains
            queue.extend((k, i) for k in domains if k != i and k != j)
    return all(domains.values()), domains


def _search(tasks, domains, advanced):
    tried = 0

    def visit(assigned, remaining_domains):
        nonlocal tried
        if len(assigned) == len(tasks):
            return assigned
        unassigned = [i for i in range(len(tasks)) if i not in assigned]
        var = min(unassigned, key=lambda i: len(remaining_domains[i])) if advanced else unassigned[0]
        for value in list(remaining_domains[var]):
            tried += 1
            if any(_overlap(value, tasks[var], other_value, tasks[other])
                   for other, other_value in assigned.items()):
                continue
            next_assigned = dict(assigned, **{str(var): value})
            next_assigned = {int(k): v for k, v in next_assigned.items()}
            next_domains = {i: list(domain) for i, domain in remaining_domains.items()}
            next_domains[var] = [value]
            failed = False
            if advanced:
                # Forward checking removes values incompatible with this assignment.
                for other in unassigned:
                    if other == var:
                        continue
                    next_domains[other] = [candidate for candidate in next_domains[other]
                                           if not _overlap(value, tasks[var], candidate, tasks[other])]
                    if not next_domains[other]:
                        failed = True
                        break
                # AC-3 propagates the remaining pairwise constraints further.
                if not failed:
                    ok, next_domains = _ac3(next_domains, tasks)
                    failed = not ok
            if failed:
                continue
            result = visit(next_assigned, next_domains)
            if result is not None:
                return result
        return None

    result = visit({}, domains)
    return result, tried


def schedule(tasks, strategy="ac3"):
    """Solve a schedule and return assignment, counters, runtime, and conflicts."""
    tasks = [task if isinstance(task, Task) else Task(**task) for task in tasks]
    started = perf_counter()
    domains = _domains(tasks)
    initial_domains = {i: list(values) for i, values in domains.items()}
    precheck_conflicts = [tasks[i].title for i, values in domains.items() if not values]
    propagation_conflicts = []
    if strategy == "ac3" and not precheck_conflicts:
        ok, domains = _ac3(domains, tasks)
        if not ok:
            propagation_conflicts = [tasks[i].title for i, values in domains.items() if not values]
    if precheck_conflicts:
        result, tried = None, 0
    else:
        result, tried = _search(tasks, domains if strategy == "ac3" else initial_domains,
                                advanced=(strategy == "ac3"))
    elapsed = perf_counter() - started
    conflicts = []
    if result is None:
        if precheck_conflicts:
            conflicts.extend(f"{name}: no slot satisfies working hours, deadline, break, or fixed-time constraints"
                             for name in precheck_conflicts)
        elif propagation_conflicts:
            conflicts.extend(f"{name}: no start time remains compatible with the no-overlap constraints after AC-3"
                             for name in propagation_conflicts)
        else:
            conflicts.append("Constraint conflict: each task must fit its time window, and every pair of tasks must not overlap.")
            for i, first in enumerate(tasks):
                for second in tasks[i + 1:]:
                    if first.fixed_start and second.fixed_start:
                        a, b = to_minutes(first.fixed_start), to_minutes(second.fixed_start)
                        if _overlap(a, first, b, second):
                            conflicts.append(f"'{first.title}' overlaps fixed task '{second.title}'.")
    plan = {} if result is None else {
        tasks[i].title: {"start": to_clock(start), "end": to_clock(start + tasks[i].duration)}
        for i, start in result.items()
    }
    return {"success": result is not None, "plan": plan, "assignments_tried": tried,
            "runtime_seconds": elapsed, "conflicts": conflicts}


def benchmark_plans():
    """Three deterministic increasing-size examples used in the report/demo."""
    plans = {
        "small (3 tasks)": [Task("Email", 30), Task("Study", 60), Task("Walk", 30)],
        "medium (5 tasks)": [Task("Email", 30), Task("Study", 60), Task("Call", 30),
                             Task("Shopping", 60), Task("Walk", 30)],
        "large (8 tasks)": [Task("Email", 30), Task("Study", 60), Task("Call", 30),
                            Task("Shopping", 60), Task("Walk", 30), Task("Project", 90),
                            Task("Read", 60), Task("Exercise", 60)],
    }
    rows = []
    for name, tasks in plans.items():
        rows.append((name, schedule(tasks, "plain"), schedule(tasks, "ac3")))
    return rows
