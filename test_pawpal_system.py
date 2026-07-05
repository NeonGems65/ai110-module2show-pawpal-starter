"""Tests for the PawPal+ scheduling backend."""

from datetime import datetime, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task, TimeSlot

# Fixed reference times so tests are deterministic.
DAY = datetime(2026, 7, 5, 8, 0)


def make_task(description="Walk", duration=30, priority=2, due=None):
    return Task(
        description=description,
        duration=duration,
        priority=priority,
        due_time=due or (DAY + timedelta(hours=1)),
    )


# --- Task ------------------------------------------------------------------


def test_mark_complete_changes_status():
    """Task Completion: mark_complete() changes the task's status."""
    task = make_task()
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    """Task Addition: adding a task increases the pet's task count."""
    pet = Pet(name="Mochi", species="dog")
    before = len(pet.list_tasks())
    pet.add_task("Feed", 10, 3, DAY)
    assert len(pet.list_tasks()) == before + 1


def test_mark_complete_flips_flag():
    task = make_task()
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_is_overdue_true_when_past_due_and_incomplete():
    task = make_task(due=DAY)
    assert task.is_overdue(DAY + timedelta(minutes=1)) is True


def test_is_overdue_false_when_completed():
    task = make_task(due=DAY)
    task.mark_complete()
    assert task.is_overdue(DAY + timedelta(minutes=1)) is False


def test_is_overdue_false_before_due():
    task = make_task(due=DAY + timedelta(hours=2))
    assert task.is_overdue(DAY) is False


def test_non_recurring_task_has_no_next_occurrence():
    task = make_task()
    assert task.is_recurring() is False
    assert task.next_occurrence() is None


def test_daily_task_next_occurrence_advances_one_day():
    task = make_task(due=DAY, priority=3)
    task.recurrence = "daily"
    nxt = task.next_occurrence()
    assert nxt is not None
    assert nxt.due_time == DAY + timedelta(days=1)
    assert nxt.completed is False
    # Same details, distinct identity.
    assert nxt.description == task.description
    assert nxt.duration == task.duration
    assert nxt.priority == task.priority
    assert nxt.recurrence == "daily"
    assert nxt.id != task.id


def test_weekly_task_next_occurrence_advances_one_week():
    task = make_task(due=DAY)
    task.recurrence = "weekly"
    nxt = task.next_occurrence()
    assert nxt is not None
    assert nxt.due_time == DAY + timedelta(weeks=1)


# --- Pet -------------------------------------------------------------------


def test_add_task_returns_and_appends():
    pet = Pet(name="Mochi", species="dog")
    task = pet.add_task("Feed", 10, 3, DAY)
    assert isinstance(task, Task)
    assert pet.list_tasks() == [task]


def test_manage_task_toggles_completion():
    pet = Pet(name="Mochi", species="dog")
    task = pet.add_task("Feed", 10, 3, DAY)
    pet.manage_task(task)
    assert task.completed is True
    pet.manage_task(task)
    assert task.completed is False


def test_complete_task_one_off_adds_nothing():
    pet = Pet(name="Mochi", species="dog")
    task = pet.add_task("Feed", 10, 3, DAY)
    result = pet.complete_task(task)
    assert result is None
    assert task.completed is True
    assert pet.list_tasks() == [task]


def test_complete_task_daily_spawns_next_occurrence():
    pet = Pet(name="Mochi", species="dog")
    task = pet.add_task("Feed", 10, 3, DAY, recurrence="daily")
    nxt = pet.complete_task(task)
    assert task.completed is True
    # A fresh, pending instance was appended for tomorrow.
    assert nxt is not None
    assert nxt in pet.list_tasks()
    assert len(pet.list_tasks()) == 2
    assert nxt.due_time == DAY + timedelta(days=1)
    assert nxt.completed is False


def test_complete_task_weekly_spawns_next_occurrence():
    pet = Pet(name="Mochi", species="dog")
    task = pet.add_task("Bath", 30, 1, DAY, recurrence="weekly")
    nxt = pet.complete_task(task)
    assert nxt is not None
    assert nxt.due_time == DAY + timedelta(weeks=1)
    assert len(pet.list_tasks()) == 2


# --- Owner -----------------------------------------------------------------


def test_create_pet_creates_and_stores():
    owner = Owner(name="Jordan", contact_info="jordan@example.com")
    pet = owner.create_pet("Mochi", "cat")
    assert isinstance(pet, Pet)
    assert owner.list_pets() == [pet]


def _owner_with_tasks():
    owner = Owner(name="Jordan", contact_info="j@example.com")
    mochi = owner.create_pet("Mochi", "cat")
    rex = owner.create_pet("Rex", "dog")
    walk = mochi.add_task("Walk", 20, 2, DAY)
    feed = mochi.add_task("Feed", 10, 3, DAY)
    fetch = rex.add_task("Fetch", 15, 1, DAY)
    feed.mark_complete()
    return owner, {"walk": walk, "feed": feed, "fetch": fetch}


def test_filter_tasks_no_args_returns_all():
    owner, t = _owner_with_tasks()
    assert owner.filter_tasks() == [t["walk"], t["feed"], t["fetch"]]


def test_filter_tasks_by_completion_status():
    owner, t = _owner_with_tasks()
    assert owner.filter_tasks(completed=True) == [t["feed"]]
    assert owner.filter_tasks(completed=False) == [t["walk"], t["fetch"]]


