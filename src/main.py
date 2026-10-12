"""Context-aware Smart Personal Assistant command-line application."""
from datetime import datetime
import ast
import json
import operator
from pathlib import Path
import re

try:
    from .knowledge import forward_chain, task_facts
    from .planner import Task, benchmark_plans, schedule
except ImportError:  # supports `python src/main.py` from the repository root
    from knowledge import forward_chain, task_facts
    from planner import Task, benchmark_plans, schedule

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "assistant_data.json"
CONFIDENCE_THRESHOLD = 0.62


def load_data():
    if not DATA_PATH.exists():
        return {"notes": [], "reminders": [], "unanswered_queries": []}
    with DATA_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)
    data.setdefault("notes", [])
    data.setdefault("reminders", [])
    data.setdefault("unanswered_queries", [])
    return data


def save_data(data):
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DATA_PATH.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def perceive(user_input):
    """Normalize a message before intent recognition."""
    return " ".join(user_input.lower().strip().split())


INTENT_PATTERNS = (
    ("forget_data", re.compile(r"\b(forget my data|delete my data|clear my data)\b"), 1.0),
    ("explain", re.compile(r"\b(why did you do that|why did you|explain that|why this)\b"), 1.0),
    ("plan_day", re.compile(r"\b(plan my day|schedule my day|make my schedule)\b"), 1.0),
    ("add_note", re.compile(r"\b(add|save|write)\s+(a\s+)?note\b"), 0.96),
    ("view_notes", re.compile(r"\b(show|view|list)\s+(my\s+)?notes\b"), 0.96),
    ("add_reminder", re.compile(r"\b(add|set|create)\s+(a\s+)?(reminder|meeting|task)\b"), 0.96),
    ("view_reminders", re.compile(r"\b(show|view|list)\s+(my\s+)?(reminders|meetings|tasks)\b"), 0.96),
    ("calculator", re.compile(r"\b(calculate|compute)\b|\bwhat is\s+[\d(+-][\d\s()+*/%.-]*$"), 0.90),
    ("datetime", re.compile(r"\b(what time|current time|what date|today's date|date today|time now)\b|\b(date|time)\b"), 0.88),
    ("greeting", re.compile(r"^(hi|hello|hey|good morning|good afternoon|good evening)\b"), 0.91),
    ("lookup", re.compile(r"\b(what is|who is|define|tell me about)\b"), 0.66),
)


def recognize(user_input):
    """Return (intent, confidence) from transparent phrase rules."""
    text = perceive(user_input)
    for intent, pattern, confidence in INTENT_PATTERNS:
        if pattern.search(text):
            return intent, confidence
    return "unknown", 0.25


def decide(user_input):
    """Backward-compatible intent-only interface used by the Phase-1 tests."""
    return recognize(user_input)[0]


_OPERATORS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
              ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
              ast.Mod: operator.mod, ast.Pow: operator.pow, ast.USub: operator.neg,
              ast.UAdd: operator.pos}


