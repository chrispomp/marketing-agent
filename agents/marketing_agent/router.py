import time
from fastapi import APIRouter, HTTPException, Query
from agents.marketing_agent.agent import MarketingAgent
from agents.marketing_agent.schemas import (
    BriefRequest, BriefResponse,
    ScriptRequest, ScriptResponse,
    StoryboardRequest, StoryboardResponse, StoryboardItem,
    AnimaticRequest, AnimaticResponse,
    ErrorResponse
)
from agents.marketing_agent.telemetry import LOGGER, REQUEST_COUNTER, ERROR_COUNTER, LATENCY_MS

router = APIRouter()
agent = MarketingAgent()

@router.post("/brief", response_model=BriefResponse, responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
def create_brief(req: BriefRequest):
    t0 = time.time()
    REQUEST_COUNTER.add(1, {"endpoint": "brief"})
    try:
        md, tin, tout, lat = agent.generate_brief(req.prompt)
        LATENCY_MS.record(int((time.time()-t0)*1000), {"endpoint": "brief"})
        return BriefResponse(markdown=md, tokens_input=tin, tokens_output=tout, latency_ms=lat)
    except Exception as e:
        ERROR_COUNTER.add(1, {"endpoint": "brief"})
        LOGGER.exception("Brief generation failed")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/script", response_model=ScriptResponse)
def create_script(req: ScriptRequest):
    t0 = time.time()
    REQUEST_COUNTER.add(1, {"endpoint": "script"})
    try:
        text, tin, tout, lat = agent.generate_script(prompt=req.prompt or "", brief_markdown=req.brief_markdown or "")
        LATENCY_MS.record(int((time.time()-t0)*1000), {"endpoint": "script"})
        return ScriptResponse(screenplay=text, tokens_input=tin, tokens_output=tout, latency_ms=lat)
    except Exception as e:
        ERROR_COUNTER.add(1, {"endpoint": "script"})
        LOGGER.exception("Script generation failed")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/storyboard", response_model=StoryboardResponse)
def create_storyboard(req: StoryboardRequest):
    t0 = time.time()
    REQUEST_COUNTER.add(1, {"endpoint": "storyboard"})
    try:
        sb = agent.generate_storyboard(script=req.script, image_size=req.image_size)
        LATENCY_MS.record(int((time.time()-t0)*1000), {"endpoint": "storyboard"})
        return StoryboardResponse(
            storyboard=[StoryboardItem(**x) for x in sb],
            latency_ms=int((time.time()-t0)*1000)
        )
    except Exception as e:
        ERROR_COUNTER.add(1, {"endpoint": "storyboard"})
        LOGGER.exception("Storyboard generation failed")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/animatic", response_model=AnimaticResponse)
def create_animatic(req: AnimaticRequest):
    t0 = time.time()
    REQUEST_COUNTER.add(1, {"endpoint": "animatic"})
    try:
        gcs_url = agent.generate_animatic(script=req.script, duration_seconds=req.duration_seconds)
        LATENCY_MS.record(int((time.time()-t0)*1000), {"endpoint": "animatic"})
        return AnimaticResponse(gcs_url=gcs_url, latency_ms=int((time.time()-t0)*1000))
    except Exception as e:
        ERROR_COUNTER.add(1, {"endpoint": "animatic"})
        LOGGER.exception("Animatic generation failed")
        raise HTTPException(status_code=500, detail=str(e))
