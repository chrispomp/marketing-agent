from typing import List, Optional
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant|system)$")
    content: str

class BriefRequest(BaseModel):
    prompt: str

class BriefResponse(BaseModel):
    markdown: str
    tokens_input: Optional[int] = 0
    tokens_output: Optional[int] = 0
    latency_ms: Optional[int] = 0

class ScriptRequest(BaseModel):
    prompt: Optional[str] = None
    brief_markdown: Optional[str] = None

class ScriptResponse(BaseModel):
    screenplay: str
    tokens_input: Optional[int] = 0
    tokens_output: Optional[int] = 0
    latency_ms: Optional[int] = 0

class StoryboardRequest(BaseModel):
    script: str
    image_size: str = "1024x1024"

class StoryboardItem(BaseModel):
    scene_number: int
    scene_slug: str
    prompt: str
    gcs_url: str

class StoryboardResponse(BaseModel):
    storyboard: List[StoryboardItem]
    latency_ms: Optional[int] = 0

class AnimaticRequest(BaseModel):
    script: str
    duration_seconds: int = 45  # target 30-60

class AnimaticJobResponse(BaseModel):
    job_name: str
    latency_ms: Optional[int] = 0

class AnimaticStatusResponse(BaseModel):
    status: str
    gcs_url: Optional[str] = None
    error: Optional[dict] = None

class ChatTurn(BaseModel):
    messages: List[ChatMessage]

class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None
