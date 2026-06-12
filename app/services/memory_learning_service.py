"""
Long-term memory and learning service for intelligent user assistance
Provides persistent memory, profile learning, and pattern recognition
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import numpy as np
from collections import defaultdict, Counter
import hashlib

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Types of memories stored"""
    CONVERSATION = "conversation"
    PROFILE_FACT = "profile_fact"
    PREFERENCE = "preference"
    CORRECTION = "correction"
    PATTERN = "pattern"
    OUTCOME = "outcome"
    DOCUMENT = "document"


class Memory:
    """Individual memory unit"""

    def __init__(
        self,
        memory_type: MemoryType,
        content: str,
        metadata: Dict[str, Any] = None,
        embedding: Optional[List[float]] = None
    ):
        self.id = self._generate_id(content)
        self.memory_type = memory_type
        self.content = content
        self.metadata = metadata or {}
        self.embedding = embedding
        self.created_at = datetime.utcnow()
        self.accessed_count = 0
        self.last_accessed = None
        self.confidence = 1.0

    def _generate_id(self, content: str) -> str:
        """Generate unique ID for memory"""
        return hashlib.md5(f"{content}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]

    def access(self):
        """Record memory access"""
        self.accessed_count += 1
        self.last_accessed = datetime.utcnow()

    def decay(self, days: int = 30):
        """Apply time-based confidence decay"""
        age_days = (datetime.utcnow() - self.created_at).days
        if age_days > days:
            self.confidence = max(0.5, self.confidence * (days / age_days))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'type': self.memory_type.value,
            'content': self.content,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'accessed_count': self.accessed_count,
            'confidence': self.confidence
        }


class ProfileLearner:
    """Learn and update user profiles from conversations"""

    def __init__(self):
        self.profiles = {}
        self.extraction_patterns = {
            'children': [
                r'my (?:son|daughter|child) (\w+)',
                r'(\w+) is \d+ years old',
                r'children?: ([\w\s,]+)'
            ],
            'employment': [
                r'I work (?:at|for) ([\w\s]+)',
                r'my job (?:at|as) ([\w\s]+)',
                r'employed (?:by|at) ([\w\s]+)'
            ],
            'location': [
                r'I live in ([\w\s]+)',
                r'moved to ([\w\s]+)',
                r'residing in ([\w\s]+)'
            ],
            'financial': [
                r'income (?:is|of) \$?([\d,]+)',
                r'make \$?([\d,]+)',
                r'earn \$?([\d,]+)'
            ]
        }

    def extract_facts(self, text: str, user_id: str) -> List[Dict[str, Any]]:
        """Extract facts from conversation text"""
        import re
        facts = []

        for category, patterns in self.extraction_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    facts.append({
                        'category': category,
                        'value': match.group(1),
                        'confidence': 0.8,
                        'source': 'conversation',
                        'extracted_at': datetime.utcnow().isoformat()
                    })

        return facts

    def update_profile(self, user_id: str, facts: List[Dict[str, Any]]):
        """Update user profile with new facts"""
        if user_id not in self.profiles:
            self.profiles[user_id] = {
                'facts': {},
                'relationships': {},
                'timeline': [],
                'last_updated': None
            }

        profile = self.profiles[user_id]

        for fact in facts:
            category = fact['category']
            value = fact['value']

            # Store with confidence scoring
            if category not in profile['facts']:
                profile['facts'][category] = []

            # Check if fact already exists
            existing = next(
                (f for f in profile['facts'][category] if f['value'] == value),
                None
            )

            if existing:
                # Increase confidence for repeated facts
                existing['confidence'] = min(1.0, existing['confidence'] + 0.1)
                existing['mentioned_count'] = existing.get('mentioned_count', 1) + 1
            else:
                # Add new fact
                profile['facts'][category].append({
                    'value': value,
                    'confidence': fact['confidence'],
                    'first_mentioned': fact['extracted_at'],
                    'mentioned_count': 1
                })

        profile['last_updated'] = datetime.utcnow().isoformat()

    def get_profile_summary(self, user_id: str) -> Dict[str, Any]:
        """Get summarized profile information"""
        if user_id not in self.profiles:
            return {}

        profile = self.profiles[user_id]
        summary = {}

        # Get high-confidence facts
        for category, facts in profile['facts'].items():
            high_confidence = [
                f for f in facts
                if f['confidence'] >= 0.7
            ]
            if high_confidence:
                summary[category] = high_confidence

        return summary


