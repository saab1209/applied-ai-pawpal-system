import streamlit as st
from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+ | Smart Pet Care", page_icon="🐾", layout="wide")

st.title("🐾 PawPal+ — Smart Pet Care Management")
st.caption("Modular OOP scheduling engine with conflict detection, priority sorting, and recurring routines.")

# Persist Owner object in Streamlit session_state so data survives reruns
if "owner" not in st.session_state:
    default_owner = Owner(name="Salmaa", email="salmaa@example.com")
    bella = Pet(name="Bella", species="Dog", age=3)
    milo = Pet(name="Milo", species="Cat", age=2)
    bella.add_task(Task(title="Morning Walk", category="Walk", time="08:00", duration_minutes=30, priority="High", frequency="Daily"))
    milo.add_task(Task(title="Thyroid Medication", category="Medication", time="08:15", duration_minutes=15, priority="High", frequency="Daily"))
    bella.add_task(Task(title="Evening Feeding", category="Feeding", time="18:00", duration_minutes=15, priority="Medium", frequency="Daily"))
    default_owner.add_pet(bella)
    default_owner.add_pet(milo)
    st.session_state.owner = default_owner

owner: Owner = st.session_state.owner
scheduler = Scheduler(owner)

# Sidebar: Owner Info & Register New Pet
with st.sidebar:
    st.header("👤 Owner & Household")
    updated_name = st.text_input("Owner Name", value=owner.name)
    if updated_name != owner.name:
        owner.name = updated_name

    st.divider()
    st.subheader("➕ Add a New Pet")
    with st.form("add_pet_form", clear_on_submit=True):
        new_pet_name = st.text_input("Pet Name", placeholder="e.g., Mochi")
        new_pet_species = st.selectbox("Species", ["Dog", "Cat", "Bird", "Rabbit", "Other"])
        new_pet_age = st.number_input("Age (years)", min_value=0, max_value=35, value=2)
        submitted_pet = st.form_submit_button("Register Pet")
        if submitted_pet:
            if not new_pet_name.strip():
                st.error("Please enter a pet name.")
            elif owner.get_pet(new_pet_name.strip()):
                st.warning(f"{new_pet_name.strip()} is already registered.")
            else:
                owner.add_pet(Pet(name=new_pet_name.strip(), species=new_pet_species, age=int(new_pet_age)))
                st.success(f"Added {new_pet_name.strip()}!")
                st.rerun()

    st.divider()
    st.subheader("🐶 Registered Pets")
    if owner.pets:
        for p in owner.pets:
            st.markdown(f"**{p.name}** ({p.species}, {p.age} yrs) — `{len(p.get_pending_tasks())} pending`")
    else:
        st.info("No pets registered yet.")

# Main Area: Schedule a New Care Task
st.subheader("📅 Schedule a Pet Care Task")
if not owner.pets:
    st.warning("Register at least one pet in the sidebar before adding tasks.")
else:
    with st.form("add_task_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            selected_pet = st.selectbox("Select Pet", [p.name for p in owner.pets])
            task_title = st.text_input("Task Title", placeholder="e.g., Afternoon Walk")
        with c2:
            category = st.selectbox("Category", ["Feeding", "Walk", "Medication", "Appointment", "Enrichment"])
            task_time = st.text_input("Time (24h HH:MM)", value="12:00")
        with c3:
            duration = st.number_input("Duration (mins)", min_value=5, max_value=240, value=20, step=5)
            priority = st.selectbox("Priority", ["High", "Medium", "Low"], index=1)
            frequency = st.selectbox("Frequency", ["Once", "Daily", "Weekly"], index=0)

        submitted_task = st.form_submit_button("Add Care Task")
        if submitted_task:
            if not task_title.strip():
                st.error("Please enter a task title.")
            else:
                target_pet = owner.get_pet(selected_pet)
                if target_pet:
                    target_pet.add_task(
                        Task(
                            title=task_title.strip(),
                            category=category,
                            time=task_time.strip(),
                            duration_minutes=int(duration),
                            priority=priority,
                            frequency=frequency,
                        )
                    )
                    st.success(f"Scheduled '{task_title.strip()}' for {selected_pet} at {task_time.strip()}.")
                    st.rerun()

st.divider()

# Conflict Alerts
conflicts = scheduler.detect_conflicts()
if conflicts:
    st.warning(f"⚠️ **{len(conflicts)} Scheduling Conflict(s) Detected:**")
    for task_a, task_b in conflicts:
        st.write(
            f"- **{task_a.pet_name}: {task_a.title}** (`{task_a.time}`, {task_a.duration_minutes}m) overlaps with "
            f"**{task_b.pet_name}: {task_b.title}** (`{task_b.time}`, {task_b.duration_minutes}m)"
        )

# Daily Schedule View & Controls
st.subheader(f"📋 {owner.name}'s Daily Care Schedule")
f1, f2, f3 = st.columns(3)
with f1:
    sort_choice = st.selectbox("Sort By", ["time", "priority"], format_func=lambda x: "Chronological Time" if x == "time" else "Priority (High → Low)")
with f2:
    pet_filter = st.selectbox("Filter by Pet", ["All"] + [p.name for p in owner.pets])
with f3:
    status_filter = st.selectbox("Filter by Status", ["all", "pending", "completed"], format_func=str.capitalize)

tasks = scheduler.filter_tasks(pet_name=pet_filter, status=status_filter)
if sort_choice == "priority":
    priority_rank = {"High": 0, "Medium": 1, "Low": 2}
    tasks = sorted(tasks, key=lambda t: (priority_rank.get(t.priority, 1), t.time))

if not tasks:
    st.info("No tasks match the current filter.")
else:
    for idx, task in enumerate(tasks):
        col_info, col_action = st.columns([4, 1])
        badge = "✅ Done" if task.completed else "⏳ Pending"
        with col_info:
            st.markdown(
                f"**`{task.time}`** | **{task.pet_name}** — **{task.title}** "
                f"(`{task.category}` • `{task.duration_minutes}m` • Priority: **{task.priority}** • `{task.frequency}`) — {badge}"
            )
        with col_action:
            if not task.completed:
                if st.button("Complete", key=f"complete_{task.pet_name}_{task.title}_{idx}"):
                    next_occurrence = scheduler.complete_task(task.pet_name, task.title)
                    if next_occurrence:
                        st.toast(f"Completed '{task.title}' and scheduled next {task.frequency} occurrence!")
                    else:
                        st.toast(f"Completed '{task.title}'!")
                    st.rerun()
