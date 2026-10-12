"""Regenerate report.pdf from the final-project report content."""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(__file__).resolve().parent / "report.pdf"
NAVY = colors.HexColor("#18324A")
TEAL = colors.HexColor("#1E7A78")
PALE = colors.HexColor("#EAF1F5")


def make_styles():
    base = getSampleStyleSheet()
    base.add(ParagraphStyle(name="CoverTitle", parent=base["Title"], fontName="Helvetica-Bold",
        fontSize=23, leading=28, textColor=NAVY, alignment=TA_CENTER, spaceAfter=5*mm))
    base.add(ParagraphStyle(name="CoverSub", parent=base["Normal"], fontSize=11, leading=15,
        textColor=TEAL, alignment=TA_CENTER, spaceAfter=8*mm))
    base.add(ParagraphStyle(name="Section", parent=base["Heading1"], fontName="Helvetica-Bold",
        fontSize=15, leading=19, textColor=NAVY, spaceBefore=2*mm, spaceAfter=3*mm))
    base.add(ParagraphStyle(name="Subsection", parent=base["Heading2"], fontName="Helvetica-Bold",
        fontSize=11, leading=14, textColor=TEAL, spaceBefore=2*mm, spaceAfter=1.5*mm))
    base.add(ParagraphStyle(name="BodyReport", parent=base["BodyText"], fontName="Helvetica",
        fontSize=9.4, leading=13.2, spaceAfter=2.7*mm))
    base.add(ParagraphStyle(name="SmallReport", parent=base["BodyText"], fontName="Helvetica",
        fontSize=8, leading=10.4, spaceAfter=1.4*mm))
    base.add(ParagraphStyle(name="HeadCell", parent=base["BodyText"], fontName="Helvetica-Bold",
        fontSize=7.1, leading=8.4, textColor=colors.white))
    base.add(ParagraphStyle(name="BodyCell", parent=base["BodyText"], fontName="Helvetica",
        fontSize=7.7, leading=9.3))
    base.add(ParagraphStyle(name="CodeReport", parent=base["BodyText"], fontName="Courier",
        fontSize=8.2, leading=11.2, leftIndent=5*mm, textColor=NAVY, spaceAfter=1.4*mm))
    base.add(ParagraphStyle(name="CalloutReport", parent=base["BodyText"], fontName="Helvetica-Bold",
        fontSize=9, leading=12.5, backColor=PALE, borderColor=TEAL, borderWidth=.6,
        borderPadding=6, spaceBefore=2*mm, spaceAfter=3*mm))
    return base


