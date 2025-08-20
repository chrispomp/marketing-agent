#!/bin/bash

# This script creates the complete directory structure and populates all the
# source code files for the Marketing Agent project.

echo "🚀 Starting project setup for Marketing Agent..."

# Create the main project directory
mkdir -p marketing-agent
cd marketing-agent

# Create the agent's subdirectory structure
echo "📁 Creating directories..."
mkdir -p agents/marketing_agent/storage
mkdir -p agents/marketing_agent/models
mkdir -p tests

# --- Root Files ---

echo "📄 Populating root files..."

# requirements.txt
cat <<'EOF' > requirements.txt
fastapi==0.112.2
uvicorn[standard]==0.30.6
pydantic==2.8.2
google-cloud-aiplatform==1.67.0
google-cloud-storage==2.18.2
google-cloud-logging==3.11.2
google-api-core==2.19.1
tenacity==9.0.0
opentelemetry-api==1.26.0
opentelemetry-sdk==1.26.0
opentelemetry-exporter-gcp-monitoring==2.20.0
opentelemetry-exporter-gcp-trace==2.20.0
EOF

# adk.yaml
cat <<'EOF' > adk.yaml
name: marketing-agent
entry: app:app
port: 8080
description: "Enterprise-grade Marketing Agent (brief, script, storyboard, animatic) on Vertex AI"
EOF

# engine.yaml
cat <<'EOF' > engine.yaml
apiVersion: agentengine.cloud.google.com/v1
kind: AgentService
metadata:
  name: marketing-agent
  namespace: default
spec:
  image: gcr.io/${GCP_PROJECT}/marketing-agent:latest
  env:
    - name: GCP_PROJECT
      value: ${GCP_PROJECT}
    - name: VERTEX_LOCATION
      value: ${VERTEX_LOCATION}
    - name: REGION
      value: ${REGION}
    - name: GCS_BUCKET
      value: ${GCS_BUCKET}
    - name: GEMINI_MODEL
      value: ${GEMINI_MODEL}
    - name: IMAGEN_MODEL
      value: ${IMAGEN_MODEL}
    - name: VEO_MODEL
      value: ${VEO_MODEL}
  resources:
    cpu: "2"
    memory: "4Gi"
  autoscaling:
    minReplicas: 1
    maxReplicas: 5
  iam:
    workloadIdentity: true
  ingress:
    public: true
  observability:
    logging: gcp
    metrics: gcp
    tracing: gcp
  health:
    path: /healthz
    port: 8080
EOF

# Dockerfile
cat <<'EOF' > Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
EOF

# app.py
cat <<'EOF' > app.py
from fastapi import FastAPI
from agents.marketing_agent.router import router as marketing_router
from agents.marketing_agent.telemetry import setup_logging_metrics

app = FastAPI(title="Marketing Agent", version="1.0.0")

setup_logging_metrics()

@app.get("/healthz")
def health():
    return {"status": "ok"}

app.include_router(marketing_router, prefix="/v1/marketing", tags=["marketing"])
EOF

# README.md
cat <<'EOF' > README.md
# Marketing Agent (ADK + Vertex AI on GCP)

Enterprise-grade generative agent that produces:
- **Marketing Briefs** (Gemini 2.5)
- **Commercial Scripts** (Gemini 2.5)
- **Storyboards** (Imagen 4) → returns ordered JSON of **GCS URLs**
- **Animatics** (Veo 3) → returns **GCS URL** to a short MP4

## Architecture

- **Framework:** Python (FastAPI) in an ADK-style service (`adk.yaml`).
- **Models:** Vertex AI — `gemini-2.5-pro`, `imagen-4.0-generate`, `veo-3.0`.
- **Storage:** Google Cloud Storage (no keys; ADC only).
- **Observability:** Google Cloud Logging + Cloud Monitoring (OpenTelemetry).

## Prerequisites

- GCP project with billing enabled.
- IAM: you or your runtime must have permissions to call Vertex AI + write to GCS.
- Enable APIs:
  ```bash
  gcloud services enable aiplatform.googleapis.com storage.googleapis.com logging.googleapis.com monitoring.googleapis.com
  ```
