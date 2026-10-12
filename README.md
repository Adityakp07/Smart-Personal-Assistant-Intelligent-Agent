# Smart Personal Assistant - Context-Aware Intelligent Agent

A small Python command-line assistant that applies the **Perceive -> Decide -> Act** loop to daily tasks. The final-project extension adds a day-planning CSP, a transparent forward-chaining rule base, confidence-aware clarification, multi-turn slot filling, decision explanations, and user-controlled data deletion.

## Features

- Greeting, date/time, safe arithmetic, and small built-in information lookup.
- Add and view notes; add and view reminders and meetings. Data persists locally in `data/assistant_data.json`, which is created when the assistant first saves data and is excluded from Git to keep personal data out of the repository.
- `plan my day` assigns tasks to 30-minute time slots between 09:00 and 17:00, leaving 12:00-13:00 free. It respects task durations, earliest times, deadlines, fixed start times, and no-overlap constraints.
- Day planning uses backtracking with forward checking and AC-3. The comparison command runs plain backtracking and the enhanced solver on three increasing task sets.
- Rule-based intent recognition reports confidence; low-confidence requests trigger a clarification and are logged in the JSON file.
- Forward chaining applies the explicit rules in `src/knowledge.py` to task facts.
- `why did you do that?` prints the last decision trace. `forget my data` clears notes, reminders, and unanswered-query history.
- Unknown information requests are logged for future improvement.

## Requirements

- Python 3.10 or newer.
- The assistant itself uses only the Python standard library. `pytest` is listed for the existing course test suite; `reportlab` is used only to regenerate the PDF report.

## Run in VS Code

1. Clone this repository and open its folder in VS Code.
2. Open **Terminal -> New Terminal** in the repository root.
3. (Optional) Create/activate a virtual environment and install dependencies:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   py -m pip install -r requirements.txt
   ```

4. Start the assistant:

   ```powershell
   py src/main.py
   ```

   You can also select the repository's Python interpreter in VS Code and run `src/main.py`.

## Example interaction

```text
You: add meeting
Assistant: What should I add as a meeting? You can include duration, deadline, earliest time, and fixed time.
You: Project review; duration 60; deadline 11:30; fixed 09:30
Assistant: Reminder/meeting saved. Ask 'plan my day' to schedule it.
You: add reminder: finish lab; duration 60; deadline 16:00
You: plan my day
Assistant: Your day plan (work hours 09:00-17:00; break 12:00-13:00):
Project review: 09:30-10:30
finish lab: 10:30-11:30
...
You: why did you do that?
Assistant: Decision explanation:
Perceived: plan my day
Decided: plan_day (confidence 1.00).
...
You: forget my data
Assistant: Your saved notes, reminders, and unanswered-query log have been cleared.
```

Task fields use `;` separators and 24-hour `HH:MM` times. For example:

```text
add meeting: Design review; duration 60; earliest 09:00; deadline 11:00; fixed 10:00
```

Add `due today` to mark a task for the high-priority inference rule:

```text
add reminder: submit assignment; duration 60; deadline 16:00; due today
```

## Intent to action map

| Intent | Example | Action |
|---|---|---|
| Greeting | `hello` | Return greeting |
| Date/time | `what time is it?` | Display local system date/time |
| Calculator | `calculate 12 * (4 + 2)` | Safely evaluate basic arithmetic |
| Add/view note | `add note: call the lab` / `show notes` | Save or list persistent notes; asks a follow-up if content is missing |
| Add/view reminder | `add reminder: submit form` / `show reminders` | Save/list schedulable tasks |
| Plan day | `plan my day` | Solve the scheduling CSP and report conflicts if unsatisfiable |
| Basic lookup | `what is AC-3?` | Answer from the small local knowledge list; otherwise log and clarify |
| Explain | `why did you do that?` | Print the previous decision and applicable rule trace |
| Forget data | `forget my data` | Clear saved notes, reminders, and unanswered queries |
| Unknown | Any unsupported request | Ask for clarification and append it to unanswered query history |

## Agent and reasoning model

```text
Perceive: normalize the text
    -> Decide: phrase rules select intent and attach confidence
    -> Reason: forward-chain applicable facts/rules
    -> Act: answer, clarify, store data, or solve the day-planning CSP
```

The rule base is written in first-order-style predicates in `src/knowledge.py`, for example:

```text
Meeting(x) AND StartsBefore(x, "10:00") -> Remind(x, 30)
Task(x) AND DueToday(x) -> Priority(x, "high")
```

## CSP formulation and comparison

- **Variables:** one start-time variable per reminder/meeting.
- **Domains:** 30-minute start slots inside each task's earliest/deadline window, working hours, and outside the fixed lunch break. Fixed meetings have singleton domains.
- **Constraints:** tasks cannot overlap; all unary time-window and working-hour constraints must hold.
- **Plain solver:** chronological backtracking.
- **Enhanced solver:** minimum-remaining-values ordering, forward checking, and AC-3 propagation.

At the assistant prompt, type `benchmark plans` to print assignments tried and runtime for 3, 5, and 8 tasks. Runtime is machine-dependent; the report records the run used for submission. On impossible plans the assistant lists empty-domain causes and fixed-time overlaps when identifiable.

To regenerate the submitted PDF after editing `docs/build_report.py`, install the listed requirements and run `py docs/build_report.py` from the repository root.

## Project layout

```text
src/main.py       CLI, intent confidence, slot filling and actions
src/planner.py    CSP domains, backtracking, forward checking and AC-3
src/knowledge.py  explicit rules and forward-chaining inference
tests/            Phase-1 intent tests
data/             local persistent JSON state (created at runtime; not tracked)
docs/             project report (Markdown and PDF) and report builder
```

## Limitations and responsible use

Lookup is local and intentionally small; it does not browse the web or provide professional advice. Intent confidence is a transparent rule score, not a calibrated probability. The planner schedules within one day and uses 30-minute granularity. Data is stored locally as plain JSON; do not enter sensitive information on a shared device. The user can erase this data with `forget my data`. Query logs may contain the text entered by the user, so inspect/clear them before sharing the repository.

## References

- Python Software Foundation, *Python 3 Documentation*, https://docs.python.org/3/
- Mackworth, A. K. (1977), “Consistency in Networks of Relations,” *Artificial Intelligence*, 8(1), 99-118. (Constraint propagation / arc consistency.)
- Russell, S. and Norvig, P., *Artificial Intelligence: A Modern Approach*, 4th edition, Pearson, 2021. (Search, constraint satisfaction, and intelligent-agent concepts.)

## License

MIT. See [LICENSE](LICENSE).