def footer(canvas, doc):
    canvas.saveState()
    width, _ = A4
    canvas.setStrokeColor(colors.HexColor("#D8E1E8"))
    canvas.line(18*mm, 14*mm, width-18*mm, 14*mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#647582"))
    canvas.drawString(18*mm, 9*mm, "Smart Personal Assistant | Final Project Report")
    canvas.drawRightString(width-18*mm, 9*mm, str(doc.page))
    canvas.restoreState()


def build():
    s = make_styles()
    p = lambda text, style="BodyReport": Paragraph(text, s[style])
    doc = SimpleDocTemplate(str(OUTPUT), pagesize=A4, rightMargin=19*mm, leftMargin=19*mm,
        topMargin=17*mm, bottomMargin=20*mm,
        title="Smart Personal Assistant - Final Project Report", author="Student project")
    story = []
    # Page 1: formulation and approach.
    story += [Spacer(1, 5*mm), p("Smart Personal Assistant", "CoverTitle"),
        p("Context-Aware Intelligent Agent | Final Project Extension", "CoverSub"),
        p("Course project: Intelligent Agent<br/>Implementation: Python command-line application", "CalloutReport"),
        p("1. Problem formulation", "Section"),
        p("The project is a local text assistant for everyday requests. Phase 1 handles greetings, date and time, basic arithmetic, notes, and reminders. The final extension adds day planning, rule-based reasoning, uncertainty-aware clarification, explanations, and user-controlled data deletion. The agent follows <b>Perceive -&gt; Decide -&gt; Act</b>: it normalizes a message, selects an intent with a confidence score, applies relevant rules, and responds or takes an action."),
        p("The scheduling extension is a constraint satisfaction problem (CSP). Each reminder or meeting is a variable whose value is its start time. Its domain contains 30-minute slots that satisfy task duration, earliest time, deadline, working hours (09:00-17:00), and fixed lunch break (12:00-13:00). Fixed-time meetings have singleton domains. Binary constraints require every pair of tasks to have non-overlapping intervals. The goal test is a complete assignment satisfying every constraint."),
        p("2. Approach", "Section"),
        p("Intent recognition uses transparent phrase patterns rather than a hidden model. Each recognized pattern returns a score. Below 0.62, the assistant asks a clarifying question and stores the unanswered query. This score is a rule-based confidence indicator, not a calibrated probability. Missing note or task information starts multi-turn slot filling. Task fields include duration, earliest time, deadline, and fixed start."),
        p("The knowledge base uses first-order-style predicates and forward chaining. The engine matches premises to facts, binds variables, appends conclusions, and records a trace. The assistant can show this trace with <b>why did you do that?</b>.")]
    story.append(PageBreak())
    # Page 2: solver, complexity, and measured comparison.
    story += [p("Algorithms and analysis", "Section"), p("The explicit rules are:", "BodyReport"),
        p('Meeting(x) AND StartsBefore(x, "10:00") -&gt; Remind(x, 30)<br/>Task(x) AND DueToday(x) -&gt; Priority(x, "high")', "CodeReport"),
        p("The plain CSP solver uses chronological backtracking. The enhanced solver selects the variable with the smallest remaining domain, applies forward checking after each choice, and enforces arc consistency with AC-3. If scheduling fails, the assistant reports empty domains and identifiable fixed-time overlaps."),
        p("3. Complexity", "Section"),
        p("Let <i>n</i> be task count and <i>d</i> the largest domain size. Plain backtracking has worst-case time <b>O(d^n)</b> and uses <b>O(nd)</b> space for domains and recursion state. Forward checking filters neighboring domains after each assignment but does not improve the worst-case exponential bound. AC-3 has the standard worst-case bound <b>O(e d^3)</b> for <i>e</i> directed constraint arcs and domain size <i>d</i>. Domains and the arc queue use <b>O(nd + e)</b> space."),
        p("The planner uses fixed 30-minute granularity and one workday. It returns the first valid schedule rather than optimizing preferences. Longer tasks must be multiples of 30 minutes. Travel time, priorities, and task dependencies are not modeled."),
        p("4. Results", "Section"),
        p("Three deterministic plans with 3, 5, and 8 tasks were each solved once by both methods. The table shows assignment attempts and wall-clock time from one local run. Runtime varies by computer and Python version.")]
    table_data = [[p("Plan", "HeadCell"), p("Tasks", "HeadCell"),
        p("Plain BT<br/>tried", "HeadCell"), p("Plain BT<br/>seconds", "HeadCell"),
        p("BT + FC + AC-3<br/>tried", "HeadCell"), p("BT + FC + AC-3<br/>seconds", "HeadCell")],
        ["Small", "3", "7", "0.0000614", "3", "0.0001226"],
        ["Medium", "5", "19", "0.0000643", "5", "0.0002950"],
        ["Large", "8", "47", "0.0001145", "8", "0.0008583"]]
    table = Table(table_data, colWidths=[22*mm, 13*mm, 23*mm, 27*mm, 38*mm, 40*mm], repeatRows=1)
    table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),NAVY), ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("GRID",(0,0),(-1,-1),.4,colors.HexColor("#CBD6DE")), ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,PALE]),
        ("ALIGN",(1,1),(-1,-1),"CENTER"), ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("LEFTPADDING",(0,0),(-1,-1),4), ("RIGHTPADDING",(0,0),(-1,-1),4),
        ("TOPPADDING",(0,0),(-1,-1),5), ("BOTTOMPADDING",(0,0),(-1,-1),5)]))
    story += [table, Spacer(1, 3*mm), p("Both solvers found schedules for all plans. The enhanced solver tried fewer values through constrained-variable selection and propagation. Its runtime was higher on these tiny cases because propagation adds overhead; fewer assignments do not guarantee lower runtime for small instances. Larger or tighter plans are needed to see where pruning pays off.", "SmallReport")]
    story.append(PageBreak())
    # Page 3: inference trace, explanation, agent loop, reproducibility.
    story += [p("Evidence and explainability", "Section"), p("Inference trace example", "Subsection"),
        p("Given the facts:", "BodyReport"), p('Meeting("Project review")<br/>StartsBefore("Project review", "10:00")', "CodeReport"),
        p("The forward-chaining engine matches both premises of <b>early_meeting_reminder</b>, binds ?x to Project review, and infers:", "BodyReport"),
        p('Remind("Project review", 30)', "CodeReport"),
        p("The recorded trace includes both source facts, the rule name, the inferred fact, and its explanation that meetings before 10:00 receive a 30-minute advance reminder."),
        p("Example shown to the user", "Subsection"),
        p("After <b>plan my day</b>, the assistant presents scheduled tasks and assignments tried. If the user asks <b>why did you do that?</b>, it prints the perceived text, selected intent and confidence, and action. When a reminder rule fires, the trace identifies the meeting facts behind that recommendation."),
        p("Agent loop and action mapping", "Subsection")]
    loop = Table([[p("Perceive", "HeadCell"), p("Decide", "HeadCell"), p("Act", "HeadCell")],
        [p("Normalize user text", "BodyCell"), p("Select intent and confidence", "BodyCell"),
         p("Answer, clarify, store, explain, or schedule", "BodyCell")]],
        colWidths=[48*mm, 62*mm, 68*mm])
    loop.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),NAVY), ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("GRID",(0,0),(-1,-1),.4,colors.HexColor("#CBD6DE")), ("BACKGROUND",(0,1),(-1,-1),PALE),
        ("VALIGN",(0,0),(-1,-1),"TOP"), ("LEFTPADDING",(0,0),(-1,-1),6),
        ("RIGHTPADDING",(0,0),(-1,-1),6), ("TOPPADDING",(0,0),(-1,-1),6),
        ("BOTTOMPADDING",(0,0),(-1,-1),6)]))
    story += [loop, Spacer(1, 5*mm), p("Reproducibility", "Subsection"),
        p("The comparison is available in the running application with the <b>benchmark plans</b> command. The three inputs are deterministic and require no external dataset. Runtime is machine-dependent; rerun the command from a fresh clone. User data is stored locally and excluded from Git."),
        p("The existing Phase-1 tests remain in the repository. The extension is not claimed to be covered by those tests; its required comparison and inference example are available through the application and this report.", "CalloutReport")]
    story.append(PageBreak())
    # Page 4: responsible AI, reflection, references.
    story += [p("5. Responsible AI and reflection", "Section"), p("Privacy", "Subsection"),
        p("Notes, tasks, and unanswered query text are stored in a local JSON file without encryption. Queries can contain personal information. Users should avoid sensitive content and clear the data with <b>forget my data</b> before sharing a device or repository. The live data file is excluded from Git. The command clears notes, reminders, and query history together."),
        p("Bias and fairness", "Subsection"),
        p("The planner uses user-supplied time windows and does not use demographic attributes. Default working hours and a fixed lunch break may not suit every schedule, culture, care responsibility, accessibility need, or workplace. Users can enter earliest, deadline, and fixed-time constraints. Future work should make hours and breaks configurable and invite users to review recommendations before acting."),
        p("Accountability and governance", "Subsection"),
        p("The assistant does not send reminders externally or take actions without the user. It presents schedules for review, explains rule conclusions, and logs unanswered requests for improvement. Query logs should be reviewed and deleted when no longer needed. Before use beyond a classroom demo, data handling, retention, access controls, and applicable institutional and privacy requirements should be reviewed. The local lookup is limited; the assistant is not a source of professional advice."),
        p("Reflection", "Subsection"),
        p("The main design challenge is balancing search reduction against propagation overhead while keeping the CSP understandable. The enhanced solver reduced assignments in the sample plans, but propagation overhead made it slower at these small sizes. Next steps include automated tests for unsatisfiable schedules, configurable work hours, improved date/time parsing, and a visual schedule."),
        p("Conclusion", "Subsection"),
        p("The project demonstrates the intelligent-agent loop, explicit rules, forward-chaining inference, confidence-based clarification, explainable actions, user-controlled data deletion, and measurable CSP comparison. AI assistance was used during development. The student should review and be prepared to explain every component and adapt it during the viva."),
        p("References", "Subsection"),
        p("Python Software Foundation, <i>Python 3 Documentation</i>, https://docs.python.org/3/<br/>Mackworth, A. K. (1977), “Consistency in Networks of Relations,” <i>Artificial Intelligence</i>, 8(1), 99-118.<br/>Russell, S. and Norvig, P., <i>Artificial Intelligence: A Modern Approach</i>, 4th edition, Pearson, 2021.", "SmallReport")]
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(OUTPUT.resolve())


if __name__ == "__main__":
    build()
