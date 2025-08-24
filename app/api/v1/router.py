"""
Main API router
"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, profiles, motions, llm, documents, intake

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["Profiles"])
api_router.include_router(motions.router, prefix="/motions", tags=["Motions"])
api_router.include_router(intake.router, prefix="/intake", tags=["Intake"])
api_router.include_router(llm.router, prefix="/llm", tags=["LLM"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])