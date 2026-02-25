from datetime import date

from task import Task, TaskStatus, TaskType


# ── Storage ──────────────────────────────────────────────────────────────────

tasks: list[Task] = []


# ── Service functions ─────────────────────────────────────────────────────────

def add_task(
    code: str,
    title: str,
    description: str = "",
    type: TaskType = TaskType.TASK,
    start_date: date | None = None,
    due_date: date | None = None,
    status: TaskStatus = TaskStatus.PENDING,
) -> Task:
    """Create a new Task and append it to the task list."""
    task = Task(
        code=code,
        title=title,
        description=description,
        type=type,
        start_date=start_date,
        due_date=due_date,
        status=status,
    )
    tasks.append(task)
    return task


def get_tasks(
    status: TaskStatus | None = None,
    type: TaskType | None = None,
    search: str | None = None,
) -> list[Task]:
    """Return tasks with optional filters.

    Args:
        status: Keep only tasks with this status.
        type:   Keep only tasks of this type.
        search: Case-insensitive substring match on title or description.

    Returns:
        A filtered list of Task objects.
    """
    result = tasks

    if status is not None:
        result = [t for t in result if t.status == status]

    if type is not None:
        result = [t for t in result if t.type == type]

    if search is not None:
        keyword = search.lower()
        result = [
            t for t in result
            if keyword in t.title.lower() or keyword in t.description.lower()
        ]

    return result


def update_task(
    code: str,
    title: str | None = None,
    description: str | None = None,
    type: TaskType | None = None,
    start_date: date | None = None,
    due_date: date | None = None,
    status: TaskStatus | None = None,
) -> Task:
    """Update fields of an existing task identified by its code.

    Only the provided (non-None) arguments are applied.
    Raises ValueError if no task with the given code exists.
    """
    task = next((t for t in tasks if t.code == code), None)
    if task is None:
        raise ValueError(f"No task found with code '{code}'")

    if title is not None:
        task.title = title
    if description is not None:
        task.description = description
    if type is not None:
        task.type = type
    if start_date is not None:
        task.start_date = start_date
    if due_date is not None:
        task.due_date = due_date
    if status is not None:
        task.status = status

    return task


def delete_task(code: str) -> Task:
    """Remove a task by its code and return it.

    Raises ValueError if no task with the given code exists.
    """
    for index, task in enumerate(tasks):
        if task.code == code:
            tasks.pop(index)
            return task
    raise ValueError(f"No task found with code '{code}'")
