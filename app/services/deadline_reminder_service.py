"""
Deadline reminder service for court dates and filing deadlines
Calculates important dates and sends reminders
"""
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional
from enum import Enum
import logging
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

logger = logging.getLogger(__name__)


class DeadlineType(Enum):
    """Types of court deadlines"""
    HEARING_DATE = "hearing_date"
    SERVICE_DEADLINE = "service_deadline"
    RESPONSE_DEADLINE = "response_deadline"
    PROOF_OF_SERVICE = "proof_of_service"
    DISCOVERY_CUTOFF = "discovery_cutoff"
    MOTION_FILING = "motion_filing"
    EXPARTE_NOTICE = "exparte_notice"
    FINANCIAL_DISCLOSURE = "financial_disclosure"


class ReminderFrequency(Enum):
    """Reminder frequency options"""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    CUSTOM = "custom"


class Deadline:
    """Individual deadline with calculated dates"""

    def __init__(
        self,
        deadline_type: DeadlineType,
        base_date: date,
        deadline_date: date,
        description: str
    ):
        self.deadline_type = deadline_type
        self.base_date = base_date
        self.deadline_date = deadline_date
        self.description = description
        self.reminders = []
        self.completed = False

    def days_until(self) -> int:
        """Calculate days until deadline"""
        today = date.today()
        delta = self.deadline_date - today
        return delta.days

    def is_overdue(self) -> bool:
        """Check if deadline is past"""
        return date.today() > self.deadline_date

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'type': self.deadline_type.value,
            'base_date': self.base_date.isoformat(),
            'deadline_date': self.deadline_date.isoformat(),
            'description': self.description,
            'days_until': self.days_until(),
            'is_overdue': self.is_overdue(),
            'completed': self.completed,
            'reminders': self.reminders
        }


