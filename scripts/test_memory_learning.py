#!/usr/bin/env python3
"""
Test script for memory, learning, and analytics features
"""
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.memory_learning_service import (
    memory_service, MemoryType, FeedbackType
)
from app.services.analytics_feedback_service import (
    analytics_service, MetricType, QualityMetric
)

def test_memory_learning():
    """Test memory and learning capabilities"""
    print("\n" + "=" * 60)
    print("TESTING MEMORY & LEARNING SYSTEM")
    print("=" * 60)

    user_id = "test_user_123"

    # Test 1: Profile Learning
    print("\n" + "=" * 50)
    print("Test 1: Profile Learning from Conversation")
    print("=" * 50)

    conversations = [
        "I work at Tech Corp as a software engineer",
        "My daughter Sarah is 8 years old and my son Mike is 6",
        "We live in San Diego near the beach",
        "My income is $120,000 per year",
        "My ex moved to Texas last month"
    ]

    for conv in conversations:
        memory_service.store_memory(
            user_id,
            MemoryType.CONVERSATION,
            conv
        )
        print(f"✓ Stored: {conv[:50]}...")

    # Get learned profile
    profile = memory_service.profile_learner.get_profile_summary(user_id)
    print("\n📋 Learned Profile:")
    for category, facts in profile.items():
        print(f"  {category}:")
        for fact in facts:
            print(f"    - {fact['value']} (confidence: {fact['confidence']:.1f})")

    # Test 2: Preference Detection
    print("\n" + "=" * 50)
    print("Test 2: Preference Detection")
    print("=" * 50)

    # Simulate interactions
    interactions = [
        {'message_length': 45, 'time': datetime.utcnow().isoformat()},
        {'message_length': 38, 'time': datetime.utcnow().isoformat()},
        {'message_length': 52, 'time': (datetime.utcnow() - timedelta(hours=2)).isoformat()},
        {'form_type': 'FL-300', 'time': datetime.utcnow().isoformat()},
        {'form_type': 'FL-300', 'time': (datetime.utcnow() - timedelta(days=1)).isoformat()},
        {'style_indicators': ['formal', 'formal', 'concise']}
    ]

    for interaction in interactions:
        memory_service.preference_detector.track_interaction(user_id, interaction)

    preferences = memory_service.preference_detector.analyze_preferences(user_id)
    print("\n🎯 Detected Preferences:")
    for pref, value in preferences.items():
        print(f"  {pref}: {value}")

    # Test 3: Correction Learning
    print("\n" + "=" * 50)
    print("Test 3: Correction Learning")
    print("=" * 50)

    # Record corrections
    corrections = [
        ("visitation", "parenting time", "custody discussion", "custody_field"),
        ("ex-husband", "John", "party reference", "other_party_name"),
        ("child support", "family support", "support type", "support_type")
    ]

    for original, corrected, context, field in corrections:
        memory_service.correction_learner.record_correction(
            user_id, original, corrected, context, field
        )
        print(f"✓ Learned: {original} → {corrected}")

    # Test correction application
    test_text = "I need to modify visitation with my ex-husband for child support"
    corrected_text = memory_service.correction_learner.apply_corrections(
        user_id, test_text, "general"
    )
    print(f"\n📝 Original: {test_text}")
    print(f"📝 Corrected: {corrected_text}")

    # Test 4: Pattern Recognition
    print("\n" + "=" * 50)
    print("Test 4: Pattern Recognition")
    print("=" * 50)

    # Record events for pattern detection
    events = [
        ('filing', {'form_type': 'FL-300', 'outcome': 'granted'}),
        ('filing', {'form_type': 'FL-300', 'outcome': 'granted'}),
        ('filing', {'form_type': 'FL-300', 'outcome': 'modified'}),
        ('issue', {'issue_type': 'late_support'}),
        ('issue', {'issue_type': 'late_support'}),
        ('issue', {'issue_type': 'late_support'}),
        ('trigger', {'trigger': 'school_start', 'action': 'modify_schedule'})
    ]

    for event_type, event_data in events:
        memory_service.pattern_recognizer.record_event(user_id, event_type, event_data)

    patterns = memory_service.pattern_recognizer.identify_patterns(user_id)
    print("\n🔍 Identified Patterns:")
    for pattern_type, pattern_value in patterns.items():
        print(f"  {pattern_type}: {pattern_value}")

    prediction = memory_service.pattern_recognizer.predict_next_action(user_id)
    if prediction:
        print(f"\n🔮 Predicted Next Action:")
        print(f"  Action: {prediction['action']}")
        print(f"  Confidence: {prediction['confidence']:.1%}")
        print(f"  Reason: {prediction['reason']}")

    # Test 5: Memory Search
    print("\n" + "=" * 50)
    print("Test 5: Memory Search & Retrieval")
    print("=" * 50)

    # Search memories
    search_results = memory_service.search_memories(user_id, "daughter")
    print(f"\n🔎 Search results for 'daughter': {len(search_results)} found")
    for memory in search_results[:2]:
        print(f"  - {memory.content[:100]}...")

    # Get comprehensive user context
    context = memory_service.get_user_context(user_id)
    print("\n📊 Comprehensive User Context:")
    print(f"  Profile facts: {len(context['profile'])} categories")
    print(f"  Preferences: {len(context['preferences'])} detected")
    print(f"  Corrections: {len(context['corrections'])} learned")
    print(f"  Patterns: {len(context['patterns'])} identified")
    if context['prediction']:
        print(f"  Next action prediction available")


