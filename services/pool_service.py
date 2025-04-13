import os
import json
from typing import List, Optional, Dict
from models.data import Pool, Participant, Storage
from datetime import datetime
import random
import string

# Use an absolute path that works with Vercel
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORAGE_FILE = os.path.join(BASE_DIR, "storage", "storage.json")

def _ensure_storage_file():
    os.makedirs(os.path.dirname(STORAGE_FILE), exist_ok=True)
    if not os.path.exists(STORAGE_FILE):
        with open(STORAGE_FILE, 'w') as f:
            json.dump({"pools": {}}, f)

def _get_storage() -> Storage:
    _ensure_storage_file()
    return Storage.load_from_file(STORAGE_FILE)

def _save_storage(storage: Storage):
    storage.save_to_file(STORAGE_FILE)

def generate_invitation_code(pool_name: str, user_id: int) -> Optional[str]:
    """
    Generate an invitation code for a pool.
    Only participants of the pool can generate invitation codes.
    
    :param pool_name: The name of the pool
    :param user_id: The user ID of the participant generating the code
    :return: The invitation code or None if the user is not authorized
    """
    storage = _get_storage()
    
    # Check if the pool exists
    if pool_name not in storage.pools:
        return None
    
    pool = storage.pools[pool_name]
    
    # Check if the user is a participant
    for participant in pool.participants:
        if participant.user_id == user_id:
            break
    else:
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