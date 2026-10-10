from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator
from uuid import UUID

class CheckinItem(BaseModel):
    id: str = Field(..., description="Client-generated UUID primary key")
    @field_validator('id')
    @classmethod
    def uuid_id(cls, value):
        return str(UUID(value))

    group_code: str = Field(..., min_length=6, max_length=6)
    checkpoint_id: int
    signed_qr: str = Field(..., description="Raw scanned QR string e.g. YK1:CP:2:a1b2c3d4")
    source: Literal["self", "volunteer"] = "self"
    direction: Literal["outbound", "returning", "exit"] = "outbound"
    member_ids: List[int] = Field(default_factory=list, max_length=50)
    volunteer_id: Optional[int] = None
    headcount: int = Field(..., ge=1, le=50)
    client_ts: datetime
    clock_skew_s: float = Field(0.0, allow_inf_nan=False)
    lat: Optional[float] = None
    lon: Optional[float] = None

class CheckinBatchRequest(BaseModel):
    events: List[CheckinItem] = Field(..., max_length=50)

class CheckinResultItem(BaseModel):
    id: str
    status: Literal["accepted", "duplicate", "invalid"]
    valid: bool
    invalid_reason: Optional[str] = None
    server_ts: datetime

class CheckinBatchResponse(BaseModel):
    results: List[CheckinResultItem]
    processed_count: int
    accepted_count: int
    duplicate_count: int
    invalid_count: int
