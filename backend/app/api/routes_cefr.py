from fastapi import APIRouter
from pydantic import BaseModel
from ..services.cefr_predictor import CEFRPredictor

router = APIRouter()
predictor = CEFRPredictor()

class PredictRequest(BaseModel):
    text: str

@router.post("/predict-level")
def predict_level(payload: PredictRequest):
    return {"level": predictor.predict(payload.text)}