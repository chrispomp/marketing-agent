#!/bin/bash

# ==============================================================================
#                 Marketing Agent Project Scaffolding Script (v2)
# ==============================================================================
# This script creates the full project structure and populates all necessary
# files for an enterprise-grade Marketing Agent using the Google ADK.
#
# Changelog (v2):
# - Corrected ADK package name in requirements.txt.
# - Updated all Python imports to use the 'google.adk' namespace as per
#   official documentation.
# - Updated Dockerfile CMD and README instructions for clarity and robustness.
# ==============================================================================

echo "🚀 Starting the setup for the Marketing Agent project..."

# Create the root project directory
mkdir -p marketing-agent
cd marketing-agent

# Create the core application structure
mkdir -p app/agents app/tools

# Create __init__.py files to designate directories as Python packages
touch app/__init__.py
touch app/agents/__init__.py
touch app/tools/__init__.py

echo "✅ Created project directory structure."

# --- Create and Populate Project Configuration Files ---

# requirements.txt
echo "📄 Creating requirements.txt with corrected libraries..."
cat << 'EOF' > requirements.txt
# Core ADK and GCP libraries
# NOTE: This is the correct package name for the Agent Development Kit.
google-cloud-agent-development-kit
google-cloud-aiplatform
python-dotenv

# Required for direct REST API calls with auth
google-api-python-client
EOF

# .env (Template for user configuration)
echo "🔑 Creating .env template file..."
cat << 'EOF' > .env
# ----------------------------------------------------
# --- Environment Variables for Marketing Agent ---
# ----------------------------------------------------
# Please fill in these values with your specific GCP configuration.

# Your Google Cloud Project ID
GCP_PROJECT="fsi-banking-agentspace"

# The region for Cloud Run / Agent Engine deployment (e.g., us-central1)
REGION="us-central1"

# The location for Vertex AI models (e.g., us-central1)
VERTEX_LOCATION="us-central1"

# The name of the GCS bucket for storing generated assets (images, videos)
# This bucket must exist in your GCP_PROJECT.
BUCKET_NAME="marketing-agent-assets"
EOF

# .gitignore
echo "🙈 Creating .gitignore..."
cat << 'EOF' > .gitignore
# Python artifacts
__pycache__/
*.py[cod]
*$py.class
*.so

# Environment variables
.env

# Virtual environments
.venv/
venv/
env/

# IDE and editor directories
.idea/
.vscode/
*.swp
EOF

# Dockerfile
echo "🐳 Creating Dockerfile for containerization..."
cat << 'EOF' > Dockerfile
# Use an official Python 3.11 slim runtime as a parent image
# This provides a lightweight and secure base.
FROM python:3.11-slim

# Set environment variables to ensure logs are sent straight to the console
# and to prevent Python from writing .pyc files.
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory inside the container to /app
WORKDIR /app

# Copy the requirements file first to leverage Docker layer caching.
# Dependencies will only be re-installed if requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire 'app' directory into the container at /app
COPY ./app /app

# Expose port 8080 to allow communication with the app
EXPOSE 8080

# Command to run the application using the ADK's built-in web server.
# This server automatically discovers the 'root_agent' in the specified module ('main.py'),
# serves the API, and provides a web-based test UI.
CMD ["adk", "web", "main:root_agent", "--host", "0.0.0.0", "--port", "8080"]
EOF

# --- Create and Populate Tool Logic Files ---

# app/tools/brief_tool.py
echo "🛠️  Creating app/tools/brief_tool.py..."
cat << 'EOF' > app/tools/brief_tool.py
import logging
from google.adk.tools import Tool
from vertexai.generative_models import GenerativeModel, Part

class BriefTool(Tool):
    """A tool for generating structured marketing briefs."""

    def __init__(self):
        super().__init__(
            name="generate_brief",
            description="Generates a structured marketing brief based on user input about a product or campaign.",
        )
        self.model = GenerativeModel("gemini-2.5-pro")
        self.system_prompt = """
You are an expert Marketing Strategist. Your task is to take a user's prompt and transform it into a professional, structured marketing brief.
The output MUST be in Markdown format.
The brief must contain the following sections:
- ## Objective: The primary goal of the campaign.
- ## Target Audience: A detailed description of the intended audience.
- ## Key Message: The single most important takeaway for the audience.
- ## Tone of Voice: The style and personality of the communication.
- ## Mandatories: Any legal disclaimers, brand guidelines, or required elements.
"""

    def _call(self, prompt: str) -> str:
        """Invokes the Gemini 2.5 Pro model to generate the marketing brief."""
        try:
            logging.info(f"Generating brief for prompt: {prompt}")
            full_prompt = [
                Part.from_text(self.system_prompt),
                Part.from_text(f"User Prompt: {prompt}")
            ]
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            logging.error(f"Error in BriefTool: {e}", exc_info=True)
            return "I'm sorry, I encountered an error while generating the brief. Please try again."
