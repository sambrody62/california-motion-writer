"""
Progress indicator service for long-running operations
Provides real-time progress updates for PDF generation, form processing, etc.
"""
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class OperationType(Enum):
    """Types of long-running operations"""
    PDF_GENERATION = "pdf_generation"
    FORM_PROCESSING = "form_processing"
    DOCUMENT_ANALYSIS = "document_analysis"
    DATA_EXTRACTION = "data_extraction"
    FILE_UPLOAD = "file_upload"
    BATCH_OPERATION = "batch_operation"


class ProgressStatus(Enum):
    """Status of an operation"""
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProgressIndicator:
    """Track progress for a single operation"""

    def __init__(self, operation_id: str, operation_type: OperationType, total_steps: int = 100):
        self.operation_id = operation_id
        self.operation_type = operation_type
        self.total_steps = total_steps
        self.current_step = 0
        self.status = ProgressStatus.QUEUED
        self.message = "Initializing..."
        self.started_at = None
        self.completed_at = None
        self.error_message = None
        self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for client consumption"""
        return {
            'operation_id': self.operation_id,
            'type': self.operation_type.value,
            'status': self.status.value,
            'progress': self.get_percentage(),
            'current_step': self.current_step,
            'total_steps': self.total_steps,
            'message': self.message,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration': self.get_duration(),
            'error': self.error_message,
            'metadata': self.metadata
        }

    def get_percentage(self) -> float:
        """Get progress as percentage"""
        if self.total_steps == 0:
            return 100.0 if self.status == ProgressStatus.COMPLETED else 0.0
        return min(100.0, (self.current_step / self.total_steps) * 100)

    def get_duration(self) -> Optional[float]:
        """Get operation duration in seconds"""
        if not self.started_at:
            return None
        end_time = self.completed_at or datetime.utcnow()
        return (end_time - self.started_at).total_seconds()


class ProgressIndicatorService:
    """Service for managing progress indicators across operations"""

    def __init__(self):
        self.operations: Dict[str, ProgressIndicator] = {}
        self.listeners: Dict[str, List[asyncio.Queue]] = {}

    def create_operation(
        self,
        operation_type: OperationType,
        total_steps: int = 100,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Create a new operation with progress tracking"""
        operation_id = str(uuid.uuid4())
        operation = ProgressIndicator(operation_id, operation_type, total_steps)
        operation.metadata = metadata or {}

        self.operations[operation_id] = operation
        self.listeners[operation_id] = []

        logger.info(f"Created operation {operation_id} of type {operation_type.value}")
        return operation_id

    async def start_operation(self, operation_id: str, message: str = "Starting..."):
        """Start an operation"""
        if operation_id not in self.operations:
            logger.warning(f"Operation {operation_id} not found")
            return

        operation = self.operations[operation_id]
        operation.status = ProgressStatus.IN_PROGRESS
        operation.started_at = datetime.utcnow()
        operation.message = message

        await self._notify_listeners(operation_id)
        logger.info(f"Started operation {operation_id}")

    async def update_progress(
        self,
        operation_id: str,
        current_step: int = None,
        message: str = None,
        increment: int = None
    ):
        """Update operation progress"""
        if operation_id not in self.operations:
            logger.warning(f"Operation {operation_id} not found")
            return

        operation = self.operations[operation_id]

        if current_step is not None:
            operation.current_step = min(current_step, operation.total_steps)
        elif increment is not None:
            operation.current_step = min(operation.current_step + increment, operation.total_steps)

        if message:
            operation.message = message

        await self._notify_listeners(operation_id)

    async def complete_operation(
        self,
        operation_id: str,
        message: str = "Completed successfully",
        result: Any = None
    ):
        """Mark operation as completed"""
        if operation_id not in self.operations:
            logger.warning(f"Operation {operation_id} not found")
            return

        operation = self.operations[operation_id]
        operation.status = ProgressStatus.COMPLETED
        operation.current_step = operation.total_steps
        operation.completed_at = datetime.utcnow()
        operation.message = message

        if result:
            operation.metadata['result'] = result

        await self._notify_listeners(operation_id)
        logger.info(f"Completed operation {operation_id}")

    async def fail_operation(self, operation_id: str, error_message: str):
        """Mark operation as failed"""
        if operation_id not in self.operations:
            logger.warning(f"Operation {operation_id} not found")
            return

        operation = self.operations[operation_id]
        operation.status = ProgressStatus.FAILED
        operation.completed_at = datetime.utcnow()
        operation.error_message = error_message
        operation.message = "Operation failed"

        await self._notify_listeners(operation_id)
        logger.error(f"Failed operation {operation_id}: {error_message}")

    async def cancel_operation(self, operation_id: str):
        """Cancel an operation"""
        if operation_id not in self.operations:
            logger.warning(f"Operation {operation_id} not found")
            return

        operation = self.operations[operation_id]
        operation.status = ProgressStatus.CANCELLED
        operation.completed_at = datetime.utcnow()
        operation.message = "Operation cancelled"

        await self._notify_listeners(operation_id)
        logger.info(f"Cancelled operation {operation_id}")

    def get_operation(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get operation status"""
        operation = self.operations.get(operation_id)
        return operation.to_dict() if operation else None

    def get_user_operations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all operations for a user"""
        user_operations = []
        for operation in self.operations.values():
            if operation.metadata.get('user_id') == user_id:
                user_operations.append(operation.to_dict())
        return user_operations

    async def subscribe_to_operation(self, operation_id: str) -> asyncio.Queue:
        """Subscribe to operation progress updates"""
        if operation_id not in self.listeners:
            self.listeners[operation_id] = []

        queue = asyncio.Queue()
        self.listeners[operation_id].append(queue)

        # Send initial state
        if operation_id in self.operations:
            await queue.put(self.operations[operation_id].to_dict())

        return queue

    async def unsubscribe_from_operation(self, operation_id: str, queue: asyncio.Queue):
        """Unsubscribe from operation updates"""
        if operation_id in self.listeners:
            if queue in self.listeners[operation_id]:
                self.listeners[operation_id].remove(queue)

    async def _notify_listeners(self, operation_id: str):
        """Notify all listeners of operation update"""
        if operation_id not in self.listeners:
            return

        operation = self.operations.get(operation_id)
        if not operation:
            return

        update = operation.to_dict()

        # Send update to all listeners
        dead_queues = []
        for queue in self.listeners[operation_id]:
            try:
                await queue.put(update)
            except asyncio.QueueFull:
                # Queue is full, mark for removal
                dead_queues.append(queue)

        # Clean up dead queues
        for queue in dead_queues:
            self.listeners[operation_id].remove(queue)

    def cleanup_completed_operations(self, max_age_seconds: int = 3600):
        """Clean up old completed operations"""
        now = datetime.utcnow()
        to_remove = []

        for operation_id, operation in self.operations.items():
            if operation.status in [ProgressStatus.COMPLETED, ProgressStatus.FAILED, ProgressStatus.CANCELLED]:
                if operation.completed_at:
                    age = (now - operation.completed_at).total_seconds()
                    if age > max_age_seconds:
                        to_remove.append(operation_id)

        for operation_id in to_remove:
            del self.operations[operation_id]
            if operation_id in self.listeners:
                del self.listeners[operation_id]

        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old operations")

    # Context manager for operations
    class OperationContext:
        """Context manager for operations with automatic progress updates"""

        def __init__(self, service, operation_type: OperationType, total_steps: int = 100, metadata: Dict = None):
            self.service = service
            self.operation_type = operation_type
            self.total_steps = total_steps
            self.metadata = metadata
            self.operation_id = None

        async def __aenter__(self):
            self.operation_id = self.service.create_operation(
                self.operation_type,
                self.total_steps,
                self.metadata
            )
            await self.service.start_operation(self.operation_id)
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            if exc_type is None:
                await self.service.complete_operation(self.operation_id)
            else:
                await self.service.fail_operation(
                    self.operation_id,
                    f"{exc_type.__name__}: {exc_val}"
                )

        async def update(self, step: int = None, message: str = None, increment: int = None):
            await self.service.update_progress(
                self.operation_id,
                current_step=step,
                message=message,
                increment=increment
            )

    def track_operation(self, operation_type: OperationType, total_steps: int = 100, metadata: Dict = None):
        """Create a context manager for tracking an operation"""
        return self.OperationContext(self, operation_type, total_steps, metadata)


# Example usage functions
async def track_pdf_generation_example(progress_service: ProgressIndicatorService, user_id: str):
    """Example of tracking PDF generation"""
    async with progress_service.track_operation(
        OperationType.PDF_GENERATION,
        total_steps=5,
        metadata={'user_id': user_id}
    ) as tracker:
        await tracker.update(1, "Loading form templates...")
        await asyncio.sleep(1)

        await tracker.update(2, "Extracting conversation data...")
        await asyncio.sleep(1)

        await tracker.update(3, "Mapping fields to PDF...")
        await asyncio.sleep(1)

        await tracker.update(4, "Generating PDF document...")
        await asyncio.sleep(2)

        await tracker.update(5, "Finalizing and saving...")


async def track_batch_forms_example(progress_service: ProgressIndicatorService, user_id: str, forms: List[str]):
    """Example of tracking batch form processing"""
    total_forms = len(forms)

    async with progress_service.track_operation(
        OperationType.BATCH_OPERATION,
        total_steps=total_forms,
        metadata={'user_id': user_id, 'forms': forms}
    ) as tracker:
        for i, form in enumerate(forms, 1):
            await tracker.update(i, f"Processing form {form} ({i}/{total_forms})...")
            await asyncio.sleep(1)  # Simulate processing


# Singleton instance
progress_service = ProgressIndicatorService()