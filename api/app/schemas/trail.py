from datetime import date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict

class CheckpointSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    route_id: int
    seq: int
    name_en: str
    name_hi: str
    lat: float
    lon: float
    altitude_m: int
    dist_from_prev_km: float
    min_minutes: int
    max_minutes: int
    cutoff_time: Optional[str] = None
    capacity_hint: Optional[int] = None
    facilities: Dict[str, Any]
    has_network: bool
    status: str
    qr_key_version: int
    verified: bool

class RouteSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    yatra_id: int
    name: str
    type: str
    total_distance_km: float
    base_altitude_m: int
    max_altitude_m: int
    rules_config: Dict[str, Any]
    verified: bool
    checkpoints: List[CheckpointSchema] = []

class YatraSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name_en: str
    name_hi: str
    district: str
    season_start: date
    season_end: date
    description_en: Optional[str] = None
    description_hi: Optional[str] = None
    status: str
    routes: List[RouteSchema] = []