EOF

# app/tools/script_tool.py
echo "🛠️  Creating app/tools/script_tool.py..."
cat << 'EOF' > app/tools/script_tool.py
import logging
from google.adk.tools import Tool
from vertexai.generative_models import GenerativeModel, Part

class ScriptTool(Tool):
    """A tool for writing commercial scripts."""

    def __init__(self):
        super().__init__(
            name="generate_script",
            description="Writes a commercial script based on a marketing brief or user prompt.",
        )
        self.model = GenerativeModel("gemini-2.5-pro")
        self.system_prompt = """
You are a professional Screenwriter. Your task is to write a compelling commercial script.
The output MUST follow industry-standard screenplay format:
- SCENE HEADINGS (e.g., INT. COFFEE SHOP - DAY) in all caps.
- ACTION descriptions are in present tense.
- DIALOGUE is centered under the character's name.

Transform the provided brief/prompt into a complete script.
"""

    def _call(self, prompt_or_brief: str) -> str:
        """Invokes Gemini 2.5 Pro to generate the script."""
        try:
            logging.info("Generating script from brief/prompt...")
            full_prompt = [
                Part.from_text(self.system_prompt),
                Part.from_text(f"Input Brief/Prompt: {prompt_or_brief}")
            ]
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            logging.error(f"Error in ScriptTool: {e}", exc_info=True)
            return "I'm sorry, I had trouble writing the script. Please provide more details or try again."
EOF

# app/tools/storyboard_tools.py
echo "🛠️  Creating app/tools/storyboard_tools.py..."
cat << 'EOF' > app/tools/storyboard_tools.py
import os
import json
import logging
import uuid
from google.adk.tools import Tool
from vertexai.generative_models import GenerativeModel, Part
from google.cloud import aiplatform

# Environment variables are loaded in main.py and are available here
GCP_PROJECT = os.getenv("GCP_PROJECT")
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION")
BUCKET_NAME = os.getenv("BUCKET_NAME")

class ParseScriptTool(Tool):
    """A tool to parse a script into distinct visual scenes for a storyboard."""

    def __init__(self):
        super().__init__(
            name="parse_script_for_scenes",
            description="Analyzes a script and breaks it down into 3-5 distinct visual scenes, outputting JSON.",
        )
        self.model = GenerativeModel("gemini-2.5-pro")
        self.system_prompt = """
You are a film director's assistant. Your job is to read a script and identify 3-5 key visual moments for a storyboard.
- Analyze the provided script.
- Identify the most important, distinct scenes or key visual actions.
- For each moment, write a concise visual description suitable for an image generation model.
- Output ONLY a valid JSON array of objects. Each object must have two keys: "scene" (int) and "description" (str).

Example Output:
[
  {"scene": 1, "description": "Close up on a steaming cup of coffee on a rustic wooden table, morning light."},
  {"scene": 2, "description": "A young woman (Gen Z) smiles as she taps her phone, revealing a clean, modern financial app."},
  {"scene": 3, "description": "The woman confidently pays for her coffee using a sleek, minimalist credit card with a tap."}
]
"""

    def _call(self, script: str) -> str:
        try:
            logging.info("Parsing script for storyboard scenes...")
            full_prompt = [
                Part.from_text(self.system_prompt),
                Part.from_text(f"Script to analyze: {script}")
            ]
            response = self.model.generate_content(full_prompt)
            # Clean up potential markdown code fences from the LLM response
            cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
            json.loads(cleaned_response) # Validate that the output is valid JSON
            return cleaned_response
        except Exception as e:
            logging.error(f"Error in ParseScriptTool: {e}", exc_info=True)
            return '{"error": "Failed to parse the script into scenes."}'

