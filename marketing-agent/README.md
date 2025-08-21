# Marketing Agent (ADK + Vertex AI)

The Marketing Agent is an enterprise-grade generative AI assistant designed to accelerate the creative marketing lifecycle. It integrates Google Cloud's Gemini 2.5, Imagen 4, and Veo 3 models to automate the creation of marketing briefs, commercial scripts, storyboards, and animatics.

This project is built with the Python **Agent Development Kit (ADK)** and is designed for containerized deployment on **Agent Engine** (Cloud Run) within Google Cloud Platform (GCP).

## ✨ Features

-   **Marketing Brief Generation**: Converts high-level ideas into structured Markdown briefs.
-   **Commercial Script Generation**: Writes industry-standard scripts from a brief or prompt.
-   **Storyboard Generation**: Parses a script and generates a sequence of images (using Imagen 4) for each key scene.
-   **Animatic Generation**: Synthesizes a script into a prompt and generates a short video (using Veo 3).

## 🛠️ Prerequisites

1.  **Google Cloud Project**: A GCP project with billing enabled.
2.  **APIs Enabled**: Ensure these APIs are enabled: `aiplatform.googleapis.com`, `storage.googleapis.com`, `artifactregistry.googleapis.com`, `run.googleapis.com`, `cloudbuild.googleapis.com`.
3.  **GCS Bucket**: A Google Cloud Storage bucket for storing generated assets.
4.  **Permissions**: Your service account (or local user) must have these IAM roles:
    * `Vertex AI User`
    * `Storage Object Admin`
    * `Cloud Run Admin`
    * `Artifact Registry Writer`
    * `Service Account User`
5.  **Local Tools**:
    * [Google Cloud SDK (gcloud)](https://cloud.google.com/sdk/install)
    * [Docker](https://www.docker.com/products/docker-desktop/)
    * Python 3.11+

## 🚀 Local Development

### 1. Configure Your Environment

**A. Create Project Files**

If you haven't already, run the `create_project.sh` script to generate the project structure and code.

**B. Set Up Environment Variables**

Open the `.env` file and replace the placeholder values with your actual GCP configuration.

```ini
# .env
GCP_PROJECT="your-gcp-project-id"
REGION="us-central1"
VERTEX_LOCATION="us-central1"
BUCKET_NAME="your-unique-gcs-bucket-name"
