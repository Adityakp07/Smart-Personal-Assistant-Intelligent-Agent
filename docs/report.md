# Smart Personal Assistant - Final Project Report

**Course project:** Intelligent Agent
**Extension:** Context-Aware Conversational Agent
**Implementation:** Python command-line application

## 1. Problem formulation

The project is a local text assistant for everyday requests. Its Phase-1 features include greetings, date/time, basic arithmetic, notes, and reminders. The final extension adds day planning, rule-based reasoning, uncertainty-aware clarification, explanations, and a user command to delete stored data. The agent follows **Perceive -> Decide -> Act**: it normalizes a message, selects an intent with a confidence score, applies relevant rules, and responds or takes an action.

The extension's scheduling problem is a constraint satisfaction problem (CSP). Each saved reminder or meeting is a variable whose value is its start time. A variable's domain is the set of 30-minute start slots that fit the task's duration, earliest time, deadline, working hours (09:00-17:00), and fixed lunch break (12:00-13:00). A fixed-time meeting has a singleton domain. Binary constraints require every pair of tasks to have non-overlapping intervals. The goal test is a complete assignment satisfying every unary and pairwise constraint.

## 2. Approach

Intent recognition uses transparent phrase patterns rather than a hidden model. Each recognized pattern returns a score; when the score is below 0.62 the agent asks the user to clarify and stores the unanswered query. The score is a rule-based confidence indicator, not a calibrated probability. A missing note or task title starts a multi-turn slot-filling exchange. Tasks accept duration, earliest time, deadline, and fixed start fields.

The knowledge base uses first-order-style predicates and a forward-chaining engine. Current rules are:

1. `Meeting(x) AND StartsBefore(x, "10:00") -> Remind(x, 30)`
2. `Task(x) AND DueToday(x) -> Priority(x, "high")`

The engine repeatedly matches rule premises against known facts, binds variables, adds new conclusions, and records the premises and rule name as a trace. The `why did you do that?` command displays the preceding decision trace and, when applicable, the fired rules and evidence.

The plain CSP solver uses chronological backtracking. The enhanced solver chooses a variable with the smallest remaining domain, applies forward checking after each choice, and enforces arc consistency with AC-3. When scheduling fails, it reports empty domains and fixed-time overlaps when they can be identified.

## 3. Complexity

Let *n* be the number of tasks and *d* the largest domain size. Plain backtracking has worst-case time **O(d^n)** and uses **O(nd)** space to retain domains and recursion state. Forward checking filters neighboring domains after each assignment; this can reduce explored search but does not improve the worst-case exponential bound. AC-3 has the standard worst-case bound **O(e d^3)** for *e* directed constraint arcs and domain size *d*. The implementation also stores the domains and arc queue, using **O(nd + e)** space. These bounds describe the general problem; the small one-day plans here have modest domains and are solved quickly.

The planner uses fixed 30-minute granularity and a single workday. It is not an optimization solver: it returns the first valid schedule found. Longer tasks must be multiples of 30 minutes. It does not model travel time, task priorities, or dependencies between tasks.

## 4. Results

The deterministic comparison plans contain 3, 5, and 8 tasks. Each solver is run once per plan. The table reports assignments attempted and elapsed wall-clock time from one local run; runtime varies by computer and Python version.

| Plan | Tasks | Plain BT assignments | Plain BT runtime (s) | BT + FC + AC-3 assignments | BT + FC + AC-3 runtime (s) |
|---|---:|---:|---:|---:|---:|
| Small | 3 | 7 | 0.0000614 | 3 | 0.0001226 |
| Medium | 5 | 19 | 0.0000643 | 5 | 0.0002950 |
| Large | 8 | 47 | 0.0001145 | 8 | 0.0008583 |

Both solvers found a schedule for all three plans. The enhanced solver tried fewer values because it selects the most constrained task and removes incompatible times early. Its measured runtime was higher on these tiny cases because forward checking and AC-3 add overhead; fewer assignments do not guarantee a shorter runtime for small instances. Larger or tighter schedules are needed to see when pruning pays off.

**Inference trace example.** Given `Meeting("Project review")` and `StartsBefore("Project review", "10:00")`, the forward-chaining engine matches both premises of `early_meeting_reminder`, binds `?x = Project review`, and infers `Remind("Project review", 30)`. The trace includes the two source facts, the rule name, the inferred fact, and its explanation.

**User-visible explanation example.** After a `plan my day` request, `why did you do that?` returns the perceived text, the selected `plan_day` intent and confidence, and the action taken. When a reminder rule fires, the trace also shows which meeting facts caused the recommendation. This makes both intent selection and rule-based advice inspectable.

## 5. Responsible AI, reflection, and conclusion

**Privacy:** Notes, tasks, and unanswered query text are stored in a local JSON file without encryption. A query may contain personal information. Users should avoid sensitive content and clear the file with `forget my data` before sharing a device or repository. The data file is excluded from Git. The deletion command clears notes, reminders, and query history together.

**Bias and fairness:** The planner uses time windows supplied by the user and does not use demographic attributes. Default working hours and a fixed lunch break may not fit every user's schedule, culture, care responsibilities, accessibility needs, or workplace. The current model permits user-entered earliest/deadline/fixed times; future work should make working hours and breaks configurable and invite users to review recommendations before acting.

**Accountability and governance:** The assistant does not send reminders externally or take actions without the user. It presents schedules for review, explains rule conclusions, and logs unanswered requests for improvement. Query logs should be reviewed and deleted when no longer needed. Before deployment beyond a classroom demo, data handling, retention, access controls, and applicable institutional and privacy requirements should be reviewed. The local lookup is limited and the assistant should not be treated as professional advice.

The most difficult design issue is balancing search reduction against propagation overhead while keeping the CSP understandable. A next version should add automated tests for unsatisfiable schedules, make work hours configurable, improve date/time parsing, and provide a visual schedule. The project demonstrates the required agent loop, an explicit knowledge base, uncertainty handling, explainability, data deletion, and measurable CSP comparison. The assistant was developed with AI assistance; the student should review and be prepared to explain every component and adapt it live for the viva.

## References

- Python Software Foundation, *Python 3 Documentation*, https://docs.python.org/3/
- Mackworth, A. K. (1977), “Consistency in Networks of Relations,” *Artificial Intelligence*, 8(1), 99-118.
- Russell, S. and Norvig, P., *Artificial Intelligence: A Modern Approach*, 4th edition, Pearson, 2021.
