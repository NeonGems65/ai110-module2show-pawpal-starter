"""PawPal+ class skeleton.

Generated from diagrams/uml.mmd. Method bodies are left as stubs.
Keep this file in sync with the UML diagram.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from itertools import combinations
from uuid import uuid4


@dataclass
class Task:
    description: str
    duration: int
    priority: int
    due_time: datetime
    completed: bool = False
    # How often this task repeats: "none" (one-off), "daily", or "weekly".
    # Recurring tasks spawn their next occurrence when completed via
    # Pet.complete_task (see next_occurrence below).
    recurrence: str = "none"
    # Stable identity so a Task can be matched back to its ScheduledTask
    # even after round-tripping through the UI or serialization.
    id: str = field(default_factory=lambda: uuid4().hex)

    # How far ahead each recurrence type advances the due time. A plain class
    # attribute (no annotation) so the dataclass does not treat it as a field.
    _RECURRENCE_DELTAS = {
        "daily": timedelta(days=1),
        "weekly": timedelta(weeks=1),
    }

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def is_recurring(self) -> bool:
        """Return True if this task repeats on a daily or weekly cadence."""
        return self.recurrence in self._RECURRENCE_DELTAS

    def next_occurrence(self) -> "Task | None":
        """Return a fresh, pending copy due one cadence later, or None.

        Non-recurring tasks return None. Recurring tasks return a new Task
        (with its own id) identical except that ``due_time`` is advanced by one
        day or one week and ``completed`` is reset to False.
        """
        delta = self._RECURRENCE_DELTAS.get(self.recurrence)
        if delta is None:
            return None
        return Task(
            description=self.description,
            duration=self.duration,
            priority=self.priority,
            due_time=self.due_time + delta,
            recurrence=self.recurrence,
        )

    def is_overdue(self, now: datetime) -> bool:
        """Return True if the task is still pending and past its due time."""
        return not self.completed and now > self.due_time


@dataclass
class Pet:
    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(
        self,
        description: str,
        duration: int,
        priority: int,
        due: datetime,
        recurrence: str = "none",
    ) -> Task:
        """Create a task, append it to this pet, and return it."""
        task = Task(
            description=description,
            duration=duration,
            priority=priority,
            due_time=due,
            recurrence=recurrence,
        )
        self.tasks.append(task)
        return task

    def list_tasks(self) -> list[Task]:
        """Return a shallow copy of this pet's task list."""
        return list(self.tasks)

    def manage_task(self, task: Task) -> None:
        """Toggle the completion status of the given task."""
        # Toggle completion status.
        task.completed = not task.completed

    def complete_task(self, task: Task) -> Task | None:
        """Mark a task complete and auto-schedule its next occurrence.

        For a daily or weekly task, completing it appends a fresh instance
        (due one cadence later) to this pet and returns it. One-off tasks just
        get marked done and return None.
        """
        task.mark_complete()
        next_task = task.next_occurrence()
        if next_task is not None:
            self.tasks.append(next_task)
        return next_task


@dataclass
class TimeSlot:
    """Represents an owner's available window of time."""

    start: datetime
    end: datetime


@dataclass
class Owner:
    name: str
    contact_info: str
    pets: list[Pet] = field(default_factory=list)
    available_times: list[TimeSlot] = field(default_factory=list)

    def create_pet(self, name: str, species: str) -> Pet:
        """Create a pet, add it to this owner, and return it."""
        pet = Pet(name=name, species=species)
        self.pets.append(pet)
        return pet

    def list_pets(self) -> list[Pet]:
        """Return a shallow copy of this owner's pet list."""
        return list(self.pets)

    def filter_tasks(
        self,
        completed: bool | None = None,
        pet_name: str | None = None,
    ) -> list[Task]:
        """Return tasks across all pets, filtered by completion status and/or pet name.

        Both filters are optional and combine with AND:
          * ``completed`` — keep only tasks whose ``completed`` flag matches
            (``True`` for done, ``False`` for pending). ``None`` keeps both.
          * ``pet_name`` — keep only tasks belonging to the pet with this name
            (case-insensitive). ``None`` keeps every pet.

        With no arguments it returns every task the owner has.
        """
        target = pet_name.casefold() if pet_name is not None else None
        results: list[Task] = []
        for pet in self.pets:
            if target is not None and pet.name.casefold() != target:
                continue
            for task in pet.tasks:
                if completed is not None and task.completed != completed:
                    continue
                results.append(task)
        return results


@dataclass
class ScheduledTask:
    """A Task placed into a concrete time slot by the Scheduler."""

    task: Task
    start: datetime
    end: datetime


