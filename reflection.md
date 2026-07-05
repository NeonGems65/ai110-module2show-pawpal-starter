# PawPal+ Project Reflection


## 1. System Design

Three Core Actions
- Add a pet
- Schedule Walks
- See Today's Tasks

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

My initial UML centered on four classes, each with a single clear responsibility:

- **Owner** — identifying info plus the list of pets and the times the owner is
  available. Methods: `create_pet`, and (later) `filter_tasks`.
- **Pet** — owns its own care tasks. Methods: `add_task`, `list_tasks`,
  `manage_task`. Attributes: name, species, tasks.
- **Task** — holds one unit of work. Attributes: description, due time,
  duration, priority, completion status. Method: `mark_complete`.
- **Scheduler** — the only class that reaches *across* pets. It doesn't hold
  data; it retrieves, orders, filters, and places tasks into a plan.

The guiding principle was that data classes (Owner/Pet/Task) stay "dumb" about
scheduling, and all the cross-cutting logic lives in one place — the Scheduler.

**b. Design changes**

- Did your design change during implementation? **Yes.**
- If yes, describe at least one change and why you made it.

Two changes stand out:

1. **Added two wrapper classes — `TimeSlot` and `ScheduledTask`.** Early on,
   availability was going to be a bare `(start, end)` tuple and a placed task
   was going to be a `(task, start, end)` tuple. Once the scheduler pipeline
   grew (`filter_by_available_time` → `resolve_conflicts` → `generate_plan`),
   the tuples became hard to read and easy to index wrong. Promoting them to
   small `@dataclass` wrappers made every signature self-documenting
   (`list[ScheduledTask]` instead of `list[tuple]`) and gave the UI stable
   attribute names (`item.start`, `item.task.description`) to render against.

2. **Gave `Task` a stable `id` and recurrence support.** I needed to match a
   `Task` back to its `ScheduledTask` after it round-tripped through the
   Streamlit UI, so I added a `uuid4` id. Recurrence (`none`/`daily`/`weekly`)
   and `next_occurrence()` came in once I realized "routines" — not one-off
   chores — were the real use case.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

The scheduler considers three constraints:

- **Priority** (high → low) — the primary ordering. The most important care
  claims slot time first.
- **Availability** — tasks are only placed inside the owner's `TimeSlot`
  window(s); anything that fits no window is dropped before placement.
- **Time / duration & overlap** — each task occupies `duration` minutes, and a
  per-slot cursor guarantees placed tasks never overlap.