def test_filter_tasks_by_pet_name_is_case_insensitive():
    owner, t = _owner_with_tasks()
    assert owner.filter_tasks(pet_name="mochi") == [t["walk"], t["feed"]]


def test_filter_tasks_combines_pet_name_and_status():
    owner, t = _owner_with_tasks()
    assert owner.filter_tasks(completed=False, pet_name="Mochi") == [t["walk"]]


def test_filter_tasks_unknown_pet_returns_empty():
    owner, _ = _owner_with_tasks()
    assert owner.filter_tasks(pet_name="Nobody") == []


# --- Scheduler -------------------------------------------------------------


def test_sort_by_priority_high_to_low_with_due_tiebreak():
    low = make_task("low", priority=1)
    high = make_task("high", priority=3)
    mid_early = make_task("mid-early", priority=2, due=DAY)
    mid_late = make_task("mid-late", priority=2, due=DAY + timedelta(hours=3))

    ordered = Scheduler().sort_by_priority([low, mid_late, high, mid_early])
    assert ordered == [high, mid_early, mid_late, low]


def test_filter_drops_too_long_and_completed():
    slots = [TimeSlot(DAY, DAY + timedelta(minutes=60))]
    fits = make_task("fits", duration=45)
    too_long = make_task("too-long", duration=90)
    done = make_task("done", duration=10)
    done.mark_complete()

    kept = Scheduler().filter_by_available_time([fits, too_long, done], slots)
    assert kept == [fits]


def test_resolve_conflicts_no_overlap_and_correct_duration():
    slots = [TimeSlot(DAY, DAY + timedelta(minutes=60))]
    first = make_task("first", duration=30)
    second = make_task("second", duration=20)

    plan = Scheduler().resolve_conflicts([first, second], slots)
    assert len(plan) == 2
    assert plan[0].start == DAY
    assert plan[0].end == DAY + timedelta(minutes=30)
    # Second starts exactly where the first ends -> no overlap.
    assert plan[1].start == plan[0].end
    assert plan[1].end - plan[1].start == timedelta(minutes=20)


def test_resolve_conflicts_drops_tasks_that_do_not_fit():
    slots = [TimeSlot(DAY, DAY + timedelta(minutes=40))]
    first = make_task("first", duration=30)
    overflow = make_task("overflow", duration=30)  # only 10 min left

    plan = Scheduler().resolve_conflicts([first, overflow], slots)
    assert [p.task for p in plan] == [first]


def test_generate_plan_end_to_end_orders_by_priority():
    owner = Owner(name="Jordan", contact_info="j@example.com")
    owner.available_times = [TimeSlot(DAY, DAY + timedelta(minutes=60))]
    pet = owner.create_pet("Mochi", "dog")
    pet.add_task("Low", 20, 1, DAY)
    pet.add_task("High", 30, 3, DAY)

    plan = Scheduler().generate_plan(owner)
    assert [p.task.description for p in plan] == ["High", "Low"]
    assert plan[0].start == DAY
    assert plan[1].start == plan[0].end


def test_explain_plan_mentions_tasks():
    owner = Owner(name="Jordan", contact_info="j@example.com")
    owner.available_times = [TimeSlot(DAY, DAY + timedelta(minutes=60))]
    pet = owner.create_pet("Mochi", "dog")
    pet.add_task("Morning walk", 30, 3, DAY)

    scheduler = Scheduler()
    text = scheduler.explain_plan(scheduler.generate_plan(owner))
    assert "Morning walk" in text


def test_explain_plan_empty():
    assert "No tasks" in Scheduler().explain_plan([])


# --- Conflict detection ----------------------------------------------------


def test_detect_conflicts_flags_overlapping_tasks():
    owner = Owner(name="Jordan", contact_info="j@example.com")
    pet = owner.create_pet("Mochi", "cat")
    pet.add_task("Walk", 30, 2, DAY)
    pet.add_task("Feed", 15, 3, DAY)  # same start time -> overlaps

    conflicts = Scheduler().detect_conflicts(owner)
    assert len(conflicts) == 1
    assert "Walk" in conflicts[0] and "Feed" in conflicts[0]


def test_detect_conflicts_across_different_pets():
    owner = Owner(name="Jordan", contact_info="j@example.com")
    mochi = owner.create_pet("Mochi", "cat")
    rex = owner.create_pet("Rex", "dog")
    mochi.add_task("Walk", 30, 2, DAY)
    rex.add_task("Fetch", 30, 2, DAY)  # overlaps Mochi's walk

    conflicts = Scheduler().detect_conflicts(owner)
    assert len(conflicts) == 1
    assert "different pets" in conflicts[0]


def test_detect_conflicts_none_when_windows_do_not_overlap():
    owner = Owner(name="Jordan", contact_info="j@example.com")
    pet = owner.create_pet("Mochi", "cat")
    pet.add_task("Walk", 30, 2, DAY)
    pet.add_task("Feed", 15, 3, DAY + timedelta(hours=1))  # starts after Walk ends

    assert Scheduler().detect_conflicts(owner) == []


def test_detect_conflicts_ignores_completed_tasks():
    owner = Owner(name="Jordan", contact_info="j@example.com")
    pet = owner.create_pet("Mochi", "cat")
    pet.add_task("Walk", 30, 2, DAY)
    done = pet.add_task("Feed", 15, 3, DAY)
    done.mark_complete()

    assert Scheduler().detect_conflicts(owner) == []
