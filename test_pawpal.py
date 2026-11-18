from datetime import date, timedelta
from pawpal_system import Owner, Pet, Scheduler, Task


def test_task_completion_updates_status():
    task = Task(title="Morning Walk", category="Walk", time="08:00", frequency="Once")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Bella", species="Dog", age=3)
    assert len(pet.tasks) == 0
    pet.add_task(Task(title="Dinner", category="Feeding", time="18:00"))
    assert len(pet.tasks) == 1
    assert pet.tasks[0].pet_name == "Bella"


def test_sort_by_time_returns_chronological_order():
    owner = Owner(name="Salmaa")
    dog = Pet(name="Bella", species="Dog", age=3)
    dog.add_task(Task(title="Evening Walk", category="Walk", time="18:30"))
    dog.add_task(Task(title="Morning Walk", category="Walk", time="07:30"))
    dog.add_task(Task(title="Midday Lunch", category="Feeding", time="12:15"))
    owner.add_pet(dog)

    scheduler = Scheduler(owner)
    sorted_titles = [t.title for t in scheduler.sort_by_time()]
    assert sorted_titles == ["Morning Walk", "Midday Lunch", "Evening Walk"]


def test_recurring_daily_task_creates_next_day_occurrence():
    today = date.today()
    owner = Owner(name="Salmaa")
    dog = Pet(name="Bella", species="Dog", age=3)
    dog.add_task(Task(title="Daily Vitamin", category="Medication", time="09:00", frequency="Daily", due_date=today))
    owner.add_pet(dog)

    scheduler = Scheduler(owner)
    next_task = scheduler.complete_task("Bella", "Daily Vitamin")
    assert next_task is not None
    assert next_task.completed is False
    assert next_task.due_date == today + timedelta(days=1)
    assert len(dog.tasks) == 2


def test_conflict_detection_flags_overlapping_and_duplicate_times():
    owner = Owner(name="Salmaa")
    dog = Pet(name="Bella", species="Dog", age=3)
    cat = Pet(name="Milo", species="Cat", age=2)

    dog.add_task(Task(title="Walk", category="Walk", time="08:00", duration_minutes=30))
    cat.add_task(Task(title="Meds", category="Medication", time="08:00", duration_minutes=15))
    owner.add_pet(dog)
    owner.add_pet(cat)

    scheduler = Scheduler(owner)
    conflicts = scheduler.detect_conflicts()
    assert len(conflicts) == 1
    first_pair = conflicts[0]
    assert first_pair[0].title == "Walk"
    assert first_pair[1].title == "Meds"


def test_edge_case_pet_with_no_tasks_returns_empty_schedule():
    owner = Owner(name="Salmaa")
    owner.add_pet(Pet(name="Mochi", species="Rabbit", age=1))
    scheduler = Scheduler(owner)
    assert scheduler.sort_by_time() == []
    assert scheduler.detect_conflicts() == []

