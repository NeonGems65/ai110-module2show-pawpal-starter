from datetime import datetime, time

import streamlit as st

from pawpal_system import Owner, Scheduler, TimeSlot

PRIORITY_MAP = {"low": 1, "medium": 2, "high": 3}

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Quick Demo Inputs (UI only)")
owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

st.markdown("### Tasks")
st.caption("Add a few tasks. In your final version, these should feed into your scheduler.")

if "tasks" not in st.session_state:
    st.session_state.tasks = []

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

if st.button("Add task"):
    st.session_state.tasks.append(
        {"title": task_title, "duration_minutes": int(duration), "priority": priority}
    )

if st.session_state.tasks:
    st.write("Current tasks:")
    st.table(st.session_state.tasks)
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Availability")
st.caption("The scheduler places tasks inside this window (today).")
avail_col1, avail_col2 = st.columns(2)
with avail_col1:
    avail_start = st.time_input("Available from", value=time(8, 0))
with avail_col2:
    avail_end = st.time_input("Available until", value=time(18, 0))

st.divider()

st.subheader("Build Schedule")
st.caption("Builds a plan from your tasks, ordered by priority within your availability.")

if st.button("Generate schedule"):
    if avail_end <= avail_start:
        st.error("'Available until' must be later than 'Available from'.")
    elif not st.session_state.tasks:
        st.info("Add at least one task before generating a schedule.")
    else:
        today = datetime.now().date()
        slot = TimeSlot(
            start=datetime.combine(today, avail_start),
            end=datetime.combine(today, avail_end),
        )

        owner = Owner(name=owner_name, contact_info="")
        owner.available_times = [slot]
        pet = owner.create_pet(pet_name, species)
        for entry in st.session_state.tasks:
            pet.add_task(
                description=entry["title"],
                duration=entry["duration_minutes"],
                priority=PRIORITY_MAP.get(entry["priority"], 2),
                due=slot.end,
            )

        scheduler = Scheduler()
        plan = scheduler.generate_plan(owner)
        scheduled_ids = {item.task.id for item in plan}

        if not plan:
            st.warning("No tasks fit in the available time. Try widening your window.")
        else:
            st.success(f"Scheduled {len(plan)} task(s) for {pet.name}.")
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

        unscheduled = [t for t in pet.list_tasks() if t.id not in scheduled_ids]
        if unscheduled:
            st.caption(
                "Did not fit: " + ", ".join(t.description for t in unscheduled)
            )
