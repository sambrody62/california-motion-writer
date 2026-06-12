"""
Analytics and feedback service for conversation quality and user satisfaction
Tracks metrics, collects feedback, and generates insights
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from collections import defaultdict, Counter
import statistics

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics tracked"""
    CONVERSATION_LENGTH = "conversation_length"
    COMPLETION_RATE = "completion_rate"
    ERROR_RATE = "error_rate"
    RESPONSE_TIME = "response_time"
    USER_SATISFACTION = "user_satisfaction"
    FORM_ACCURACY = "form_accuracy"
    SESSION_DURATION = "session_duration"
    CLARIFICATION_COUNT = "clarification_count"


class FeedbackType(Enum):
    """Types of user feedback"""
    RATING = "rating"
    SUGGESTION = "suggestion"
    COMPLAINT = "complaint"
    COMPLIMENT = "compliment"
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"


class QualityMetric(Enum):
    """Quality scoring metrics"""
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    CLARITY = "clarity"
    EFFICIENCY = "efficiency"
    USER_SATISFACTION = "user_satisfaction"


class ConversationAnalytics:
    """Analytics for conversation performance"""

    def __init__(self):
        self.sessions = defaultdict(dict)
        self.metrics = defaultdict(list)
        self.aggregated_metrics = {}

    def start_session(self, session_id: str, user_id: str):
        """Start tracking a conversation session"""
        self.sessions[session_id] = {
            'user_id': user_id,
            'start_time': datetime.utcnow(),
            'messages': [],
            'errors': 0,
            'clarifications': 0,
            'forms_generated': 0,
            'completed': False
        }

    def track_message(
        self,
        session_id: str,
        message_type: str,
        content: str,
        response_time: float = None
    ):
        """Track a message in the conversation"""
        if session_id not in self.sessions:
            return

        session = self.sessions[session_id]
        session['messages'].append({
            'type': message_type,
            'content_length': len(content),
            'timestamp': datetime.utcnow().isoformat(),
            'response_time': response_time
        })

        # Track response time metric
        if response_time:
            self.metrics[MetricType.RESPONSE_TIME].append(response_time)

    def track_error(self, session_id: str, error_type: str, error_message: str):
        """Track an error in the conversation"""
        if session_id not in self.sessions:
            return

        self.sessions[session_id]['errors'] += 1
        logger.error(f"Session {session_id} error: {error_type} - {error_message}")

    def track_clarification(self, session_id: str):
        """Track when clarification is needed"""
        if session_id not in self.sessions:
            return

        self.sessions[session_id]['clarifications'] += 1

    def track_form_generation(self, session_id: str, form_type: str, success: bool):
        """Track form generation"""
        if session_id not in self.sessions:
            return

        if success:
            self.sessions[session_id]['forms_generated'] += 1

    def end_session(self, session_id: str, completed: bool = True):
        """End a conversation session and calculate metrics"""
        if session_id not in self.sessions:
            return

        session = self.sessions[session_id]
        session['completed'] = completed
        session['end_time'] = datetime.utcnow()

        # Calculate session duration
        duration = (session['end_time'] - session['start_time']).total_seconds()
        session['duration'] = duration

        # Store metrics
        self.metrics[MetricType.SESSION_DURATION].append(duration)
        self.metrics[MetricType.CONVERSATION_LENGTH].append(len(session['messages']))
        self.metrics[MetricType.CLARIFICATION_COUNT].append(session['clarifications'])
        self.metrics[MetricType.COMPLETION_RATE].append(1 if completed else 0)
        self.metrics[MetricType.ERROR_RATE].append(
            session['errors'] / max(1, len(session['messages']))
        )

    def calculate_aggregated_metrics(self) -> Dict[str, Any]:
        """Calculate aggregated metrics"""
        aggregated = {}

        for metric_type, values in self.metrics.items():
            if values:
                aggregated[metric_type.value] = {
                    'mean': statistics.mean(values),
                    'median': statistics.median(values),
                    'min': min(values),
                    'max': max(values),
                    'count': len(values)
                }

                if len(values) > 1:
                    aggregated[metric_type.value]['std_dev'] = statistics.stdev(values)

        self.aggregated_metrics = aggregated
        return aggregated

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary for a specific session"""
        if session_id not in self.sessions:
            return {}

        session = self.sessions[session_id]
        return {
            'duration': session.get('duration', 0),
            'message_count': len(session['messages']),
            'error_count': session['errors'],
            'clarification_count': session['clarifications'],
            'forms_generated': session['forms_generated'],
            'completed': session['completed'],
            'efficiency_score': self._calculate_efficiency_score(session)
        }

    def _calculate_efficiency_score(self, session: Dict) -> float:
        """Calculate efficiency score for a session"""
        if not session.get('duration') or not session['messages']:
            return 0.0

        # Factors for efficiency
        message_efficiency = min(1.0, 20 / len(session['messages']))  # Fewer messages is better
        time_efficiency = min(1.0, 1800 / session['duration'])  # Under 30 minutes is good
        error_penalty = max(0, 1 - (session['errors'] * 0.2))  # Deduct for errors
        clarification_penalty = max(0, 1 - (session['clarifications'] * 0.1))  # Deduct for clarifications

        # Weighted average
        score = (
            message_efficiency * 0.3 +
            time_efficiency * 0.3 +
            error_penalty * 0.2 +
            clarification_penalty * 0.2
        )

        return round(score, 2)

    def get_insights(self) -> List[str]:
        """Generate insights from analytics"""
        insights = []
        metrics = self.calculate_aggregated_metrics()

        # Response time insights
        if MetricType.RESPONSE_TIME.value in metrics:
            avg_response = metrics[MetricType.RESPONSE_TIME.value]['mean']
            if avg_response > 3:
                insights.append(f"⚠️ Average response time ({avg_response:.1f}s) exceeds target (3s)")
            else:
                insights.append(f"✅ Good response time: {avg_response:.1f}s average")

        # Completion rate insights
        if MetricType.COMPLETION_RATE.value in metrics:
            completion = metrics[MetricType.COMPLETION_RATE.value]['mean'] * 100
            if completion < 80:
                insights.append(f"⚠️ Low completion rate: {completion:.0f}%")
            else:
                insights.append(f"✅ High completion rate: {completion:.0f}%")

        # Error rate insights
        if MetricType.ERROR_RATE.value in metrics:
            error_rate = metrics[MetricType.ERROR_RATE.value]['mean'] * 100
            if error_rate > 5:
                insights.append(f"⚠️ High error rate: {error_rate:.1f}%")
            else:
                insights.append(f"✅ Low error rate: {error_rate:.1f}%")

        # Session duration insights
        if MetricType.SESSION_DURATION.value in metrics:
            avg_duration = metrics[MetricType.SESSION_DURATION.value]['mean'] / 60
            if avg_duration > 45:
                insights.append(f"⚠️ Long sessions: {avg_duration:.0f} minutes average")
            else:
                insights.append(f"✅ Efficient sessions: {avg_duration:.0f} minutes average")

        return insights


class FeedbackCollector:
    """Collect and analyze user feedback"""

    def __init__(self):
        self.feedback_items = []
        self.ratings = defaultdict(list)
        self.suggestions = defaultdict(list)

    def collect_feedback(
        self,
        user_id: str,
        session_id: str,
        feedback_type: FeedbackType,
        content: Any,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Collect user feedback"""
        feedback_id = f"fb_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{user_id[:8]}"

        feedback_item = {
            'id': feedback_id,
            'user_id': user_id,
            'session_id': session_id,
            'type': feedback_type.value,
            'content': content,
            'metadata': metadata or {},
            'timestamp': datetime.utcnow().isoformat()
        }

        self.feedback_items.append(feedback_item)

        # Process specific feedback types
        if feedback_type == FeedbackType.RATING:
            self.ratings[user_id].append(content)
        elif feedback_type == FeedbackType.SUGGESTION:
            self.suggestions[user_id].append(content)

        logger.info(f"Collected {feedback_type.value} feedback from user {user_id}")
        return feedback_id

    def get_average_rating(self, user_id: str = None) -> float:
        """Get average rating"""
        if user_id:
            ratings = self.ratings.get(user_id, [])
        else:
            # All ratings
            ratings = []
            for user_ratings in self.ratings.values():
                ratings.extend(user_ratings)

        if ratings:
            return statistics.mean(ratings)
        return 0.0

    def get_feedback_summary(self) -> Dict[str, Any]:
        """Get summary of all feedback"""
        feedback_by_type = defaultdict(int)
        for item in self.feedback_items:
            feedback_by_type[item['type']] += 1

        # Calculate sentiment distribution for ratings
        rating_distribution = defaultdict(int)
        all_ratings = []
        for user_ratings in self.ratings.values():
            all_ratings.extend(user_ratings)

        for rating in all_ratings:
            if rating >= 4:
                rating_distribution['positive'] += 1
            elif rating >= 3:
                rating_distribution['neutral'] += 1
            else:
                rating_distribution['negative'] += 1

        return {
            'total_feedback': len(self.feedback_items),
            'feedback_by_type': dict(feedback_by_type),
            'average_rating': self.get_average_rating(),
            'rating_distribution': dict(rating_distribution),
            'total_suggestions': sum(len(s) for s in self.suggestions.values()),
            'recent_feedback': self.feedback_items[-5:] if self.feedback_items else []
        }

    def get_common_themes(self) -> List[Tuple[str, int]]:
        """Extract common themes from feedback"""
        # Simple keyword extraction (would use NLP in production)
        keywords = []

        for item in self.feedback_items:
            if item['type'] in ['suggestion', 'complaint', 'feature_request']:
                content = str(item['content']).lower()
                # Extract potential keywords
                words = content.split()
                keywords.extend([
                    word for word in words
                    if len(word) > 4 and word not in ['would', 'could', 'should', 'please']
                ])

        # Count frequencies
        theme_counts = Counter(keywords)
        return theme_counts.most_common(10)


