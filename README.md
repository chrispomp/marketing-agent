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

## Prerequisites

- GCP project with billing enabled.
- IAM: you or your runtime must have permissions to call Vertex AI + write to GCS.
- Enable APIs:
  ```bash
  gcloud services enable aiplatform.googleapis.com storage.googleapis.com
  ```
- Python 3.11+
- `gcloud` CLI authenticated to your project.
- Create a GCS bucket (or use an existing one):
  ```bash
  export GCP_PROJECT=
  export REGION=us-central1
  export VERTEX_LOCATION=us-central1
  export BUCKET_NAME=marketing-agent-assets
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