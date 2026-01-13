from fastapi import FastAPI
from src.routers import chat, health

app = FastAPI(
    title="Chatbot API",
    description="FastAPI backend for chatbot application",
    version="1.0.0"
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(chat.router, prefix="/api", tags=["chat"])

@app.get("/")
async def root():
    return {"message": "Welcome to Chatbot API"}
