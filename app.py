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

    if st.button("Add task"):
        if not task_title.strip():
            st.warning("Give the task a title first.")
        else:
            # add_task builds the Task and appends it to the pet for us.
            # Due time is filled in at schedule-time (see below) — here we just
            # give it a placeholder of "now" so the object is valid.
            selected_pet.add_task(
                description=task_title.strip(),
                duration=int(duration),
                priority=PRIORITY_MAP.get(priority, 2),
                due=datetime.now(),
            )
            st.success(f"Added '{task_title.strip()}' for {selected_pet.name}.")

    # Show every pet's current tasks.
    rows = [
        {
            "Pet": p.name,
            "Task": t.description,
            "Duration (min)": t.duration,
            "Priority": t.priority,
            "Done": t.completed,
        }
        for p in pets
        for t in p.list_tasks()
    ]
    if rows:
        st.write("Current tasks:")
        st.table(rows)
    else:
        st.info("No tasks yet. Add one above.")
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
        # Update the persisted owner's availability, and align each task's due
        # time to the end of the window so overdue checks stay meaningful.
        owner.available_times = [slot]
        for task in all_tasks:
            task.due_time = slot.end

        scheduler = Scheduler()
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
                        "Priority": item.task.priority,
                    }
                    for item in plan
                ]
            )
            st.text(scheduler.explain_plan(plan))

        unscheduled = [t for t in all_tasks if t.id not in scheduled_ids]
        if unscheduled:
            st.caption("Did not fit: " + ", ".join(t.description for t in unscheduled))
