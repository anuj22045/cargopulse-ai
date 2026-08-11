from fastapi import FastAPI

app = FastAPI(
    title="CargoPulse AI",
    description="AI-Powered Shipment Risk Intelligence & Decision Platform",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "message": "CargoPulse AI backend is running",
        "version": "0.1.0",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "CargoPulse AI API",
    }