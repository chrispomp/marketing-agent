import os
import sys
import logging
import vertexai
from dotenv import load_dotenv
from app.marketing_agent import MarketingAgent

# --- Configuration & Initialization ---

# Configure structured logging to provide clear, actionable output.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    stream=sys.stdout
)

# Load environment variables from the .env file in the root directory.
# This makes configuration portable and secure.
load_dotenv()

GCP_PROJECT = os.getenv("GCP_PROJECT")
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION")
BUCKET_NAME = os.getenv("BUCKET_NAME")

# Fail-fast validation: Check for critical environment variables at startup.
if not all([GCP_PROJECT, VERTEX_LOCATION, BUCKET_NAME]):
    logging.error("FATAL: Missing critical environment variables. Ensure GCP_PROJECT, VERTEX_LOCATION, and BUCKET_NAME are set in your .env file.")
    sys.exit(1)

try:
    # Initialize the Vertex AI SDK globally. This should only be done once.
    vertexai.init(project=GCP_PROJECT, location=VERTEX_LOCATION)
    logging.info(f"Vertex AI initialized successfully for project '{GCP_PROJECT}' in '{VERTEX_LOCATION}'.")
except Exception as e:
    logging.error(f"FATAL: Error initializing Vertex AI: {e}", exc_info=True)
    sys.exit(1)
    
# --- Agent Instantiation ---

# Instantiate the main orchestrator agent. The ADK CLI will discover this
# 'root_agent' variable and serve it automatically.
root_agent = MarketingAgent()
