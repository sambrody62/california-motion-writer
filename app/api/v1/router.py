"""
Main API router
"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, profiles, motions, llm, documents, intake, violations, evidence, evidence_batch, evidence_gmail, served_motion
from app.api.v1 import chat, chat_pdf

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["Profiles"])
api_router.include_router(motions.router, prefix="/motions", tags=["Motions"])
api_router.include_router(intake.router, prefix="/intake", tags=["Intake"])
api_router.include_router(llm.router, prefix="/llm", tags=["LLM"])
api_router.include_router(served_motion.router, prefix="/llm", tags=["LLM"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
# violations and chat_pdf carry their own path prefixes; evidence and evidence_gmail
# declare frontend-facing paths (/motions/..., /evidence/..., /gmail/...) directly.
# Adding prefixes here doubled every path and broke the frontend contract.
api_router.include_router(violations.router, tags=["Violations"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(chat_pdf.router, tags=["Chat-to-PDF"])
api_router.include_router(evidence.router, tags=["Evidence"])
api_router.include_router(evidence_batch.router, tags=["Evidence-Batch"])
api_router.include_router(evidence_gmail.router, tags=["Evidence-Gmail"])