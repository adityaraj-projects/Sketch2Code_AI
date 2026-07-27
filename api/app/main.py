from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    admin,
    auth,
    beautifier,
    bugdetector,
    chatassistant,
    codegen,
    codetoflow,
    collaboration,
    collaboration_ws,
    complexity,
    execution,
    explainer,
    projects,
    recognition,
    templates,
    users,
    voicemode,
)
from app.core.config import settings
from app.db.database import Base, engine

# Phase 1: create tables directly. Swap for Alembic migrations once the
# schema needs versioned changes across environments (Phase 2+).
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="From Hand Drawn Logic to Production Code.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(recognition.router, prefix="/api")
app.include_router(codegen.router, prefix="/api")
app.include_router(codetoflow.router, prefix="/api")
app.include_router(execution.router, prefix="/api")
app.include_router(explainer.router, prefix="/api")
app.include_router(complexity.router, prefix="/api")
app.include_router(bugdetector.router, prefix="/api")
app.include_router(beautifier.router, prefix="/api")
app.include_router(templates.router, prefix="/api")
app.include_router(chatassistant.router, prefix="/api")
app.include_router(voicemode.router, prefix="/api")
app.include_router(collaboration.router, prefix="/api")
app.include_router(collaboration_ws.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.get("/api/health", tags=["health"])
def health_check():
    return {"status": "ok", "service": settings.APP_NAME}
