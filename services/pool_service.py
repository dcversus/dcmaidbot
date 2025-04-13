import os
import json
from typing import List, Optional, Dict
from models.data import Pool, Participant, Storage
from datetime import datetime
import random
import string
import redis

# Use an absolute path that works with Vercel
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORAGE_FILE = os.path.join(BASE_DIR, "storage", "storage.json")

# Get Redis URL from environment (if available)
REDIS_URL = os.environ.get("REDIS_URL")
redis_client = redis.from_url(REDIS_URL) if REDIS_URL else None

# Configure Storage class with Redis client if available
if redis_client:
    Storage.configure_redis(redis_client)

def _ensure_storage_file():
    if REDIS_URL:
        return  # No need for file if using Redis
    os.makedirs(os.path.dirname(STORAGE_FILE), exist_ok=True)
    if not os.path.exists(STORAGE_FILE):
        with open(STORAGE_FILE, 'w') as f:
            json.dump({"pools": {}}, f)

def _get_storage() -> Storage:
    # Use the enhanced Storage.load method that automatically detects storage type
    if REDIS_URL and redis_client:
        return Storage.load(storage_type="redis")
    else:
        _ensure_storage_file()
        return Storage.load(storage_type="file", filename=STORAGE_FILE)

def _save_storage(storage: Storage):
    # Use the enhanced Storage.save method that automatically detects storage type
    if REDIS_URL and redis_client:
        storage.save(storage_type="redis")
    else:
        storage.save(storage_type="file", filename=STORAGE_FILE)

def generate_invitation_code(user_id: int, pool_name: str) -> Optional[str]:
    """
    Generate an invitation code for a pool.
    Only the creator of the pool can generate invitation codes.
    
    :param user_id: The user ID of the participant generating the code
    :param pool_name: The name of the pool
    :return: The invitation code or None if the user is not authorized
    """
    storage = _get_storage()
    
    # Check if the pool exists
    if pool_name not in storage.pools:
        return None
    
    pool = storage.pools[pool_name]
    
    # Check if the user is the creator
    if pool.creator_id != user_id:
        return None
    
    # Simple code generation - combine pool name with random chars
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    code = f"{pool_name}_{random_part}"
    
    # Initialize invites dict if it doesn't exist
    if not hasattr(pool, 'invites') or pool.invites is None:
        pool.invites = {}
    
    # Store the code with the inviter's ID
    pool.invites[code] = user_id
    _save_storage(storage)
    
    return code

def validate_invitation_code(code: str) -> Optional[str]:
    """Validate an invitation code and return the pool name if valid"""
    storage = _get_storage()
    
    for pool_name, pool in storage.pools.items():
        if hasattr(pool, 'invites') and pool.invites and code in pool.invites:
            return pool_name
    
    return None

def create_pool(pool_name: str, participants: List[Participant]) -> Optional[Pool]:
    """Create a new pool with the given name and participants"""
    storage = _get_storage()
    
    # Check if pool with this name already exists
    if pool_name in storage.pools:
        return None
    
    # Get creator id from the first participant
    creator_id = participants[0].user_id if participants else 0
    
    # Create new pool
    new_pool = Pool(
        name=pool_name,
        creator_id=creator_id,
        participants=participants
    )
    
    # Add to storage
    storage.pools[pool_name] = new_pool
    _save_storage(storage)
    
    return new_pool

def add_participant(pool_name: str, participant: Participant) -> bool:
    """Add a participant to an existing pool"""
    storage = _get_storage()
    
    # Check if pool exists
    if pool_name not in storage.pools:
        return False
    
    pool = storage.pools[pool_name]
    
    # Check if participant already exists in the pool
    for p in pool.participants:
        if p.user_id == participant.user_id:
            return False
    
    # Add participant
    pool.participants.append(participant)
    _save_storage(storage)
    
    return True

def remove_participant(pool_name: str, user_id: int) -> bool:
    """Remove a participant from a pool"""
    storage = _get_storage()
    
    # Check if pool exists
    if pool_name not in storage.pools:
        return False
    
    pool = storage.pools[pool_name]
    
    # Find and remove participant
    initial_count = len(pool.participants)
    pool.participants = [p for p in pool.participants if p.user_id != user_id]
    
    # If participant removed, update storage
    if len(pool.participants) < initial_count:
        # Remove penalties for this user
        if user_id in pool.penalties:
            del pool.penalties[user_id]
        
        _save_storage(storage)
        return True
    
    return False

def get_pools_by_participant(user_id: int) -> List[Pool]:
    """Get all pools that include the user as a participant"""
    storage = _get_storage()
    
    user_pools = []
    for pool_name, pool in storage.pools.items():
        for participant in pool.participants:
            if participant.user_id == user_id:
                user_pools.append(pool)
                break
    
    return user_pools

def get_pool(pool_name: str) -> Optional[Pool]:
    """Get a pool by name"""
    storage = _get_storage()
    
    return storage.pools.get(pool_name)

def get_pool_by_name_and_creator(pool_name: str, creator_id: int) -> Optional[Pool]:
    """Get a pool by name and creator ID"""
    storage = _get_storage()
    
    pool = storage.pools.get(pool_name)
    if pool and pool.creator_id == creator_id:
        return pool
    
    return None

def get_pools_by_creator(creator_id: int) -> List[Pool]:
    """Get all pools where the user is the creator"""
    storage = _get_storage()
    
    creator_pools = []
    for pool_name, pool in storage.pools.items():
        if pool.creator_id == creator_id:
            creator_pools.append(pool)
    
    return creator_pools

def is_user_authorized_for_pool(pool_name: str, user_id: int) -> bool:
    """Check if a user is authorized to invite others to a pool (only the creator can invite)"""
    pool = get_pool(pool_name)
    if not pool:
        return False
    
    # Only the creator can invite others
    return pool.creator_id == user_id

def delete_pool(pool_name: str) -> bool:
    """Delete a pool by name"""
    storage = _get_storage()
    
    if pool_name in storage.pools:
        del storage.pools[pool_name]
        _save_storage(storage)
        return True
    
    return False 