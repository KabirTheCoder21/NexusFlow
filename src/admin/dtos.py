
from pydantic import BaseModel


class DashboardResponseDTO(BaseModel):
    total_users:int
    active_users:int
    inactive_user:int
    deleted_users:int

    total_tasks:int
    completed_tasks:int
    pending_tasks:int


