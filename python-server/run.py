from app.main import app

if __name__ == "__main__":
    import uvicorn
    from app.core.config import settings
    
    uvicorn.run(
        "run:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
