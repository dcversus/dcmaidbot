import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from aiogram.types import Message, User, Chat
from aiogram.fsm.context import FSMContext
from datetime import datetime

from handlers import categories, activities, selection, info
from models.data import Pool, Participant, Activity
from services import pool_service

# Mock user and chat for testing
@pytest.fixture
def mock_user():
    return User(id=1, is_bot=False, first_name="Test", username="test_user")

@pytest.fixture
def mock_chat():
    return Chat(id=1, type="private")

@pytest.fixture
def mock_message(mock_user, mock_chat):
    message = AsyncMock(spec=Message)
    message.from_user = mock_user
    message.chat = mock_chat
    message.text = ""
    # Ensure answer method is properly mocked for async usage
    message.answer = AsyncMock() 
    return message

@pytest.fixture
def mock_state():
    state = AsyncMock(spec=FSMContext)
    state.get_data.return_value = {}
    return state

# Tests for categories handlers
@pytest.mark.asyncio
@patch("services.pool_service.create_pool")
async def test_handle_create_pool_command(mock_create_pool, mock_message, mock_state):
    # First message to start pool creation
    await categories.cmd_create_pool(mock_message, mock_state)
    
    # Check that state was set
    mock_state.set_state.assert_called_once_with(categories.PoolCreation.waiting_for_name)
    
    # Simulate user entering pool name
    mock_message.text = "test_pool"
    
    # Mock get_pool to return None (pool doesn't exist)
    with patch("services.pool_service.get_pool", return_value=None):
        # Create a new pool object to return
        test_pool = Pool(name="test_pool", participants=[
            Participant(user_id=1, username="test_user")
        ])
        
        # Set mock to return the test pool
        mock_create_pool.return_value = test_pool
        
        # Process pool name
        await categories.process_pool_name(mock_message, mock_state)
        
        # Check that create_pool was called with correct params
        mock_create_pool.assert_called_once()
        args, kwargs = mock_create_pool.call_args
        assert args[0] == "test_pool"
        assert len(args[1]) == 1
        assert args[1][0].user_id == 1
        
        # Check that state was cleared
        mock_state.clear.assert_called_once()

@pytest.mark.asyncio
@patch("services.pool_service.add_participant")
@patch("services.pool_service.get_pool")
@patch("services.pool_service.validate_invitation_code")
async def test_handle_join_pool_command(mock_validate_code, mock_get_pool, mock_add_participant, mock_message, mock_state):
    # Set up a valid invitation code
    mock_message.text = "/join_pool test_code"
    mock_validate_code.return_value = "test_pool"
    
    # Create a test pool with no participants
    test_pool = Pool(name="test_pool", participants=[])
    mock_get_pool.return_value = test_pool
    
    # Mock add_participant to succeed
    mock_add_participant.return_value = True
    
    # First message to start joining with code
    await categories.cmd_join_pool(mock_message, mock_state)
    
    # Check that process_join_with_code was called via add_participant
    mock_add_participant.assert_called_once()
    
    # Check that state was cleared
    mock_state.clear.assert_called_once()

@pytest.mark.asyncio
@patch("services.pool_service.get_pools_by_participant")
@patch("services.pool_service.remove_participant")
async def test_handle_exit_pool_command(mock_remove_participant, mock_get_pools, mock_message, mock_state):
    # Create two test pools for the user
    test_pools = [
        Pool(name="pool1", participants=[Participant(user_id=1, username="test_user")]),
        Pool(name="pool2", participants=[Participant(user_id=1, username="test_user")])
    ]
    
    # Mock get_pools_by_participant to return test pools
    mock_get_pools.return_value = test_pools
    
    # First message to start exiting
    await categories.cmd_exit_pool(mock_message, mock_state)
    
    # Check that state was set and user_pools was stored
    mock_state.set_state.assert_called_once_with(categories.PoolParticipant.waiting_for_pool_name)
    mock_state.update_data.assert_called_once()
    
    # Reset mocks
    mock_state.reset_mock()
    
    # Set up state data for the next handler
    mock_state.get_data.return_value = {"user_pools": test_pools}
    
    # Simulate user selecting the first pool (index 1)
    mock_message.text = "1"
    
    # Mock remove_participant to succeed
    mock_remove_participant.return_value = True
    
    # Process exit pool selection
    await categories.process_exit_pool(mock_message, mock_state)
    
    # Check that remove_participant was called correctly
    mock_remove_participant.assert_called_once_with("pool1", 1)
    
    # Check that state was cleared
    mock_state.clear.assert_called_once()

# Tests for activities handlers
@pytest.mark.asyncio
@patch("services.pool_service.get_pools_by_participant")
async def test_handle_add_activity_command(mock_get_pools, mock_message, mock_state):
    # Create test pool for the user
    test_pool = Pool(name="test_pool", participants=[Participant(user_id=1, username="test_user")])
    
    # Mock get_pools_by_participant to return test pool
    mock_get_pools.return_value = [test_pool]
    
    # First message to start adding activity
    await activities.cmd_add_activity(mock_message, mock_state)
    
    # Check that state was set and user_pools was stored
    mock_state.set_state.assert_called_once_with(activities.ActivityManagement.selecting_pool)
    mock_state.update_data.assert_called_once()
    
    # Reset mocks
    mock_state.reset_mock()
    
    # Set up state data for the next handler
    mock_state.get_data.return_value = {"user_pools": [test_pool]}
    
    # Simulate user selecting the first pool (index 1)
    mock_message.text = "1"
    
    # Process pool selection
    await activities.process_pool_selection(mock_message, mock_state)
    
    # Check that state was updated and set to entering_content
    mock_state.update_data.assert_called_once_with(selected_pool="test_pool")
    mock_state.set_state.assert_called_once_with(activities.ActivityManagement.entering_activity_content)
    
    # Reset mocks
    mock_state.reset_mock()
    
    # Set up state data for the next handler
    mock_state.get_data.return_value = {"selected_pool": "test_pool"}
    
    # Simulate user entering activity content
    mock_message.text = "Test activity content"
    
    # Mock add_activity to succeed
    with patch("services.activity_service.add_activity", return_value=True):
        # Process activity content
        await activities.process_activity_content(mock_message, mock_state)
        
        # Check that state was cleared
        mock_state.clear.assert_called_once()

# Tests for selection handlers
@pytest.mark.asyncio
@patch("services.pool_service.get_pools_by_participant")
async def test_handle_selection_command(mock_get_pools, mock_message, mock_state):
    # Create test pool with activities
    test_pool = Pool(
        name="test_pool",
        participants=[Participant(user_id=1, username="test_user")],
        activities=[
            Activity(content="Activity 1", added_by=1, added_at=datetime.now()),
            Activity(content="Activity 2", added_by=1, added_at=datetime.now())
        ]
    )
    
    # Mock get_pools_by_participant to return test pool
    mock_get_pools.return_value = [test_pool]
    
    # First message to start selection
    await selection.cmd_select(mock_message, mock_state)
    
    # Check that state was set and valid_pools was stored
    mock_state.set_state.assert_called_once_with(selection.ActivitySelection.selecting_pools)
    mock_state.update_data.assert_called_once()
    
    # Skip the rest of the test for now as it needs more complex mocking
    # of the process_direct_selection and process_pool_selection functions
    pass 