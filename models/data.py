from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional, Any, ClassVar
from datetime import datetime
import json
import os


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
        if "added_at" in data and data["added_at"]:
            data["added_at"] = data["added_at"].isoformat()
        if "last_selected" in data and data["last_selected"]:
            data["last_selected"] = data["last_selected"].isoformat()
        return data


class Pool(BaseModel):
    name: str
    creator_id: int = 0
    participants: List[Participant] = Field(default_factory=list)
    activities: List[Activity] = Field(default_factory=list)
    penalties: Dict[int, float] = Field(default_factory=dict)
    invites: Dict[str, int] = Field(default_factory=dict)  # Code -> Inviter ID

    @field_validator("name")
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Pool name cannot be empty")
        return v

    def to_dict(self):
        return self.model_dump(mode="json")


class Storage(BaseModel):
    pools: Dict[str, Pool] = Field(default_factory=dict)
    _redis_client: ClassVar[Any] = None
    _redis_key: ClassVar[str] = "dcmaidbot:storage"

    def save_to_file(self, filename: str):
        with open(filename, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json())

    @classmethod
    def load_from_file(cls, filename: str):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls.model_validate(data)
        except FileNotFoundError:
            return cls()
        except json.JSONDecodeError:
            return cls()

    @classmethod
    def configure_redis(cls, redis_client, redis_key=None):
        """Configure Redis client for Storage class"""
        cls._redis_client = redis_client
        if redis_key:
            cls._redis_key = redis_key

    @classmethod
    def load_from_redis(cls):
        """Load storage data from Redis"""
        if not cls._redis_client:
            raise ValueError("Redis client not configured")

        raw_data = cls._redis_client.get(cls._redis_key)
        if raw_data:
            data = json.loads(raw_data)
            return cls.model_validate(data)
        return cls()

    def save_to_redis(self):
        """Save storage data to Redis"""
        if not self.__class__._redis_client:
            raise ValueError("Redis client not configured")

        self.__class__._redis_client.set(
            self.__class__._redis_key, self.model_dump_json()
        )

    @classmethod
    def load(
        cls,
        storage_type: str = "auto",
        filename: str = None,
        redis_client=None,
        redis_key=None,
    ):
        """
        Load storage from specified source

        :param storage_type: "auto", "file", or "redis"
        :param filename: Path to file if using file storage
        :param redis_client: Redis client if using redis storage
        :param redis_key: Redis key if using redis storage
        :return: Storage instance
        """
        # Auto-detect storage type if not specified
        if storage_type == "auto":
            redis_url = os.environ.get("REDIS_URL")
            storage_type = "redis" if redis_url and cls._redis_client else "file"

        if storage_type == "redis":
            if redis_client:
                cls.configure_redis(redis_client, redis_key)
            return cls.load_from_redis()
        else:  # "file"
            if not filename:
                raise ValueError("Filename must be provided for file storage")
            return cls.load_from_file(filename)

    def save(self, storage_type: str = "auto", filename: str = None):
        """
        Save storage to specified destination

        :param storage_type: "auto", "file", or "redis"
        :param filename: Path to file if using file storage
        """
        # Auto-detect storage type if not specified
        if storage_type == "auto":
            redis_url = os.environ.get("REDIS_URL")
            storage_type = (
                "redis" if redis_url and self.__class__._redis_client else "file"
            )

        if storage_type == "redis":
            self.save_to_redis()
        else:  # "file"
            if not filename:
                raise ValueError("Filename must be provided for file storage")
            self.save_to_file(filename)
