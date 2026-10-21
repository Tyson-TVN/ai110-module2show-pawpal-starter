import json
from dataclasses import asdict, dataclass, field, replace
from datetime import date, datetime, timedelta
from typing import List, Optional

PRIORITIES = {"high": 0, "medium": 1, "low": 2}
FREQUENCIES = ("once", "daily", "weekly")
RECURRENCE_DAYS = {"daily": 1, "weekly": 7}


@dataclass
class Task:
    """A single pet care activity."""

    description: str
    time: str  # "HH:MM", 24-hour
    due_date: date = field(default_factory=date.today)
    duration_minutes: int = 15
    priority: str = "medium"
    frequency: str = "once"
    completed: bool = False
    pet_name: str = ""

    def __post_init__(self) -> None:
        """Reject times, priorities and frequencies we don't know how to handle."""
        try:
            datetime.strptime(self.time, "%H:%M")
        except ValueError:
            raise ValueError("time must look like HH:MM, e.g. 07:30") from None
        if len(self.time) != 5:
            raise ValueError("time must be zero-padded, e.g. 07:30")
        if self.priority not in PRIORITIES:
            raise ValueError(f"priority must be one of {list(PRIORITIES)}")
        if self.frequency not in FREQUENCIES:
            raise ValueError(f"frequency must be one of {list(FREQUENCIES)}")

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def to_dict(self) -> dict:
        """Return a JSON-friendly dict (the date becomes an ISO string)."""
        data = asdict(self)
        data["due_date"] = self.due_date.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Rebuild a task from the dict made by to_dict()."""
        data = dict(data)
        data["due_date"] = date.fromisoformat(data["due_date"])
        return cls(**data)


@dataclass
class Pet:
    """A pet and the tasks that belong to it."""

    name: str
    species: str
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet and tag it with the pet's name."""
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet if it is there."""
        if task in self.tasks:
            self.tasks.remove(task)

    def get_tasks(self) -> List[Task]:
        """Return a copy of this pet's task list."""
        return list(self.tasks)

    def to_dict(self) -> dict:
        """Return a JSON-friendly dict of this pet and its tasks."""
        return {"name": self.name, "species": self.species,
                "tasks": [t.to_dict() for t in self.tasks]}

    @classmethod
    def from_dict(cls, data: dict) -> "Pet":
        """Rebuild a pet and its tasks from to_dict() output."""
        pet = cls(data["name"], data["species"])
        for task_data in data.get("tasks", []):
            pet.add_task(Task.from_dict(task_data))
        return pet


@dataclass
class Owner:
    """A person who owns one or more pets."""

    name: str
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def get_pet(self, name: str) -> Optional[Pet]:
        """Find a pet by name, ignoring case."""
        for pet in self.pets:
            if pet.name.lower() == name.lower():
                return pet
        return None

    def get_all_tasks(self) -> List[Task]:
        """Return every task from every pet in one list."""
        return [task for pet in self.pets for task in pet.tasks]

    def to_dict(self) -> dict:
        """Return a JSON-friendly dict of the owner, pets and tasks."""
        return {"name": self.name, "pets": [p.to_dict() for p in self.pets]}

    @classmethod
    def from_dict(cls, data: dict) -> "Owner":
        """Rebuild an owner from to_dict() output."""
        return cls(data["name"], [Pet.from_dict(p) for p in data.get("pets", [])])

    def save_to_json(self, path: str) -> None:
        """Write the owner, pets and tasks to a JSON file."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_json(cls, path: str) -> "Owner":
        """Read an owner back from a JSON file written by save_to_json()."""
        with open(path, encoding="utf-8") as f:
            return cls.from_dict(json.load(f))


class Scheduler:
    """Organizes tasks across all of an owner's pets."""

    def __init__(self, owner: Owner):
        self.owner = owner

    def sort_by_time(self) -> List[Task]:
        """Return all tasks ordered by due date, then by HH:MM time."""
        return sorted(self.owner.get_all_tasks(),
                      key=lambda t: (t.due_date, t.time))

    def sort_by_priority(self) -> List[Task]:
        """Return all tasks ordered by priority (high first), then by time."""
        return sorted(self.owner.get_all_tasks(),
                      key=lambda t: (PRIORITIES[t.priority], t.due_date, t.time))

    def filter_tasks(self, pet_name: Optional[str] = None,
                     completed: Optional[bool] = None) -> List[Task]:
        """Return tasks matching the given pet name and/or completion status."""
        tasks = self.owner.get_all_tasks()
        if pet_name is not None:
            tasks = [t for t in tasks if t.pet_name.lower() == pet_name.lower()]
        if completed is not None:
            tasks = [t for t in tasks if t.completed == completed]
        return tasks

    def detect_conflicts(self) -> List[str]:
        """Return a warning for each date and time with more than one pending task."""
        slots = {}
        for task in self.owner.get_all_tasks():
            if not task.completed:
                slots.setdefault((task.due_date, task.time), []).append(task)

        warnings = []
        for (due, time), tasks in sorted(slots.items()):
            if len(tasks) > 1:
                names = ", ".join(f"{t.description} ({t.pet_name})" for t in tasks)
                warnings.append(f"Conflict on {due} at {time}: {names}")
        return warnings

    def mark_task_complete(self, task: Task) -> Optional[Task]:
        """Complete a task; for daily/weekly tasks, add and return the next one."""
        if task.completed:
            return None
        task.mark_complete()

        days = RECURRENCE_DAYS.get(task.frequency)
        if days is None:
            return None

        next_task = replace(task, due_date=task.due_date + timedelta(days=days),
                            completed=False)
        pet = self.owner.get_pet(task.pet_name)
        if pet is not None:
            pet.add_task(next_task)
        return next_task

    def next_available_slot(self, duration_minutes: int, on_date: date,
                            day_start: str = "07:00",
                            day_end: str = "21:00") -> Optional[str]:
        """Return the earliest HH:MM where a task of this length fits, or None."""
        if duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")

        def to_minutes(hhmm: str) -> int:
            hours, minutes = hhmm.split(":")
            return int(hours) * 60 + int(minutes)

        # Busy blocks (start, end) of pending tasks that day, earliest first.
        busy = sorted(
            (to_minutes(t.time), to_minutes(t.time) + max(t.duration_minutes, 0))
            for t in self.owner.get_all_tasks()
            if not t.completed and t.due_date == on_date
        )

        candidate = to_minutes(day_start)
        for start, end in busy:
            if start >= candidate + duration_minutes:
                break  # the gap before this block is big enough
            candidate = max(candidate, end)  # otherwise move past it

        if candidate + duration_minutes <= to_minutes(day_end):
            return f"{candidate // 60:02d}:{candidate % 60:02d}"
        return None

    def todays_schedule(self) -> List[Task]:
        """Return today's tasks in time order."""
        today = date.today()
        return [t for t in self.sort_by_time() if t.due_date == today]
