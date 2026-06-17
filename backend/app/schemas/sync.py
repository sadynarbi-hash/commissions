from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from ..models.sales import SyncSourceType, SyncStatut


class SyncRequest(BaseModel):
    source: SyncSourceType
    periode: str  # YYYY-MM
    force: bool = False


class SyncLogRead(BaseModel):
    id: int
    source: SyncSourceType
    periode: Optional[str] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    statut: SyncStatut
    nb_records: int
    message: Optional[str] = None
    model_config = {"from_attributes": True}


class ConnectionTestRequest(BaseModel):
    source: SyncSourceType
