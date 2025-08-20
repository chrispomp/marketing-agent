from fastapi import FastAPI
from agents.marketing_agent.router import router as marketing_router
from agents.marketing_agent.telemetry import setup_logging_metrics

app = FastAPI(title="Marketing Agent", version="1.0.0")

setup_logging_metrics()

@app.get("/healthz")
def health():
    return {"status": "ok"}

app.include_router(marketing_router, prefix="/v1/marketing", tags=["marketing"])