- Python 3.11+
- `gcloud` CLI authenticated to your project.
- Create a GCS bucket (or use an existing one):
  ```bash
  export GCP_PROJECT=<your-project>
  export REGION=us-central1
  export VERTEX_LOCATION=us-central1
  export BUCKET_NAME=<your-unique-bucket-name>
  gsutil mb -p $GCP_PROJECT -l $REGION gs://$BUCKET_NAME
  ```
## Configuration
Set environment:
```bash
export GCP_PROJECT=<your-project>
export REGION=us-central1
export VERTEX_LOCATION=us-central1
export GCS_BUCKET=gs://$BUCKET_NAME
export GEMINI_MODEL=gemini-2.5-pro
export IMAGEN_MODEL=imagen-4.0-generate
export VEO_MODEL=veo-3.0
```
Authentication is via Application Default Credentials (ADC). Locally, run `gcloud auth application-default login`. In production, use Workload Identity (no keys).

## Local Development

### Option A: ADK CLI (`adk web`)
If you have an ADK CLI that discovers `adk.yaml`, from project root:
```bash
# (Optional) create venv
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Ensure ADC is set up
gcloud auth application-default login

# Start the agent
adk web
```
The service listens on `http://localhost:8080`.

Test endpoints:
```bash
curl -s http://localhost:8080/healthz

curl -s -X POST http://localhost:8080/v1/marketing/brief \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Gen Z credit card launch: Financial freedom without the fees"}' | jq .

curl -s -X POST http://localhost:8080/v1/marketing/script \
  -H 'Content-Type: application/json' \
  -d '{"brief_markdown":"(paste brief here)","prompt":"Write a 30-second TVC"}' | jq .

curl -s -X POST http://localhost:8080/v1/marketing/storyboard \
  -H 'Content-Type: application/json' \
  -d '{"script":"(paste screenplay here)","image_size":"1024x1024"}' | jq .

curl -s -X POST http://localhost:8080/v1/marketing/animatic \
  -H 'Content-Type: application/json' \
  -d '{"script":"(paste screenplay here)","duration_seconds":45}' | jq .
```

### Option B: Plain Uvicorn
```bash
pip install -r requirements.txt
gcloud auth application-default login
uvicorn app:app --reload --port 8080
```

## Container Build & Push
```bash
export IMAGE=gcr.io/$GCP_PROJECT/marketing-agent:latest
gcloud builds submit --tag $IMAGE
```

## Deploy to Agent Engine (on GCP)
If your Agent Engine uses a declarative spec, you can apply `engine.yaml` via your platform’s tooling or UI. If it’s Cloud Run–backed, you can deploy directly:
```bash
gcloud run deploy marketing-agent \
  --image $IMAGE \
  --project $GCP_PROJECT \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT=$GCP_PROJECT,VERTEX_LOCATION=$VERTEX_LOCATION,REGION=$REGION,GCS_BUCKET=gs://$BUCKET_NAME,GEMINI_MODEL=$GEMINI_MODEL,IMAGEN_MODEL=$IMAGEN_MODEL,VEO_MODEL=$VEO_MODEL
```
Grab the URL and test the same `curl` commands against it.

If your Agent Engine has a UI/CLI to register agents, reference:
- **Image:** `gcr.io/$GCP_PROJECT/marketing-agent:latest`
- **Entrypoint:** `uvicorn app:app --host 0.0.0.0 --port 8080`
- **Health:** `/healthz`
- **Routes:** `/v1/marketing/*`

## SLOs, Retries, Error Handling
- **Text (brief/script):** p95 < 5s — Gemini calls are retried (exponential backoff).
- **Media (storyboard/animatic):** p95 < 90s — Imagen/Veo calls are retried.
- **Graceful errors:** API exceptions return HTTP 500 with a safe message; details in Cloud Logging.
- **Observability:** Request counters + latency histograms exported to Cloud Monitoring.

