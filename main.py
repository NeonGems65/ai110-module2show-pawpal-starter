"""Demo script for PawPal+.

Testing ground to verify the scheduling logic in the terminal.
Run with: python main.py
"""

from datetime import datetime, timedelta

from pawpal_system import Owner, Scheduler, TimeSlot


def build_demo_owner() -> Owner:
    """Create an owner with two pets and a few tasks due today."""
    owner = Owner(name="Alex Rivera", contact_info="alex@example.com")

    # Anchor everything to today at 8:00 AM so the demo is reproducible.
    today = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)

    # One free window this morning for the scheduler to pack tasks into.
    owner.available_times.append(
        TimeSlot(start=today, end=today + timedelta(hours=4))
    )

    dog = owner.create_pet(name="Rex", species="Dog")
    cat = owner.create_pet(name="Miso", species="Cat")

    # description, duration (min), priority (higher = more urgent), due time
    dog.add_task("Morning walk", 30, 3, today + timedelta(hours=1))
    dog.add_task("Vet appointment", 45, 5, today + timedelta(hours=2))
    cat.add_task("Feed breakfast", 15, 4, today + timedelta(minutes=30))

    return owner


def print_schedule(owner: Owner) -> None:
    """Print a readable 'Today's Schedule' to the terminal."""
    scheduler = Scheduler()
    plan = scheduler.generate_plan(owner)

    header = f"Today's Schedule for {owner.name}"
    print(header)
    print("=" * len(header))
    print(scheduler.explain_plan(plan))


if __name__ == "__main__":
    print_schedule(build_demo_owner())
