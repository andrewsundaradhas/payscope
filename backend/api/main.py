"""
FastAPI backend for PayScope ML services
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="PayScope ML API",
    description="Machine Learning backend for PayScope",
    version="1.0.0"
)

# CORS configuration for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Example request/response models
class HealthResponse(BaseModel):
    status: str
    message: str


class PredictionRequest(BaseModel):
    data: dict


class PredictionResponse(BaseModel):
    prediction: dict
    confidence: float


@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "PayScope ML API is running"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "message": "All systems operational"
    }


@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """
    ML prediction endpoint
    
    Add your ML model inference logic here
    """
    try:
        # TODO: Add your ML model prediction logic
        prediction = {
            "result": "example_prediction",
            "details": request.data
        }
        
        return {
            "prediction": prediction,
            "confidence": 0.95
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "localhost")
    port = int(os.getenv("API_PORT", 8000))
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True
    )

