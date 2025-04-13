from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional
from datetime import datetime
import json

class Participant(BaseModel):
    user_id: int
    username: str

class Activity(BaseModel):
    content: str
    media: Optional[List[str]] = Field(default_factory=list)
    added_by: int
    added_at: datetime = Field(default_factory=datetime.now)
    last_selected: Optional[datetime] = None
    selection_count: int = 0

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class Pool(BaseModel):
    name: str
    creator_id: int = 0
    participants: List[Participant] = Field(default_factory=list)
    activities: List[Activity] = Field(default_factory=list)
    penalties: Dict[int, float] = Field(default_factory=dict)
    invites: Dict[str, int] = Field(default_factory=dict)  # Code -> Inviter ID

    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Pool name cannot be empty')
        return v

    def to_dict(self):
        return json.loads(self.json())

class Storage(BaseModel):
    pools: Dict[str, Pool] = Field(default_factory=dict)

    def save_to_file(self, filename: str):
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(self.json())

    @classmethod
    def load_from_file(cls, filename: str):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls.parse_obj(data)
        except FileNotFoundError:
            return cls()
        except json.JSONDecodeError:
            return cls() 