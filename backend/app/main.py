from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db


app = FastAPI(
    title="CargoPulse AI API",
    version="0.1.0"
)


@app.get("/")
def root():
    return {
        "message": "CargoPulse AI API",
        "version": "0.1.0"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "CargoPulse AI API"
    }


@app.get("/health/db")
def database_health_check(db: Session = Depends(get_db)):
    try:
        database_name = db.execute(
            text("SELECT current_database()")
        ).scalar_one()

        return {
            "status": "healthy",
            "database": database_name
        }

    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed"
        )

# cd backend
# python -m uvicorn app.main:app --reload