def safe_calculate(expression):
    def evaluate(node):
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
            left, right = evaluate(node.left), evaluate(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 8:
                raise ValueError("Exponent is too large")
            return _OPERATORS[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
            return _OPERATORS[type(node.op)](evaluate(node.operand))
        raise ValueError("Only basic arithmetic is supported")
    tree = ast.parse(expression, mode="eval")
    return evaluate(tree)


def _parse_task(message, kind="reminder"):
    """Parse `title; duration 30; deadline 15:00; earliest 09:30; fixed 10:00`."""
    segments = [part.strip() for part in message.split(";") if part.strip()]
    if not segments:
        return None
    title = re.sub(r"^(add|set|create)\s+(a\s+)?(reminder|meeting|task)\s*:?\s*", "", segments[0], flags=re.I).strip()
    fields = {"duration": 30, "deadline": "17:00", "earliest": "09:00", "fixed_start": None,
              "due_today": False}
    for segment in segments[1:]:
        if re.fullmatch(r"due\s+today", segment, flags=re.I):
            fields["due_today"] = True
            continue
        match = re.fullmatch(r"(duration|deadline|earliest|fixed(?:_start)?)\s+(.+)", segment, flags=re.I)
        if not match:
            continue
        key, value = match.group(1).lower(), match.group(2).strip()
        if key == "duration":
            try:
                fields["duration"] = int(value.split()[0])
            except ValueError:
                continue
        elif key == "deadline":
            fields["deadline"] = value
        elif key == "earliest":
            fields["earliest"] = value
        else:
            fields["fixed_start"] = value
    try:
        # Validate times before saving malformed task data.
        for key in ("deadline", "earliest", "fixed_start"):
            if fields[key] is not None and not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", fields[key]):
                return None
        if fields["duration"] <= 0:
            return None
    except (TypeError, ValueError):
        return None
    return {"title": title, **fields, "kind": kind}


def _format_tasks(reminders):
    if not reminders:
        return "You have no saved reminders or meetings."
    lines = []
    for i, task in enumerate(reminders, 1):
        if isinstance(task, str):  # Phase-1 JSON compatibility
            lines.append(f"{i}. {task}")
        else:
            suffix = f" ({task.get('duration', 30)} min)"
            if task.get("fixed_start"):
                suffix += f" at {task['fixed_start']}"
            lines.append(f"{i}. {task['title']}{suffix}")
    return "Your reminders and meetings:\n" + "\n".join(lines)


def _stored_tasks(reminders):
    tasks = []
    for item in reminders:
        if isinstance(item, str):
            tasks.append(Task(title=item))
        else:
            tasks.append(Task(title=item["title"], duration=item.get("duration", 30),
                              earliest=item.get("earliest", "09:00"),
                              deadline=item.get("deadline", "17:00"),
                              fixed_start=item.get("fixed_start"),
                              kind=item.get("kind", "reminder"),
                              due_today=item.get("due_today", False)))
    return tasks


def _lookup(text):
    text = perceive(text)
    knowledge = {
        "python": "Python is a general-purpose programming language known for readable syntax.",
        "csp": "A constraint satisfaction problem assigns values to variables while satisfying constraints.",
        "intelligent agent": "An intelligent agent perceives its environment, chooses an action, and acts on it.",
        "ac-3": "AC-3 removes domain values that have no compatible value in a neighboring variable's domain.",
    }
    for topic, answer in knowledge.items():
        if topic in text:
            return answer
    return None


def respond(intent, message, last_trace=None):
    """Execute non-interactive intents; the CLI handles missing slots interactively."""
    data = load_data()
    if intent == "greeting":
        return "Hello! How can I help you?", []
    if intent == "datetime":
        return datetime.now().strftime("Current date and time: %d-%m-%Y %I:%M %p"), []
    if intent == "calculator":
        expression = re.sub(r"^(calculate|compute|what is)\s*", "", message, flags=re.I).rstrip("? .")
        try:
            return f"Result: {safe_calculate(expression)}", []
        except (ValueError, SyntaxError, ZeroDivisionError, TypeError, OverflowError) as error:
            return f"I couldn't calculate that: {error}", []
    if intent == "view_notes":
        if not data["notes"]:
            return "You have no saved notes.", []
        return "Your notes:\n" + "\n".join(f"{i}. {note}" for i, note in enumerate(data["notes"], 1)), []
    if intent == "view_reminders":
        return _format_tasks(data["reminders"]), []
    if intent == "lookup":
        answer = _lookup(message)
        if answer:
            return answer, []
    if intent == "forget_data":
        save_data({"notes": [], "reminders": [], "unanswered_queries": []})
        return "Your saved notes, reminders, and unanswered-query log have been cleared.", []
    if intent == "explain":
        if not last_trace:
            return "I don't have a previous decision trace in this session yet.", []
        return "Decision explanation:\n" + "\n".join(last_trace), []
    if intent == "plan_day":
        tasks = _stored_tasks(data["reminders"])
        if not tasks:
            return "Add at least one reminder or meeting first, then ask me to plan your day.", []
        result = schedule(tasks, "ac3")
        explanation = ["CSP variables: reminder and meeting start times in 30-minute slots.",
                       "Constraints: task time windows and durations, 09:00-17:00 working hours, 12:00-13:00 break, and no overlaps.",
                       "Solver: backtracking with forward checking and AC-3."]
        if not result["success"]:
            explanation.extend("Conflict: " + conflict for conflict in result["conflicts"])
            return "I couldn't make a schedule:\n- " + "\n- ".join(result["conflicts"]), explanation
        lines = [f"{title}: {slot['start']}-{slot['end']}" for title, slot in result["plan"].items()]
        explanation.extend(f"Assigned {title} to {slot['start']}-{slot['end']}."
                           for title, slot in result["plan"].items())
        return ("Your day plan (work hours 09:00-17:00; break 12:00-13:00):\n" +
                "\n".join(lines) + f"\nAssignments tried: {result['assignments_tried']}"), explanation
    return "", []


def _record_unknown(message):
    data = load_data()
    data["unanswered_queries"].append({"query": message, "logged_at": datetime.now().isoformat(timespec="seconds")})
    save_data(data)


def _save_note(note):
    data = load_data()
    data["notes"].append(note.strip())
    save_data(data)


def _save_task(task):
    data = load_data()
    data["reminders"].append(task)
    save_data(data)
    _, trace = forward_chain(task_facts(_stored_tasks(data["reminders"])))
    return trace


def _run_benchmark():
    print("Plan comparison (runtime varies by computer):")
    print("Plan | Plain BT tried/time | BT + FC + AC-3 tried/time")
    for name, plain, advanced in benchmark_plans():
        print(f"{name} | {plain['assignments_tried']} / {plain['runtime_seconds']:.6f}s | "
              f"{advanced['assignments_tried']} / {advanced['runtime_seconds']:.6f}s")


def run_agent():
    print("Smart Personal Assistant — Context-Aware Intelligent Agent")
    print("Type 'exit' to stop. Add tasks as: add meeting: title; duration 60; deadline 11:00")
    print("Ask 'benchmark plans' for the required CSP comparison.")
    last_trace = []
    pending = None
    while True:
        try:
            message = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAssistant: Goodbye!")
            break
        if message.lower() == "exit":
            print("Assistant: Goodbye!")
            break
        if message.lower() in {"benchmark plans", "compare planners"}:
            _run_benchmark()
            continue
        if pending:
            if pending == "note":
                _save_note(message)
                last_trace = ["Perceived a note response while note entry was pending.", "Decided to save_note.", "Saved the note to the JSON file."]
                print("Assistant: Note saved successfully.")
            elif pending == "calculator":
                try:
                    answer = f"Result: {safe_calculate(message)}"
                except (ValueError, SyntaxError, ZeroDivisionError, TypeError, OverflowError) as error:
                    answer = f"I couldn't calculate that: {error}"
                last_trace = ["Perceived a calculation response while calculator input was pending.",
                              "Decided to evaluate basic arithmetic safely.", "Action: " + answer]
                print("Assistant:", answer)
            else:
                task = _parse_task(message, pending)
                if not task or not task["title"]:
                    print("Assistant: I couldn't read that. Give a title, optionally followed by '; duration 30; deadline 15:00'.")
                    continue
                rule_trace = _save_task(task)
                last_trace = [f"Perceived a {pending} entry.", "Decided to save it as a schedulable task.",
                              f"Stored '{task['title']}' ({task['duration']} minutes)."]
                last_trace.extend(f"Rule {item['rule']}: {item['explanation']} Evidence: {', '.join(item['premises'])} => {item['conclusion']}"
                                  for item in rule_trace)
                print("Assistant: Reminder/meeting saved. Ask 'plan my day' to schedule it.")
            pending = None
            continue

        if message.lower().startswith("benchmark"):
            _run_benchmark()
            continue
        if message.lower() in {"help", "what can you do"}:
            print("Assistant: I can greet you, give date/time, calculate, look up basic topics, manage notes and reminders, plan your day, explain a decision, and forget saved data.")
            last_trace = ["Recognized help request (confidence 0.95).", "Selected the help response action."]
            continue
        intent, confidence = recognize(message)
        if confidence < CONFIDENCE_THRESHOLD:
            _record_unknown(message)
            last_trace = [f"Recognized intent as unknown with confidence {confidence:.2f}, below threshold {CONFIDENCE_THRESHOLD:.2f}.",
                          "Logged the unanswered query and asked the user to clarify."]
            print(f"Assistant: I'm not sure what you mean (confidence {confidence:.2f}). Could you rephrase or tell me what you want me to do?")
            continue

        trace = [f"Perceived: {perceive(message)}", f"Decided: {intent} (confidence {confidence:.2f})."]
        if intent == "add_note":
            content = re.sub(r"^(add|save|write)\s+(a\s+)?note\s*:?\s*", "", message, flags=re.I).strip()
            if content:
                _save_note(content)
                response = "Note saved successfully."
            else:
                pending = "note"
                response = "Sure, what would you like me to note?"
        elif intent == "calculator" and not re.sub(r"^(calculate|compute|what is)\s*", "", message, flags=re.I).strip("? ."):
            pending = "calculator"
            response = "What expression should I calculate?"
        elif intent == "add_reminder":
            kind = "meeting" if "meeting" in message.lower() else "reminder"
            task = _parse_task(message, kind)
            if task and task["title"]:
                rule_trace = _save_task(task)
                response = "Reminder/meeting saved. Ask 'plan my day' to schedule it."
                trace.extend(f"Rule {item['rule']}: {item['explanation']} Evidence: {', '.join(item['premises'])} => {item['conclusion']}"
                             for item in rule_trace)
            else:
                pending = kind
                response = f"What should I add as a {kind}? You can include duration, deadline, earliest time, and fixed time."
        else:
            response, extra = respond(intent, message, last_trace)
            if response:
                trace.extend(extra)
            else:
                _record_unknown(message)
                intent = "unknown"
                response = "I don't know that yet, so I've logged your question to improve the assistant. Could you clarify or ask about Python, CSP, AC-3, or intelligent agents?"
        if intent != "explain":
            last_trace = trace + (["Action: " + response.splitlines()[0]] if response else [])
        print("Assistant:", response)


if __name__ == "__main__":
    run_agent()