class QualityScorer:
    """Score conversation and document quality"""

    def __init__(self):
        self.quality_scores = defaultdict(list)
        self.quality_thresholds = {
            QualityMetric.COMPLETENESS: 0.8,
            QualityMetric.ACCURACY: 0.9,
            QualityMetric.CLARITY: 0.7,
            QualityMetric.EFFICIENCY: 0.7,
            QualityMetric.USER_SATISFACTION: 0.8
        }

    def score_conversation(
        self,
        session_id: str,
        conversation_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """Score conversation quality"""
        scores = {}

        # Completeness score
        required_fields = conversation_data.get('required_fields', [])
        collected_fields = conversation_data.get('collected_fields', [])
        if required_fields:
            completeness = len(collected_fields) / len(required_fields)
        else:
            completeness = 1.0
        scores[QualityMetric.COMPLETENESS] = completeness

        # Accuracy score (based on corrections needed)
        corrections = conversation_data.get('corrections', 0)
        total_inputs = conversation_data.get('total_inputs', 1)
        accuracy = max(0, 1 - (corrections / total_inputs))
        scores[QualityMetric.ACCURACY] = accuracy

        # Clarity score (based on clarifications needed)
        clarifications = conversation_data.get('clarifications', 0)
        messages = conversation_data.get('message_count', 1)
        clarity = max(0, 1 - (clarifications / messages))
        scores[QualityMetric.CLARITY] = clarity

        # Efficiency score
        duration = conversation_data.get('duration', 1800)  # seconds
        target_duration = 1800  # 30 minutes target
        efficiency = min(1.0, target_duration / max(1, duration))
        scores[QualityMetric.EFFICIENCY] = efficiency

        # User satisfaction (if available)
        if 'user_rating' in conversation_data:
            satisfaction = conversation_data['user_rating'] / 5.0
            scores[QualityMetric.USER_SATISFACTION] = satisfaction

        # Store scores
        for metric, score in scores.items():
            self.quality_scores[metric].append(score)

        # Calculate overall quality
        overall = statistics.mean(scores.values())

        return {
            'scores': {k.value: v for k, v in scores.items()},
            'overall': overall,
            'passed': all(
                scores.get(metric, 0) >= threshold
                for metric, threshold in self.quality_thresholds.items()
            )
        }

    def score_document(
        self,
        document_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """Score document quality"""
        scores = {}

        # Completeness of required fields
        required = document_data.get('required_fields', [])
        filled = document_data.get('filled_fields', [])
        completeness = len(filled) / len(required) if required else 1.0
        scores['field_completeness'] = completeness

        # Validation passing
        validation_errors = document_data.get('validation_errors', [])
        validation_score = max(0, 1 - (len(validation_errors) * 0.1))
        scores['validation'] = validation_score

        # Formatting quality
        formatting_issues = document_data.get('formatting_issues', 0)
        formatting_score = max(0, 1 - (formatting_issues * 0.05))
        scores['formatting'] = formatting_score

        # Overall document quality
        overall = statistics.mean(scores.values())
        scores['overall'] = overall

        return scores

    def get_quality_trends(self) -> Dict[str, Any]:
        """Get quality score trends"""
        trends = {}

        for metric, scores in self.quality_scores.items():
            if len(scores) > 1:
                # Calculate trend
                recent_avg = statistics.mean(scores[-10:])
                older_avg = statistics.mean(scores[:-10]) if len(scores) > 10 else scores[0]

                trend = "improving" if recent_avg > older_avg else "declining" if recent_avg < older_avg else "stable"

                trends[metric.value] = {
                    'current_average': recent_avg,
                    'trend': trend,
                    'threshold': self.quality_thresholds[metric],
                    'meets_threshold': recent_avg >= self.quality_thresholds[metric]
                }

        return trends


class AnalyticsFeedbackService:
    """Main service for analytics and feedback"""

    def __init__(self):
        self.analytics = ConversationAnalytics()
        self.feedback_collector = FeedbackCollector()
        self.quality_scorer = QualityScorer()

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        return {
            'metrics': self.analytics.calculate_aggregated_metrics(),
            'insights': self.analytics.get_insights(),
            'feedback_summary': self.feedback_collector.get_feedback_summary(),
            'quality_trends': self.quality_scorer.get_quality_trends(),
            'common_themes': self.feedback_collector.get_common_themes(),
            'average_rating': self.feedback_collector.get_average_rating()
        }

    def generate_report(self, period_days: int = 30) -> str:
        """Generate analytics report"""
        data = self.get_dashboard_data()

        report = f"""
📊 **Analytics Report - Last {period_days} Days**

## Key Metrics
- Average Session Duration: {data['metrics'].get('session_duration', {}).get('mean', 0) / 60:.1f} minutes
- Completion Rate: {data['metrics'].get('completion_rate', {}).get('mean', 0) * 100:.1f}%
- Average Response Time: {data['metrics'].get('response_time', {}).get('mean', 0):.2f}s
- Error Rate: {data['metrics'].get('error_rate', {}).get('mean', 0) * 100:.2f}%

## User Satisfaction
- Average Rating: {data['average_rating']:.1f}/5.0
- Total Feedback Items: {data['feedback_summary']['total_feedback']}

## Quality Trends
"""
        for metric, trend_data in data['quality_trends'].items():
            status = "✅" if trend_data['meets_threshold'] else "⚠️"
            report += f"- {metric}: {trend_data['current_average']:.2f} ({trend_data['trend']}) {status}\n"

        report += "\n## Insights\n"
        for insight in data['insights']:
            report += f"- {insight}\n"

        report += "\n## Common User Themes\n"
        for theme, count in data['common_themes'][:5]:
            report += f"- {theme}: mentioned {count} times\n"

        return report

    def create_quality_improvement_plan(self) -> List[Dict[str, Any]]:
        """Create recommendations for quality improvement"""
        recommendations = []
        trends = self.quality_scorer.get_quality_trends()

        for metric, data in trends.items():
            if not data['meets_threshold']:
                recommendation = {
                    'metric': metric,
                    'current': data['current_average'],
                    'target': data['threshold'],
                    'priority': 'high' if data['trend'] == 'declining' else 'medium'
                }

                # Add specific recommendations
                if metric == 'completeness':
                    recommendation['actions'] = [
                        "Improve question flow to capture all required fields",
                        "Add validation to prevent incomplete submissions",
                        "Provide clearer guidance on required information"
                    ]
                elif metric == 'accuracy':
                    recommendation['actions'] = [
                        "Enhance entity extraction accuracy",
                        "Add confirmation steps for critical data",
                        "Improve error handling and recovery"
                    ]
                elif metric == 'efficiency':
                    recommendation['actions'] = [
                        "Optimize conversation flow to reduce steps",
                        "Implement smart defaults and auto-fill",
                        "Add conversation templates for common scenarios"
                    ]

                recommendations.append(recommendation)

        return recommendations


# Singleton instance
analytics_service = AnalyticsFeedbackService()