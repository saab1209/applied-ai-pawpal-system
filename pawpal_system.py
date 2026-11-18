from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple

PRIORITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}


@dataclass
class Task:
    """Represents a single pet care activity such as feeding, walking, or medication."""
    title: str
    category: str
    time: str  # 24-hour format "HH:MM", e.g., "08:30"
    duration_minutes: int = 30
    priority: str = "Medium"
    frequency: str = "Once"  # "Once", "Daily", "Weekly"
    completed: bool = False
    pet_name: str = ""
    due_date: date = field(default_factory=date.today)

    def mark_complete(self) -> Optional["Task"]:
        """Mark task complete and return the next recurring Task shifted by timedelta if Daily or Weekly."""
        self.completed = True
        if self.frequency == "Daily":
            next_due = self.due_date + timedelta(days=1)
        elif self.frequency == "Weekly":
            next_due = self.due_date + timedelta(days=7)
        else:
            return None

        return Task(
            title=self.title,
            category=self.category,
            time=self.time,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            frequency=self.frequency,
            completed=False,
            pet_name=self.pet_name,
            due_date=next_due,
        )


@dataclass
class Pet:
    """Stores pet details and manages its assigned list of care tasks."""
    name: str
    species: str
    age: int
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet and tag it with the pet's name."""
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, task_title: str) -> bool:
        """Remove a task matching task_title and return True if removed."""
        for idx, task in enumerate(self.tasks):
            if task.title.lower() == task_title.lower():
                self.tasks.pop(idx)
                return True
        return False

    def get_pending_tasks(self) -> List[Task]:
        """Return all incomplete tasks assigned to this pet."""
        return [task for task in self.tasks if not task.completed]


@dataclass
class Owner:
    """Manages multiple pets and aggregates tasks across the entire household."""
    name: str
    email: str = ""
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a new Pet under this owner."""
        self.pets.append(pet)

    def get_pet(self, pet_name: str) -> Optional[Pet]:
        """Find and return a registered Pet by name."""
        for pet in self.pets:
            if pet.name.lower() == pet_name.lower():
                return pet
        return None

    def get_all_tasks(self) -> List[Task]:
        """Collect and return every pet's tasks combined in a single list."""
        all_tasks: List[Task] = []
        for pet in self.pets:
            for task in pet.tasks:
                if not task.pet_name:
                    task.pet_name = pet.name
                all_tasks.append(task)
        return all_tasks


class Scheduler:
    """Coordinates multi-pet scheduling, sorting, filtering, conflict detection, and recurrence."""

    def __init__(self, owner: Owner):
        """Initialize the Scheduler with an Owner instance."""
        self.owner = owner

    @staticmethod
    def _parse_minutes(time_str: str) -> int:
        """Convert 'HH:MM' time string into minutes since midnight for sorting and overlap checks."""
        try:
            dt = datetime.strptime(time_str.strip(), "%H:%M")
            return dt.hour * 60 + dt.minute
        except ValueError:
            return 0

    def sort_by_time(self) -> List[Task]:
        """Return all owner tasks sorted chronologically by their 'HH:MM' time attribute."""
        return sorted(self.owner.get_all_tasks(), key=lambda t: self._parse_minutes(t.time))

    def get_daily_schedule(self, sort_by: str = "time") -> List[Task]:
        """Retrieve all tasks from Owner and sort by chronological time or priority."""
        tasks = self.owner.get_all_tasks()
        if sort_by == "priority":
            return sorted(
                tasks,
                key=lambda t: (PRIORITY_ORDER.get(t.priority, 1), self._parse_minutes(t.time)),
            )
        return self.sort_by_time()

    def filter_tasks(self, pet_name: Optional[str] = None, status: str = "all") -> List[Task]:
        """Filter tasks across pets by pet_name and completion status ('all', 'pending', 'completed')."""
        tasks = self.sort_by_time()
        if pet_name and pet_name.lower() != "all":
            tasks = [t for t in tasks if t.pet_name.lower() == pet_name.lower()]
        if status.lower() == "pending":
            tasks = [t for t in tasks if not t.completed]
        elif status.lower() == "completed":
            tasks = [t for t in tasks if t.completed]
        return tasks

    def detect_conflicts(self) -> List[Tuple[Task, Task]]:
        """Detect pairs of incomplete tasks whose scheduled time windows overlap."""
        pending = sorted(
            [t for t in self.owner.get_all_tasks() if not t.completed],
            key=lambda t: self._parse_minutes(t.time),
        )
        conflicts: List[Tuple[Task, Task]] = []
        for i in range(len(pending)):
            start_a = self._parse_minutes(pending[i].time)
            end_a = start_a + pending[i].duration_minutes
            for j in range(i + 1, len(pending)):
                start_b = self._parse_minutes(pending[j].time)
                if start_b < end_a:
                    conflicts.append((pending[i], pending[j]))
                else:
                    break
        return conflicts

    def complete_task(self, pet_name: str, task_title: str) -> Optional[Task]:
        """Mark a pet's task complete and auto-append the next instance if it is recurring."""
        pet = self.owner.get_pet(pet_name)
        if not pet:
            return None
        for task in pet.tasks:
            if task.title.lower() == task_title.lower() and not task.completed:
                next_task = task.mark_complete()
                if next_task:
                    pet.add_task(next_task)
                return next_task
        return None
