import random
from datetime import datetime
from typing import List, Optional, Tuple, Dict
from models.data import Activity, Pool
from services.pool_service import _get_storage, _save_storage, get_pool

# Constants for penalty calculation
PENALTY_BASE = 1.5
PENALTY_DECAY = 0.9  # Penalty reduction per day


def _calculate_activity_weights(pool: Pool, user_id: int) -> List[float]:
    """Calculate weights for activities based on selection history and penalties"""
    weights = []

    # If there are no activities, return empty list
    if not pool.activities:
        return weights

    total_selections = sum(a.selection_count for a in pool.activities)
    now = datetime.now()

    for activity in pool.activities:
        # Base weight is 1.0
        weight = 1.0

        # Adjust weight based on selection count
        if total_selections > 0:
            usage_factor = activity.selection_count / total_selections
            # Reduce weight by up to 50% based on usage
            weight *= 1.0 - usage_factor * 0.5

        # Adjust weight based on recency
        if activity.last_selected:
            days_since_selection = (now - activity.last_selected).days
            # Reduce weight for activities selected in the last 7 days
            if days_since_selection < 7:
                recency_factor = 1.0 - ((7 - days_since_selection) / 7)
                weight *= recency_factor

        weights.append(max(0.1, weight))  # Ensure minimum weight

    return weights


def _apply_user_penalty(weights: List[float], user_penalty: float) -> List[float]:
    """Apply user penalty to the weights"""
    if user_penalty <= 0:
        return weights

    # Scale down weights based on penalty
    penalty_factor = 1.0 / (1.0 + user_penalty)
    return [w * penalty_factor for w in weights]


def _normalize_weights(weights: List[float]) -> List[float]:
    """Normalize weights to sum to 1.0"""
    total = sum(weights)
    if total <= 0:
        # If total is zero or negative, return equal weights
        return [1.0 / len(weights)] * len(weights) if weights else []

    return [w / total for w in weights]


def _update_penalty(pool: Pool, user_id: int, selected_index: int) -> None:
    """Update user penalty after selection"""
    # Get the selected activity
    if selected_index < 0 or selected_index >= len(pool.activities):
        return

    # Get the user who created the activity (added_by)
    activity_creator_id = pool.activities[selected_index].added_by

    # Initialize penalty if not exists
    if activity_creator_id not in pool.penalties:
        pool.penalties[activity_creator_id] = 0.0

    # Increase penalty for the user who created the activity
    pool.penalties[activity_creator_id] += PENALTY_BASE

    # Decay penalties for all users
    for uid in pool.penalties:
        pool.penalties[uid] = max(0, pool.penalties[uid] * PENALTY_DECAY)


def select_activity(
    pools: List[str], user_id: int
) -> Optional[Tuple[str, Activity, int]]:
    """
    Select an activity from the given pools for the user
    Returns a tuple (pool_name, selected_activity, activity_index)
    or None if selection fails
    """
    storage = _get_storage()

    valid_pools = []
    for pool_name in pools:
        pool = storage.pools.get(pool_name)
        if pool:  # Check if pool exists before accessing attributes
            user_is_participant = user_id in [p.user_id for p in pool.participants]
            if pool.activities and user_is_participant:
                valid_pools.append(pool_name)

    if not valid_pools:
        return None

    # Select a random pool from valid pools
    selected_pool_name = random.choice(valid_pools)
    pool = storage.pools[selected_pool_name]

    # Calculate weights for activities
    weights = _calculate_activity_weights(pool, user_id)

    # Apply user penalty
    user_penalty = pool.penalties.get(user_id, 0.0)
    adjusted_weights = _apply_user_penalty(weights, user_penalty)

    # Normalize weights
    normalized_weights = _normalize_weights(adjusted_weights)

    # Select activity based on weights
    if not normalized_weights:
        return None

    selected_index = random.choices(
        range(len(pool.activities)), weights=normalized_weights, k=1
    )[0]

    selected_activity = pool.activities[selected_index]

    # Update selection data
    selected_activity.selection_count += 1
    selected_activity.last_selected = datetime.now()

    # Update penalties
    _update_penalty(pool, user_id, selected_index)

    # Save changes
    _save_storage(storage)

    return (selected_pool_name, selected_activity, selected_index)


def get_penalties(pool_name: str) -> Dict[int, float]:
    """Get current penalties for all users in a pool"""
    pool = get_pool(pool_name)
    if not pool:
        return {}

    return pool.penalties


def reset_penalties(pool_name: str) -> bool:
    """Reset all penalties in a pool"""
    storage = _get_storage()

    if pool_name not in storage.pools:
        return False

    pool = storage.pools[pool_name]
    pool.penalties = {}

    _save_storage(storage)
    return True
