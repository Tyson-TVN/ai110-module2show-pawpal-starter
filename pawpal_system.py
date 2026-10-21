from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional


@dataclass
class Task:
    description: str
    time: str
    due_date: date = field(default_factory=date.today)
    duration_minutes: int = 15
    priority: str = "medium"
    frequency: str = "once"
    completed: bool = False
    pet_name: str = ""

    def mark_complete(self) -> None:
        pass


@dataclass
class Pet:
    name: str
    species: str
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        pass

    def remove_task(self, task: Task) -> None:
        pass

    def get_tasks(self) -> List[Task]:
        pass


@dataclass
class Owner:
    name: str
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        pass

    def get_pet(self, name: str) -> Optional[Pet]:
        pass

    def get_all_tasks(self) -> List[Task]:
        pass


class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner

    def sort_by_time(self) -> List[Task]:
        pass

    def sort_by_priority(self) -> List[Task]:
        pass

    def filter_tasks(self, pet_name: Optional[str] = None,
                     completed: Optional[bool] = None) -> List[Task]:
        pass

    def detect_conflicts(self) -> List[str]:
        pass

    def mark_task_complete(self, task: Task) -> Optional[Task]:
        pass

    def todays_schedule(self) -> List[Task]:
        pass
