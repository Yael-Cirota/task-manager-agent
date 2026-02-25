import json
from datetime import date

import truststore
truststore.inject_into_ssl()  # use Windows system certificate store

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

import todo_service
from task import TaskStatus, TaskType

client = OpenAI()

# ── Tool schemas ──────────────────────────────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "add_task",
            "description": "Create a new task and add it to the list.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Unique task code, e.g. 'TASK-001'.",
                    },
                    "title": {
                        "type": "string",
                        "description": "Short title of the task.",
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description of the task.",
                    },
                    "type": {
                        "type": "string",
                        "enum": [t.value for t in TaskType],
                        "description": "Type of task.",
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format.",
                    },
                    "due_date": {
                        "type": "string",
                        "description": "Due date in YYYY-MM-DD format.",
                    },
                    "status": {
                        "type": "string",
                        "enum": [s.value for s in TaskStatus],
                        "description": "Current status of the task.",
                    },
                },
                "required": ["code", "title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_tasks",
            "description": "Retrieve tasks with optional filters.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": [s.value for s in TaskStatus],
                        "description": "Filter by task status.",
                    },
                    "type": {
                        "type": "string",
                        "enum": [t.value for t in TaskType],
                        "description": "Filter by task type.",
                    },
                    "search": {
                        "type": "string",
                        "description": "Substring search on title or description.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_task",
            "description": "Update one or more fields of an existing task.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Code of the task to update.",
                    },
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "type": {
                        "type": "string",
                        "enum": [t.value for t in TaskType],
                    },
                    "start_date": {
                        "type": "string",
                        "description": "New start date in YYYY-MM-DD format.",
                    },
                    "due_date": {
                        "type": "string",
                        "description": "New due date in YYYY-MM-DD format.",
                    },
                    "status": {
                        "type": "string",
                        "enum": [s.value for s in TaskStatus],
                    },
                },
                "required": ["code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_task",
            "description": "Delete a task by its code.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Code of the task to delete.",
                    },
                },
                "required": ["code"],
            },
        },
    },
]

# ── Function dispatcher ───────────────────────────────────────────────────────

def _parse_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _dispatch(name: str, arguments: dict):
    """Call the matching todo_service function and return a JSON-serialisable result."""
    if name == "add_task":
        arguments["type"] = TaskType(arguments["type"]) if "type" in arguments else TaskType.TASK
        arguments["status"] = TaskStatus(arguments["status"]) if "status" in arguments else TaskStatus.PENDING
        arguments["start_date"] = _parse_date(arguments.get("start_date"))
        arguments["due_date"] = _parse_date(arguments.get("due_date"))
        task = todo_service.add_task(**arguments)
        return task.to_dict()

    elif name == "get_tasks":
        if "status" in arguments:
            arguments["status"] = TaskStatus(arguments["status"])
        if "type" in arguments:
            arguments["type"] = TaskType(arguments["type"])
        tasks = todo_service.get_tasks(**arguments)
        return [t.to_dict() for t in tasks]

    elif name == "update_task":
        if "type" in arguments:
            arguments["type"] = TaskType(arguments["type"])
        if "status" in arguments:
            arguments["status"] = TaskStatus(arguments["status"])
        arguments["start_date"] = _parse_date(arguments.get("start_date"))
        arguments["due_date"] = _parse_date(arguments.get("due_date"))
        # Remove None date values so update_task doesn't overwrite with None
        arguments = {k: v for k, v in arguments.items() if v is not None or k == "code"}
        task = todo_service.update_task(**arguments)
        return task.to_dict()

    elif name == "delete_task":
        task = todo_service.delete_task(**arguments)
        return task.to_dict()

    raise ValueError(f"Unknown function: {name}")


# ── Agent ─────────────────────────────────────────────────────────────────────

def agent(query: str, model: str = "gpt-4o-mini") -> str:
    """Process a natural-language query about tasks.

    1. Sends the query to GPT with the available tool schemas.
    2. Executes the function(s) GPT selects.
    3. Sends the results back to GPT for a human-readable response.
    4. Returns the final response string.
    """
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful task management assistant. "
                "Use the provided tools to manage the user's task list. "
                "Always respond in clear, friendly language."
            ),
        },
        {"role": "user", "content": query},
    ]

    # ── First call: let GPT decide which tool(s) to use ──────────────────────
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
    )

    message = response.choices[0].message
    messages.append(message)

    # ── Execute every tool call GPT requested ────────────────────────────────
    if message.tool_calls:
        for tool_call in message.tool_calls:
            name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            try:
                result = _dispatch(name, arguments)
            except Exception as exc:
                result = {"error": str(exc)}

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, default=str),
                }
            )

        # ── Second call: GPT formulates the final human-readable response ────
        followup = client.chat.completions.create(
            model=model,
            messages=messages,
        )
        return followup.choices[0].message.content

    # GPT answered directly without needing a tool
    return message.content