I decided priority mattered most because the whole point of the app is to keep a
busy owner *consistent on what matters* — if something has to be dropped, it
should be the low-priority task, not the vet appointment. Availability is the
hard boundary (you physically can't schedule outside it), and time/duration is
what turns an ordered list into a concrete agenda. Ties in priority break by
earliest due time (`key=lambda t: (-t.priority, t.due_time)`).

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.

`Scheduler.resolve_conflicts` uses a **greedy first-fit** placement: each
priority-sorted task drops into the first slot with room. This is
O(tasks × slots) and does *not* guarantee a globally optimal packing — a clever
reshuffle could sometimes fit one more low-priority task. I chose the greedy
approach anyway.

- Why is that tradeoff reasonable for this scenario?

At this scale (a handful of pets and a day's worth of tasks), O(tasks × slots)
is effectively instant, and greedy-by-priority produces exactly the behavior a
user expects: important tasks land first, and if something doesn't fit, it's the
least important one. The "optimal" alternative (bin-packing / interval trees)
adds real complexity and hurts readability for a payoff that only appears at a
slot count this app will never see. Keeping placement greedy also keeps each
step independently testable, which is worth more here than squeezing in one
extra task.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used AI across every phase, but in different modes:

- **Design brainstorming** — bouncing the class breakdown back and forth ("does
  the Scheduler belong as its own class or as methods on Owner?") to pressure-test
  responsibilities before writing code.
- **Scaffolding** — turning the finalized UML into Python `@dataclass` stubs so
  the file structure matched the diagram exactly.
- **Implementation & refactoring** — filling in method bodies incrementally, then
  refactoring (e.g. the tuple → `TimeSlot`/`ScheduledTask` change).
- **Testing** — generating edge-case test ideas (completed tasks, unknown pet,
  tasks that fit no window, same-pet vs. cross-pet conflicts) that grew the suite
  to 34 tests.

The most helpful prompts were **specific and constraint-bearing** — e.g. "write
conflict detection as a *non-fatal* check that returns warning strings instead
of raising," or "sort by priority descending with earliest due time as the
tiebreak." Vague prompts ("build a scheduler") produced generic code; naming the
exact contract and edge behavior produced code I could drop in with minimal edits.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

At one point the assistant suggested having `detect_conflicts` **raise an
exception** when two tasks overlapped. I rejected that: a scheduling conflict is
information the owner should *see*, not a crash. I reworked it to return a list
of human-readable warning strings so the plan still generates and the UI can show
`⚠️` messages alongside it. That decision is why `app.py` can display conflicts
and a schedule at the same time.

I verified AI output three ways: (1) reading it against the UML to confirm it
respected the class boundaries, (2) running `python -m pytest` (34 passing tests)
after each increment, and (3) driving the Streamlit UI manually to confirm the
end-to-end wiring (add pet → add task → conflict warning → generate plan).

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

The 34-test suite (`test_pawpal_system.py`) covers:

- **Task lifecycle** — `mark_complete`, `is_overdue` (respecting both due time
  and completion), and recurrence cadence reporting.
- **Recurrence** — completing a daily/weekly task spawns a fresh, pending
  occurrence with a new id, one cadence later.
- **Pet & Owner management** — adding/toggling tasks, creating pets, and
  `filter_tasks` by status and (case-insensitive) pet name, including combined
  and unknown-pet cases.
- **Sorting** — priority-first with due-time tiebreak, and chronological sort.
- **Filtering & placement** — dropping done/too-long tasks, and greedy
  non-overlapping packing within the window.
- **Conflict detection** — same-pet and cross-pet overlaps, ignoring completed
  and non-overlapping tasks.
- **End-to-end** — `generate_plan` ordering and `explain_plan` output, including
  the empty-plan case.

These matter because the scheduler is the heart of the app: every one of these
behaviors is a promise the UI makes to the user, so each is pinned by a test that
would break loudly if I refactored something wrong.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

**4 / 5.** All 34 tests pass and cover the core logic end-to-end, including the
tricky edge cases. I hold back the fifth star because the tests exercise the
backend directly — the Streamlit layer in `app.py` is still verified by hand.

Next, I'd test: **multiple availability windows** (the code supports a list of
`TimeSlot`s but the UI only sets one); **tasks spanning across two slots**; the
exact **boundary case** where a task's duration equals a slot's span; and
**recurrence rolling across a day/week boundary** (e.g. a daily task completed
just before midnight).

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

The clean separation between the "dumb" data classes and the Scheduler. Because
each scheduling step (`sort_by_priority`, `filter_by_available_time`,
`resolve_conflicts`, `detect_conflicts`) is a small, independent method, I could
test each in isolation *and* compose them in `generate_plan`. That structure is
also what let the UI stay thin — `app.py` mostly wires widgets straight to domain
methods.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

I'd expose **multiple availability windows** in the UI (the backend already
supports it), add **automated UI tests** to earn the fifth confidence star, and
let the scheduler **respect a task's own due time** during placement rather than
packing purely back-to-back from the window start.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

Design the *contracts* first. Once the UML pinned down each class's
responsibility and each method's signature, AI became far more useful — it filled
in bodies that fit the design instead of inventing its own architecture. The
human job wasn't typing code; it was deciding the shape.

---

## 6. AI Strategy

**a. Which AI coding assistant features were most effective for building your scheduler?**

- **UML-to-stub scaffolding** was the biggest win — handing the assistant the
  finalized `uml_final.mmd` and getting back `@dataclass` skeletons that matched
  it one-to-one meant implementation started from a correct structure instead of
  a blank file.
- **Inline, contract-driven code generation** — describing a single method's
  exact behavior and edge cases and getting a focused implementation I could
  verify against a test. This worked far better than asking for whole files.
- **Test-idea generation** — the assistant was good at surfacing edge cases I
  hadn't written down (unknown pet, task that fits no window, cross-pet vs.
  same-pet conflict), which is how the suite reached 34 tests.
- **Refactoring on request** — the tuple → `TimeSlot`/`ScheduledTask` change was
  a mechanical but wide edit that the assistant applied consistently across the
  pipeline and the UI.

**b. One AI suggestion you rejected or modified to keep the design clean.**

The assistant proposed making `detect_conflicts` **raise an exception** on an
overlap. I modified it to **return a list of warning strings** instead. Raising
would have coupled conflict detection to control flow and made it impossible to
show a plan *and* its conflicts together. The warning-list design kept the method
non-fatal and let the UI render `⚠️` messages beside a fully generated schedule —
a cleaner separation of "detect" from "decide what to do about it."

**c. How did using separate chat sessions for different phases help you stay organized?**

Keeping design, implementation, and testing in **separate chat sessions** meant
each conversation carried only the context it needed. The design session stayed
focused on responsibilities and relationships without drowning in Python details;
the implementation session worked method-by-method against a settled UML; the
testing session concentrated on edge cases without re-litigating design. This
prevented context bleed (the assistant wasn't tempted to re-open architecture
questions mid-implementation) and made it easy to go back to the right session
when I needed to revisit a decision. It mirrored the phased workflow in the
README: design → stubs → logic → tests → UI → refine UML.

**d. What I learned about being the "lead architect" when collaborating with powerful AI tools.**

The AI is an extremely fast implementer, but it is not the decision-maker. My
value was in the choices it *couldn't* make well on its own: which
responsibilities belong to which class, that conflicts should warn rather than
crash, that greedy placement is the right tradeoff at this scale, and which edge
cases actually matter. When I gave it a precise contract, it produced excellent
code; when I gave it a vague goal, it produced generic code that quietly drifted
from my design. So the lead-architect role came down to three habits: **define
the contract before asking for code, verify everything against the UML and the
test suite, and keep the human judgment calls (tradeoffs, error handling, scope)
firmly mine.** The AI accelerated the work by an order of magnitude — but the
system is coherent because a person owned the design.
