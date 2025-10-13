from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import APP_NAME, DEBUG, ALLOWED_ORIGINS
from config.database import create_tables
from routes import auth, experts, chat, voice, knowledge_base, images, conversation, tools, expert_progress
from services.queue_worker import start_worker, stop_worker

# Create FastAPI app
app = FastAPI(
    title=APP_NAME,
    description="Dilan AI Backend - Voice-powered AI assistant platform",
    version="1.0.0",
    debug=DEBUG
)

# Database initialization
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        # Import models to ensure they're registered
        from models.user_db import UserDB
        from models.file_db import FileDB
        from models.expert_db import ExpertDB
        from models.expert_processing_progress import ExpertProcessingProgress
        from models.processing_queue import ProcessingQueue
        
        # Create tables
        create_tables()
        print("✅ Database tables initialized successfully!")
        
        # Start background queue worker in separate thread
        print("🚀 Starting background queue worker...")
        start_worker()
        print("✅ Queue worker started in background thread!")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        # Don't fail startup, but log the error
        pass

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        print("🛑 Stopping queue worker...")
        stop_worker()
        print("✅ Queue worker stopped!")
    except Exception as e:
        print(f"❌ Error stopping queue worker: {e}")

# Add CORS middleware - Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=False,  # Must be False when using wildcard
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(experts.router, prefix="/experts", tags=["Experts"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(voice.router, prefix="/voice", tags=["Voice"])
app.include_router(conversation.router, prefix="/conversation", tags=["Conversation"])
app.include_router(knowledge_base.router, prefix="/knowledge-base", tags=["Knowledge Base"])
app.include_router(images.router, prefix="/images", tags=["Images"])
app.include_router(tools.router, prefix="/tools", tags=["Tools"])
app.include_router(expert_progress.router, prefix="/api", tags=["Expert Progress"])

@app.get("/")
def read_root():
    return {
        "message": "Welcome to Dilan AI Backend",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": APP_NAME}

if __name__ == "__main__":
    import uvicorn
    from config.settings import HOST, PORT
    uvicorn.run("main:app", host=HOST, port=PORT, reload=DEBUG)
