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


# --- Owner -----------------------------------------------------------------


def test_create_pet_creates_and_stores():
    owner = Owner(name="Jordan", contact_info="jordan@example.com")
    pet = owner.create_pet("Mochi", "cat")
    assert isinstance(pet, Pet)
    assert owner.list_pets() == [pet]


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
