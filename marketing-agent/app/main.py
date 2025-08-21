import os
import sys
import logging
import vertexai
from dotenv import load_dotenv
from adk.api.fastapi import create_app
from app.marketing_agent import MarketingAgent

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

# Load environment variables from .env file
load_dotenv()

# --- Configuration & Initialization ---
GCP_PROJECT = os.getenv("GCP_PROJECT")
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION")
BUCKET_NAME = os.getenv("BUCKET_NAME")

if not all([GCP_PROJECT, VERTEX_LOCATION, BUCKET_NAME]):
    logging.error("Missing critical environment variables. Please check your .env file.")
    sys.exit(1)

try:
    vertexai.init(project=GCP_PROJECT, location=VERTEX_LOCATION)
    logging.info(f"Vertex AI initialized successfully for project '{GCP_PROJECT}' in '{VERTEX_LOCATION}'.")
except Exception as e:
    logging.error(f"Error initializing Vertex AI: {e}", exc_info=True)
    sys.exit(1)
    
# Instantiate the main agent and name it root_agent
# THIS IS THE CRITICAL LINE THE ADK LOOKS FOR
root_agent = MarketingAgent()

# Create the FastAPI application
app = create_app(root_agent)

# Optional: Add a root endpoint for basic health checks or info
@app.get("/")
def read_root():
    return {"message": "Marketing Agent is running"}
