import os
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.database.session import Base, engine

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Document RAG API",
    description="API for document management and chat with RAG capabilities",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Delay startup if STARTUP_DELAY is set
startup_delay = int(os.environ.get("STARTUP_DELAY", 0))
if startup_delay > 0:
    print(f"Delaying startup by {startup_delay} seconds...")
    time.sleep(startup_delay)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 