class DeadlineReminderService:
    """Service for managing court deadlines and reminders"""

    def __init__(self):
        self.deadlines: Dict[str, List[Deadline]] = {}
        self.reminder_tasks: Dict[str, asyncio.Task] = {}

    def calculate_court_days(self, start_date: date, days: int, backwards: bool = True) -> date:
        """
        Calculate date considering only court days (excluding weekends and holidays)

        Args:
            start_date: Starting date
            days: Number of court days
            backwards: Count backwards from start_date if True

        Returns:
            Calculated date
        """
        # California court holidays (simplified - add more as needed)
        holidays = [
            date(2025, 1, 1),   # New Year's Day
            date(2025, 1, 20),  # MLK Day
            date(2025, 2, 17),  # Presidents Day
            date(2025, 5, 26),  # Memorial Day
            date(2025, 7, 4),   # Independence Day
            date(2025, 9, 1),   # Labor Day
            date(2025, 11, 27), # Thanksgiving
            date(2025, 11, 28), # Day after Thanksgiving
            date(2025, 12, 25), # Christmas
        ]

        current_date = start_date
        days_counted = 0
        direction = -1 if backwards else 1

        while days_counted < days:
            current_date += timedelta(days=direction)

            # Skip weekends
            if current_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                continue

            # Skip holidays
            if current_date in holidays:
                continue

            days_counted += 1

        return current_date

    def calculate_deadlines(self, hearing_date: date, motion_type: str = "RFO") -> List[Deadline]:
        """
        Calculate all deadlines based on hearing date

        Args:
            hearing_date: The court hearing date
            motion_type: Type of motion (RFO, Ex Parte, etc.)

        Returns:
            List of calculated deadlines
        """
        deadlines = []

        if motion_type == "RFO":
            # Request for Order deadlines
            deadlines.append(Deadline(
                DeadlineType.SERVICE_DEADLINE,
                hearing_date,
                self.calculate_court_days(hearing_date, 16, backwards=True),
                "Serve Request for Order on other party (16 court days before hearing)"
            ))

            deadlines.append(Deadline(
                DeadlineType.RESPONSE_DEADLINE,
                hearing_date,
                self.calculate_court_days(hearing_date, 9, backwards=True),
                "File Responsive Declaration (9 court days before hearing)"
            ))

            deadlines.append(Deadline(
                DeadlineType.PROOF_OF_SERVICE,
                hearing_date,
                self.calculate_court_days(hearing_date, 5, backwards=True),
                "File Proof of Service (5 court days before hearing)"
            ))

            deadlines.append(Deadline(
                DeadlineType.FINANCIAL_DISCLOSURE,
                hearing_date,
                hearing_date - timedelta(days=90),
                "Update Income & Expense Declaration if older than 3 months"
            ))

        elif motion_type == "Ex Parte":
            # Ex Parte deadlines
            deadlines.append(Deadline(
                DeadlineType.EXPARTE_NOTICE,
                hearing_date,
                self.calculate_court_days(hearing_date, 1, backwards=True),
                "Give notice to other party by 10 AM (unless true emergency)"
            ))

            deadlines.append(Deadline(
                DeadlineType.MOTION_FILING,
                hearing_date,
                hearing_date,
                "File Ex Parte Application on morning of hearing"
            ))

        elif motion_type == "Response":
            # Response to RFO deadlines
            deadlines.append(Deadline(
                DeadlineType.RESPONSE_DEADLINE,
                hearing_date,
                self.calculate_court_days(hearing_date, 9, backwards=True),
                "File Response to Request for Order (9 court days before hearing)"
            ))

            deadlines.append(Deadline(
                DeadlineType.SERVICE_DEADLINE,
                hearing_date,
                self.calculate_court_days(hearing_date, 9, backwards=True),
                "Serve Response on other party (same day as filing)"
            ))

            deadlines.append(Deadline(
                DeadlineType.PROOF_OF_SERVICE,
                hearing_date,
                self.calculate_court_days(hearing_date, 5, backwards=True),
                "File Proof of Service (5 court days before hearing)"
            ))

        # Add hearing date itself
        deadlines.append(Deadline(
            DeadlineType.HEARING_DATE,
            hearing_date,
            hearing_date,
            "Court hearing - arrive 30 minutes early"
        ))

        # Sort by date
        deadlines.sort(key=lambda x: x.deadline_date)

        return deadlines

    def add_user_deadlines(self, user_id: str, hearing_date: date, motion_type: str = "RFO"):
        """Add deadlines for a user"""
        deadlines = self.calculate_deadlines(hearing_date, motion_type)
        self.deadlines[user_id] = deadlines

        # Set up reminders
        for deadline in deadlines:
            self._schedule_reminders(user_id, deadline)

        logger.info(f"Added {len(deadlines)} deadlines for user {user_id}")

    def _schedule_reminders(self, user_id: str, deadline: Deadline):
        """Schedule reminders for a deadline"""
        days_until = deadline.days_until()

        # Set reminder schedule based on urgency
        if days_until > 14:
            # Reminder 2 weeks before
            deadline.reminders.append(days_until - 14)
            # Reminder 1 week before
            deadline.reminders.append(days_until - 7)
        elif days_until > 7:
            # Reminder 1 week before
            deadline.reminders.append(days_until - 7)
            # Reminder 3 days before
            deadline.reminders.append(3)
        elif days_until > 3:
            # Reminder 3 days before
            deadline.reminders.append(3)
            # Reminder 1 day before
            deadline.reminders.append(1)
        elif days_until >= 0:
            # Reminder today
            deadline.reminders.append(0)

    def get_user_deadlines(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all deadlines for a user"""
        if user_id not in self.deadlines:
            return []

        return [d.to_dict() for d in self.deadlines[user_id]]

    def get_upcoming_deadlines(self, user_id: str, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Get deadlines coming up in the next N days"""
        if user_id not in self.deadlines:
            return []

        upcoming = []
        for deadline in self.deadlines[user_id]:
            if 0 <= deadline.days_until() <= days_ahead and not deadline.completed:
                upcoming.append(deadline.to_dict())

        return upcoming

    def get_overdue_deadlines(self, user_id: str) -> List[Dict[str, Any]]:
        """Get overdue deadlines"""
        if user_id not in self.deadlines:
            return []

        overdue = []
        for deadline in self.deadlines[user_id]:
            if deadline.is_overdue() and not deadline.completed:
                overdue.append(deadline.to_dict())

        return overdue

    def mark_deadline_complete(self, user_id: str, deadline_type: DeadlineType) -> bool:
        """Mark a deadline as completed"""
        if user_id not in self.deadlines:
            return False

        for deadline in self.deadlines[user_id]:
            if deadline.deadline_type == deadline_type:
                deadline.completed = True
                logger.info(f"Marked {deadline_type.value} as complete for user {user_id}")
                return True

        return False

    def generate_deadline_summary(self, user_id: str) -> str:
        """Generate a text summary of deadlines"""
        if user_id not in self.deadlines:
            return "No deadlines set."

        deadlines = self.deadlines[user_id]
        active_deadlines = [d for d in deadlines if not d.completed]

        if not active_deadlines:
            return "All deadlines completed!"

        summary = "📅 **Your Court Deadlines:**\n\n"

        # Group by urgency
        urgent = []
        upcoming = []
        future = []

        for deadline in active_deadlines:
            days = deadline.days_until()

            if deadline.is_overdue():
                urgent.append(f"⚠️ **OVERDUE**: {deadline.description}")
            elif days <= 3:
                urgent.append(f"🚨 **{days} days**: {deadline.description}")
            elif days <= 7:
                upcoming.append(f"⏰ **{days} days**: {deadline.description}")
            else:
                future.append(f"📆 **{days} days**: {deadline.description}")

        if urgent:
            summary += "**Urgent Action Required:**\n"
            for item in urgent:
                summary += f"• {item}\n"
            summary += "\n"

        if upcoming:
            summary += "**Coming Up This Week:**\n"
            for item in upcoming:
                summary += f"• {item}\n"
            summary += "\n"

        if future:
            summary += "**Future Deadlines:**\n"
            for item in future:
                summary += f"• {item}\n"

        return summary

    def calculate_service_methods(self, service_deadline: date) -> Dict[str, date]:
        """Calculate deadlines for different service methods"""
        today = date.today()
        days_available = (service_deadline - today).days

        methods = {}

        # Personal service - can be done up to deadline
        methods['personal'] = {
            'method': 'Personal Service',
            'deadline': service_deadline,
            'feasible': days_available >= 0,
            'description': 'Hand delivery by someone over 18 (not you)'
        }

        # Mail service - needs 5 extra days
        mail_deadline = service_deadline - timedelta(days=5)
        methods['mail'] = {
            'method': 'Service by Mail',
            'deadline': mail_deadline,
            'feasible': today <= mail_deadline,
            'description': 'Mail with 5 extra days for delivery'
        }

        # Electronic service - if agreed
        methods['electronic'] = {
            'method': 'Electronic Service',
            'deadline': service_deadline,
            'feasible': days_available >= 0,
            'description': 'Email/e-filing if parties agreed'
        }

        return methods

    async def send_reminder(self, user_id: str, deadline: Deadline):
        """Send a reminder for a deadline (placeholder for notification system)"""
        # This would integrate with your notification system
        reminder_text = f"Court deadline reminder: {deadline.description}"
        days_until = deadline.days_until()

        if days_until == 0:
            reminder_text = f"🚨 TODAY: {deadline.description}"
        elif days_until == 1:
            reminder_text = f"⏰ TOMORROW: {deadline.description}"
        else:
            reminder_text = f"📅 In {days_until} days: {deadline.description}"

        logger.info(f"Reminder for user {user_id}: {reminder_text}")

        # Here you would send actual notification
        # await notification_service.send(user_id, reminder_text)

    def get_deadline_checklist(self, deadline_type: DeadlineType) -> List[str]:
        """Get checklist for a specific deadline type"""
        checklists = {
            DeadlineType.SERVICE_DEADLINE: [
                "Complete all forms",
                "Make required copies",
                "Choose service method",
                "Find process server or adult to serve",
                "Prepare service instructions"
            ],
            DeadlineType.RESPONSE_DEADLINE: [
                "Review the Request for Order",
                "Complete Response form (FL-320)",
                "Prepare Income & Expense Declaration if needed",
                "Write your declaration",
                "Make copies for filing and service"
            ],
            DeadlineType.PROOF_OF_SERVICE: [
                "Get completed Proof of Service from server",
                "Review for accuracy and completeness",
                "Make copies",
                "File with court clerk",
                "Keep copy for your records"
            ],
            DeadlineType.HEARING_DATE: [
                "Review all documents",
                "Prepare what you'll say (3 minutes typical)",
                "Organize exhibits in order",
                "Plan arrival 30 minutes early",
                "Bring copies of everything",
                "Arrange childcare if needed"
            ]
        }

        return checklists.get(deadline_type, [])


# Singleton instance
deadline_service = DeadlineReminderService()