# Marketing Agent (Optimized ADK Project)

The Marketing Agent is an enterprise-grade generative AI assistant designed to accelerate the creative marketing lifecycle. This project is an **optimized implementation** using the Python **Agent Development Kit (ADK)**, consolidating all logic into a streamlined, single-agent structure.

It integrates Google Cloud's Gemini 1.5 Pro, Imagen 4, and Veo 3 models to automate the creation of marketing briefs, commercial scripts, storyboards, and animatics.

## ✨ Features

-   **Marketing Brief Generation**: Converts high-level ideas into structured Markdown briefs.
-   **Commercial Script Generation**: Writes industry-standard scripts from a brief or prompt.
-   **Storyboard Generation**: Parses a script and generates a sequence of images (using Imagen 4).
-   **Animatic Generation**: Synthesizes a script and generates a short video (using Veo 3).

## 🛠️ Prerequisites

1.  **Google Cloud Project**: A GCP project with billing enabled.
2.  **APIs Enabled**: In your GCP project, enable: `aiplatform.googleapis.com`, `storage.googleapis.com`.
3.  **GCS Bucket**: A Google Cloud Storage bucket for storing generated assets.
4.  **Permissions**: Your service account (or local user) must have these IAM roles:
    * `Vertex AI User`
    * `Storage Object Admin`
5.  **Local Tools**:
    * [Google Cloud SDK (gcloud)](https://cloud.google.com/sdk/install)
    * [Docker](https://www.docker.com/products/docker-desktop/)
    * Python 3.11+

## 🚀 Local Development

### 1. Configure Your Environment

**A. Generate Project Files**
Save the setup script as `create_project.sh` and run it in your terminal:
```sh
bash create_project.sh
