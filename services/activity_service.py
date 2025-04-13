from typing import List, Optional
from models.data import Activity, Storage
from services.pool_service import _get_storage, _save_storage

def add_activity(pool_name: str, activity: Activity) -> bool:
    """Add a new activity to a pool"""
    storage = _get_storage()
    
    # Check if pool exists
    if pool_name not in storage.pools:
        return False
    
    pool = storage.pools[pool_name]
    
    # Check if user is a participant
    participant_exists = any(p.user_id == activity.added_by for p in pool.participants)
    if not participant_exists:
        return False
    
    # Add activity to pool
    pool.activities.append(activity)
    _save_storage(storage)
    
    return True

def get_activities(pool_name: str) -> List[Activity]:
    """Get all activities from a pool"""
    storage = _get_storage()
    
    # Check if pool exists
    if pool_name not in storage.pools:
        return []
    
    return storage.pools[pool_name].activities

def remove_activity(pool_name: str, activity_index: int) -> bool:
    """Remove an activity from a pool by index"""
    storage = _get_storage()
    
    # Check if pool exists
    if pool_name not in storage.pools:
        return False
    
    pool = storage.pools[pool_name]
    
    # Check if activity index is valid
    if activity_index < 0 or activity_index >= len(pool.activities):
        return False
    
    # Remove activity
    pool.activities.pop(activity_index)
    _save_storage(storage)
    
    return True

def update_activity_selection(pool_name: str, activity_index: int, user_id: int) -> bool:
    """Update an activity's selection count and last_selected time"""
    from datetime import datetime
    
    storage = _get_storage()
    
    # Check if pool exists
    if pool_name not in storage.pools:
        return False
    
    pool = storage.pools[pool_name]
    
    # Check if activity index is valid
    if activity_index < 0 or activity_index >= len(pool.activities):
        return False
    
    # Update activity
    activity = pool.activities[activity_index]
    activity.selection_count += 1
    activity.last_selected = datetime.now()
    
    # Save changes
    _save_storage(storage)
    
    return True 