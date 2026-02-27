from fastapi import FastAPI
from .db.session import Base, engine
from .api.routes_auth import router as auth_router
from .api.routes_chat import router as chat_router
from .api.routes_stats import router as stats_router

app = FastAPI(title="LearnLanguage API")

Base.metadata.create_all(bind=engine)

@app.get("/")
def health():
    return {"status": "ok"}
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(stats_router)
