from pathlib import Path

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

DATA_FILE = Path(__file__).with_name("data.json")

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Plan feedings, walks, meds and appointments for all your pets.")

# Streamlit reruns this script on every click, so the Owner lives in session_state.
if "owner" not in st.session_state:
    try:
        st.session_state.owner = Owner.load_from_json(str(DATA_FILE))
    except (FileNotFoundError, ValueError, KeyError, TypeError):
        st.session_state.owner = Owner("Jordan")
owner = st.session_state.owner
scheduler = Scheduler(owner)


def save():
    """Write everything to data.json so it is still there next run."""
    owner.save_to_json(str(DATA_FILE))


def rows(tasks):
    """Turn tasks into dicts for st.table."""
    return [
        {
            "Date": str(t.due_date),
            "Time": t.time,
            "Pet": t.pet_name,
            "Task": t.description,
            "Minutes": t.duration_minutes,
            "Priority": t.priority,
            "Repeats": t.frequency,
            "Done": "✅" if t.completed else "",
        }
        for t in tasks
    ]


def complete_selected():
    """Callback for the 'Mark complete' button."""
    pending = scheduler.filter_tasks(completed=False)
    label = st.session_state.get("complete_choice")
    for task in pending:
        if f"{task.time} {task.description} ({task.pet_name}, {task.due_date})" == label:
            nxt = scheduler.mark_task_complete(task)
            msg = f"Completed '{task.description}' for {task.pet_name}."
            if nxt:
                msg += f" Next one scheduled for {nxt.due_date}."
            st.session_state.flash = msg
            save()
            return


st.subheader("Owner")
new_name = st.text_input("Owner name", value=owner.name)
if new_name != owner.name:
    owner.name = new_name
    save()

st.subheader("Add a pet")
with st.form("add_pet", clear_on_submit=True):
    pet_name = st.text_input("Pet name")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    if st.form_submit_button("Add pet"):
        if not pet_name.strip():
            st.error("Please enter a pet name.")
        elif owner.get_pet(pet_name.strip()):
            st.error(f"You already have a pet named {pet_name.strip()}.")
        else:
            owner.add_pet(Pet(pet_name.strip(), species))
            save()
            st.success(f"Added {pet_name.strip()} the {species}.")

st.subheader("Schedule a task")
if not owner.pets:
    st.info("Add a pet first, then you can schedule tasks for them.")
else:
    with st.form("add_task", clear_on_submit=False):
        target = st.selectbox("Pet", [p.name for p in owner.pets])
        description = st.text_input("Task", value="Morning walk")
        c1, c2, c3 = st.columns(3)
        with c1:
            due = st.date_input("Date")
            at = st.time_input("Time", value=None)
        with c2:
            minutes = st.number_input("Duration (minutes)", 1, 240, 20)
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=1)
        with c3:
            frequency = st.selectbox("Repeats", ["once", "daily", "weekly"])
        if st.form_submit_button("Add task"):
            if not description.strip() or at is None:
                st.error("Please enter a task description and a time.")
            else:
                owner.get_pet(target).add_task(
                    Task(description.strip(), at.strftime("%H:%M"), due,
                         int(minutes), priority, frequency)
                )
                save()
                st.success(f"Scheduled '{description.strip()}' for {target} at {at.strftime('%H:%M')}.")

st.divider()
st.subheader("Schedule")

if "flash" in st.session_state:
    st.success(st.session_state.pop("flash"))

conflicts = scheduler.detect_conflicts()
for warning in conflicts:
    st.warning(f"⚠️ {warning}. Consider moving one of these tasks.")

view = st.radio("Show", ["Today", "All tasks", "By priority"], horizontal=True)
f1, f2 = st.columns(2)
with f1:
    pet_filter = st.selectbox("Pet", ["All pets"] + [p.name for p in owner.pets])
with f2:
    status_filter = st.selectbox("Status", ["All", "Pending", "Completed"])

if view == "Today":
    tasks = scheduler.todays_schedule()
elif view == "By priority":
    tasks = scheduler.sort_by_priority()
else:
    tasks = scheduler.sort_by_time()
if pet_filter != "All pets":
    tasks = [t for t in tasks if t.pet_name == pet_filter]
if status_filter != "All":
    tasks = [t for t in tasks if t.completed == (status_filter == "Completed")]

if tasks:
    st.table(rows(tasks))
    if not conflicts:
        st.success("No scheduling conflicts.")
else:
    st.info("No tasks to show yet.")

pending = scheduler.filter_tasks(completed=False)
if pending:
    st.selectbox(
        "Mark a task complete",
        [f"{t.time} {t.description} ({t.pet_name}, {t.due_date})" for t in scheduler.sort_by_time() if not t.completed],
        key="complete_choice",
    )
    st.button("Mark complete", on_click=complete_selected)

st.divider()
st.subheader("Find a free slot")
c1, c2 = st.columns(2)
with c1:
    slot_minutes = st.number_input("Task length (minutes)", 1, 600, 30, key="slot_minutes")
with c2:
    slot_date = st.date_input("Day", key="slot_date")
if st.button("Find next available slot"):
    slot = scheduler.next_available_slot(int(slot_minutes), slot_date)
    if slot:
        st.success(f"A {int(slot_minutes)} minute task fits at {slot} on {slot_date}.")
    else:
        st.warning("No free slot that day between 07:00 and 21:00.")
