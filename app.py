from datetime import datetime, time

import streamlit as st

from pawpal_system import Owner, Scheduler, TimeSlot

PRIORITY_MAP = {"low": 1, "medium": 2, "high": 3}

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to PawPal+, a pet care planning assistant. Add your pets, give each one
some care tasks, set your availability, and let the scheduler build a plan.
"""
)

# --- Application "memory" ---------------------------------------------------
# Streamlit re-runs this whole script top-to-bottom on every interaction, so a
# plain `Owner()` here would be recreated (and wiped) on every click. We stash a
# single Owner instance in st.session_state — Streamlit's per-session "vault" —
# and only create it the first time, so pets/tasks persist across reruns.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", contact_info="")

owner: Owner = st.session_state.owner

st.divider()

# --- Owner ------------------------------------------------------------------
st.subheader("Owner")
owner.name = st.text_input("Owner name", value=owner.name)
owner.contact_info = st.text_input("Contact info", value=owner.contact_info)

st.divider()

# --- Pets -------------------------------------------------------------------
st.subheader("Pets")
st.caption("Add a pet, then give it care tasks below.")

pet_col1, pet_col2 = st.columns(2)
with pet_col1:
    new_pet_name = st.text_input("Pet name", value="Mochi")
with pet_col2:
    new_pet_species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Add pet"):
    if not new_pet_name.strip():
        st.warning("Give your pet a name first.")
    else:
        # Wire the UI action straight to the domain method. Because `owner`
        # lives in session_state, the new pet sticks around after this rerun.
        owner.create_pet(new_pet_name.strip(), new_pet_species)
        st.success(f"Added {new_pet_name.strip()} ({new_pet_species}).")

pets = owner.list_pets()
if pets:
    st.write("Your pets:")
    st.table([{"Name": p.name, "Species": p.species, "Tasks": len(p.tasks)} for p in pets])
else:
    st.info("No pets yet. Add one above.")

st.divider()

# --- Tasks ------------------------------------------------------------------
st.subheader("Tasks")

PRIORITY_LABEL = {1: "low", 2: "medium", 3: "high"}

if pets:
    pet_names = [p.name for p in pets]
    selected_name = st.selectbox("Add a task for", pet_names)
    selected_pet = next(p for p in pets if p.name == selected_name)

    task_col1, task_col2, task_col3 = st.columns(3)
    with task_col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with task_col2:
        duration = st.number_input(
            "Duration (minutes)", min_value=1, max_value=240, value=20
        )
    with task_col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

    due_col1, due_col2 = st.columns(2)
    with due_col1:
        # A real due time (today) so conflict detection and overdue checks are
        # meaningful — two tasks whose [due, due+duration) windows overlap will
        # be flagged below by Scheduler.detect_conflicts.
        due_time = st.time_input("Due at (today)", value=time(9, 0))
    with due_col2:
        recurrence = st.selectbox("Repeats", ["none", "daily", "weekly"])

    if st.button("Add task"):
        if not task_title.strip():
            st.warning("Give the task a title first.")
        else:
            # add_task builds the Task and appends it to the pet for us.
            due = datetime.combine(datetime.now().date(), due_time)
            selected_pet.add_task(
                description=task_title.strip(),
                duration=int(duration),
                priority=PRIORITY_MAP.get(priority, 2),
                due=due,
                recurrence=recurrence,
            )
            st.success(f"Added '{task_title.strip()}' for {selected_pet.name}.")

    # --- Conflict warnings --------------------------------------------------
    # Ask the Scheduler whether any pending tasks overlap in time. We show one
    # warning per clash, naming the tasks/pets and the time so the owner knows
    # exactly what to move — non-fatal, the plan still generates below.
    scheduler = Scheduler()
    conflicts = scheduler.detect_conflicts(owner)
    if conflicts:
        st.warning(f"⚠️ {len(conflicts)} scheduling conflict(s) detected:")
        for message in conflicts:
            st.warning(message)

    # --- Filter + sort the task list ----------------------------------------
    st.write("Current tasks:")
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    with filter_col1:
        pet_filter = st.selectbox("Filter by pet", ["All pets"] + pet_names)
    with filter_col2:
        status_filter = st.selectbox("Status", ["All", "Pending", "Done"])
    with filter_col3:
        sort_by = st.selectbox("Sort by", ["Priority", "Due time"])

    # Owner.filter_tasks does the pet/completion filtering for us.
    completed = {"All": None, "Pending": False, "Done": True}[status_filter]
    tasks = owner.filter_tasks(
        completed=completed,
        pet_name=None if pet_filter == "All pets" else pet_filter,
    )

    # Let the Scheduler's sort methods order the filtered results.
    if sort_by == "Priority":
        tasks = scheduler.sort_by_priority(tasks)
    else:
        tasks = scheduler.sort_by_time(tasks)

    # Map each task back to its pet so the table can name the owner of the task.
    pet_of = {id(t): p.name for p in pets for t in p.tasks}
    now = datetime.now()

    if tasks:
        st.table(
            [
                {
                    "Pet": pet_of.get(id(t), "?"),
                    "Task": t.description,
                    "Due": t.due_time.strftime("%H:%M"),
                    "Duration (min)": t.duration,
                    "Priority": PRIORITY_LABEL.get(t.priority, t.priority),
                    "Repeats": t.recurrence,
                    "Status": (
                        "✅ done"
                        if t.completed
                        else "⏰ overdue"
                        if t.is_overdue(now)
                        else "🕒 pending"
                    ),
                }
                for t in tasks
            ]
        )
    else:
        st.info("No tasks match the current filter.")
else:
    st.info("Add a pet before creating tasks.")

st.divider()

# --- Availability -----------------------------------------------------------
st.subheader("Availability")
st.caption("The scheduler places tasks inside this window (today).")
avail_col1, avail_col2 = st.columns(2)
with avail_col1:
    avail_start = st.time_input("Available from", value=time(8, 0))
with avail_col2:
    avail_end = st.time_input("Available until", value=time(18, 0))

st.divider()

# --- Build schedule ---------------------------------------------------------
st.subheader("Build Schedule")
st.caption("Builds a plan from your tasks, ordered by priority within your availability.")

if st.button("Generate schedule"):
    all_tasks = [t for p in owner.list_pets() for t in p.list_tasks()]
    if avail_end <= avail_start:
        st.error("'Available until' must be later than 'Available from'.")
    elif not all_tasks:
        st.info("Add at least one task before generating a schedule.")
    else:
        today = datetime.now().date()
        slot = TimeSlot(
            start=datetime.combine(today, avail_start),
            end=datetime.combine(today, avail_end),
        )
        # Persist the availability window so the scheduler can pack into it.
        # Task due times are left as the owner set them, so conflict and
        # overdue checks keep reflecting the real intended times.
        owner.available_times = [slot]

        scheduler = Scheduler()
        # Surface any time conflicts alongside the plan so the owner can act.
        for message in scheduler.detect_conflicts(owner):
            st.warning(message)

        plan = scheduler.generate_plan(owner)
        scheduled_ids = {item.task.id for item in plan}

        if not plan:
            st.warning("No tasks fit in the available time. Try widening your window.")
        else:
            st.success(f"Scheduled {len(plan)} task(s).")
            st.table(
                [
                    {
                        "Start": item.start.strftime("%H:%M"),
                        "End": item.end.strftime("%H:%M"),
                        "Task": item.task.description,
                        "Duration (min)": item.task.duration,
                        "Priority": PRIORITY_LABEL.get(
                            item.task.priority, item.task.priority
                        ),
                    }
                    for item in plan
                ]
            )
            st.text(scheduler.explain_plan(plan))

        unscheduled = [t for t in all_tasks if t.id not in scheduled_ids]
        if unscheduled:
            st.caption("Did not fit: " + ", ".join(t.description for t in unscheduled))
