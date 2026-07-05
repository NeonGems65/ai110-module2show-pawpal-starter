"""PawPal+ class skeleton.

Generated from diagrams/uml.mmd. Method bodies are left as stubs.
Keep this file in sync with the UML diagram.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from uuid import uuid4


@dataclass
class Task:
    description: str
    duration: int
    priority: int
    due_time: datetime
    completed: bool = False
    # Stable identity so a Task can be matched back to its ScheduledTask
    # even after round-tripping through the UI or serialization.
    id: str = field(default_factory=lambda: uuid4().hex)

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def is_overdue(self, now: datetime) -> bool:
        """Return True if the task is still pending and past its due time."""
        return not self.completed and now > self.due_time


@dataclass
class Pet:
    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(
        self, description: str, duration: int, priority: int, due: datetime
    ) -> Task:
        """Create a task, append it to this pet, and return it."""
        task = Task(
            description=description,
            duration=duration,
            priority=priority,
            due_time=due,
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


@dataclass
class ScheduledTask:
    """A Task placed into a concrete time slot by the Scheduler."""

    task: Task
    start: datetime
    end: datetime


class Scheduler:
    def generate_plan(self, owner: Owner) -> list[ScheduledTask]:
        """Build a scheduled plan for all of the owner's tasks across their pets."""
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
        """Sort tasks by highest priority first, breaking ties by earliest due time."""
        # Highest priority first; earlier due_time breaks ties.
        return sorted(tasks, key=lambda t: (-t.priority, t.due_time))

    def filter_by_available_time(
        self, tasks: list[Task], slots: list[TimeSlot]
    ) -> list[Task]:
        """Keep pending tasks that fit within at least one availability window."""
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
        """Greedily pack tasks into available slots, assigning non-overlapping times."""
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