## Security
- No keys in code. Uses IAM via ADC / Workload Identity.
- Buckets and Vertex AI access controlled by IAM roles:
  - `roles/aiplatform.user`
  - `roles/storage.objectAdmin` (or narrower `objectCreator` + `objectViewer`)
  - `roles/logging.logWriter`, `roles/monitoring.metricWriter`

## Notes & Model Versions
You can pin exact model versions if required by your governance. Update:
- `GEMINI_MODEL=gemini-2.5-pro-[revision]`
- `IMAGEN_MODEL=imagen-4.0-generate-[revision]`
- `VEO_MODEL=veo-3.0-[revision]`

## Troubleshooting
- **Permission errors:** Check ADC and IAM on Vertex AI + GCS.
- **Model not found:** Verify region (`VERTEX_LOCATION`) supports your models.
- **Large uploads:** Ensure Cloud Run/Engine request timeouts and memory are sufficient for MP4 responses.
EOF

# --- Agent Files ---
echo "📄 Populating agent source files..."

# agents/marketing_agent/__init__.py
touch agents/marketing_agent/__init__.py

# agents/marketing_agent/errors.py
cat <<'EOF' > agents/marketing_agent/errors.py
from pydantic import BaseModel

class UserFacingError(BaseModel):
    code: str
    message: str
EOF

# agents/marketing_agent/schemas.py
cat <<'EOF' > agents/marketing_agent/schemas.py
from typing import List, Optional
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant|system)$")
    content: str

class BriefRequest(BaseModel):
    prompt: str

class BriefResponse(BaseModel):
    markdown: str
    tokens_input: Optional[int] = 0
    tokens_output: Optional[int] = 0
    latency_ms: Optional[int] = 0

class ScriptRequest(BaseModel):
    prompt: Optional[str] = None
    brief_markdown: Optional[str] = None

class ScriptResponse(BaseModel):
    screenplay: str
    tokens_input: Optional[int] = 0
    tokens_output: Optional[int] = 0
    latency_ms: Optional[int] = 0

class StoryboardRequest(BaseModel):
    script: str
    image_size: str = "1024x1024"

class StoryboardItem(BaseModel):
    scene_number: int
    scene_slug: str
    prompt: str
    gcs_url: str

class StoryboardResponse(BaseModel):
    storyboard: List[StoryboardItem]
    latency_ms: Optional[int] = 0

class AnimaticRequest(BaseModel):
    script: str
    duration_seconds: int = 45  # target 30-60

class AnimaticResponse(BaseModel):
    gcs_url: str
    operation_id: Optional[str] = None
    latency_ms: Optional[int] = 0

class ChatTurn(BaseModel):
    messages: List[ChatMessage]

class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None
EOF

# agents/marketing_agent/state.py
cat <<'EOF' > agents/marketing_agent/state.py
from typing import List, Dict
from agents.marketing_agent.schemas import ChatMessage

class ConversationState:
    """
    Minimal in-memory state. For production, back this with Redis/Firestore.
    """
    def __init__(self):
        self.sessions: Dict[str, List[ChatMessage]] = {}

    def get(self, session_id: str) -> List[ChatMessage]:
        return self.sessions.get(session_id, [])

    def append(self, session_id: str, message: ChatMessage):
        self.sessions.setdefault(session_id, []).append(message)

STATE = ConversationState()
EOF

# agents/marketing_agent/telemetry.py
cat <<'EOF' > agents/marketing_agent/telemetry.py
import logging
import os
from google.cloud import logging as cloud_logging
from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.gcp_monitoring import GcpMonitoringMetricsExporter
from opentelemetry.exporter.gcp_trace import GcpTraceExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

def setup_logging_metrics():
    # Cloud Logging
    try:
        client = cloud_logging.Client()
        client.setup_logging()
    except Exception:
        logging.basicConfig(level=logging.INFO)

    # OpenTelemetry -> Cloud Monitoring/Trace
    resource = Resource.create({"service.name": "marketing-agent"})
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(GcpTraceExporter()))
    trace.set_tracer_provider(tracer_provider)

    meter_provider = MeterProvider(
        metric_readers=[PeriodicExportingMetricReader(GcpMonitoringMetricsExporter())],
        resource=resource,
    )
    metrics.set_meter_provider(meter_provider)