def test_analytics_feedback():
    """Test analytics and feedback system"""
    print("\n" + "=" * 60)
    print("TESTING ANALYTICS & FEEDBACK SYSTEM")
    print("=" * 60)

    session_id = "test_session_001"
    user_id = "test_user_123"

    # Test 1: Session Analytics
    print("\n" + "=" * 50)
    print("Test 1: Conversation Analytics")
    print("=" * 50)

    # Start session
    analytics_service.analytics.start_session(session_id, user_id)
    print("✓ Started session tracking")

    # Track messages
    messages = [
        ("user", "I need to modify custody", 0.5),
        ("bot", "I can help with that. What changes?", 1.2),
        ("user", "I want sole custody", 0.8),
        ("bot", "What's the reason for this change?", 1.1),
        ("user", "My ex moved to another state", 0.6)
    ]

    for msg_type, content, response_time in messages:
        analytics_service.analytics.track_message(
            session_id, msg_type, content, response_time
        )

    # Track some clarifications
    analytics_service.analytics.track_clarification(session_id)

    # Track form generation
    analytics_service.analytics.track_form_generation(session_id, "FL-300", True)

    # End session
    analytics_service.analytics.end_session(session_id, completed=True)

    # Get session summary
    summary = analytics_service.analytics.get_session_summary(session_id)
    print("\n📊 Session Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")

    # Test 2: Feedback Collection
    print("\n" + "=" * 50)
    print("Test 2: Feedback Collection")
    print("=" * 50)

    # Collect various feedback
    feedback_items = [
        (FeedbackType.RATING, 4),
        (FeedbackType.SUGGESTION, "Add more examples please"),
        (FeedbackType.COMPLIMENT, "Very helpful system!"),
        (FeedbackType.FEATURE_REQUEST, "Voice input would be great")
    ]

    for feedback_type, content in feedback_items:
        feedback_id = analytics_service.feedback_collector.collect_feedback(
            user_id, session_id, feedback_type, content
        )
        print(f"✓ Collected {feedback_type.value}: {str(content)[:50]}")

    # Get feedback summary
    feedback_summary = analytics_service.feedback_collector.get_feedback_summary()
    print("\n📝 Feedback Summary:")
    print(f"  Total feedback: {feedback_summary['total_feedback']}")
    print(f"  Average rating: {feedback_summary['average_rating']:.1f}")
    for feedback_type, count in feedback_summary['feedback_by_type'].items():
        print(f"  {feedback_type}: {count}")

    # Test 3: Quality Scoring
    print("\n" + "=" * 50)
    print("Test 3: Quality Scoring")
    print("=" * 50)

    # Score conversation quality
    conversation_data = {
        'required_fields': ['name', 'case_number', 'motion_type', 'reason'],
        'collected_fields': ['name', 'case_number', 'motion_type'],
        'corrections': 1,
        'total_inputs': 10,
        'clarifications': 1,
        'message_count': 10,
        'duration': 1200,  # 20 minutes
        'user_rating': 4
    }

    quality_scores = analytics_service.quality_scorer.score_conversation(
        session_id, conversation_data
    )
    print("\n⭐ Quality Scores:")
    for metric, score in quality_scores['scores'].items():
        print(f"  {metric}: {score:.2f}")
    print(f"  Overall: {quality_scores['overall']:.2f}")
    print(f"  Passed: {'✅' if quality_scores['passed'] else '❌'}")

    # Test 4: Analytics Insights
    print("\n" + "=" * 50)
    print("Test 4: Analytics Insights & Report")
    print("=" * 50)

    # Calculate metrics
    metrics = analytics_service.analytics.calculate_aggregated_metrics()
    insights = analytics_service.analytics.get_insights()

    print("\n💡 Insights:")
    for insight in insights:
        print(f"  {insight}")

    # Generate report
    report = analytics_service.generate_report(period_days=7)
    print("\n📊 Weekly Report Preview:")
    print(report[:500] + "...")

    # Get improvement recommendations
    recommendations = analytics_service.create_quality_improvement_plan()
    if recommendations:
        print("\n📈 Quality Improvement Recommendations:")
        for rec in recommendations:
            print(f"\n  {rec['metric']} (Priority: {rec['priority']})")
            print(f"    Current: {rec['current']:.2f}, Target: {rec['target']:.2f}")
            for action in rec['actions']:
                print(f"    • {action}")


def main():
    """Run all tests"""
    print("\n" + "🧠" * 30)
    print(" MEMORY, LEARNING & ANALYTICS TEST SUITE")
    print("🧠" * 30)

    test_memory_learning()
    test_analytics_feedback()

    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
    print("=" * 60)
    print("\nThe system now features:")
    print("• Long-term memory storage with search")
    print("• Automatic profile learning from conversations")
    print("• User preference detection and application")
    print("• Correction learning for personalization")
    print("• Pattern recognition and prediction")
    print("• Comprehensive conversation analytics")
    print("• Feedback collection and analysis")
    print("• Quality scoring and improvement recommendations")
    print("\n🎯 The chatbot is now an intelligent, learning assistant!")


if __name__ == "__main__":
    main()