import pytest
import os
import json
import shutil
from datetime import datetime, timedelta
from models.data import Pool, Participant, Activity, Storage
from services import pool_service, activity_service, selection_service

# Test storage file for tests
TEST_STORAGE_FILE = "storage/test_storage.json"

# Set the storage file for all service modules
pool_service.STORAGE_FILE = TEST_STORAGE_FILE
activity_service.STORAGE_FILE = TEST_STORAGE_FILE

@pytest.fixture
def setup_test_storage():
    """Setup test storage and clean it after tests"""
    # Make sure the directory exists
    os.makedirs(os.path.dirname(TEST_STORAGE_FILE), exist_ok=True)
    
    # Create empty storage file
    with open(TEST_STORAGE_FILE, 'w') as f:
        json.dump({"pools": {}}, f)
    
    yield
    
    # Clean up after tests
    if os.path.exists(TEST_STORAGE_FILE):
        os.remove(TEST_STORAGE_FILE)

def test_create_pool(setup_test_storage):
    # Create test participants
    participants = [
        Participant(user_id=1, username="user1"),
        Participant(user_id=2, username="user2")
    ]
    
    # Create a pool
    pool = pool_service.create_pool("test_pool", participants)
    
    # Verify pool was created
    assert pool is not None
    assert pool.name == "test_pool"
    assert len(pool.participants) == 2
    assert pool.participants[0].user_id == 1
    assert pool.participants[1].user_id == 2
    
    # Try to create pool with same name
    duplicate_pool = pool_service.create_pool("test_pool", participants)
    assert duplicate_pool is None

def test_add_participant(setup_test_storage):
    # Create a pool with one participant
    pool_service.create_pool("test_pool", [
        Participant(user_id=1, username="user1")
    ])
    
    # Add another participant
    new_participant = Participant(user_id=2, username="user2")
    result = pool_service.add_participant("test_pool", new_participant)
    
    # Verify participant was added
    assert result is True
    
    # Get the pool and check participants
    pool = pool_service.get_pool("test_pool")
    assert len(pool.participants) == 2
    assert pool.participants[1].user_id == 2
    
    # Try to add the same participant again
    result = pool_service.add_participant("test_pool", new_participant)
    assert result is False
    
    # Try to add participant to non-existent pool
    result = pool_service.add_participant("non_existent_pool", new_participant)
    assert result is False

def test_remove_participant(setup_test_storage):
    # Create a pool with two participants
    pool_service.create_pool("test_pool", [
        Participant(user_id=1, username="user1"),
        Participant(user_id=2, username="user2")
    ])
    
    # Remove one participant
    result = pool_service.remove_participant("test_pool", 1)
    
    # Verify participant was removed
    assert result is True
    
    # Get the pool and check participants
    pool = pool_service.get_pool("test_pool")
    assert len(pool.participants) == 1
    assert pool.participants[0].user_id == 2
    
    # Try to remove non-existent participant
    result = pool_service.remove_participant("test_pool", 999)
    assert result is False
    
    # Try to remove from non-existent pool
    result = pool_service.remove_participant("non_existent_pool", 2)
    assert result is False

def test_get_pools_by_participant(setup_test_storage):
    # Create multiple pools with different participants
    pool_service.create_pool("pool1", [
        Participant(user_id=1, username="user1"),
        Participant(user_id=2, username="user2")
    ])
    
    pool_service.create_pool("pool2", [
        Participant(user_id=1, username="user1"),
        Participant(user_id=3, username="user3")
    ])
    
    pool_service.create_pool("pool3", [
        Participant(user_id=3, username="user3")
    ])
    
    # Get pools for user 1
    user1_pools = pool_service.get_pools_by_participant(1)
    
    # Verify correct pools were returned
    assert len(user1_pools) == 2
    pool_names = [pool.name for pool in user1_pools]
    assert "pool1" in pool_names
    assert "pool2" in pool_names
    assert "pool3" not in pool_names
    
    # Get pools for user 3
    user3_pools = pool_service.get_pools_by_participant(3)
    assert len(user3_pools) == 2
    pool_names = [pool.name for pool in user3_pools]
    assert "pool1" not in pool_names
    assert "pool2" in pool_names
    assert "pool3" in pool_names
    
    # Get pools for non-existent user
    user999_pools = pool_service.get_pools_by_participant(999)
    assert len(user999_pools) == 0

