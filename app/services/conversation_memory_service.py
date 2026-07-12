"""
Conversation memory and reference resolution service
"""
import json
import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict

from app.services.llm_chat_service import llm_chat_service

logger = logging.getLogger(__name__)

@dataclass
class ConversationMemory:
    """Stores conversation memory and context"""
    key_facts: Dict[str, Any]
    entity_references: Dict[str, str]  # Maps pronouns/references to actual names
    summary: str
    important_messages: List[Dict]
    timestamp: datetime

class MemoryService:
    """Manages conversation memory, summarization, and reference resolution"""

    def __init__(self):
        self.memories = {}  # session_id -> ConversationMemory
        self.reference_patterns = {
            "other_party": [
                r"\bmy ex\b", r"\bex-?(?:husband|wife|spouse|partner)\b",
                r"\bthe (?:other party|respondent|petitioner)\b",
                r"\b(?:he|she|they)\b"  # Context-dependent
            ],
            "children": [
                r"\bmy (?:kid|kids|child|children|son|daughter)\b",
                r"\bour (?:kid|kids|child|children|son|daughter)\b",
                r"\bthe (?:kid|kids|child|children|minor|minors)\b"
            ],
            "self": [
                r"\bI\b", r"\bme\b", r"\bmy\b", r"\bmyself\b"
            ]
        }

    async def summarize_conversation(
        self,
        messages: List[Dict],
        max_length: int = 500
    ) -> str:
        """
        Summarize conversation for memory storage

        Args:
            messages: List of message dictionaries
            max_length: Maximum summary length

        Returns:
            Conversation summary
        """
        if not messages:
            return ""

        # Use LLM for summarization if available
        if llm_chat_service:
            summary = await llm_chat_service.summarize_conversation(
                messages, max_length
            )
            return summary

        # Fallback to simple extraction
        return self._simple_summarization(messages, max_length)

    def _simple_summarization(
        self,
        messages: List[Dict],
        max_length: int
    ) -> str:
        """Simple fallback summarization without LLM"""
        key_points = []

        for msg in messages:
            if msg.get("sender") == "user":
                content = msg.get("content", "")
                # Extract key information patterns
                if any(word in content.lower() for word in ["custody", "support", "violation"]):
                    key_points.append(content[:100])
                elif any(word in content.lower() for word in ["emergency", "urgent", "immediate"]):
                    key_points.append(f"URGENT: {content[:80]}")

        summary = " | ".join(key_points[:5])  # Keep top 5 points
        if len(summary) > max_length:
            summary = summary[:max_length-3] + "..."

        return summary

    async def extract_key_facts(
        self,
        messages: List[Dict]
    ) -> Dict[str, Any]:
        """
        Extract key facts from conversation

        Returns:
            Dictionary of key facts
        """
        facts = {
            "motion_type": None,
            "party_names": {},
            "case_number": None,
            "children": [],
            "urgency": None,
            "amounts": [],
            "dates": [],
            "main_issues": []
        }

        for msg in messages:
            content = msg.get("content", "").lower()

            # Extract motion type
            if not facts["motion_type"]:
                if "custody" in content:
                    facts["motion_type"] = "custody"
                elif "support" in content:
                    facts["motion_type"] = "support"
                elif "violation" in content:
                    facts["motion_type"] = "violation"

            # Extract urgency
            if "emergency" in content or "urgent" in content:
                facts["urgency"] = "emergency"

            # Extract case number
            case_pattern = r'\b[A-Z]{2}-?\d{4}-?\d+\b'
            case_match = re.search(case_pattern, msg.get("content", ""), re.IGNORECASE)
            if case_match:
                facts["case_number"] = case_match.group()

            # Extract dates
            date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'
            dates = re.findall(date_pattern, msg.get("content", ""))
            facts["dates"].extend(dates)

            # Extract money amounts
            money_pattern = r'\$[\d,]+(?:\.\d{2})?'
            amounts = re.findall(money_pattern, msg.get("content", ""))
            facts["amounts"].extend(amounts)

            # Extract names (capitalized words)
            if msg.get("sender") == "user":
                name_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b'
                names = re.findall(name_pattern, msg.get("content", ""))
                for name in names:
                    if len(facts["party_names"]) < 2:
                        if not facts["party_names"]:
                            facts["party_names"]["self"] = name
                        else:
                            facts["party_names"]["other_party"] = name

        return facts

    def build_entity_references(
        self,
        facts: Dict[str, Any],
        profile_data: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        Build entity reference mapping

        Args:
            facts: Extracted facts from conversation
            profile_data: User profile data

        Returns:
            Dictionary mapping references to actual names/values
        """
        references = {}

        # Add party names
        if profile_data:
            if "party_name" in profile_data:
                references["I"] = profile_data["party_name"]
                references["me"] = profile_data["party_name"]
                references["my"] = profile_data["party_name"] + "'s"

            if "other_party_name" in profile_data:
                references["my ex"] = profile_data["other_party_name"]
                references["ex-husband"] = profile_data["other_party_name"]
                references["ex-wife"] = profile_data["other_party_name"]
                references["the other party"] = profile_data["other_party_name"]
                references["respondent"] = profile_data["other_party_name"]

        # Override with facts from conversation
        if facts.get("party_names"):
            if "self" in facts["party_names"]:
                references["I"] = facts["party_names"]["self"]
                references["me"] = facts["party_names"]["self"]

            if "other_party" in facts["party_names"]:
                references["my ex"] = facts["party_names"]["other_party"]
                references["the other party"] = facts["party_names"]["other_party"]

        # Add children references
        if profile_data and "children_info" in profile_data:
            children = profile_data["children_info"]
            if isinstance(children, list) and children:
                if len(children) == 1:
                    references["my child"] = children[0].get("name", "the child")
                    references["our child"] = children[0].get("name", "the child")
                else:
                    child_names = [c.get("name", f"child {i+1}") for i, c in enumerate(children)]
                    references["the children"] = ", ".join(child_names)
                    references["our children"] = ", ".join(child_names)
                    references["my children"] = ", ".join(child_names)

        return references

    def resolve_references(
        self,
        text: str,
        references: Dict[str, str],
        context: Optional[str] = None
    ) -> str:
        """
        Resolve pronouns and references in text

        Args:
            text: Text containing references
            references: Reference mapping dictionary
            context: Additional context for resolution

        Returns:
            Text with references resolved
        """
        resolved_text = text

        # Sort references by length (longer first) to avoid partial replacements
        sorted_refs = sorted(references.items(), key=lambda x: len(x[0]), reverse=True)

        for ref_pattern, actual_value in sorted_refs:
            # Case-insensitive replacement for most references
            if ref_pattern.lower() in ["i", "me", "my"]:
                # These are case-sensitive
                resolved_text = re.sub(
                    r'\b' + re.escape(ref_pattern) + r'\b',
                    actual_value,
                    resolved_text,
                    flags=re.IGNORECASE if ref_pattern != "I" else 0
                )
            else:
                # Case-insensitive for other references
                resolved_text = re.sub(
                    r'\b' + re.escape(ref_pattern) + r'\b',
                    actual_value,
                    resolved_text,
                    flags=re.IGNORECASE
                )

        return resolved_text

    async def update_memory(
        self,
        session_id: str,
        messages: List[Dict],
        profile_data: Optional[Dict] = None
    ) -> ConversationMemory:
        """
        Update conversation memory for a session

        Args:
            session_id: Chat session ID
            messages: All messages in conversation
            profile_data: User profile data

        Returns:
            Updated ConversationMemory
        """
        # Extract key facts
        facts = await self.extract_key_facts(messages)

        # Build references
        references = self.build_entity_references(facts, profile_data)

        # Summarize if conversation is long
        summary = ""
        if len(messages) > 20:
            summary = await self.summarize_conversation(messages[-30:])  # Last 30 messages

        # Identify important messages
        important = self._identify_important_messages(messages, facts)

        # Create or update memory
        memory = ConversationMemory(
            key_facts=facts,
            entity_references=references,
            summary=summary,
            important_messages=important,
            timestamp=datetime.utcnow()
        )

        self.memories[session_id] = memory
        return memory

    def _identify_important_messages(
        self,
        messages: List[Dict],
        facts: Dict[str, Any]
    ) -> List[Dict]:
        """Identify important messages to preserve"""
        important = []

        importance_keywords = [
            "emergency", "urgent", "violated", "custody", "support",
            "case number", "hearing date", "deadline"
        ]

        for msg in messages:
            content_lower = msg.get("content", "").lower()

            # Check if message contains important information
            if any(keyword in content_lower for keyword in importance_keywords):
                important.append({
                    "content": msg["content"][:200],  # Keep first 200 chars
                    "sender": msg.get("sender"),
                    "timestamp": msg.get("timestamp")
                })

            # Keep messages with extracted facts
            if msg.get("entities") and len(msg["entities"]) > 0:
                important.append({
                    "content": msg["content"][:200],
                    "entities": msg["entities"],
                    "sender": msg.get("sender")
                })

        # Keep only the most recent important messages
        return important[-10:]  # Keep last 10 important messages

    def get_memory_context(
        self,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get memory context for a session

        Args:
            session_id: Chat session ID

        Returns:
            Memory context dictionary or None
        """
        if session_id not in self.memories:
            return None

        memory = self.memories[session_id]

        # Check if memory is still fresh (within 2 hours)
        if datetime.utcnow() - memory.timestamp > timedelta(hours=2):
            logger.info(f"Memory for session {session_id} is stale")

        return {
            "facts": memory.key_facts,
            "references": memory.entity_references,
            "summary": memory.summary,
            "important_points": [msg["content"] for msg in memory.important_messages]
        }

    def clear_old_memories(self, max_age_hours: int = 24):
        """Clear memories older than specified hours"""
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)

        to_remove = []
        for session_id, memory in self.memories.items():
            if memory.timestamp < cutoff:
                to_remove.append(session_id)

        for session_id in to_remove:
            del self.memories[session_id]
            logger.info(f"Cleared old memory for session {session_id}")

        return len(to_remove)

# Singleton instance
memory_service = MemoryService()