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

## ✨ Features

PawPal+ implements the following algorithms and behaviors (all backed by tests
in [`test_pawpal_system.py`](test_pawpal_system.py)):

- **Priority-first scheduling** — [`Scheduler.generate_plan()`](pawpal_system.py#L178)
  orders tasks by descending priority (ties broken by earliest due time), then
  greedily packs them into your availability window so the most important care
  happens first.
- **Sorting by time** — [`Scheduler.sort_by_time()`](pawpal_system.py#L219)
  reorders tasks chronologically by due time for a "what's next" view.
- **Sorting by priority** — [`Scheduler.sort_by_priority()`](pawpal_system.py#L205)
  ranks tasks high-to-low priority with an earliest-due-time tiebreak.
- **Availability filtering** — [`Scheduler.filter_by_available_time()`](pawpal_system.py#L230)
  drops any task that is already done or whose duration fits in no open window.
- **Pet / status filtering** — [`Owner.filter_tasks()`](pawpal_system.py#L141)
  filters tasks across all pets by pet name (case-insensitive) and/or completion
  status, combined with AND.
- **Conflict warnings** — [`Scheduler.detect_conflicts()`](pawpal_system.py#L291)
  compares every pair of pending tasks and flags any whose
  `[due, due + duration)` windows overlap, naming whether the clash is for the
  same pet or across pets — non-fatal, so a plan is still produced.
- **Greedy conflict resolution** — [`Scheduler.resolve_conflicts()`](pawpal_system.py#L254)
  places each priority-sorted task into the first slot with room, advancing a
  per-slot cursor so scheduled tasks never overlap.
- **Daily / weekly recurrence** — completing a recurring task via
  [`Pet.complete_task()`](pawpal_system.py#L102) automatically spawns its next
  occurrence one day or one week later ([`Task.next_occurrence()`](pawpal_system.py#L45)),
  so routines roll forward on their own.
- **Overdue detection** — [`Task.is_overdue()`](pawpal_system.py) flags pending
  tasks whose due time has already passed.
- **Plan explanation** — [`Scheduler.explain_plan()`](pawpal_system.py)
  renders the chosen plan as a readable, time-stamped daily agenda.

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

Run the full test suite from the project root:

```bash
python -m pytest
```

The suite in [`test_pawpal_system.py`](test_pawpal_system.py) contains 34 tests
covering every scheduling behavior the app relies on:

- **Task lifecycle** — `mark_complete()` flips status, `is_overdue()` respects
  due time and completion, and recurring tasks report the right cadence.
- **Recurrence logic** — completing a `daily`/`weekly` task spawns a fresh,
  pending occurrence one day/week later with a distinct id.
- **Pet & Owner management** — adding tasks, toggling completion, creating pets,
  and `Owner.filter_tasks()` filtering by completion status and (case-insensitive)
  pet name, including the combined-filter and unknown-pet cases.
- **Sorting** — priority-first ordering with a due-time tiebreak, and
  chronological ordering via `sort_by_time()`.
- **Filtering & placement** — dropping tasks that fit no window or are already
  done, and greedily packing tasks into non-overlapping slots without exceeding
  the window.
- **Conflict detection** — flagging overlapping/duplicate-time tasks (same pet
  and across different pets) while ignoring completed and non-overlapping tasks.
- **End-to-end planning** — `generate_plan()` orders by priority with no overlap,
  and `explain_plan()` describes the chosen tasks (and the empty-plan case).

Test output from a successful run:

```
============================= test session starts =============================
platform win32 -- Python 3.13.7, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\Ishaa\OneDrive\Documents\GitHub\ai110-module2show-pawpal-starter
plugins: anyio-4.9.0, dash-3.1.1
collected 34 items

test_pawpal_system.py ..................................                 [100%]

============================= 34 passed in 0.10s ==============================
```

### Confidence Level: ⭐⭐⭐⭐☆ (4/5)

All 34 tests pass, covering the core scheduling logic — sorting, filtering,
conflict detection, recurrence, and end-to-end plan generation — including edge
cases like completed tasks, unknown pets, and tasks that fit no window. I'm
holding back the fifth star because the tests exercise the backend logic
directly; the Streamlit UI layer in `app.py` is not yet covered by automated
tests, so UI wiring is verified manually.

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

Launch the Streamlit app from the project root:

```bash
streamlit run app.py
```

### Main UI features

The app is a single scrolling page divided into sections, each wired to the
domain logic:

- **Owner** — edit the owner name and contact info.
- **Pets** — add a pet (name + species: dog / cat / other) and see a table of
  your pets with their task counts.
- **Tasks** — pick a pet, then add a care task with a title, duration (minutes),
  priority (low / medium / high), a due time for today, and a recurrence
  (none / daily / weekly). Below the form you can **filter** the task list by
  pet and status and **sort** it by priority or due time. Each row shows its
  status badge (🕒 pending, ⏰ overdue, ✅ done).
- **Availability** — set the daily window (from / until) the scheduler is
  allowed to place tasks into.
- **Build Schedule** — generate a priority-ordered, non-overlapping plan that
  fits inside your availability window, plus a plain-text explanation and a list
  of any tasks that did not fit.

### Example workflow

1. Under **Pets**, type `Rex`, choose `dog`, and click **Add pet**. Add a second
   pet `Miso` (`cat`) the same way.
2. Under **Tasks**, select `Rex` and add **Vet appointment** — 45 min, high
   priority, due at 10:00. Add **Morning walk** — 30 min, medium, due 09:00.
3. Select `Miso` and add **Feed breakfast** — 15 min, high, due 08:30.
4. Add a second task due at 09:00 (e.g. **Grooming** for Rex) — because its
   window overlaps the 09:00 walk, a ⚠️ conflict warning appears immediately.
5. Under **Availability**, leave the window at 08:00–18:00.
6. Click **Generate schedule**. The plan appears as a time-stamped table,
   ordered by priority, with the explanation text below it and any unscheduled
   tasks listed under "Did not fit."

### Key Scheduler behaviors shown

- **Sorting** — the plan and the "Sort by → Priority" view list high-priority
  tasks first, breaking ties by the earlier due time; "Sort by → Due time" gives
  a chronological view.
- **Conflict warnings** — tasks whose `[due, due + duration)` windows overlap are
  flagged (both for the same pet and across pets) without blocking the plan.
- **Filtering** — the task list respects the pet and status filters, and the
  scheduler drops tasks that are done or fit no window before placing the rest.
- **Non-overlapping placement** — tasks are packed back-to-back into the
  availability window so no two scheduled slots collide.
- **Recurrence** — daily/weekly tasks are labeled in the "Repeats" column and
  spawn their next occurrence when completed.

### Sample CLI output

Running the demo script (`python main.py`) exercises the same logic against a
fixed two-pet scenario with a deliberate 09:00 clash:

```
Today's Schedule for Alex Rivera
================================
Daily plan:
  08:00–08:45  Vet appointment (45 min) [priority 5]
  08:45–09:00  Feed breakfast (15 min) [priority 4]
  09:00–09:30  Morning walk (30 min) [priority 3]
  09:30–10:00  Grooming (30 min) [priority 2]
  10:00–10:20  Playtime (20 min) [priority 2]

Schedule warnings:
  Conflict: 'Morning walk' and 'Grooming' for the same pet (Rex) overlap around 09:00.
  Conflict: 'Morning walk' and 'Playtime' for different pets (Rex & Miso) overlap around 09:00.
  Conflict: 'Grooming' and 'Playtime' for different pets (Rex & Miso) overlap around 09:00.
```

**Screenshots or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here for human reviewers -->