class PreferenceDetector:
    """Detect and track user preferences"""

    def __init__(self):
        self.preferences = {}
        self.interaction_patterns = {}

    def track_interaction(self, user_id: str, interaction: Dict[str, Any]):
        """Track user interaction patterns"""
        if user_id not in self.interaction_patterns:
            self.interaction_patterns[user_id] = {
                'response_lengths': [],
                'question_types': [],
                'time_of_day': [],
                'session_durations': [],
                'form_choices': [],
                'communication_style': []
            }

        patterns = self.interaction_patterns[user_id]

        # Track various interaction aspects
        if 'message_length' in interaction:
            patterns['response_lengths'].append(interaction['message_length'])

        if 'time' in interaction:
            hour = datetime.fromisoformat(interaction['time']).hour
            patterns['time_of_day'].append(hour)

        if 'form_type' in interaction:
            patterns['form_choices'].append(interaction['form_type'])

        if 'style_indicators' in interaction:
            patterns['communication_style'].extend(interaction['style_indicators'])

    def analyze_preferences(self, user_id: str) -> Dict[str, Any]:
        """Analyze user preferences from patterns"""
        if user_id not in self.interaction_patterns:
            return {}

        patterns = self.interaction_patterns[user_id]
        preferences = {}

        # Analyze response length preference
        if patterns['response_lengths']:
            avg_length = np.mean(patterns['response_lengths'])
            if avg_length < 50:
                preferences['response_style'] = 'concise'
            elif avg_length > 200:
                preferences['response_style'] = 'detailed'
            else:
                preferences['response_style'] = 'balanced'

        # Analyze time preferences
        if patterns['time_of_day']:
            common_hours = Counter(patterns['time_of_day']).most_common(3)
            peak_hours = [h[0] for h in common_hours]

            if all(6 <= h < 12 for h in peak_hours):
                preferences['active_time'] = 'morning'
            elif all(12 <= h < 17 for h in peak_hours):
                preferences['active_time'] = 'afternoon'
            elif all(17 <= h < 22 for h in peak_hours):
                preferences['active_time'] = 'evening'
            else:
                preferences['active_time'] = 'varied'

        # Analyze form preferences
        if patterns['form_choices']:
            most_used = Counter(patterns['form_choices']).most_common(1)[0][0]
            preferences['preferred_forms'] = most_used

        # Analyze communication style
        if patterns['communication_style']:
            style_counts = Counter(patterns['communication_style'])
            if style_counts.get('formal', 0) > style_counts.get('casual', 0):
                preferences['communication'] = 'formal'
            else:
                preferences['communication'] = 'casual'

        self.preferences[user_id] = preferences
        return preferences

    def get_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences"""
        return self.preferences.get(user_id, {})


class CorrectionLearner:
    """Learn from user corrections to improve accuracy"""

    def __init__(self):
        self.corrections = defaultdict(list)
        self.correction_patterns = {}

    def record_correction(
        self,
        user_id: str,
        original: str,
        corrected: str,
        context: str = "",
        field: str = ""
    ):
        """Record a user correction"""
        correction = {
            'original': original,
            'corrected': corrected,
            'context': context,
            'field': field,
            'timestamp': datetime.utcnow().isoformat()
        }

        self.corrections[user_id].append(correction)

        # Learn correction pattern
        pattern_key = f"{user_id}:{field}:{original.lower()}"
        self.correction_patterns[pattern_key] = corrected

        logger.info(f"Learned correction for {user_id}: {original} → {corrected}")

    def apply_corrections(self, user_id: str, text: str, field: str = "") -> str:
        """Apply learned corrections to text"""
        # Check for exact corrections
        pattern_key = f"{user_id}:{field}:{text.lower()}"
        if pattern_key in self.correction_patterns:
            return self.correction_patterns[pattern_key]

        # Check for partial corrections
        for correction in self.corrections[user_id]:
            if correction['original'].lower() in text.lower():
                text = text.replace(
                    correction['original'],
                    correction['corrected']
                )

        return text

    def get_user_corrections(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all corrections for a user"""
        return self.corrections.get(user_id, [])


