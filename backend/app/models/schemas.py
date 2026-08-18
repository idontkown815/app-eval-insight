from pydantic import BaseModel
from typing import Optional, Dict, List, Any


class ValidateLinkRequest(BaseModel):
    url: str


class ValidateLinkResponse(BaseModel):
    valid: bool
    bundle_id: Optional[str] = None
    app_info: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class CreateTaskRequest(BaseModel):
    bundle_id: str
    url: str = ""
    app_info: Dict[str, Any] = {}
    user_goal: str = ""
    filters: Dict[str, Any] = {}
    config: Dict[str, Any] = {}  # 兼容旧字段


class CreateTaskResponse(BaseModel):
    task_id: str
    status: str


class ProgressResponse(BaseModel):
    task_id: str
    status: str
    current_stage: Optional[str] = None
    progress_percent: int
    is_using_cache: bool
    stages: List[Any]


class ResultsResponse(BaseModel):
    task_id: str
    status: str
    data_source: str
    deliverables: Dict[str, Any]


class ImportResponse(BaseModel):
    import_id: str
    status: str
    statistics: Dict[str, Any]


class HealthResponse(BaseModel):
    network: bool
    llm: bool