LOGGER = logging.getLogger("marketing-agent")
TRACER = trace.get_tracer(__name__)
METER = metrics.get_meter(__name__)

# Basic counters/histograms
REQUEST_COUNTER = METER.create_counter("requests_total")
ERROR_COUNTER = METER.create_counter("errors_total")
LATENCY_MS = METER.create_histogram("latency_ms")
EOF

# agents/marketing_agent/utils.py
cat <<'EOF' > agents/marketing_agent/utils.py
import hashlib
import re

def slugify(text: str, max_len: int = 40) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    if len(text) <= max_len:
        return text
    h = hashlib.sha1(text.encode()).hexdigest()[:6]
    return f"{text[:max_len-7]}-{h}"
EOF

# agents/marketing_agent/storage/gcs.py
cat <<'EOF' > agents/marketing_agent/storage/gcs.py
import io
import os
import time
from typing import Tuple
from google.cloud import storage

_BUCKET = None
_BUCKET_NAME = None

def _bucket():
    global _BUCKET, _BUCKET_NAME
    if _BUCKET is None:
        bucket_uri = os.environ["GCS_BUCKET"]
        if not bucket_uri.startswith("gs://"):
            raise ValueError("GCS_BUCKET must start with gs://")
        _BUCKET_NAME = bucket_uri.replace("gs://", "", 1)
        client = storage.Client()
        _BUCKET = client.bucket(_BUCKET_NAME)
    return _BUCKET, _BUCKET_NAME

def upload_bytes(content: bytes, path: str, content_type: str) -> str:
    bucket, bucket_name = _bucket()
    blob = bucket.blob(path)
    blob.upload_from_file(io.BytesIO(content), content_type=content_type)
    blob.cache_control = "public, max-age=3600"
    blob.patch()
    return f"gs://{bucket_name}/{path}"

def upload_file(local_path: str, dest_path: str, content_type: str) -> str:
    bucket, bucket_name = _bucket()
    blob = bucket.blob(dest_path)
    blob.content_type = content_type
    blob.upload_from_filename(local_path)
    return f"gs://{bucket_name}/{dest_path}"

def gcs_path(prefix: str, name: str, ext: str) -> str:
    ts = int(time.time() * 1000)
    return f"{prefix}/{ts}_{name}.{ext}"
EOF

# agents/marketing_agent/models/gemini_client.py
cat <<'EOF' > agents/marketing_agent/models/gemini_client.py
import os
import time
from typing import Tuple
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from vertexai.generative_models import GenerativeModel, SafetySetting
import vertexai

class GeminiClient:
    def __init__(self):
        self.project = os.environ["GCP_PROJECT"]
        self.location = os.environ.get("VERTEX_LOCATION", "us-central1")
        self.model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-pro")
        vertexai.init(project=self.project, location=self.location)
        self.model = GenerativeModel(self.model_name)

        # Conservative safety defaults; adjust per policy.
        self.safety = [
            SafetySetting.HarmBlockThreshold.HARM_BLOCK_THRESHOLD_MEDIUM  # type: ignore
        ]

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(Exception),
    )
    def generate(self, prompt: str, system_instruction: str = "") -> Tuple[str, int, int, int]:
        """
        Returns text, tokens_in, tokens_out, latency_ms
        """
        start = time.time()
        content = []
        if system_instruction:
            content.append({"role": "user", "parts": [system_instruction + "\n\n" + prompt]})
        else:
            content.append({"role": "user", "parts": [prompt]})

        resp = self.model.generate_content(
            content,
            safety_settings=self.safety,
            generation_config={"temperature": 0.4, "top_p": 0.9, "top_k": 40, "max_output_tokens": 2048},
        )
        text = resp.text or ""
        usage = getattr(resp, "usage_metadata", None)
        tokens_in = getattr(usage, "prompt_token_count", 0) if usage else 0
        tokens_out = getattr(usage, "candidates_token_count", 0) if usage else 0
        latency_ms = int((time.time() - start) * 1000)
        return text, tokens_in, tokens_out, latency_ms
