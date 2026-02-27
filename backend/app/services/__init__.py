from pathlib import Path
import joblib

MODEL_PATH = Path("ml/models/cefr_model.pkl")

class CEFRPredictor:
    def __init__(self):
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Model not found: {MODEL_PATH}")
        self.model = joblib.load(MODEL_PATH)

    def predict(self, text: str) -> str:
        text = (text or "").strip()
        if not text:
            return "A2"  # default safe
        return self.model.predict([text])[0]