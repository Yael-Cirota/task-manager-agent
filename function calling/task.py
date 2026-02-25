from dataclasses import dataclass
from datetime import date
from enum import Enum


class TaskType(str, Enum):
    BUG = "bug"
    FEATURE = "feature"
    IMPROVEMENT = "improvement"
    TASK = "task"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


@dataclass
class Task:
    code: str                          # Unique identifier, e.g. "TASK-001"
    title: str
    description: str = ""
    type: TaskType = TaskType.TASK
    start_date: date | None = None
    due_date: date | None = None
    status: TaskStatus = TaskStatus.PENDING

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "title": self.title,
            "description": self.description,
            "type": self.type.value,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "status": self.status.value,
        }
