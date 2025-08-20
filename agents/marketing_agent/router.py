import time
from functools import lru_cache
from fastapi import APIRouter, HTTPException, Query, Depends
from agents.marketing_agent.agent import MarketingAgent
from agents.marketing_agent.models.gemini_client import GeminiClient
from agents.marketing_agent.models.imagen_client import ImagenClient
from agents.marketing_agent.models.veo_client import VeoClient
from agents.marketing_agent.schemas import (
    BriefRequest, BriefResponse,
    ScriptRequest, ScriptResponse,
    StoryboardRequest, StoryboardResponse, StoryboardItem,
    AnimaticRequest, AnimaticResponse,
    ErrorResponse
)
from agents.marketing_agent.telemetry import LOGGER, REQUEST_COUNTER, ERROR_COUNTER, LATENCY_MS

router = APIRouter()

@lru_cache(maxsize=1)
def get_gemini_client() -> GeminiClient:
    return GeminiClient()

@lru_cache(maxsize=1)
def get_imagen__client() -> ImagenClient:
    return ImagenClient()

@lru_cache(maxsize=1)
def get_veo_client() -> VeoClient:
    return VeoClient()

def get_marketing_agent(
    gemini_client: GeminiClient = Depends(get_gemini_client),
    imagen_client: ImagenClient = Depends(get_imagen_client),
    veo_client: VeoClient = Depends(get_veo_client),
) -> MarketingAgent:
    return MarketingAgent(
        gemini_client=gemini_client,
        imagen_client=imagen_client,
        veo_client=veo_client,
    )

@router.post("/brief", response_model=BriefResponse, responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
def create_brief(req: BriefRequest, agent: MarketingAgent = Depends(get_marketing_agent)):
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
def create_script(req: ScriptRequest, agent: MarketingAgent = Depends(get_marketing_agent)):
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
def create_storyboard(req: StoryboardRequest, agent: MarketingAgent = Depends(get_marketing_agent)):
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
def create_animatic(req: AnimaticRequest, agent: MarketingAgent = Depends(get_marketing_agent)):
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
