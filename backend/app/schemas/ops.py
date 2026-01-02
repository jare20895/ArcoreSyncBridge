from uuid import UUID
from pydantic import BaseModel
from typing import List, Optional

class DriftReportRequest(BaseModel):
    sync_def_id: UUID
    check_type: str = "LEDGER_VALIDITY" # LEDGER_VALIDITY (Check if ledger items exist in SP), FULL_RECONCILE (Two-way check)

class DriftItem(BaseModel):
    item_id: str
    list_id: str
    issue: str # ORPHANED_IN_LEDGER, UNTRACKED_IN_SP
    details: Optional[str] = None

class DriftReportResponse(BaseModel):
    sync_def_id: UUID
    timestamp: str
    total_issues: int
    items: List[DriftItem]