EOF

# agents/marketing_agent/models/imagen_client.py
cat <<'EOF' > agents/marketing_agent/models/imagen_client.py
import os
import base64
import time
from typing import Tuple
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel

class ImagenClient:
    def __init__(self):
        self.project = os.environ["GCP_PROJECT"]
        self.location = os.environ.get("VERTEX_LOCATION", "us-central1")
        self.model_name = os.environ.get("IMAGEN_MODEL", "imagen-4.0-generate")
        vertexai.init(project=self.project, location=self.location)
        self.model = ImageGenerationModel(self.model_name)

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=16),
        retry=retry_if_exception_type(Exception),
    )
    def generate_image(self, prompt: str, image_size: str = "1024x1024") -> Tuple[bytes, int]:
        """
        Returns (image_bytes_png, latency_ms)
        """
        start = time.time()
        result = self.model.generate_images(
            prompt=prompt,
            number_of_images=1,
            image_size=image_size,
            # optional: safety filter tuning, style, etc.
        )
        img = result.images[0]
        # SDK returns PIL Image-like or bytes depending on version; normalize to bytes
        if hasattr(img, "to_bytes"):
            png_bytes = img.to_bytes()
        elif hasattr(img, "image_bytes"):
            png_bytes = img.image_bytes
        else:
            # some versions provide base64
            png_bytes = base64.b64decode(img.base64_data)  # type: ignore
        latency_ms = int((time.time() - start) * 1000)
        return png_bytes, latency_ms
EOF

# agents/marketing_agent/models/veo_client.py
cat <<'EOF' > agents/marketing_agent/models/veo_client.py
import os
import time
from typing import Tuple
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import vertexai
from vertexai.preview.vision_models import VideoGenerationModel

class VeoClient:
    def __init__(self):
        self.project = os.environ["GCP_PROJECT"]
        self.location = os.environ.get("VERTEX_LOCATION", "us-central1")
        self.model_name = os.environ.get("VEO_MODEL", "veo-3.0")
        vertexai.init(project=self.project, location=self.location)
        self.model = VideoGenerationModel(self.model_name)

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=16),
        retry=retry_if_exception_type(Exception),
    )
    def generate_video(self, prompt: str, duration_seconds: int = 45) -> Tuple[bytes, int]:
        """
        Synchronously generate a single MP4 clip; returns (mp4_bytes, latency_ms)
        (If your project has async long-running ops, you can adapt to poll Operation.)
        """
        start = time.time()
        result = self.model.generate_video(
            prompt=prompt,
            duration_seconds=duration_seconds,
            # optional params: fps, aspect_ratio, style_preset, etc.
        )
        # Normalization across SDK versions:
        if hasattr(result, "video_bytes"):
            mp4_bytes = result.video_bytes
        else:
            mp4_bytes = result[0].video_bytes  # type: ignore
        latency_ms = int((time.time() - start) * 1000)
        return mp4_bytes, latency_ms
EOF

# agents/marketing_agent/agent.py
cat <<'EOF' > agents/marketing_agent/agent.py
import time
from typing import List
from agents.marketing_agent.models.gemini_client import GeminiClient
from agents.marketing_agent.models.imagen_client import ImagenClient
from agents.marketing_agent.models.veo_client import VeoClient
from agents.marketing_agent.storage.gcs import upload_bytes, gcs_path
from agents.marketing_agent.utils import slugify

BRIEF_SYS = """You are a senior marketing strategist. Produce a concise, structured marketing brief in Markdown with:
- Objective
- Target Audience
- Key Message
- Tone of Voice
- Mandatories
Keep it crisp, actionable, and brand-agnostic unless specified.
"""

SCRIPT_SYS = """You are a senior copywriter. Produce a 30s TVC screenplay in standard format:
- Scene Heading (INT/EXT – LOCATION – TIME)
- Action
- Character: DIALOGUE
Use 3-4 scenes, concise lines, cinematic pacing, and include brief SFX/VFX cues where helpful.
"""

