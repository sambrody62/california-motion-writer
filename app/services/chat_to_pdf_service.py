"""
Service to connect chat conversation data to PDF generation
"""
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.chat import ChatSession, ChatMessage, ChatSessionState
from app.models.motion import Motion, MotionType
from app.models.user import User, Profile
from app.services.form_field_mapper import form_mapper
from app.services.pdf_service import PDFService
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)

class ChatToPDFService:
    """Orchestrates the flow from chat conversation to PDF generation"""

    def __init__(self):
        self.pdf_service = PDFService()
        self.form_mapper = form_mapper

    async def prepare_motion_from_chat(
        self,
        db: AsyncSession,
        session_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Prepare motion data from chat conversation

        Args:
            db: Database session
            session_id: Chat session ID
            user_id: User ID

        Returns:
            Motion preparation result
        """
        try:
            # Get chat session with messages
            stmt = select(ChatSession).where(ChatSession.id == session_id)
            result = await db.execute(stmt)
            chat_session = result.scalar_one_or_none()

            if not chat_session:
                return {
                    "success": False,
                    "error": "Chat session not found"
                }

            # Get user profile
            stmt_profile = select(Profile).where(Profile.user_id == user_id)
            result_profile = await db.execute(stmt_profile)
            profile = result_profile.scalar_one_or_none()

            if not profile:
                return {
                    "success": False,
                    "error": "User profile not found. Please complete your profile first."
                }

            # Extract conversation data
            conversation_data = self._extract_conversation_data(chat_session)

            # Determine motion type
            motion_type = self._determine_motion_type(conversation_data, chat_session)

            # Determine required forms
            required_forms = self._get_required_forms(motion_type, conversation_data)

            # Map to form fields for each required form
            form_data = {}
            for form_type in required_forms:
                mapped_fields = self.form_mapper.map_conversation_to_form(
                    form_type,
                    conversation_data,
                    self._profile_to_dict(profile)
                )
                form_data[form_type] = mapped_fields

            # Validate completeness
            validation_results = {}
            missing_fields = []
            for form_type, fields in form_data.items():
                is_valid, missing = self.form_mapper.validate_required_fields(
                    form_type, fields
                )
                validation_results[form_type] = is_valid
                if missing:
                    missing_fields.extend(missing)

            # Create motion record
            motion = await self._create_motion_record(
                db, user_id, motion_type, conversation_data, form_data
            )

            # Update chat session with motion reference
            chat_session.motion_id = motion.id
            chat_session.current_state = ChatSessionState.PDF_GENERATION
            await db.commit()

            return {
                "success": True,
                "motion_id": str(motion.id),
                "motion_type": motion_type,
                "required_forms": required_forms,
                "form_data": form_data,
                "validation": validation_results,
                "missing_fields": missing_fields,
                "ready_for_pdf": all(validation_results.values())
            }

        except Exception as e:
            logger.error(f"Error preparing motion from chat: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _extract_conversation_data(self, chat_session: ChatSession) -> Dict[str, Any]:
        """Extract structured data from chat session"""
        data = chat_session.context.copy() if chat_session.context else {}

        # Add session metadata
        data["chat_session_id"] = str(chat_session.id)
        data["session_intent"] = chat_session.intent
        data["motion_type_detected"] = chat_session.motion_type_detected

        # Extract from messages if needed
        if hasattr(chat_session, 'messages'):
            for msg in chat_session.messages:
                if msg.entities:
                    data.update(msg.entities)

        return data

    def _determine_motion_type(
        self,
        conversation_data: Dict[str, Any],
        chat_session: ChatSession
    ) -> str:
        """Determine the type of motion from conversation"""

        # Priority order for motion type detection
        if chat_session.motion_type_detected:
            return chat_session.motion_type_detected

        motion_type = conversation_data.get("motion_type")
        if motion_type:
            return motion_type

        # Infer from intent
        intent = chat_session.intent
        if intent == "REPORT_VIOLATION":
            return "violation"
        elif intent == "MODIFY_ORDER":
            if "custody" in str(conversation_data):
                return "custody_modification"
            elif "support" in str(conversation_data):
                return "support_modification"
        elif intent == "FILE_MOTION":
            return "rfo"  # Default to Request for Order
        elif intent == "RESPOND_MOTION":
            return "response"

        return "rfo"  # Default

    def _get_required_forms(
        self,
        motion_type: str,
        conversation_data: Dict[str, Any]
    ) -> List[str]:
        """Determine which forms are needed based on motion type"""

        form_sets = {
            "rfo": ["FL-300", "MC-030"],
            "response": ["FL-320", "MC-030"],
            "custody_modification": ["FL-300", "FL-311", "MC-030"],
            "support_modification": ["FL-300", "FL-150", "MC-030"],
            "violation": ["FL-300", "MC-030"],
            "emergency": ["FL-300", "MC-030"]
        }

        forms = form_sets.get(motion_type, ["FL-300", "MC-030"])

        # Add additional forms based on specifics
        if conversation_data.get("is_emergency"):
            forms.append("FL-301")  # Emergency order form

        if conversation_data.get("children_info"):
            if "FL-311" not in forms:
                forms.append("FL-311")  # Child custody form

        return list(set(forms))  # Remove duplicates

    def _profile_to_dict(self, profile: Profile) -> Dict[str, Any]:
        """Convert profile object to dictionary"""
        return {
            "party_name": profile.party_name,
            "other_party_name": profile.other_party_name,
            "case_number": profile.case_number,
            "county": profile.county,
            "court_branch": profile.court_branch,
            "department": profile.department,
            "is_petitioner": profile.is_petitioner,
            "party_address": profile.party_address,
            "party_phone": profile.party_phone,
            "other_party_address": profile.other_party_address,
            "children_info": profile.children_info
        }

    async def _create_motion_record(
        self,
        db: AsyncSession,
        user_id: str,
        motion_type: str,
        conversation_data: Dict[str, Any],
        form_data: Dict[str, Any]
    ) -> Motion:
        """Create a motion record in the database"""

        motion = Motion(
            user_id=user_id,
            motion_type=MotionType.RFO if motion_type == "rfo" else MotionType.RESPONSE,
            status="draft",
            title=f"{motion_type.replace('_', ' ').title()} - {datetime.utcnow().strftime('%Y-%m-%d')}",
            data={
                "conversation_data": conversation_data,
                "form_data": form_data,
                "created_from": "chat"
            }
        )
        db.add(motion)
        await db.commit()

        return motion

    async def generate_pdf_from_motion(
        self,
        db: AsyncSession,
        motion_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Generate PDF documents from motion data

        Args:
            db: Database session
            motion_id: Motion ID
            user_id: User ID

        Returns:
            PDF generation result
        """
        try:
            # Get motion record
            stmt = select(Motion).where(
                Motion.id == motion_id,
                Motion.user_id == user_id
            )
            result = await db.execute(stmt)
            motion = result.scalar_one_or_none()

            if not motion:
                return {
                    "success": False,
                    "error": "Motion not found"
                }

            form_data = motion.data.get("form_data", {})
            if not form_data:
                return {
                    "success": False,
                    "error": "No form data available"
                }

            # Generate PDFs for each form
            generated_pdfs = []
            errors = []

            for form_type, fields in form_data.items():
                try:
                    # Generate individual PDF
                    pdf_result = await self.pdf_service.fill_form(
                        form_type,
                        fields
                    )

                    if pdf_result["success"]:
                        generated_pdfs.append({
                            "form_type": form_type,
                            "file_path": pdf_result["file_path"],
                            "file_name": pdf_result["file_name"]
                        })
                    else:
                        errors.append(f"{form_type}: {pdf_result.get('error', 'Unknown error')}")

                except Exception as e:
                    logger.error(f"Error generating PDF for {form_type}: {e}")
                    errors.append(f"{form_type}: {str(e)}")

            # Generate combined packet if multiple forms
            packet_path = None
            if len(generated_pdfs) > 1:
                try:
                    packet_result = await self.pdf_service.create_packet(
                        [pdf["file_path"] for pdf in generated_pdfs],
                        motion_id
                    )
                    if packet_result["success"]:
                        packet_path = packet_result["packet_path"]
                except Exception as e:
                    logger.error(f"Error creating packet: {e}")

            # Update motion status
            motion.status = "completed" if not errors else "draft"
            motion.data["generated_pdfs"] = generated_pdfs
            motion.data["packet_path"] = packet_path
            motion.data["generation_errors"] = errors
            await db.commit()

            return {
                "success": len(errors) == 0,
                "motion_id": str(motion.id),
                "generated_pdfs": generated_pdfs,
                "packet_path": packet_path,
                "errors": errors,
                "status": motion.status.value
            }

        except Exception as e:
            logger.error(f"Error generating PDFs: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_missing_information(
        self,
        db: AsyncSession,
        session_id: str
    ) -> List[Dict[str, str]]:
        """
        Identify missing information needed for forms

        Args:
            db: Database session
            session_id: Chat session ID

        Returns:
            List of missing fields with questions
        """
        try:
            # Get chat session
            stmt = select(ChatSession).where(ChatSession.id == session_id)
            result = await db.execute(stmt)
            chat_session = result.scalar_one_or_none()

            if not chat_session:
                return []

            # Extract conversation data
            conversation_data = self._extract_conversation_data(chat_session)

            # Determine motion type
            motion_type = self._determine_motion_type(conversation_data, chat_session)

            # Get required forms
            required_forms = self._get_required_forms(motion_type, conversation_data)

            # Collect all missing fields
            all_missing = []
            for form_type in required_forms:
                missing_info = self.form_mapper.get_missing_information(
                    form_type,
                    conversation_data
                )
                all_missing.extend(missing_info)

            # Remove duplicates based on field_name
            seen_fields = set()
            unique_missing = []
            for item in all_missing:
                if item["field_name"] not in seen_fields:
                    unique_missing.append(item)
                    seen_fields.add(item["field_name"])

            return unique_missing

        except Exception as e:
            logger.error(f"Error getting missing information: {e}")
            return []

    async def create_confirmation_summary(
        self,
        db: AsyncSession,
        session_id: str
    ) -> str:
        """
        Create a confirmation summary of collected information

        Args:
            db: Database session
            session_id: Chat session ID

        Returns:
            Formatted confirmation summary
        """
        try:
            # Get chat session
            stmt = select(ChatSession).where(ChatSession.id == session_id)
            result = await db.execute(stmt)
            chat_session = result.scalar_one_or_none()

            if not chat_session:
                return "Unable to create summary."

            # Extract conversation data
            data = self._extract_conversation_data(chat_session)

            # Build summary
            summary_parts = ["📋 **Summary of Information Collected**\n"]

            # Basic information
            if data.get("motion_type"):
                summary_parts.append(f"**Motion Type**: {data['motion_type'].replace('_', ' ').title()}")

            if data.get("case_number"):
                summary_parts.append(f"**Case Number**: {data['case_number']}")

            # Parties
            if data.get("party_name") or data.get("other_party_name"):
                summary_parts.append("\n**Parties**")
                if data.get("party_name"):
                    summary_parts.append(f"  • You: {data['party_name']}")
                if data.get("other_party_name"):
                    summary_parts.append(f"  • Other Party: {data['other_party_name']}")

            # Request details
            if data.get("requested_custody_arrangement") or data.get("requested_support_amount"):
                summary_parts.append("\n**What You're Requesting**")
                if data.get("requested_custody_arrangement"):
                    summary_parts.append(f"  • Custody: {data['requested_custody_arrangement']}")
                if data.get("requested_support_amount"):
                    summary_parts.append(f"  • Support: {data['requested_support_amount']}")

            # Reason
            if data.get("change_reason") or data.get("violation_details"):
                summary_parts.append("\n**Reason/Details**")
                reason = data.get("change_reason") or data.get("violation_details", "")
                summary_parts.append(f"  {reason[:200]}...")

            # Emergency status
            if data.get("is_emergency"):
                summary_parts.append("\n⚠️ **Emergency Filing**: Yes")

            summary_parts.append("\n---\n✅ Is this information correct?")

            return "\n".join(summary_parts)

        except Exception as e:
            logger.error(f"Error creating summary: {e}")
            return "Unable to create summary at this time."

# Singleton instance
chat_to_pdf_service = ChatToPDFService()