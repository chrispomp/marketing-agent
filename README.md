# Marketing Agent

This project contains an enterprise-grade AI agent built with the Google Agent Development Kit (ADK) to accelerate the creative marketing lifecycle.

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.9+
- Google Cloud SDK (`gcloud`) installed and configured.

### 2. Setup
1.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment:**
    - Rename `.env.example` to `.env`.
    - Update the `GCP_PROJECT` and `BUCKET_NAME` variables with your specific GCP project ID and a GCS bucket you have access to.

4.  **Authenticate with GCP:**
    Ensure your local environment is authenticated to Google Cloud. This agent uses Application Default Credentials (ADC).
    ```bash
    gcloud auth application-default login
    ```

### 3. Run the Agent Locally
You can interact with the agent using the ADK's built-in web interface.

```bash
adk web
Navigate to http://127.0.0.1:8000 in your browser and select the MarketingAgent to begin.

Example Conversational Flow
"Draft a marketing brief for a new credit card for Gen Z. The key message is 'Financial freedom without the fees'."

"Perfect. Now write a 30-second TV script based on that."

"Create a storyboard for this script."

"Now make a simple animatic from the script."
