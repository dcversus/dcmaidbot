"""E2E tests for text RPG system.

Tests the complete RPG functionality from session creation
to multiplayer gameplay and game master actions.
"""


import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from models.game_session import GameSession, PlayerState
from services.rpg_service import RPGService


@pytest.fixture
async def rpg_service(async_session: AsyncSession):
    """Create RPG service for testing."""
    return RPGService(async_session)


@pytest.fixture
async def test_game_session(rpg_service: RPGService):
    """Create a test game session."""
    session = await rpg_service.create_game_session(
        name="Test Adventure",
        description="A test adventure for E2E testing",
        scenario_template="fantasy_adventure",
        difficulty_level="normal",
        max_players=4,
        created_by=1
    )
    return session


@pytest.fixture
async def test_player(rpg_service: RPGService, test_game_session: GameSession):
    """Create a test player in the game session."""
    player = await rpg_service.join_game_session(
        session_id=test_game_session.session_id,
        user_id=12345,
        character_name="TestHero",
        character_class="warrior"
    )
    return player


class TestRPGSystemE2E:
    """End-to-end tests for text RPG system."""

    @pytest.mark.asyncio
    async def test_complete_rpg_session_flow(
        self,
        rpg_service: RPGService,
        async_session: AsyncSession
    ):
        """Test complete RPG session from creation to gameplay."""
        # 1. Create game session
        session = await rpg_service.create_game_session(
            name="Epic Quest",
            description="An epic adventure for heroes",
            scenario_template="fantasy_adventure",
            difficulty_level="normal",
            max_players=3,
            created_by=1
        )

        assert session.name == "Epic Quest"
        assert session.session_id.startswith("rpg_")
        assert session.is_active is True
        assert session.current_step == 1
        assert session.max_players == 3
        assert len(session.world_data) > 0
        assert len(session.hidden_context) > 0

        # 2. Add first player (warrior)
        player1 = await rpg_service.join_game_session(
            session_id=session.session_id,
            user_id=1001,
            character_name="Thorin",
            character_class="warrior"
        )

        assert player1.character_name == "Thorin"
        assert player1.character_class == "warrior"
        assert player1.user_id == 1001
        assert player1.is_active is True
        assert player1.current_location == "town_square"
        assert player1.health_points == 100
        assert len(player1.inventory) > 0
        assert player1.stats["strength"] > 10  # Warrior bonus

        # 3. Add second player (mage)
        player2 = await rpg_service.join_game_session(
            session_id=session.session_id,
            user_id=1002,
            character_name="Merlin",
            character_class="mage"
        )

        assert player2.character_class == "mage"
        assert player2.stats["intelligence"] > 10  # Mage bonus

        # 4. Add third player (rogue)
        player3 = await rpg_service.join_game_session(
            session_id=session.session_id,
            user_id=1003,
            character_name="Shadow",
            character_class="rogue"
        )

        assert player3.character_class == "rogue"
        assert player3.stats["dexterity"] > 10  # Rogue bonus

        # 5. Test session state
        session_state = await rpg_service.get_session_state(session.session_id)
        assert session_state["session"]["id"] == session.id
        assert len(session_state["players"]) == 3
        assert session_state["is_active"] is True
        assert session_state["player_count"] == 3

        # 6. Test player actions - Movement
        result = await rpg_service.process_player_action(
            session_id=session.session_id,
            user_id=1001,
            action="move",
            action_data={"destination": "tavern"}
        )

        assert result["success"] is True
        assert result["action"] == "move"
        assert "tavern" in result["message"]
        assert result["new_location"] == "tavern"

        # Verify player moved
        updated_player1 = await rpg_service.get_player_state(1001, session.session_id)
        assert updated_player1.current_location == "tavern"
        assert "tavern" in updated_player1.discovered_locations

        # 7. Test player actions - Interaction
        result = await rpg_service.process_player_action(
            session_id=session.session_id,
            user_id=1001,
            action="interact",
            action_data={"target": "tavern_keeper"}
        )

        assert result["success"] is True
        assert result["action"] == "interact"
        assert "tavern_keeper" in result["message"]

        # 8. Test player actions - Exploration
        result = await rpg_service.process_player_action(
            session_id=session.session_id,
            user_id=1002,
            action="explore",
            action_data={}
        )

        assert result["success"] is True
        assert result["action"] == "explore"
        assert "explore" in result["message"].lower()

        # 9. Test session is no longer joinable (full)
        assert session.is_joinable() is False

        # 10. Test player choice history
        player1_choices = updated_player1.choices_history
        assert len(player1_choices) > 0
        assert "move_to_tavern" in player1_choices.values()

    @pytest.mark.asyncio
    async def test_rpg_difficulty_levels(
        self,
        rpg_service: RPGService
    ):
        """Test RPG difficulty levels affect player stats."""
        difficulties = ["easy", "normal", "hard", "expert"]
        players = {}

        for difficulty in difficulties:
            session = await rpg_service.create_game_session(
                name=f"Test {difficulty.title()}",
                scenario_template="fantasy_adventure",
                difficulty_level=difficulty,
                created_by=1
            )

            player = await rpg_service.join_game_session(
                session_id=session.session_id,
                user_id=int(f"{2000}{difficulties.index(difficulty)}"),
                character_name=f"Hero{difficulty.title()}",
                character_class="warrior"
            )

            players[difficulty] = player

        # Easy mode should have higher stats
        assert players["easy"].stats["strength"] > players["normal"].stats["strength"]
        assert players["normal"].stats["strength"] > players["hard"].stats["strength"]
        assert players["hard"].stats["strength"] > players["expert"].stats["strength"]

        # All should have minimum viable stats
        for player in players.values():
            assert player.stats["strength"] >= 3
            assert player.health_points == 100

    @pytest.mark.asyncio
    async def test_character_class_variations(
        self,
        rpg_service: RPGService
    ):
        """Test different character classes have different starting equipment."""
        session = await rpg_service.create_game_session(
            name="Class Test",
            scenario_template="fantasy_adventure",
            created_by=1
        )

        # Create different character classes
        warrior = await rpg_service.join_game_session(
            session_id=session.session_id,
            user_id=3001,
            character_name="Warrior",
            character_class="warrior"
        )

        mage = await rpg_service.join_game_session(
            session_id=session.session_id,
            user_id=3002,
            character_name="Mage",
            character_class="mage"
        )

        rogue = await rpg_service.join_game_session(
            session_id=session.session_id,
            user_id=3003,
            character_name="Rogue",
            character_class="rogue"
        )

        # Test class-specific stat bonuses
        assert warrior.stats["strength"] > mage.stats["strength"]
        assert warrior.stats["constitution"] > mage.stats["constitution"]

        assert mage.stats["intelligence"] > warrior.stats["intelligence"]
        assert mage.stats["wisdom"] > warrior.stats["wisdom"]

        assert rogue.stats["dexterity"] > warrior.stats["dexterity"]
        assert rogue.stats["charisma"] > warrior.stats["charisma"]

        # Test class-specific starting inventory
        assert "weapon" in warrior.inventory
        assert "weapon" in mage.inventory
        assert "tool" in rogue.inventory

        # Test basic inventory for all classes
        for player in [warrior, mage, rogue]:
            assert "gold" in player.inventory
            assert "potion" in player.inventory

    @pytest.mark.asyncio
    async def test_multiplayer_interactions(
        self,
        rpg_service: RPGService,
        test_game_session: GameSession
    ):
        """Test multiplayer interactions and shared world state."""
        session = test_game_session

        # Add multiple players
        player1 = await rpg_service.join_game_session(
            session_id=session.session_id,
            user_id=4001,
            character_name="PlayerOne",
            character_class="warrior"
        )

        player2 = await rpg_service.join_game_session(
            session_id=session.session_id,
            user_id=4002,
            character_name="PlayerTwo",
            character_class="mage"
        )

        # Player 1 discovers a new location
        result = await rpg_service.process_player_action(
            session_id=session.session_id,
            user_id=4001,
            action="move",
            action_data={"destination": "tavern"}
        )
        assert result["success"] is True

        # Player 2 should still be in the starting location
        updated_player2 = await rpg_service.get_player_state(4002, session.session_id)
        assert updated_player2.current_location == "town_square"

        # Player 2 moves to the same location
        result = await rpg_service.process_player_action(
            session_id=session.session_id,
            user_id=4002,
            action="move",
            action_data={"destination": "tavern"}
        )
        assert result["success"] is True

        # Both players should now be in the same location
        updated_player1 = await rpg_service.get_player_state(4001, session.session_id)
        updated_player2 = await rpg_service.get_player_state(4002, session.session_id)
        assert updated_player1.current_location == "tavern"
        assert updated_player2.current_location == "tavern"

        # Test session state shows both players
        session_state = await rpg_service.get_session_state(session.session_id)
        assert len(session_state["players"]) == 2
        player_ids = [p["user_id"] for p in session_state["players"]]
        assert 4001 in player_ids
        assert 4002 in player_ids

    @pytest.mark.asyncio
    async def test_invalid_actions_and_error_handling(
        self,
        rpg_service: RPGService,
        test_game_session: GameSession,
        test_player: PlayerState
    ):
        """Test error handling for invalid actions and states."""
        session = test_game_session
        player = test_player

        # Test moving to invalid location
        result = await rpg_service.process_player_action(
            session_id=session.session_id,
            user_id=player.user_id,
            action="move",
            action_data={"destination": "nonexistent_location"}
        )
        assert result["success"] is False
        assert "cannot go" in result["message"].lower()

        # Test interacting with non-existent target
        result = await rpg_service.process_player_action(
            session_id=session.session_id,
            user_id=player.user_id,
            action="interact",
            action_data={"target": "nonexistent_target"}
        )
        assert result["success"] is False
        assert "no" in result["message"].lower() and "nonexistent_target" in result["message"]

        # Test action without required data
        result = await rpg_service.process_player_action(
            session_id=session.session_id,
            user_id=player.user_id,
            action="move",
            action_data={}
        )
        assert result["success"] is False
        assert "specify" in result["message"].lower()

        # Test invalid session ID
        with pytest.raises(ValueError, match="not found"):
            await rpg_service.process_player_action(
                session_id="nonexistent_session",
                user_id=player.user_id,
                action="move",
                action_data={"destination": "tavern"}
            )

        # Test player not in session
        with pytest.raises(ValueError, match="not found in session"):
            await rpg_service.process_player_action(
                session_id=session.session_id,
                user_id=99999,
                action="move",
                action_data={"destination": "tavern"}
            )

    @pytest.mark.asyncio
    async def test_game_master_context_tracking(
        self,
        rpg_service: RPGService,
        test_game_session: GameSession,
        test_player: PlayerState,
        async_session: AsyncSession
    ):
        """Test that game master properly tracks context and player actions."""
        session = test_game_session
        player = test_player

        # Player performs several actions
        actions = [
            {"action": "move", "data": {"destination": "tavern"}},
            {"action": "interact", "data": {"target": "fountain"}},
            {"action": "explore", "data": {}},
            {"action": "talk", "data": {"character": "tavern_keeper", "message": "Hello!"}}
        ]

        for action_data in actions:
            await rpg_service.process_player_action(
                session_id=session.session_id,
                user_id=player.user_id,
                **action_data
            )

        # Refresh session and player from database
        await async_session.refresh(session)
        await async_session.refresh(player)

        # Check that context is being tracked
        assert len(session.hidden_context) > 0
        assert len(player.player_memory) > 0
        assert len(player.choices_history) > 0

        # Check that specific actions are recorded
        assert "move_to_tavern" in player.choices_history.values()
        assert any("action_" in key for key in player.player_memory.keys())

        # Check that discovered locations are tracked
        assert "tavern" in player.discovered_locations

        # Check that met characters are tracked
        assert "tavern_keeper" in player.met_characters

    @pytest.mark.asyncio
    async def test_session_capacity_and_joining_rules(
        self,
        rpg_service: RPGService
    ):
        """Test session capacity limits and joining rules."""
        # Create a session with capacity of 2
        session = await rpg_service.create_game_session(
            name="Capacity Test",
            max_players=2,
            created_by=1
        )

        # Add first player
        player1 = await rpg_service.join_game_session(
            session_id=session.session_id,
            user_id=5001,
            character_name="Player1"
        )
        assert player1.is_active is True

        # Add second player
        player2 = await rpg_service.join_game_session(
            session_id=session.session_id,
            user_id=5002,
            character_name="Player2"
        )
        assert player2.is_active is True

        # Session should now be full
        assert session.is_joinable() is False

        # Try to add third player (should fail)
        with pytest.raises(ValueError, match="not joinable"):
            await rpg_service.join_game_session(
                session_id=session.session_id,
                user_id=5003,
                character_name="Player3"
            )

        # Test reactivating inactive player
        await async_session.refresh(player1)
        player1.is_active = False
        await async_session.commit()

        # Session should now be joinable again
        await async_session.refresh(session)
        assert session.is_joinable() is True

        # Reactivate the player
        reactivated_player = await rpg_service.join_game_session(
            session_id=session.session_id,
            user_id=5001,
            character_name="Player1Reactivated"
        )
        assert reactivated_player.is_active is True
        assert reactivated_player.character_name == "Player1"

    @pytest.mark.asyncio
    async def test_scenario_template_loading(
        self,
        rpg_service: RPGService
    ):
        """Test that scenario templates are properly loaded."""
        session = await rpg_service.create_game_session(
            name="Template Test",
            scenario_template="fantasy_adventure",
            created_by=1
        )

        # Check that world data is loaded
        assert "locations" in session.world_data
        assert "characters" in session.world_data
        assert "starting_location" in session.world_data

        # Check that specific locations exist
        locations = session.world_data["locations"]
        assert "town_square" in locations
        assert "tavern" in locations

        # Check location structure
        town_square = locations["town_square"]
        assert "description" in town_square
        assert "exits" in town_square
        assert isinstance(town_square["exits"], list)

        # Check hidden context is loaded
        assert "main_quest" in session.hidden_context
        assert "secrets" in session.hidden_context
        assert isinstance(session.hidden_context["secrets"], list)

    @pytest.mark.asyncio
    async def test_player_inventory_management(
        self,
        rpg_service: RPGService,
        test_player: PlayerState
    ):
        """Test player inventory management."""
        player = test_player

        # Test initial inventory
        assert "gold" in player.inventory
        assert "potion" in player.inventory
        assert len(player.inventory["gold"]) > 0
        assert len(player.inventory["potion"]) > 0

        # Test adding items
        new_item = {
            "id": "test_sword",
            "name": "Test Sword",
            "damage": 10,
            "description": "A sword for testing"
        }
        success = player.add_to_inventory(new_item)
        assert success is True
        assert "test_sword" in player.inventory
        assert len(player.inventory["test_sword"]) == 1

        # Test removing items
        success = player.remove_from_inventory("test_sword", 1)
        assert success is True
        assert "test_sword" not in player.inventory

        # Test removing non-existent item
        success = player.remove_from_inventory("nonexistent", 1)
        assert success is False

        # Test removing more items than available
        gold_count = len(player.inventory["gold"])
        success = player.remove_from_inventory("gold", gold_count + 1)
        assert success is False

    @pytest.mark.asyncio
    async def test_player_state_persistence(
        self,
        rpg_service: RPGService,
        test_game_session: GameSession,
        test_player: PlayerState,
        async_session: AsyncSession
    ):
        """Test that player state is properly persisted and can be retrieved."""
        session = test_game_session
        player = test_player

        # Player performs some actions
        await rpg_service.process_player_action(
            session_id=session.session_id,
            user_id=player.user_id,
            action="move",
            action_data={"destination": "tavern"}
        )

        await rpg_service.process_player_action(
            session_id=session.session_id,
            user_id=player.user_id,
            action="explore",
            action_data={}
        )

        # Get fresh player state from database
        fresh_player = await rpg_service.get_player_state(
            player.user_id,
            session.session_id
        )

        # Verify state persistence
        assert fresh_player.user_id == player.user_id
        assert fresh_player.character_name == player.character_name
        assert fresh_player.current_location == "tavern"
        assert fresh_player.actions_taken == 2
        assert len(fresh_player.discovered_locations) > 0
        assert len(fresh_player.player_memory) > 0

        # Test player-specific session state
        session_state = await rpg_service.get_session_state(
            session.session_id,
            user_id=player.user_id
        )
        assert "current_player" in session_state
        assert session_state["current_player"]["user_id"] == player.user_id