class GenerateImageTool(Tool):
    """A tool to generate a single storyboard image using Imagen 4."""

    def __init__(self):
        super().__init__(
            name="generate_storyboard_image",
            description="Generates a single storyboard image using Imagen 4 based on a scene description.",
        )
        self.api_endpoint = f"{VERTEX_LOCATION}-aiplatform.googleapis.com"
        self.model_endpoint = f"projects/{GCP_PROJECT}/locations/{VERTEX_LOCATION}/publishers/google/models/imagen-4.0-generate-001"
            
    def _call(self, scene_description: str) -> str:
        try:
            job_id = str(uuid.uuid4())
            gcs_output_uri = f"gs://{BUCKET_NAME}/storyboards/{job_id}/"
            logging.info(f"Generating image for scene: '{scene_description}'. Outputting to: {gcs_output_uri}")

            instance = {
                "prompt": f"{scene_description}, cinematic storyboard style, high quality, professional grade, detailed illustration"
            }
            parameters = {
                "sampleCount": 1,
                "aspect_ratio": "16:9",
                "output_gcs_uri": gcs_output_uri,
                "person_generation": "allow_adult",
                "output_mime_type": "image/png"
            }
            
            client_options = {"api_endpoint": self.api_endpoint}
            client = aiplatform.gapic.PredictionServiceClient(client_options=client_options)
            
            # The predict method is synchronous for Imagen and waits for completion
            client.predict(
                endpoint=self.model_endpoint,
                instances=[instance],
                parameters=parameters,
            )
            
            # We construct the final GCS path. Imagen creates files like '0.png' inside the directory.
            generated_image_uri = f"{gcs_output_uri}0.png"
            logging.info(f"Successfully generated image: {generated_image_uri}")
            return generated_image_uri
        except Exception as e:
            logging.error(f"Error in GenerateImageTool: {e}", exc_info=True)
            return f"Error: Could not generate image for scene '{scene_description}'."
EOF

# app/tools/animatic_tools.py
echo "🛠️  Creating app/tools/animatic_tools.py..."
cat << 'EOF' > app/tools/animatic_tools.py
import os
import logging
from google.adk.tools import Tool
from vertexai.generative_models import GenerativeModel, Part
from google.cloud import aiplatform
from google.api_core.client_options import ClientOptions
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Value

# Environment variables are loaded in main.py
GCP_PROJECT = os.getenv("GCP_PROJECT")
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION")
BUCKET_NAME = os.getenv("BUCKET_NAME")

class CreateVideoPromptTool(Tool):
    """A tool to synthesize a script into a detailed prompt for Veo."""
    def __init__(self):
        super().__init__(
            name="create_video_prompt_from_script",
            description="Synthesizes a full script into a single, detailed, temporally-aware prompt for Veo.",
        )
        self.model = GenerativeModel("gemini-2.5-pro")
        self.system_prompt = """
You are a video editor creating a single, cohesive prompt for an AI video generation model (Veo) from a script.
Your task is to read the entire script and synthesize it into one flowing paragraph.
This paragraph must describe the visual actions sequentially. Use temporal cues like "First,", "Then,", "Next,", "The scene transitions to,", "Finally," to guide the video generation.
Focus ONLY on the visual action, camera movements, and mood. Do not include dialogue. The prompt should be rich in cinematic detail.

Example Input Script:
INT. COFFEE SHOP - DAY
A young WOMAN (20s) smiles at her phone.
...
Example Output Prompt:
"First, a cinematic close-up of a steaming coffee cup on a rustic table. Then, the camera pans up to a young Gen Z woman smiling as she looks at her phone, which displays a modern banking app with the message 'No Fees!'. Finally, she confidently taps her credit card at a terminal, with text overlay 'Financial Freedom'."
"""

    def _call(self, script: str) -> str:
        try:
            logging.info("Synthesizing script into a video prompt...")
            full_prompt = [Part.from_text(self.system_prompt), Part.from_text(f"Script to synthesize: {script}")]
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            logging.error(f"Error in CreateVideoPromptTool: {e}", exc_info=True)
            return "Error: Failed to create a video prompt from the script."