def test_add_activity(setup_test_storage):
    # Create a pool
    pool_service.create_pool("test_pool", [
        Participant(user_id=1, username="user1")
    ])
    
    # Create an activity
    activity = Activity(
        content="Test activity",
        added_by=1,
        added_at=datetime.now()
    )
    
    # Add activity to pool
    result = activity_service.add_activity("test_pool", activity)
    
    # Verify activity was added
    assert result is True
    
    # Get pool and check activities
    pool = pool_service.get_pool("test_pool")
    assert len(pool.activities) == 1
    assert pool.activities[0].content == "Test activity"
    
    # Try to add activity to non-existent pool
    result = activity_service.add_activity("non_existent_pool", activity)
    assert result is False
    
    # Try to add activity by non-participant
    activity_by_stranger = Activity(
        content="Activity by stranger",
        added_by=999,
        added_at=datetime.now()
    )
    result = activity_service.add_activity("test_pool", activity_by_stranger)
    assert result is False

def test_get_activities(setup_test_storage):
    # Create a pool
    pool_service.create_pool("test_pool", [
        Participant(user_id=1, username="user1")
    ])
    
    # Add activities
    activity1 = Activity(content="Activity 1", added_by=1, added_at=datetime.now())
    activity2 = Activity(content="Activity 2", added_by=1, added_at=datetime.now())
    
    activity_service.add_activity("test_pool", activity1)
    activity_service.add_activity("test_pool", activity2)
    
    # Get activities
    activities = activity_service.get_activities("test_pool")
    
    # Verify activities
    assert len(activities) == 2
    assert activities[0].content == "Activity 1"
    assert activities[1].content == "Activity 2"
    
    # Get activities from non-existent pool
    activities = activity_service.get_activities("non_existent_pool")
    assert len(activities) == 0

def test_select_activity(setup_test_storage):
    # Create a pool with activities
    pool_service.create_pool("test_pool", [
        Participant(user_id=1, username="user1")
    ])
    
    # Add activities
    for i in range(5):
        activity = Activity(
            content=f"Activity {i+1}",
            added_by=1,
            added_at=datetime.now() - timedelta(days=i)
        )
        activity_service.add_activity("test_pool", activity)
    
    # Select an activity
    selection_result = selection_service.select_activity(["test_pool"], 1)
    
    # Verify selection
    assert selection_result is not None
    pool_name, activity, _ = selection_result
    assert pool_name == "test_pool"
    assert activity.content.startswith("Activity ")
    assert activity.selection_count == 1
    assert activity.last_selected is not None
    
    # Check that penalty was applied
    pool = pool_service.get_pool("test_pool")
    assert 1 in pool.penalties
    assert pool.penalties[1] > 0
    
    # Select from multiple pools
    pool_service.create_pool("test_pool2", [
        Participant(user_id=1, username="user1")
    ])
    
    activity = Activity(content="Activity in pool 2", added_by=1, added_at=datetime.now())
    activity_service.add_activity("test_pool2", activity)
    
    # Reset penalties to ensure fair testing
    selection_service.reset_penalties("test_pool")
    selection_service.reset_penalties("test_pool2")
    
    # Select from both pools
    # Run this multiple times to ensure both pools have a chance to be selected
    selected_pools = set()
    for _ in range(10):
        selection_result = selection_service.select_activity(["test_pool", "test_pool2"], 1)
        if selection_result:
            pool_name, _, _ = selection_result
            selected_pools.add(pool_name)
    
    assert len(selected_pools) > 0  # At least one pool should be selected
    
    # Try to select from non-existent pool
    selection_result = selection_service.select_activity(["non_existent_pool"], 1)
    assert selection_result is None
    
    # Try to select as non-participant
    selection_result = selection_service.select_activity(["test_pool"], 999)
    assert selection_result is None

def test_penalty_logic(setup_test_storage):
    # Create a pool with a single activity
    pool_service.create_pool("test_pool", [
        Participant(user_id=1, username="user1"),
        Participant(user_id=2, username="user2")
    ])
    
    activity = Activity(content="Test activity", added_by=1, added_at=datetime.now())
    activity_service.add_activity("test_pool", activity)
    
    # First selection by user 1
    selection_service.select_activity(["test_pool"], 1)
    
    # Check penalty
    pool = pool_service.get_pool("test_pool")
    penalty_user1 = pool.penalties.get(1, 0)
    assert penalty_user1 > 0
    
    # Selection by user 2
    selection_service.select_activity(["test_pool"], 2)
    
    # Check penalties
    pool = pool_service.get_pool("test_pool")
    new_penalty_user1 = pool.penalties.get(1, 0)
    penalty_user2 = pool.penalties.get(2, 0)
    
    # User 1's penalty should have decayed
    assert new_penalty_user1 < penalty_user1
    # User 2 should have a penalty now
    assert penalty_user2 > 0
    
    # Reset penalties
    result = selection_service.reset_penalties("test_pool")
    assert result is True
    
    # Check that penalties were reset
    pool = pool_service.get_pool("test_pool")
    assert len(pool.penalties) == 0 