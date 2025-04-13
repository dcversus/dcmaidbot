from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Dict, Optional, Any
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
    
    def model_dump(self, **kwargs) -> Dict[str, Any]:
        data = super().model_dump(**kwargs)
        # Convert datetime objects to ISO format
        if 'added_at' in data and data['added_at']:
            data['added_at'] = data['added_at'].isoformat()
        if 'last_selected' in data and data['last_selected']:
            data['last_selected'] = data['last_selected'].isoformat()
        return data

class Pool(BaseModel):
    name: str
    creator_id: int = 0
    participants: List[Participant] = Field(default_factory=list)
    activities: List[Activity] = Field(default_factory=list)
    penalties: Dict[int, float] = Field(default_factory=dict)
    invites: Dict[str, int] = Field(default_factory=dict)  # Code -> Inviter ID

    @field_validator('name')
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Pool name cannot be empty')
        return v

    def to_dict(self):
        return self.model_dump(mode='json')

class Storage(BaseModel):
    pools: Dict[str, Pool] = Field(default_factory=dict)

    def save_to_file(self, filename: str):
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(self.model_dump_json())

    @classmethod
    def load_from_file(cls, filename: str):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls.model_validate(data)
        except FileNotFoundError:
            return cls()
        except json.JSONDecodeError:
            return cls() 