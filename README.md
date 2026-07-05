# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Output from running the demo script `main.py` (`python main.py`):

```
Today's Schedule for Alex Rivera
================================
Daily plan:
  08:00–08:45  Vet appointment (45 min) [priority 5]
  08:45–09:00  Feed breakfast (15 min) [priority 4]
  09:00–09:30  Morning walk (30 min) [priority 3]
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

PawPal+ goes beyond a flat task list with four scheduling behaviors. Each is
implemented as a focused method so it can be tested in isolation and reused by
the planning pipeline in [`Scheduler.generate_plan()`](pawpal_system.py#L178).

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | [`Scheduler.sort_by_priority()`](pawpal_system.py#L205), [`Scheduler.sort_by_time()`](pawpal_system.py#L219) | Priority-first (ties broken by due time) drives the plan; due-time sort available for chronological views |
| Filtering | [`Scheduler.filter_by_available_time()`](pawpal_system.py#L230), [`Owner.filter_tasks()`](pawpal_system.py#L141) | Drop tasks that fit no window; filter by pet name and/or completion status |
| Conflict handling | [`Scheduler.detect_conflicts()`](pawpal_system.py#L291), [`Scheduler.resolve_conflicts()`](pawpal_system.py#L254) | Warn on overlapping due windows; greedily pack tasks into non-overlapping slots |
| Recurring tasks | [`Task.is_recurring()`](pawpal_system.py#L41), [`Task.next_occurrence()`](pawpal_system.py#L45), [`Pet.complete_task()`](pawpal_system.py#L102) | Daily/weekly tasks spawn their next occurrence on completion |

### Sorting behavior

- **[`Scheduler.sort_by_priority(tasks)`](pawpal_system.py#L205)** — returns a
  new list ordered by descending `priority`, breaking ties by the earliest
  `due_time` (`key=lambda t: (-t.priority, t.due_time)`). This is the ordering
  `generate_plan()` uses so the most important tasks claim slot time first. The
  input list is left unmodified.
- **[`Scheduler.sort_by_time(tasks)`](pawpal_system.py#L219)** — returns tasks
  ordered by `due_time`, earliest first, for a chronological "what's next" view.

### Filtering behavior

- **[`Scheduler.filter_by_available_time(tasks, slots)`](pawpal_system.py#L230)**
  — keeps only tasks that are not yet completed **and** whose `duration` fits
  inside at least one availability window. Tasks that can never fit are dropped
  before placement, and order is preserved.
- **[`Owner.filter_tasks(completed=None, pet_name=None)`](pawpal_system.py#L141)**
  — filters tasks across all pets by **completion status** and/or **pet name**
  (case-insensitive). The two filters combine with AND; passing neither returns
  every task the owner has.

### Conflict detection logic

- **[`Scheduler.detect_conflicts(owner)`](pawpal_system.py#L291)** — a
  non-fatal check that treats each pending task as occupying the half-open
  window `[due_time, due_time + duration)`. It compares every pair of pending
  tasks (via `itertools.combinations`) and flags any overlap — two windows
  overlap iff each starts before the other ends. Rather than raising, it returns
  a human-readable warning per clash (naming whether the same pet or different
  pets are involved); an empty list means no conflicts.
- **[`Scheduler.resolve_conflicts(tasks, slots)`](pawpal_system.py#L254)** — the
  placement half of the pipeline. It greedily drops each (priority-sorted) task
  into the first slot with enough remaining room, advancing a per-slot cursor so
  scheduled tasks never overlap. Tasks that fit nowhere are omitted.

### Recurring task logic

- **[`Task.is_recurring()`](pawpal_system.py#L41)** — `True` when `recurrence`
  is `"daily"` or `"weekly"` (one-off tasks use `"none"`).
- **[`Task.next_occurrence()`](pawpal_system.py#L45)** — returns a fresh,
  pending `Task` (with its own `id`) due one cadence later (`timedelta(days=1)`
  or `timedelta(weeks=1)`), or `None` for a non-recurring task.
- **[`Pet.complete_task(task)`](pawpal_system.py#L102)** — marks the task done
  and, if it recurs, appends its next occurrence to the pet automatically so the
  routine keeps rolling forward.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
