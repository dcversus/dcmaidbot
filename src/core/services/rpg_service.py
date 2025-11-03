"""Text RPG game engine service.

This service manages multiplayer text RPG sessions where dcmaidbot
acts as game master with hidden context buffer as memory.
"""

import logging
import secrets
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.game_session import GameSession, PlayerState
from core.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class RPGService:
    """Service for managing text RPG game sessions."""

    def __init__(self, session: AsyncSession):
        """Initialize RPG service with database session."""
        self.session = session
        self.llm_service = LLMService()

    async def create_game_session(
        self,
        name: str,
        description: Optional[str] = None,
        scenario_template: str = "fantasy_adventure",
        difficulty_level: str = "normal",
        max_players: int = 4,
        created_by: int = 1,
    ) -> GameSession:
        """Create a new RPG game session."""
        # Generate unique session ID
        session_id = f"rpg_{secrets.token_urlsafe(8)}"

        # Get scenario template
        scenario_data = await self._get_scenario_template(scenario_template)

        game_session = GameSession(
            session_id=session_id,
            name=name,
            description=description,
            game_master_id=1,  # dcmaidbot's user ID
            scenario_template=scenario_template,
            difficulty_level=difficulty_level,
            max_players=max_players,
            hidden_context=scenario_data.get("hidden_context", {}),
            game_state=scenario_data.get("initial_state", {}),
            world_data=scenario_data.get("world_data", {}),
            created_by=created_by,
        )

        self.session.add(game_session)
        await self.session.commit()
        await self.session.refresh(game_session)

        logger.info(f"Created RPG session: {session_id} ({name})")
        return game_session

    async def join_game_session(
        self,
        session_id: str,
        user_id: int,
        character_name: str,
        character_class: Optional[str] = None,
    ) -> PlayerState:
        """Add a player to an existing game session."""
        # Check if session exists and is joinable
        session = await self.get_game_session(session_id)
        if not session:
            raise ValueError(f"Game session {session_id} not found")

        if not session.is_joinable():
            raise ValueError(f"Game session {session_id} is not joinable")

        # Check if player already exists
        existing_player = await self.get_player_state(user_id, session_id)
        if existing_player:
            if not existing_player.is_active:
                # Reactivate existing player
                existing_player.is_active = True
                existing_player.joined_at = datetime.utcnow()
                await self.session.commit()
                return existing_player
            else:
                raise ValueError(f"Player {user_id} already in session {session_id}")

        # Create new player state
        player_state = PlayerState(
            user_id=user_id,
            session_id=session_id,
            character_name=character_name,
            character_class=character_class,
            current_location=session.world_data.get("starting_location", "town_square"),
            inventory=self._get_starting_inventory(character_class),
            stats=self._get_starting_stats(character_class, session.difficulty_level),
            joined_at=datetime.utcnow(),
        )

        self.session.add(player_state)
        await self.session.commit()
        await self.session.refresh(player_state)

        # Update session activity
        session.last_activity_at = datetime.utcnow()
        await self.session.commit()

        logger.info(f"Player {user_id} ({character_name}) joined session {session_id}")
        return player_state

    async def process_player_action(
        self, session_id: str, user_id: int, action: str, action_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Process a player's action in the game."""
        session = await self.get_game_session(session_id)
        if not session:
            raise ValueError(f"Game session {session_id} not found")

        player = await self.get_player_state(user_id, session_id)
        if not player or not player.is_active:
            raise ValueError(f"Player {user_id} not found in session {session_id}")

        # Process action based on type
        if action == "move":
            result = await self._process_move_action(session, player, action_data)
        elif action == "interact":
            result = await self._process_interact_action(session, player, action_data)
        elif action == "use_item":
            result = await self._process_use_item_action(session, player, action_data)
        elif action == "talk":
            result = await self._process_talk_action(session, player, action_data)
        elif action == "attack":
            result = await self._process_attack_action(session, player, action_data)
        elif action == "explore":
            result = await self._process_explore_action(session, player, action_data)
        else:
            result = await self._process_custom_action(
                session, player, action, action_data
            )

        # Update player and session state
        player.last_action_at = datetime.utcnow()
        player.actions_taken += 1
        session.last_activity_at = datetime.utcnow()

        # Add to LLM context for game master decisions
        await self._update_game_master_context(session, player, action, result)

        await self.session.commit()

        return result

    async def get_game_session(self, session_id: str) -> Optional[GameSession]:
        """Get a game session by ID."""
        result = await self.session.execute(
            select(GameSession).where(GameSession.session_id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_player_state(
        self, user_id: int, session_id: str
    ) -> Optional[PlayerState]:
        """Get a player's state in a specific session."""
        result = await self.session.execute(
            select(PlayerState).where(
                and_(
                    PlayerState.user_id == user_id, PlayerState.session_id == session_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_session_state(
        self, session_id: str, user_id: Optional[int] = None
    ) -> dict[str, Any]:
        """Get the current state of a game session."""
        session = await self.get_game_session(session_id)
        if not session:
            raise ValueError(f"Game session {session_id} not found")

        # Get all active players
        result = await self.session.execute(
            select(PlayerState).where(
                and_(PlayerState.session_id == session_id, PlayerState.is_active)
            )
        )
        players = result.scalars().all()

        # Build session state
        state = {
            "session": session.to_dict(),
            "players": [player.to_dict() for player in players],
            "current_step": session.current_step,
            "is_active": session.is_active,
            "player_count": len(players),
        }

        # Add player-specific information if requested
        if user_id:
            player = next((p for p in players if p.user_id == user_id), None)
            if player:
                state["current_player"] = player.to_dict()

        return state

    async def _process_move_action(
        self, session: GameSession, player: PlayerState, action_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Process a movement action."""
        destination = action_data.get("destination")
        if not destination:
            return {
                "success": False,
                "message": "You need to specify where you want to go.",
            }

        # Check if destination is accessible
        current_location = session.world_data.get("locations", {}).get(
            player.current_location, {}
        )
        available_exits = current_location.get("exits", [])

        if destination not in available_exits:
            return {
                "success": False,
                "message": f"You cannot go to {destination} from here.",
            }

        # Move player
        old_location = player.current_location
        player.current_location = destination

        # Add to discovered locations
        if destination not in player.discovered_locations:
            player.discovered_locations.append(destination)

        # Record the choice
        player.record_choice(
            session.current_step,
            f"move_to_{destination}",
            {"old_location": old_location, "new_location": destination},
        )

        # Get new location description
        new_location = session.world_data.get("locations", {}).get(destination, {})
        description = new_location.get("description", "You arrive at a new location.")

        return {
            "success": True,
            "action": "move",
            "message": f"You move from {old_location} to {destination}. {description}",
            "new_location": destination,
            "location_description": description,
            "available_exits": new_location.get("exits", []),
            "available_actions": await self._get_available_actions(session, player),
        }

    async def _process_interact_action(
        self, session: GameSession, player: PlayerState, action_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Process an interaction action."""
        target = action_data.get("target")
        if not target:
            return {
                "success": False,
                "message": "You need to specify what you want to interact with.",
            }

        # Get location data
        location = session.world_data.get("locations", {}).get(
            player.current_location, {}
        )
        interactables = location.get("interactables", {})

        if target not in interactables:
            return {
                "success": False,
                "message": f"There is no {target} here to interact with.",
            }

        target_data = interactables[target]
        interaction_result = target_data.get(
            "interaction", "You interact with the {target}."
        )

        # Process interaction effects
        if "item_reward" in target_data:
            item = target_data["item_reward"]
            player.add_to_inventory(item)
            interaction_result += f" You found: {item.get('name', 'something')}!"

        if "unlock_location" in target_data:
            new_location = target_data["unlock_location"]
            if new_location not in player.discovered_locations:
                player.discovered_locations.append(new_location)
                interaction_result += f" You discovered: {new_location}!"

        return {
            "success": True,
            "action": "interact",
            "message": interaction_result,
            "target": target,
            "effects": target_data.get("effects", {}),
        }

    async def _process_talk_action(
        self, session: GameSession, player: PlayerState, action_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Process a conversation action."""
        character = action_data.get("character")
        message = action_data.get("message", "")

        if not character:
            return {
                "success": False,
                "message": "You need to specify who you want to talk to.",
            }

        # Use LLM to generate character response
        response = await self._generate_character_response(
            session, player, character, message
        )

        # Add character to met characters list
        if character not in player.met_characters:
            player.met_characters.append(character)

        return {
            "success": True,
            "action": "talk",
            "message": f"You talk to {character}: '{message}'",
            "character_response": response,
            "character": character,
        }

    async def _process_explore_action(
        self, session: GameSession, player: PlayerState, action_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Process an exploration action."""
        location = session.world_data.get("locations", {}).get(
            player.current_location, {}
        )

        # Check for hidden items or secrets
        secrets_found = []
        if "hidden_items" in location:
            for item in location["hidden_items"]:
                if item.get("id") not in [
                    i.get("id") for items in player.inventory.values() for i in items
                ]:
                    player.add_to_inventory(item)
                    secrets_found.append(item.get("name", "something"))

        message = "You explore the area carefully."
        if secrets_found:
            message += f" You found: {', '.join(secrets_found)}!"
        else:
            message += " You don't find anything new."

        return {
            "success": True,
            "action": "explore",
            "message": message,
            "items_found": secrets_found,
        }

    async def _process_custom_action(
        self,
        session: GameSession,
        player: PlayerState,
        action: str,
        action_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Process a custom action using LLM."""
        # Use LLM to determine the outcome
        prompt = f"""
        Game Context: Fantasy RPG session '{session.name}'
        Player: {player.character_name} at location {player.current_location}
        Player stats: {player.stats}
        Player inventory: {player.inventory}

        Action attempted: {action}
        Action details: {action_data}

        Determine if this action succeeds and what the outcome is.
        Consider the game's difficulty level: {session.difficulty_level}
        """

        try:
            llm_response = await self.llm_service.generate_response(prompt)
            return {
                "success": True,
                "action": action,
                "message": llm_response,
                "custom": True,
            }
        except Exception as e:
            logger.error(f"Error processing custom action with LLM: {e}")
            return {
                "success": False,
                "action": action,
                "message": f"You attempt to {action}, but something prevents it from working.",
            }

    async def _get_available_actions(
        self, session: GameSession, player: PlayerState
    ) -> list[str]:
        """Get available actions for a player in their current location."""
        location = session.world_data.get("locations", {}).get(
            player.current_location, {}
        )
        actions = ["move", "explore", "talk"]

        # Add interact action if there are interactables
        if location.get("interactables"):
            actions.append("interact")

        # Add combat action if there are enemies
        if location.get("enemies"):
            actions.append("attack")

        # Add item-based actions
        if player.inventory:
            actions.append("use_item")

        return actions

    async def _generate_character_response(
        self, session: GameSession, player: PlayerState, character: str, message: str
    ) -> str:
        """Generate a character response using LLM."""
        character_data = session.world_data.get("characters", {}).get(character, {})
        character_personality = character_data.get("personality", "friendly")

        prompt = f"""
        You are {character} in a fantasy RPG game.
        Personality: {character_personality}
        Player: {player.character_name} is talking to you.
        Player message: "{message}"

        Respond in character as {character}. Keep responses concise and in character.
        Consider what has happened in the game: {player.player_memory}
        """

        try:
            return await self.llm_service.generate_response(prompt)
        except Exception as e:
            logger.error(f"Error generating character response: {e}")
            return f"{character} nods thoughtfully but doesn't respond clearly."

    def _get_starting_inventory(self, character_class: Optional[str]) -> dict:
        """Get starting inventory based on character class."""
        base_inventory = {
            "gold": [{"id": "gold_coin", "name": "Gold Coin", "quantity": 10}],
            "potion": [{"id": "health_potion", "name": "Health Potion", "quantity": 1}],
        }

        if character_class == "warrior":
            base_inventory["weapon"] = [
                {"id": "rusty_sword", "name": "Rusty Sword", "damage": 5}
            ]
        elif character_class == "mage":
            base_inventory["weapon"] = [
                {"id": "basic_wand", "name": "Basic Wand", "magic_power": 3}
            ]
        elif character_class == "rogue":
            base_inventory["tool"] = [
                {"id": "lockpick", "name": "Lockpick", "quantity": 3}
            ]

        return base_inventory

    def _get_starting_stats(
        self, character_class: Optional[str], difficulty_level: str
    ) -> dict:
        """Get starting stats based on character class and difficulty."""
        base_stats = {
            "strength": 10,
            "intelligence": 10,
            "dexterity": 10,
            "constitution": 10,
            "wisdom": 10,
            "charisma": 10,
        }

        # Adjust based on character class
        if character_class == "warrior":
            base_stats["strength"] += 2
            base_stats["constitution"] += 2
        elif character_class == "mage":
            base_stats["intelligence"] += 2
            base_stats["wisdom"] += 2
        elif character_class == "rogue":
            base_stats["dexterity"] += 2
            base_stats["charisma"] += 1

        # Adjust based on difficulty
        if difficulty_level == "easy":
            for stat in base_stats:
                base_stats[stat] += 2
        elif difficulty_level == "hard":
            for stat in base_stats:
                base_stats[stat] = max(5, base_stats[stat] - 1)
        elif difficulty_level == "expert":
            for stat in base_stats:
                base_stats[stat] = max(3, base_stats[stat] - 2)

        return base_stats

    async def _get_scenario_template(self, template_name: str) -> dict:
        """Get scenario template data."""
        # Basic fantasy adventure template
        templates = {
            "fantasy_adventure": {
                "hidden_context": {
                    "main_quest": "Find the lost artifact",
                    "secrets": ["There's a hidden passage in the tavern"],
                    "npc_motivations": {
                        "tavern_keeper": "Knows more than they let on",
                        "blacksmith": "Looking for a rare ore",
                    },
                },
                "initial_state": {
                    "plot_stage": "beginning",
                    "time_of_day": "morning",
                    "weather": "clear",
                },
                "world_data": {
                    "starting_location": "town_square",
                    "locations": {
                        "town_square": {
                            "description": "A bustling town square with a fountain in the center.",
                            "exits": ["tavern", "blacksmith", "market", "gates"],
                            "interactables": {
                                "fountain": {
                                    "interaction": "You toss a coin in the fountain and make a wish.",
                                    "effects": {"luck": 1},
                                }
                            },
                        },
                        "tavern": {
                            "description": "A cozy tavern with the smell of ale and roasted meat.",
                            "exits": ["town_square"],
                            "interactables": {
                                "tavern_keeper": {
                                    "interaction": "The tavern keeper greets you warmly.",
                                    "hidden_items": [
                                        {
                                            "id": "rumor_note",
                                            "name": "Mysterious Note",
                                            "description": "A note with strange writing.",
                                        }
                                    ],
                                }
                            },
                        },
                    },
                    "characters": {
                        "tavern_keeper": {"personality": "friendly but mysterious"},
                        "blacksmith": {"personality": "gruff but honorable"},
                    },
                },
            }
        }

        return templates.get(template_name, templates["fantasy_adventure"])

    async def _update_game_master_context(
        self,
        session: GameSession,
        player: PlayerState,
        action: str,
        result: dict[str, Any],
    ) -> None:
        """Update the game master's hidden context with new information."""
        # Add to session's hidden context for future LLM decisions
        context_key = f"player_{player.user_id}_action_{session.current_step}"
        session.hidden_context[context_key] = {
            "action": action,
            "result": result,
            "player_state": player.to_dict(),
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Update player memory
        player.player_memory[f"action_{session.current_step}"] = {
            "action": action,
            "outcome": result.get("message", ""),
            "location": player.current_location,
        }
