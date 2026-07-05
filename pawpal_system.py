"""PawPal+ class skeleton.

Generated from diagrams/uml.mmd. Method bodies are left as stubs.
Keep this file in sync with the UML diagram.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
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
        ...

    def is_overdue(self, now: datetime) -> bool:
        ...


@dataclass
class Pet:
    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(
        self, description: str, duration: int, priority: int, due: datetime
    ) -> Task:
        ...

    def list_tasks(self) -> list[Task]:
        ...

    def manage_task(self, task: Task) -> None:
        ...


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
        ...

    def list_pets(self) -> list[Pet]:
        ...


@dataclass
class ScheduledTask:
    """A Task placed into a concrete time slot by the Scheduler."""

    task: Task
    start: datetime
    end: datetime


class Scheduler:
    def generate_plan(self, owner: Owner) -> list[ScheduledTask]:
        ...

    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        ...

    def filter_by_available_time(
        self, tasks: list[Task], slots: list[TimeSlot]
    ) -> list[Task]:
        ...

    def resolve_conflicts(
        self, tasks: list[Task], slots: list[TimeSlot]
    ) -> list[ScheduledTask]:
        # Needs the available slots to assign each task a concrete
        # start/end; the slot windows must survive the filter step above.
        ...

    def explain_plan(self, plan: list[ScheduledTask]) -> str:
        ...