class GenerateAnimaticTool(Tool):
    """A tool to generate a video animatic from a prompt using Veo 3 via an LRO."""

    def __init__(self):
        super().__init__(
            name="generate_animatic_video",
            description="Generates a short video animatic from a prompt using Veo 3 via a Long-Running Operation.",
        )
        self.api_endpoint = f"{VERTEX_LOCATION}-aiplatform.googleapis.com"
        self.veo_model_uri = f"projects/{GCP_PROJECT}/locations/{VERTEX_LOCATION}/publishers/google/models/veo-3.0-generate-preview"
            
    def _call(self, video_prompt: str) -> str:
        try:
            client_options = ClientOptions(api_endpoint=self.api_endpoint)
            client = aiplatform.gapic.PredictionServiceClient(client_options=client_options)
            
            gcs_output_path = f"gs://{BUCKET_NAME}/animatics/"
            logging.info(f"Starting Veo LRO with prompt: '{video_prompt}'. Outputting to: {gcs_output_path}")

            instance_dict = {"prompt": video_prompt}
            instance = json_format.ParseDict(instance_dict, Value())

            parameters_dict = {
                "storageUri": gcs_output_path,
                "durationSeconds": 8, # Fixed per Veo 3 preview documentation
                "aspectRatio": "16:9",
                "resolution": "720p",
                "generateAudio": True,
                "personGeneration": "allow_adult",
                "sampleCount": 1
            }
            parameters = json_format.ParseDict(parameters_dict, Value())
            
            # This updated implementation correctly uses the LRO method and waits for the result.
            lro_response = client.predict_long_running(
                endpoint=self.veo_model_uri,
                instances=[instance],
                parameters=parameters,
            )

            logging.info("Veo LRO initiated. Waiting for completion (this may take a few minutes)...")
            result = lro_response.result(timeout=300) # Wait for up to 5 minutes
            logging.info("Veo LRO complete. Parsing response.")

            prediction_value = result.predictions[0]
            prediction_dict = json_format.MessageToDict(prediction_value)

            if "gcsUri" in prediction_dict:
                final_video_uri = prediction_dict['gcsUri']
                logging.info(f"Video generation successful. GCS URI: {final_video_uri}")
                return f"Video generation complete. Your animatic is available at: {final_video_uri}"
            else:
                logging.error(f"Veo LRO finished but no GCS URI found in response: {prediction_dict}")
                return "Error: Video generation finished, but the output path could not be determined."

        except Exception as e:
            logging.error(f"Error in GenerateAnimaticTool: {e}", exc_info=True)
            return "Error: An unexpected error occurred while generating the animatic video."
EOF

# --- Create and Populate Agent Logic Files ---

# app/agents/brief_writer.py
echo "🤖 Creating app/agents/brief_writer.py..."
cat << 'EOF' > app/agents/brief_writer.py
from google.adk.agents import Agent
from app.tools.brief_tool import BriefTool

class BriefWriter(Agent):
    """A specialized agent that crafts structured marketing briefs from user prompts."""
    def __init__(self):
        super().__init__(
            name="BriefWriter",
            description="Use this agent when the user wants to create, draft, or write a marketing brief.",
        )
        self.add_tool(BriefTool())
EOF

# app/agents/script_writer.py
echo "🤖 Creating app/agents/script_writer.py..."
cat << 'EOF' > app/agents/script_writer.py
from google.adk.agents import Agent
from app.tools.script_tool import ScriptTool

class ScriptWriter(Agent):
    """A specialized agent that generates industry-standard commercial scripts."""
    def __init__(self):
        super().__init__(
            name="ScriptWriter",
            description="Use this agent when the user wants to create, draft, or write a commercial, ad, or video script.",
        )
        self.add_tool(ScriptTool())
EOF

# app/agents/storyboard_artist.py
echo "🤖 Creating app/agents/storyboard_artist.py..."
cat << 'EOF' > app/agents/storyboard_artist.py
import json
import logging
from google.adk.agents import Agent
from app.tools.storyboard_tools import ParseScriptTool, GenerateImageTool

class StoryboardArtist(Agent):
    """A specialized agent that transforms a script into a visual storyboard."""

    def __init__(self):
        super().__init__(
            name="StoryboardArtist",
            description="Use this agent when the user wants to create or generate a visual storyboard from a script.",
        )
        # These tools are orchestrated internally by the agent's resolve method.
        self._parse_tool = ParseScriptTool()
        self._image_tool = GenerateImageTool()

    def resolve(self, prompt: str) -> str:
        """
        Orchestrates the two-step storyboard process:
        1. Parse the script (which is the input prompt) to get scenes.
        2. Generate an image for each scene.
        """
        logging.info("StoryboardArtist: Beginning storyboard creation process.")
        
        # Step 1: Parse script to scenes
        scene_json_str = self._parse_tool(prompt)
        
        try:
            scenes = json.loads(scene_json_str)
            if "error" in scenes or not isinstance(scenes, list):
                logging.error(f"Failed to parse script. Response: {scene_json_str}")
                return "I'm sorry, I couldn't understand the structure of the script to create scenes."
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON from ParseScriptTool: {scene_json_str}")
            return "I'm sorry, I had trouble breaking the script down into scenes."

        logging.info(f"StoryboardArtist: Found {len(scenes)} scenes. Generating images...")
        
        # Step 2: Generate an image for each scene
        image_urls = []
        for i, scene in enumerate(scenes, 1):
            desc = scene.get("description")
            if desc:
                logging.info(f"Generating image for scene {i}: {desc}")
                image_url = self._image_tool(desc)
                # Append the result, whether it's a URL or an error message
                image_urls.append(image_url)
            else:
                image_urls.append(f"Scene {i} had no description and was skipped.")

        # Format the final output for the user
        result = "Here is your storyboard:\n" + "\n".join([f"- Scene {i+1}: {url}" for i, url in enumerate(image_urls)])
        return result