class PatternRecognizer:
    """Recognize patterns in user behavior and needs"""

    def __init__(self):
        self.user_patterns = defaultdict(lambda: {
            'filing_sequence': [],
            'issue_frequency': defaultdict(int),
            'seasonal_patterns': defaultdict(list),
            'trigger_events': [],
            'success_patterns': []
        })

    def record_event(self, user_id: str, event_type: str, event_data: Dict[str, Any]):
        """Record a user event for pattern analysis"""
        patterns = self.user_patterns[user_id]

        # Track filing sequence
        if event_type == 'filing':
            patterns['filing_sequence'].append({
                'form_type': event_data.get('form_type'),
                'date': datetime.utcnow().isoformat(),
                'outcome': event_data.get('outcome')
            })

        # Track issue frequency
        if event_type == 'issue':
            issue_type = event_data.get('issue_type')
            patterns['issue_frequency'][issue_type] += 1

        # Track seasonal patterns
        month = datetime.utcnow().month
        patterns['seasonal_patterns'][month].append(event_type)

        # Track trigger events
        if event_type == 'trigger':
            patterns['trigger_events'].append({
                'trigger': event_data.get('trigger'),
                'action': event_data.get('action'),
                'date': datetime.utcnow().isoformat()
            })

    def identify_patterns(self, user_id: str) -> Dict[str, Any]:
        """Identify patterns for a user"""
        if user_id not in self.user_patterns:
            return {}

        patterns = self.user_patterns[user_id]
        identified = {}

        # Identify filing patterns
        if len(patterns['filing_sequence']) >= 3:
            # Check for repeated sequences
            sequence = [f['form_type'] for f in patterns['filing_sequence'][-3:]]
            if len(set(sequence)) == 1:
                identified['repeated_filing'] = sequence[0]

        # Identify frequent issues
        if patterns['issue_frequency']:
            most_common = max(patterns['issue_frequency'].items(), key=lambda x: x[1])
            if most_common[1] >= 3:
                identified['recurring_issue'] = most_common[0]

        # Identify seasonal patterns
        current_month = datetime.utcnow().month
        if patterns['seasonal_patterns'][current_month]:
            common_events = Counter(patterns['seasonal_patterns'][current_month])
            identified['seasonal_activity'] = common_events.most_common(1)[0][0]

        # Identify trigger patterns
        if len(patterns['trigger_events']) >= 2:
            recent_triggers = patterns['trigger_events'][-5:]
            trigger_types = [t['trigger'] for t in recent_triggers]
            if len(set(trigger_types)) == 1:
                identified['predictable_trigger'] = trigger_types[0]

        return identified

    def predict_next_action(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Predict likely next action based on patterns"""
        patterns = self.identify_patterns(user_id)

        predictions = []

        # Predict based on filing sequence
        if 'repeated_filing' in patterns:
            predictions.append({
                'action': 'file_form',
                'form_type': patterns['repeated_filing'],
                'confidence': 0.7,
                'reason': 'Based on your filing history'
            })

        # Predict based on recurring issues
        if 'recurring_issue' in patterns:
            predictions.append({
                'action': 'address_issue',
                'issue_type': patterns['recurring_issue'],
                'confidence': 0.8,
                'reason': 'This issue comes up frequently'
            })

        # Predict based on seasonal patterns
        if 'seasonal_activity' in patterns:
            predictions.append({
                'action': patterns['seasonal_activity'],
                'confidence': 0.6,
                'reason': 'You often do this at this time of year'
            })

        # Return highest confidence prediction
        if predictions:
            return max(predictions, key=lambda x: x['confidence'])

        return None


class MemoryLearningService:
    """Main service orchestrating memory and learning"""

    def __init__(self):
        self.memories: Dict[str, List[Memory]] = defaultdict(list)
        self.profile_learner = ProfileLearner()
        self.preference_detector = PreferenceDetector()
        self.correction_learner = CorrectionLearner()
        self.pattern_recognizer = PatternRecognizer()

    def store_memory(
        self,
        user_id: str,
        memory_type: MemoryType,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Store a new memory"""
        memory = Memory(memory_type, content, metadata)
        self.memories[user_id].append(memory)

        # Trigger learning based on memory type
        if memory_type == MemoryType.CONVERSATION:
            # Extract facts from conversation
            facts = self.profile_learner.extract_facts(content, user_id)
            if facts:
                self.profile_learner.update_profile(user_id, facts)

        elif memory_type == MemoryType.CORRECTION:
            # Learn from correction
            if metadata:
                self.correction_learner.record_correction(
                    user_id,
                    metadata.get('original', ''),
                    metadata.get('corrected', ''),
                    metadata.get('context', ''),
                    metadata.get('field', '')
                )

        logger.info(f"Stored {memory_type.value} memory for user {user_id}")
        return memory.id

    def search_memories(
        self,
        user_id: str,
        query: str,
        memory_types: List[MemoryType] = None,
        limit: int = 10
    ) -> List[Memory]:
        """Search user memories"""
        if user_id not in self.memories:
            return []

        user_memories = self.memories[user_id]

        # Filter by memory type if specified
        if memory_types:
            user_memories = [
                m for m in user_memories
                if m.memory_type in memory_types
            ]

        # Simple text search (would use embeddings in production)
        query_lower = query.lower()
        relevant = [
            m for m in user_memories
            if query_lower in m.content.lower()
        ]

        # Sort by relevance (access count and recency)
        relevant.sort(
            key=lambda m: (m.accessed_count, -((datetime.utcnow() - m.created_at).days)),
            reverse=True
        )

        # Update access counts
        for memory in relevant[:limit]:
            memory.access()

        return relevant[:limit]

    def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user context from all learning systems"""
        context = {
            'profile': self.profile_learner.get_profile_summary(user_id),
            'preferences': self.preference_detector.get_preferences(user_id),
            'corrections': self.correction_learner.get_user_corrections(user_id),
            'patterns': self.pattern_recognizer.identify_patterns(user_id),
            'prediction': self.pattern_recognizer.predict_next_action(user_id),
            'recent_memories': [
                m.to_dict() for m in self.memories[user_id][-5:]
            ] if user_id in self.memories else []
        }

        return context

    def apply_learning(self, user_id: str, text: str, field: str = "") -> str:
        """Apply all learned corrections and preferences to text"""
        # Apply corrections
        text = self.correction_learner.apply_corrections(user_id, text, field)

        # Apply preferences
        preferences = self.preference_detector.get_preferences(user_id)

        # Adjust text based on preferences
        if preferences.get('response_style') == 'concise':
            # Truncate if too long
            if len(text) > 200:
                text = text[:197] + "..."
        elif preferences.get('response_style') == 'detailed':
            # Could expand with examples or explanations
            pass

        if preferences.get('communication') == 'formal':
            # Apply formal tone transformations
            text = text.replace("don't", "do not").replace("won't", "will not")

        return text

    def cleanup_old_memories(self, days: int = 365):
        """Clean up old memories with decay"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        for user_id in list(self.memories.keys()):
            # Apply decay to old memories
            for memory in self.memories[user_id]:
                memory.decay(days=30)

            # Remove very old or low-confidence memories
            self.memories[user_id] = [
                m for m in self.memories[user_id]
                if m.created_at > cutoff_date or m.confidence > 0.3
            ]

            # Remove user if no memories left
            if not self.memories[user_id]:
                del self.memories[user_id]


# Singleton instance
memory_service = MemoryLearningService()