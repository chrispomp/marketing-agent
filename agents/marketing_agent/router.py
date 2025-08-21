import time
import logging
from functools import lru_cache
from fastapi import APIRouter, HTTPException, Depends
from agents.marketing_agent.agent import MarketingAgent
from agents.marketing_agent.models.gemini_client import GeminiClient
from agents.marketing_agent.models.imagen_client import ImagenClient
from agents.marketing_agent.models.veo_client import VeoClient
from agents.marketing_agent.schemas import (
    BriefRequest, BriefResponse,
    ScriptRequest, ScriptResponse,
    StoryboardRequest, StoryboardResponse, StoryboardItem,
    AnimaticRequest, AnimaticJobResponse, AnimaticStatusResponse,
    ErrorResponse
)

router = APIRouter()

@lru_cache(maxsize=1)
def get_gemini_client() -> GeminiClient:
    return GeminiClient()

@lru_cache(maxsize=1)
def get_imagen_client() -> ImagenClient:
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
    try:
        md, tin, tout, lat = agent.generate_brief(req.prompt)
        return BriefResponse(markdown=md, tokens_input=tin, tokens_output=tout, latency_ms=lat)
    except Exception as e:
        logging.exception("Brief generation failed")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/script", response_model=ScriptResponse)
def create_script(req: ScriptRequest, agent: MarketingAgent = Depends(get_marketing_agent)):
    try:
        text, tin, tout, lat = agent.generate_script(prompt=req.prompt or "", brief_markdown=req.brief_markdown or "")
        return ScriptResponse(screenplay=text, tokens_input=tin, tokens_output=tout, latency_ms=lat)
    except Exception as e:
        logging.exception("Script generation failed")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/storyboard", response_model=StoryboardResponse)
def create_storyboard(req: StoryboardRequest, agent: MarketingAgent = Depends(get_marketing_agent)):
    t0 = time.time()
    try:
        sb = agent.generate_storyboard(script=req.script, image_size=req.image_size)
        return StoryboardResponse(
            storyboard=[StoryboardItem(**x) for x in sb],
            latency_ms=int((time.time()-t0)*1000)
        )
    except Exception as e:
        logging.exception("Storyboard generation failed")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/animatic", response_model=AnimaticJobResponse)
def create_animatic(req: AnimaticRequest, agent: MarketingAgent = Depends(get_marketing_agent)):
    t0 = time.time()
    try:
        job_name = agent.generate_animatic(script=req.script, duration_seconds=req.duration_seconds)
        return AnimaticJobResponse(job_name=job_name, latency_ms=int((time.time()-t0)*1000))
    except Exception as e:
        logging.exception("Animatic generation failed to start")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/animatic/status/{job_name:path}", response_model=AnimaticStatusResponse)
def get_animatic_status(job_name: str, agent: MarketingAgent = Depends(get_marketing_agent)):
    try:
        status = agent.check_animatic_job_status(job_name)
        return AnimaticStatusResponse(**status)
    except Exception as e:
        logging.exception("Animatic status check failed")
        raise HTTPException(status_code=500, detail=str(e))