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
  export GCP_PROJECT=
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
