from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
import uuid

class Horizon(str, Enum):
    SHORT_TERM = "short_term"  # 1 year
    MID_TERM = "mid_term"      # 2-5 years
    LONG_TERM = "long_term"    # Decade

class GoalCategory(str, Enum):
    FINANCIAL = "financeira"
    LIFE = "vida"
    HEALTH = "saúde"
    PROFESSIONAL = "profissional"
    OTHERS = "outros"

class GoalStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

class SmartCriteria(BaseModel):
    specific: str
    measurable: str
    achievable: str
    relevant: str
    time_bound: str

class Milestone(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    is_completed: bool = False
    completed_at: Optional[datetime] = None

class Goal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    category: GoalCategory = GoalCategory.LIFE
    horizon: Horizon
    smart_criteria: SmartCriteria
    milestones: List[Milestone] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    status: GoalStatus = GoalStatus.ACTIVE
    status_reason: Optional[str] = None
    progress_percentage: int = Field(default=0, ge=0, le=100)

class CheckInType(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

class CheckIn(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: datetime = Field(default_factory=datetime.now)
    type: CheckInType
    goals_covered: List[str]  # List of Goal IDs
    file_path: str  # Path to the markdown file containing the check-in content
    snapshot: Optional[List[dict]] = None # List of Goal dict representations at the time of check-in

class Config(BaseModel):
    user_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    last_run_at: Optional[datetime] = None
