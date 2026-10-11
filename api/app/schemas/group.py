from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, ConfigDict

AgeBandType = Literal["<18", "18-40", "41-60", "60+"]

class MemberCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=128)
    age_band: AgeBandType
    note: Optional[str] = Field(None, max_length=256)

class MemberSchema(MemberCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    group_id: int

class PlannedStop(BaseModel):
    checkpoint_id: int
    day: int  # Day 1, Day 2, etc.

class GroupCreate(BaseModel):
    consent: Literal[True]
    yatra_id: int
    route_id: int
    leader_name: str = Field(..., min_length=2, max_length=128)
    leader_phone: str = Field(..., min_length=10, max_length=10, pattern=r"^[0-9]{10}$")
    emergency_name: str = Field(..., min_length=2, max_length=128)
    emergency_phone: str = Field(..., min_length=10, max_length=10, pattern=r"^[0-9]{10}$")
    size: int = Field(..., ge=1, le=50)
    planned_start: datetime
    planned_return: Optional[datetime] = None
    members: List[MemberCreate] = Field(default_factory=list, max_length=50)
    planned_stops: List[PlannedStop] = []

class ItineraryAdvisory(BaseModel):
    rule_id: str = "R10"
    severity: str = "info"
    message_en: str
    message_hi: str
    altitude_gain_m: int
    details: dict = {}

class GroupRegisterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    pass_token: str  # YK1:<code>
    yatra_id: int
    route_id: int
    leader_name: str
    size: int
    status: str
    advisories: List[ItineraryAdvisory] = []

class GroupStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    leader_name: str
    size: int
    status: str
    started_at: Optional[datetime] = None
    last_checkpoint: Optional[dict] = None
    next_checkpoint: Optional[dict] = None
    eta_range: Optional[str] = None
    open_advice: List[dict] = []
    planned_return: Optional[datetime] = None
    members: List[dict] = []
    journey_counts: dict = {}
    checkpoint_statuses: List[dict] = []
    incidents: List[dict] = []