SCENE_SYS = """You split a TV script into visual scenes. Return a numbered list. For each scene: a short, vivid image prompt suitable for a photorealistic storyboard frame (no text overlay, cinematic lighting, camera angle)."""

ANIMATIC_SYS = """You are a storyboard-to-animatic producer. Produce a single concise prompt describing the overall commercial visuals, pacing, camera moves, transitions, and mood to generate a ~30-60s video."""
 
class MarketingAgent:
    def __init__(self):
        self.gemini = GeminiClient()
        self.imagen = ImagenClient()
        self.veo = VeoClient()

    # FR-01
    def generate_brief(self, user_prompt: str):
        text, in_toks, out_toks, latency = self.gemini.generate(
            prompt=user_prompt, system_instruction=BRIEF_SYS
        )
        return text, in_toks, out_toks, latency

    # FR-02
    def generate_script(self, prompt: str = "", brief_markdown: str = ""):
        compound = ""
        if brief_markdown:
            compound += "=== PRIOR BRIEF ===\n" + brief_markdown + "\n\n"
        if prompt:
            compound += "=== REQUEST ===\n" + prompt
        else:
            compound += "Generate a 30-second script based on the brief."
        text, in_toks, out_toks, latency = self.gemini.generate(
            prompt=compound, system_instruction=SCRIPT_SYS
        )
        return text, in_toks, out_toks, latency

    # FR-03
    def generate_storyboard(self, script: str, image_size: str = "1024x1024"):
        scenes_text, _, _, _ = self.gemini.generate(
            prompt=script, system_instruction=SCENE_SYS
        )
        # Parse numbered list into (scene_number, prompt)
        lines = [l.strip() for l in scenes_text.splitlines() if l.strip()]
        items = []
        for l in lines:
            # Accept formats like "1) prompt", "1. prompt", "1 - prompt"
            if l[0].isdigit():
                # split off the leading number and delimiter
                prompt = l.split(" ", 1)[1] if " " in l else l
                items.append(prompt.strip("-.) ").strip())
        if not items:
            items = ["Wide establishing shot of the scenario"]  # fallback

        storyboard = []
        for idx, prompt in enumerate(items, start=1):
            png_bytes, _ = self.imagen.generate_image(prompt=prompt, image_size=image_size)
            name = slugify(prompt) or f"scene-{idx}"
            path = gcs_path("storyboards", f"{name}", "png")
            gcs_url = upload_bytes(png_bytes, path, "image/png")
            storyboard.append({
                "scene_number": idx,
                "scene_slug": name,
                "prompt": prompt,
                "gcs_url": gcs_url
            })
        return storyboard

    # FR-04
    def generate_animatic(self, script: str, duration_seconds: int = 45):
        prompt, _, _, _ = self.gemini.generate(
            prompt=script, system_instruction=ANIMATIC_SYS
        )
        mp4_bytes, _ = self.veo.generate_video(prompt=prompt, duration_seconds=duration_seconds)
        name = slugify(prompt or "animatic")
        path = gcs_path("animatics", f"{name}", "mp4")
        gcs_url = upload_bytes(mp4_bytes, path, "video/mp4")
        return gcs_url
EOF

# agents/marketing_agent/router.py
cat <<'EOF' > agents/marketing_agent/router.py
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
EOF

# --- Test Files ---
echo "📄 Populating test files..."

# tests/smoke_test.py
cat <<'EOF' > tests/smoke_test.py
import os
import json
import requests

BASE = os.environ.get("BASE_URL", "http://localhost:8080/v1/marketing")

def test_brief():
    r = requests.post(f"{BASE}/brief", json={"prompt":"Gen Z credit card launch: 'Financial freedom without the fees'."})
    r.raise_for_status()
    print(r.json())

if __name__ == "__main__":
    test_brief()
EOF

# Final message
echo "✅ Marketing Agent project created successfully in the 'marketing-agent' directory."
echo "   Next steps:"
echo "   1. cd marketing-agent"
echo "   2. Set your environment variables (GCP_PROJECT, GCS_BUCKET, etc.)"
echo "   3. Follow the instructions in README.md to run locally or deploy."