EOF

# app/agents/animatic_creator.py
echo "🤖 Creating app/agents/animatic_creator.py..."
cat << 'EOF' > app/agents/animatic_creator.py
import logging
from google.adk.agents import Agent
from app.tools.animatic_tools import CreateVideoPromptTool, GenerateAnimaticTool

class AnimaticCreator(Agent):
    """A specialized agent that creates a short video animatic from a script."""

    def __init__(self):
        super().__init__(
            name="AnimaticCreator",
            description="Use this agent when the user wants to create, make, or generate a video, animatic, or movie from a script.",
        )
        self._prompt_tool = CreateVideoPromptTool()
        self._video_tool = GenerateAnimaticTool()

    def resolve(self, prompt: str) -> str:
        """
        Orchestrates the two-step animatic process:
        1. Synthesize the script into a video prompt.
        2. Generate the video with Veo.
        """
        logging.info("AnimaticCreator: Beginning animatic creation process.")
        
        # Step 1: Synthesize script into a detailed video prompt
        video_prompt = self._prompt_tool(prompt)
        
        if "Error:" in video_prompt:
            logging.error(f"Failed to create video prompt. Response: {video_prompt}")
            return video_prompt

        logging.info("AnimaticCreator: Generated video prompt. Now starting video generation.")
        
        # Acknowledge the long-running operation to the user before starting
        print("Starting animatic generation. This may take a few minutes...")

        # Step 2: Generate video with Veo
        video_result = self._video_tool(video_prompt)
        
        return video_result
EOF


# --- Create and Populate Orchestrator Agent and Main App Entrypoint ---

# app/marketing_agent.py
echo "👑 Creating orchestrator agent in app/marketing_agent.py..."
cat << 'EOF' > app/marketing_agent.py
from google.adk.agents import Agent
from google.adk.config import STORE_CONVERSATIONS
from vertexai.generative_models import GenerativeModel

from app.agents.brief_writer import BriefWriter
from app.agents.script_writer import ScriptWriter
from app.agents.storyboard_artist import StoryboardArtist
from app.agents.animatic_creator import AnimaticCreator

# Enable conversation history for multi-turn interactions
STORE_CONVERSATIONS = True

class MarketingAgent(Agent):
    """
    An orchestrator agent that acts as a creative co-pilot. It routes tasks 
    for brief writing, script writing, storyboarding, and animatic creation 
    to specialized sub-agents.
    """
    def __init__(self):
        super().__init__(
            name="MarketingAgent",
            description="A creative co-pilot for generating marketing content like briefs, scripts, storyboards, and animatics.",
            model=GenerativeModel("gemini-2.5-pro")
        )
        
        # Add the specialized sub-agents. The orchestrator uses their
        # descriptions to decide which one to route a user's request to.
        self.add_sub_agent(BriefWriter())
        self.add_sub_agent(ScriptWriter())
        self.add_sub_agent(StoryboardArtist())
        self.add_sub_agent(AnimaticCreator())

    def resolve(self, prompt: str) -> str:
        """
        Main entry point for the Marketing Agent. It uses Gemini's reasoning
        to select and delegate to the correct sub-agent.
        """
        # The base Agent class's resolve method handles the routing logic.
        # It matches the user's prompt against the sub-agents' descriptions.
        # For sub-agents with custom resolve methods (like StoryboardArtist),
        # that method will be automatically called.
        return super().resolve(prompt)
EOF

# app/main.py
echo "🏁 Creating main entrypoint in app/main.py..."
cat << 'EOF' > app/main.py
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
EOF

# README.md
echo "📖 Creating README.md with detailed instructions..."
cat << 'EOF' > README.md
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
Run the `create_project.sh` script to generate the project structure and code.

**B. Set Up Environment Variables**
Open the `.env` file and replace the placeholder values with your actual GCP configuration.

```ini
# .env
GCP_PROJECT="your-gcp-project-id"
REGION="us-central1"
VERTEX_LOCATION="us-central1"
BUCKET_NAME="your-unique-gcs-bucket-name"