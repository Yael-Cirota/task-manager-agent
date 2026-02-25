from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from agent_service import agent

app = FastAPI(title="Task Manager Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class MessageRequest(BaseModel):
    message: str


class MessageResponse(BaseModel):
    reply: str


@app.get("/")
def index():
    """Serve the chat UI."""
    return FileResponse(Path(__file__).parent / "chat_ui" / "index.html")


@app.post("/chat", response_model=MessageResponse)
def chat(request: MessageRequest) -> MessageResponse:
    """Send a natural-language message to the task agent and get a response."""
    reply = agent(request.message)
    return MessageResponse(reply=reply)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
