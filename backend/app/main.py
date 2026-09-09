from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.shipments import router as shipment_router
from app.api.shipment_events import router as shipment_event_router
from app.api.ai_predictions import router as ai_prediction_router
from app.api.simulation_events import router as simulation_event_router
from app.api.ai_recommendations import router as ai_recommendation_router
from app.api.decision_history import router as decision_history_router
from app.api.dashboard import router as dashboard_router

#auto simulation 
from contextlib import asynccontextmanager
from app.core.scheduler import start_scheduler, stop_scheduler
from app.api.websocket import router as websocket_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()

    yield

    stop_scheduler()

app = FastAPI(
    title="CargoPulse AI API",
    version="0.1.0",
    lifespan=lifespan
)

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[
#         "http://localhost:5173",
#     ],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(shipment_router)
app.include_router(shipment_event_router)
app.include_router(ai_prediction_router)
app.include_router(simulation_event_router)
app.include_router(ai_recommendation_router)
app.include_router(decision_history_router)
app.include_router(dashboard_router)
app.include_router(websocket_router)

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(
    request: Request,
    exc: SQLAlchemyError
):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "A database error occurred."
        }
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

#to run postgresql
# psql -U postgres -d cargopulse_ai