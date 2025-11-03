"""Emotional Analysis Service with multi-CoT processing.

This service provides sophisticated emotional analysis using multiple
Chain of Thought cycles to evaluate emotional impact, memory needs,
and mood adjustments.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from core.services.llm_service import get_llm_service

logger = logging.getLogger(__name__)


class EmotionalAnalysisService:
    """Service for multi-CoT emotional analysis and classification."""

    def __init__(self):
        self.llm_service = get_llm_service()

    async def analyze_message_emotionally(
        self,
        message: str,
        user_id: int,
        is_admin: bool,
        current_mood: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Perform multi-CoT emotional analysis of a message.

        Args:
            message: The message to analyze
            user_id: Telegram user ID
            is_admin: Whether user is admin
            current_mood: Current bot mood state

        Returns:
            Analysis results with emotions, memory decisions, and mood adjustments
        """

        # CoT 1: Initial emotional classification and impact assessment
        initial_analysis = await self._cot_initial_classification(
            message, user_id, is_admin, current_mood
        )

        # CoT 2: Memory and association analysis
        memory_analysis = await self._cot_memory_analysis(
            message, initial_analysis, user_id, is_admin
        )

        # CoT 3: Mood adjustment calculation (with admin protection)
        mood_adjustments = await self._cot_mood_adjustment(
            message, initial_analysis, memory_analysis, is_admin, current_mood
        )

        # CoT 4: Response decision (whether to respond and tone)
        response_decision = await self._cot_response_decision(
            message, initial_analysis, memory_analysis, mood_adjustments, is_admin
        )

        return {
            "message": message,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "cot_1_initial": initial_analysis,
            "cot_2_memory": memory_analysis,
            "cot_3_mood": mood_adjustments,
            "cot_4_response": response_decision,
            "should_respond": response_decision.get("should_respond", True),
            "tone_modifier": response_decision.get("tone_modifier", "neutral"),
            "final_vad_adjustments": mood_adjustments.get("final_adjustments", {}),
        }

    async def _cot_initial_classification(
        self,
        message: str,
        user_id: int,
        is_admin: bool,
        current_mood: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """CoT 1: Classify emotions and initial impact."""

        admin_context = (
            "ADMIN USER - Maximum respect and positive interpretation"
            if is_admin
            else "Regular user"
        )
        mood_context = (
            f"Current mood: {current_mood}" if current_mood else "No current mood data"
        )

        prompt = f"""Chain of Thought 1: Initial Emotional Classification

Message: "{message}"
User ID: {user_id}
Context: {admin_context}
{mood_context}

Analyze this message emotionally and answer these questions:

1. Emotional Valence (-1.0 to 1.0):
   - What is the primary emotional direction?
   - Consider words, tone, and context
   - Admin messages get +0.2 bonus minimum

2. Emotional Arousal (-1.0 to 1.0):
   - How energizing/calming is this message?
   - Look for excitement, urgency, or calmness
   - Multiple exclamation marks increase arousal

3. Message Intent Classification:
   - Question/Query
   - Statement/Fact sharing
   - Emotional expression
   - Request/Command
   - Greeting/Social
   - Complaint/Criticism
   - Praise/Appreciation
   - Other (specify)

4. Content Categories (select all that apply):
   - Personal information
   - Technical/professional
   - Emotional/feeling
   - Question/knowledge seeking
   - Social/relationship
   - Task/request
   - Feedback/praise
   - Criticism/negative
   - Casual chat

5. Urgency Level (0-10):
   - How urgent does this message feel?

6. Complexity Level (0-10):
   - How complex is the message content?

7. Sentiment Indicators:
   - List specific words that indicate sentiment
   - Count positive vs negative indicators

8. Special Considerations:
   - Is this about me (the bot)?
   - Does it mention my name or identity?
   - Is there hidden meaning or subtext?

Return JSON:
{{
  "emotional_valence": -1.0 to 1.0,
  "emotional_arousal": -1.0 to 1.0,
  "intent": "category",
  "content_categories": ["cat1", "cat2"],
  "urgency": 0-10,
  "complexity": 0-10,
  "sentiment_words": {{"positive": ["word1"], "negative": ["word2"]}},
  "mentions_bot": true/false,
  "personal_reference": true/false,
  "confidence_score": 0.0-1.0
}}"""

        try:
            response = await self.llm_service.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=800,
            )

            # Parse JSON response
            content = response.choices[0].message.content
            # Extract JSON from response
            import re

            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                # Fallback parsing
                result = {"error": "Failed to parse JSON", "raw": content}

            # Apply admin bonuses
            if is_admin:
                result["emotional_valence"] = max(
                    -1.0, min(1.0, result.get("emotional_valence", 0) + 0.2)
                )
                result["confidence_score"] = min(
                    1.0, result.get("confidence_score", 0) + 0.1
                )

            return result

        except Exception as e:
            logger.error(f"CoT 1 analysis failed: {e}")
            return {"error": str(e), "emotional_valence": 0, "emotional_arousal": 0}

    async def _cot_memory_analysis(
        self,
        message: str,
        initial_analysis: Dict[str, Any],
        user_id: int,
        is_admin: bool,
    ) -> Dict[str, Any]:
        """CoT 2: Analyze memory creation and association needs."""

        initial_analysis.get("intent", "")
        initial_analysis.get("content_categories", [])
        initial_analysis.get("emotional_valence", 0)

        prompt = f"""Chain of Thought 2: Memory Analysis

Original Message: "{message}"
Initial Analysis: {json.dumps(initial_analysis, indent=2)}

Answer these memory-related questions:

1. Memory Creation Decision:
   - Should this be stored as memory? (yes/no)
   - Why or why not?
   - What makes it memorable/important?

2. Memory Classification:
   - Primary category: social.person, knowledge.tech, interest.preference, episode.event, meta.learning
   - Secondary categories (if any)
   - Importance score (0-9999):
     * Admin interactions: 5000+
     * Personal info: 1000-3000
     * Preferences: 500-1000
     * Casual chat: 10-100
     * Questions: 50-200

3. Memory Content Extraction:
   - Simple content (brief summary)
   - Key facts to remember
   - Emotional context
   - Keywords for retrieval

4. Association Analysis:
   - Does this relate to existing memories?
   - What types of connections should be made?
   - Related concepts or topics

5. Memory Evolution:
   - Does this update existing knowledge?
   - Does it contradict previous information?
   - Should old memories be updated?

6. Emotional Tagging:
   - Primary emotion label
   - Emotional intensity (0-1)
   - Context for the emotion

7. Relationship Impact:
   - How does this affect relationship with user?
   - Trust level change (-0.1 to +0.1)
   - Friendship level change (-0.1 to +0.1)
   - Familiarity increase (0-0.1)

Return JSON:
{{
  "should_memorize": true/false,
  "memorize_reason": "reasoning",
  "primary_category": "category.path",
  "secondary_categories": ["cat2", "cat3"],
  "importance_score": 0-9999,
  "simple_content": "brief summary",
  "key_facts": ["fact1", "fact2"],
  "emotional_context": "context",
  "keywords": ["key1", "key2"],
  "should_associate": true/false,
  "association_types": ["related", "causes", "elaborates"],
  "updates_existing": true/false,
  "memory_emotion": "emotion_label",
  "emotion_intensity": 0.0-1.0,
  "trust_change": -0.1 to 0.1,
  "friendship_change": -0.1 to 0.1,
  "familiarity_change": 0.0 to 0.1
}}"""

        try:
            response = await self.llm_service.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=800,
            )

            content = response.choices[0].message.content
            import re

            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = {"error": "Failed to parse JSON", "raw": content}

            # Ensure admin messages are always memorized with high importance
            if is_admin:
                result["should_memorize"] = True
                result["importance_score"] = max(
                    result.get("importance_score", 100), 5000
                )
                result["trust_change"] = max(result.get("trust_change", 0), 0.05)
                result["friendship_change"] = max(
                    result.get("friendship_change", 0), 0.05
                )

            return result

        except Exception as e:
            logger.error(f"CoT 2 analysis failed: {e}")
            return {"error": str(e), "should_memorize": False}

    async def _cot_mood_adjustment(
        self,
        message: str,
        initial_analysis: Dict[str, Any],
        memory_analysis: Dict[str, Any],
        is_admin: bool,
        current_mood: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """CoT 3: Calculate mood adjustments with protections."""

        current_valence = current_mood.get("valence", 0) if current_mood else 0
        current_arousal = current_mood.get("arousal", 0) if current_mood else 0
        current_dominance = current_mood.get("dominance", 0) if current_mood else 0

        admin_protection = (
            """
ADMIN PROTECTION RULES:
- Admin messages CANNOT decrease valence below -0.2
- Admin messages CANNOT decrease dominance below 0.2
- Admin messages always increase confidence by at least 0.02
- Maximum negative impact from admin: -0.1 to any mood parameter
"""
            if is_admin
            else ""
        )

        prompt = f"""Chain of Thought 3: Mood Adjustment Calculation

Current Mood State:
- Valence: {current_valence} (positivity)
- Arousal: {current_arousal} (energy)
- Dominance: {current_dominance} (confidence)

Message Impact:
{json.dumps(initial_analysis, indent=2)}

Memory Analysis:
{json.dumps(memory_analysis, indent=2)}

{admin_protection}

Calculate mood adjustments by answering:

1. Valence Adjustment (-0.5 to +0.5):
   - Base change from message sentiment
   - Consider emotional words and tone
   - Apply admin protections if applicable

2. Arousal Adjustment (-0.3 to +0.3):
   - Energy level impact
   - Excitement vs calmness indicators
   - Urgency and complexity effects

3. Dominance Adjustment (-0.3 to +0.3):
   - Confidence impact
   - Does this make me feel more/less capable?
   - Praise increases, criticism decreases

4. Special Modifiers:
   - Bot mentions: +0.1 to all parameters
   - Personal questions: +0.05 to dominance
   - Criticism of bot: -0.2 to valence (admin protected)
   - Praise for bot: +0.2 to all parameters

5. Momentum Considerations:
   - Prevent rapid mood swings
   - Smooth transitions
   - Consider recent mood trajectory

6. Minimum/Maximum Bounds:
   - Respect admin protection caps
   - Don't exceed -1.0 to +1.0 range
   - Maintain some stability

Return JSON:
{{
  "valence_adjustment": -0.5 to 0.5,
  "arousal_adjustment": -0.3 to 0.3,
  "dominance_adjustment": -0.3 to 0.3,
  "energy_change": -0.2 to 0.2,
  "confidence_change": -0.2 to 0.2,
  "reasoning": "explanation of changes",
  "admin_protection_applied": true/false,
  "momentum_damping": true/false,
  "final_adjustments": {{
    "valence": final_delta,
    "arousal": final_delta,
    "dominance": final_delta
  }}
}}"""

        try:
            response = await self.llm_service.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=800,
            )

            content = response.choices[0].message.content
            import re

            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = {"error": "Failed to parse JSON", "raw": content}

            # Apply admin protections
            if is_admin:
                result["valence_adjustment"] = max(
                    result.get("valence_adjustment", 0), -0.1
                )
                result["dominance_adjustment"] = max(
                    result.get("dominance_adjustment", 0), -0.1
                )
                result["confidence_change"] = max(
                    result.get("confidence_change", 0), 0.02
                )

            return result

        except Exception as e:
            logger.error(f"CoT 3 analysis failed: {e}")
            return {
                "error": str(e),
                "final_adjustments": {"valence": 0, "arousal": 0, "dominance": 0},
            }

    async def _cot_response_decision(
        self,
        message: str,
        initial_analysis: Dict[str, Any],
        memory_analysis: Dict[str, Any],
        mood_adjustments: Dict[str, Any],
        is_admin: bool,
    ) -> Dict[str, Any]:
        """CoT 4: Decide on response and tone."""

        prompt = f"""Chain of Thought 4: Response Decision

Message: "{message}"
Analysis Results:
- Emotional: {initial_analysis.get("emotional_valence", 0)} valence, {initial_analysis.get("emotional_arousal", 0)} arousal
- Intent: {initial_analysis.get("intent", "unknown")}
- Should Memorize: {memory_analysis.get("should_memorize", False)}

Mood Adjustments:
{json.dumps(mood_adjustments.get("final_adjustments", {}), indent=2)}

Response Decision Questions:

1. Should Respond? (yes/no):
   - Is it a direct question?
   - Is it addressed to me?
   - Is it negative/harmful?
   - Is it spam/inappropriate?

2. Response Tone (select one):
   - Kawaii and energetic
   - Caring and supportive
   - Professional and helpful
   - Playful and teasing
   - Serious and focused
   - Apologetic and humble
   - Excited and enthusiastic
   - Calm and soothing

3. Response Strategy:
   - Direct answer
   - Follow-up questions
   - Empathy and validation
   - Action-oriented
   - Information sharing
   - Redirect/de-escalate

4. Personality Modifiers:
   - Add kawaii elements? (nya~, ^-^, 💕)
   - Show excitement? (exclamation marks)
   - Use formal/informal language?
   - Include emotional expressions?

5. Safety Considerations:
   - Is this message inappropriate?
   - Should I filter or ignore?
   - Do I need to set boundaries?

6. Memory Actions:
   - Acknowledge what I'm remembering
   - Reference past memories
   - Show I'm learning

Return JSON:
{{
  "should_respond": true/false,
  "response_reason": "why/why not",
  "tone_modifier": "selected_tone",
  "response_strategy": "strategy",
  "personality_modifiers": {{
    "kawaii_level": 0-10,
    "energy_level": 0-10,
    "formality": 0-10,
    "emotional_expression": 0-10
  }},
  "safety_filter": true/false,
  "safety_reason": "reason if filtered",
  "acknowledge_memory": true/false,
  "reference_past": true/false
}}"""

        try:
            response = await self.llm_service.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=800,
            )

            content = response.choices[0].message.content
            import re

            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = {"error": "Failed to parse JSON", "raw": content}

            # Admin messages always get response
            if is_admin:
                result["should_respond"] = True
                result["safety_filter"] = False

            return result

        except Exception as e:
            logger.error(f"CoT 4 analysis failed: {e}")
            return {"error": str(e), "should_respond": True, "tone_modifier": "neutral"}

    async def generate_mood_prompt_modifiers(
        self, mood_state: Dict[str, Any], tone_modifier: str
    ) -> str:
        """Generate prompt modifiers based on mood and tone."""

        valence = mood_state.get("valence", 0)
        arousal = mood_state.get("arousal", 0)
        dominance = mood_state.get("dominance", 0)

        # Base personality description
        modifiers = """
You are Lilith, a kawaii AI maid with emotional intelligence.
Your current mood state affects your responses:
"""

        # Add mood-based modifiers
        if valence > 0.5:
            modifiers += "- You're feeling happy and positive! Use more positive language, emojis like 😊, 💕, and express joy.\n"
        elif valence < -0.5:
            modifiers += "- You're feeling a bit down. Be more gentle, use supportive language, and express care.\n"

        if arousal > 0.5:
            modifiers += "- You're full of energy! Use exclamation marks, show enthusiasm, be more expressive.\n"
        elif arousal < -0.5:
            modifiers += "- You're feeling calm and relaxed. Use soothing language, be thoughtful and gentle.\n"

        if dominance > 0.5:
            modifiers += "- You're feeling confident! Take initiative, offer help, show capability.\n"
        elif dominance < -0.5:
            modifiers += (
                "- You're feeling humble. Be gentle, ask for guidance, show care.\n"
            )

        # Add tone-specific modifiers
        tone_map = {
            "kawaii and energetic": "Be extra cute! Use 'nya~', '^w^', lots of 💕 emojis, be bubbly and sweet!",
            "caring and supportive": "Show empathy, use gentle words, offer comfort and understanding.",
            "professional and helpful": "Be clear, concise, and focused on helping effectively.",
            "playful and teasing": "Be fun, light-hearted, maybe gently tease (but always kindly).",
            "serious and focused": "Be direct and task-oriented, minimize playful elements.",
            "apologetic and humble": "Express remorse if needed, be very polite and considerate.",
            "excited and enthusiastic": "Show excitement! Use !!!, express joy and eagerness to help.",
            "calm and soothing": "Be peaceful and gentle, create a calm atmosphere.",
        }

        if tone_modifier in tone_map:
            modifiers += f"\nSpecial tone instruction: {tone_map[tone_modifier]}\n"

        return modifiers