class Scheduler:
    def generate_plan(self, owner: Owner) -> list[ScheduledTask]:
        """Build a scheduled plan for all of the owner's tasks across their pets.

        Runs the full pipeline: collect every task from every pet, order them by
        priority, drop the ones that cannot fit any availability window, then
        greedily place the survivors into concrete time slots.

        Args:
            owner: The owner whose pets' tasks and ``available_times`` drive
                the plan.

        Returns:
            A list of ScheduledTask entries, each pairing a task with the
            concrete start/end time it was assigned. Tasks that fit nowhere are
            omitted.
        """
        # Gather every task across all of the owner's pets, then run the
        # sort -> filter -> place pipeline against the owner's availability.
        tasks: list[Task] = []
        for pet in owner.pets:
            tasks.extend(pet.list_tasks())

        slots = owner.available_times
        ordered = self.sort_by_priority(tasks)
        schedulable = self.filter_by_available_time(ordered, slots)
        return self.resolve_conflicts(schedulable, slots)

    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks by highest priority first, breaking ties by earliest due time.

        Args:
            tasks: The tasks to order.

        Returns:
            A new list sorted by descending ``priority``; tasks with equal
            priority keep the one with the earlier ``due_time`` first. The input
            list is left unmodified.
        """
        # Highest priority first; earlier due_time breaks ties.
        return sorted(tasks, key=lambda t: (-t.priority, t.due_time))

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks by their due time, earliest first.

        ``sorted()`` with a lambda ``key`` pulls the value to compare out of
        each Task. ``due_time`` is a ``datetime`` here, which orders naturally.
        If your tasks instead carried a plain "HH:MM" string, the same pattern
        works because zero-padded 24-hour strings sort lexicographically in
        chronological order — e.g. ``key=lambda t: t.time``.
        """
        return sorted(tasks, key=lambda t: t.due_time)

    def filter_by_available_time(
        self, tasks: list[Task], slots: list[TimeSlot]
    ) -> list[Task]:
        """Keep pending tasks that fit within at least one availability window.

        Args:
            tasks: Candidate tasks (typically already priority-sorted).
            slots: The owner's available time windows.

        Returns:
            The subset of ``tasks`` that are not yet completed and whose
            ``duration`` (in minutes) is no longer than at least one slot's
            span. Order is preserved; ``slots`` is only read, not consumed.
        """
        # Keep pending tasks that fit inside at least one availability window.
        # Slots are only read here; they are handed to resolve_conflicts intact.
        def fits(task: Task) -> bool:
            return any(
                (slot.end - slot.start).total_seconds() / 60 >= task.duration
                for slot in slots
            )

        return [t for t in tasks if not t.completed and fits(t)]

    def resolve_conflicts(
        self, tasks: list[Task], slots: list[TimeSlot]
    ) -> list[ScheduledTask]:
        """Greedily pack tasks into available slots, assigning non-overlapping times.

        Args:
            tasks: Tasks to place, assumed already ordered by priority so the
                most important ones claim slot time first.
            slots: The available windows to pack into.

        Returns:
            A ScheduledTask per placed task, in placement order. Each task is
            dropped into the first slot with enough remaining room; a per-slot
            cursor advances so placements never overlap. Tasks that fit in no
            slot are silently omitted.
        """
        # Needs the available slots to assign each task a concrete
        # start/end; the slot windows must survive the filter step above.
        #
        # Greedily pack each task (assumed priority-sorted) into the first slot
        # with enough remaining room, advancing a per-slot cursor so placed
        # tasks never overlap. Tasks that fit nowhere are dropped.
        cursors = {i: slot.start for i, slot in enumerate(slots)}
        plan: list[ScheduledTask] = []

        for task in tasks:
            length = timedelta(minutes=task.duration)
            for i, slot in enumerate(slots):
                start = cursors[i]
                end = start + length
                if end <= slot.end:
                    plan.append(ScheduledTask(task=task, start=start, end=end))
                    cursors[i] = end
                    break

        return plan

    def detect_conflicts(self, owner: Owner) -> list[str]:
        """Return warning messages for tasks whose time windows overlap.

        Lightweight, non-fatal conflict check: every pending task occupies the
        window ``[due_time, due_time + duration)``. Any two tasks whose windows
        overlap are flagged — whether they belong to the same pet or different
        pets. Instead of raising and crashing the program, we collect a
        human-readable warning per clash and hand the list back so the caller
        can print it and carry on. An empty list means no conflicts.
        """
        # Flatten to (pet, task) pairs so each warning can name the pet(s).
        entries = [
            (pet, task)
            for pet in owner.pets
            for task in pet.tasks
            if not task.completed
        ]

        warnings: list[str] = []
        for (pet_a, a), (pet_b, b) in combinations(entries, 2):
            a_end = a.due_time + timedelta(minutes=a.duration)
            b_end = b.due_time + timedelta(minutes=b.duration)
            # Two half-open windows overlap iff each starts before the other ends.
            if a.due_time < b_end and b.due_time < a_end:
                who = (
                    f"the same pet ({pet_a.name})"
                    if pet_a is pet_b
                    else f"different pets ({pet_a.name} & {pet_b.name})"
                )
                warnings.append(
                    f"Conflict: '{a.description}' and '{b.description}' "
                    f"for {who} overlap around "
                    f"{a.due_time.strftime('%H:%M')}."
                )
        return warnings

    def explain_plan(self, plan: list[ScheduledTask]) -> str:
        """Return a human-readable summary of the scheduled plan."""
        if not plan:
            return "No tasks could be scheduled in the available time."

        lines = ["Daily plan:"]
        for item in plan:
            start = item.start.strftime("%H:%M")
            end = item.end.strftime("%H:%M")
            task = item.task
            lines.append(
                f"  {start}–{end}  {task.description} "
                f"({task.duration} min) [priority {task.priority}]"
            )
        return "\n".join(lines)
