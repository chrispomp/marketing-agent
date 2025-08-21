import os
import sys
import json
import logging
import uuid
from dotenv import load_dotenv

import vertexai
from google.cloud import aiplatform
from google.api_core.client_options import ClientOptions
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Value

from google.adk.agents import Agent
from google.adk.tools import Tool, FunctionTool
from vertexai.generative_models import GenerativeModel, Part

# ==============================================================================
#                      CONFIGURATION & INITIALIZATION
# ==============================================================================

# Configure structured logging for clear, actionable output.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    stream=sys.stdout
)

# Load environment variables from the .env file.
load_dotenv()

GCP_PROJECT = os.getenv("GCP_PROJECT")
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION")
BUCKET_NAME = os.getenv("BUCKET_NAME")

# Fail-fast validation for critical environment variables.
if not all([GCP_PROJECT, VERTEX_LOCATION, BUCKET_NAME]):
    logging.error("FATAL: Missing environment variables. Set GCP_PROJECT, VERTEX_LOCATION, and BUCKET_NAME in .env")
    sys.exit(1)

try:
    # Initialize the Vertex AI SDK globally.
    vertexai.init(project=GCP_PROJECT, location=VERTEX_LOCATION)
    logging.info(f"Vertex AI initialized for project '{GCP_PROJECT}' in '{VERTEX_LOCATION}'.")
except Exception as e:
    logging.error(f"FATAL: Error initializing Vertex AI: {e}", exc_info=True)
    sys.exit(1)

# ==============================================================================
#                            STANDALONE TOOL CLASSES
# ==============================================================================

class BriefTool(Tool):
    """Generates a structured marketing brief from a user prompt."""

    def __init__(self):
        super().__init__(
            name="generate_marketing_brief",
            description="Use this when the user wants to create, draft, or write a marketing brief.",
        )
        self.model = GenerativeModel("gemini-2.5-flash")
        self.system_prompt = """You are an expert Marketing Strategist. Transform the user's prompt into a professional, structured marketing brief in Markdown format. The brief must contain: ## Objective, ## Target Audience, ## Key Message, ## Tone of Voice, and ## Mandatories."""

    def _call(self, prompt: str) -> str:
        """Invokes the Gemini model to generate the marketing brief."""
        try:
            logging.info(f"Generating brief for prompt: {prompt}")
            response = self.model.generate_content([self.system_prompt, f"User Prompt: {prompt}"])
            return response.text
        except Exception as e:
            logging.error(f"Error in BriefTool: {e}", exc_info=True)
            return "Error: I encountered a problem while generating the brief."

class ScriptTool(Tool):
    """Writes a commercial script from a marketing brief or user prompt."""

    def __init__(self):
        super().__init__(
            name="generate_commercial_script",
            description="Use this when the user wants to create, draft, or write a commercial, ad, or video script.",
        )
        self.model = GenerativeModel("gemini-1.5-pro-001")
        self.system_prompt = """You are a professional Screenwriter. Write a compelling commercial script based on the provided input. The output MUST follow industry-standard screenplay format (SCENE HEADINGS, ACTION, DIALOGUE)." """

    def _call(self, prompt_or_brief: str) -> str:
        """Invokes the Gemini model to generate the script."""
        try:
            logging.info("Generating script from brief/prompt...")
            response = self.model.generate_content([self.system_prompt, f"Input Brief/Prompt: {prompt_or_brief}"])
            return response.text
        except Exception as e:
            logging.error(f"Error in ScriptTool: {e}", exc_info=True)
            return "Error: I had trouble writing the script."

# ==============================================================================
#                  MULTI-STEP ORCHESTRATION FUNCTIONS & TOOLS
# ==============================================================================

def create_storyboard(script: str) -> str:
    """
    Orchestrates the two-step process of creating a storyboard from a script.
    It first parses the script into scenes, then generates an image for each scene.
    
    Args:
        script: The full text of the commercial script.

    Returns:
        A formatted string containing the results, including URLs to the generated images.
    """
    logging.info("Starting storyboard creation process...")
    # --- Step 1: Parse script into scenes ---
    parser_model = GenerativeModel("gemini-1.5-pro-001")
    parser_prompt = """You are a film director's assistant. Read the script and identify 3-5 key visual moments. For each moment, write a concise visual description for an image model. Output ONLY a valid JSON array of objects, where each object has keys "scene" (int) and "description" (str)."""
    
    try:
        response = parser_model.generate_content([parser_prompt, f"Script: {script}"])
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
        scenes = json.loads(cleaned_response)
        if "error" in scenes or not isinstance(scenes, list):
            raise ValueError("Model returned a structured error.")
    except (json.JSONDecodeError, ValueError) as e:
        logging.error(f"Failed to parse script into scenes. Response: {cleaned_response}. Error: {e}")
        return "I'm sorry, I had trouble breaking the script down into visual scenes."
    
    logging.info(f"Successfully parsed {len(scenes)} scenes. Generating images...")
    
    # --- Step 2: Generate an image for each scene ---
    image_urls = []
    api_endpoint = f"{VERTEX_LOCATION}-aiplatform.googleapis.com"
    model_endpoint = f"projects/{GCP_PROJECT}/locations/{VERTEX_LOCATION}/publishers/google/models/imagen-4.0-generate-001"
    client_options = {"api_endpoint": api_endpoint}
    client = aiplatform.gapic.PredictionServiceClient(client_options=client_options)

    for i, scene in enumerate(scenes, 1):
        desc = scene.get("description")
        if not desc:
            image_urls.append(f"Scene {i} was skipped (no description).")
            continue
            
        try:
            gcs_output_uri = f"gs://{BUCKET_NAME}/storyboards/{uuid.uuid4()}/"
            instance = {"prompt": f"{desc}, cinematic storyboard style, high quality, professional grade"}
            parameters = {"sampleCount": 1, "aspect_ratio": "16:9", "output_gcs_uri": gcs_output_uri}
            
            client.predict(endpoint=model_endpoint, instances=[instance], parameters=parameters)
            generated_image_uri = f"{gcs_output_uri}0.png"
            image_urls.append(generated_image_uri)
            logging.info(f"Generated image for scene {i}: {generated_image_uri}")
        except Exception as e:
            logging.error(f"Error generating image for scene {i}: {e}", exc_info=True)
            image_urls.append(f"Error generating image for scene {i}.")

    result = "Here is your storyboard:\n" + "\n".join([f"- Scene {i+1}: {url}" for i, url in enumerate(image_urls)])
    return result

def create_animatic(script: str) -> str:
    """
    Orchestrates creating a video animatic from a script using Veo.
    First, it synthesizes the script into a single, detailed video prompt.
    Then, it calls the Veo model via a Long-Running Operation to generate the video.

    Args:
        script: The full text of the commercial script.

    Returns:
        A string with the status and GCS URI of the generated video.
    """
    logging.info("Starting animatic creation process...")
    # --- Step 1: Synthesize a video prompt from the script ---
    prompt_creator_model = GenerativeModel("gemini-1.5-pro-001")
    prompt_creator_system_prompt = """You are a video editor creating a single, cohesive prompt for Veo from a script. Read the script and synthesize it into one flowing paragraph describing the visual actions sequentially. Use temporal cues like "First,", "Then,", "Next,". Focus ONLY on visual action, camera movements, and mood. Do not include dialogue."""
    
    try:
        response = prompt_creator_model.generate_content([prompt_creator_system_prompt, f"Script: {script}"])
        video_prompt = response.text
    except Exception as e:
        logging.error(f"Failed to create video prompt: {e}", exc_info=True)
        return "Error: Could not synthesize the script into a video prompt."

    logging.info("Video prompt created. Initiating Veo LRO...")
    print("Starting animatic generation. This may take a few minutes...")

    # --- Step 2: Generate video with Veo LRO ---
    try:
        api_endpoint = f"{VERTEX_LOCATION}-aiplatform.googleapis.com"
        veo_model_uri = f"projects/{GCP_PROJECT}/locations/{VERTEX_LOCATION}/publishers/google/models/veo-3.0-generate-preview"
        client_options = ClientOptions(api_endpoint=api_endpoint)
        client = aiplatform.gapic.PredictionServiceClient(client_options=client_options)
        
        gcs_output_path = f"gs://{BUCKET_NAME}/animatics/"
        instance = json_format.ParseDict({"prompt": video_prompt}, Value())
        parameters = json_format.ParseDict({
            "storageUri": gcs_output_path, "durationSeconds": 8, "aspectRatio": "16:9",
            "resolution": "720p", "generateAudio": True, "sampleCount": 1
        }, Value())
        
        lro_response = client.predict_long_running(endpoint=veo_model_uri, instances=[instance], parameters=parameters)
        result = lro_response.result(timeout=300)
        
        prediction_dict = json_format.MessageToDict(result.predictions[0])
        final_video_uri = prediction_dict.get('gcsUri')
        if final_video_uri:
            logging.info(f"Video generation successful: {final_video_uri}")
            return f"Video generation complete! Your animatic is at: {final_video_uri}"
        else:
            logging.error(f"Veo LRO finished but no GCS URI found: {prediction_dict}")
            return "Error: Video generation finished, but the output path is missing."
    except Exception as e:
        logging.error(f"Error during Veo generation: {e}", exc_info=True)
        return "Error: An unexpected problem occurred while generating the animatic."

# ==============================================================================
#                  ROOT AGENT (ORCHESTRATOR) DEFINITION
# ==============================================================================

class MarketingAgent(Agent):
    """
    A creative co-pilot for generating marketing content. It uses its tools to
    handle requests for briefs, scripts, storyboards, and video animatics.
    """
    def __init__(self):
        super().__init__(
            name="MarketingAgent",
            description="A creative co-pilot for marketing content creation.",
            model="gemini-1.5-pro-001",
            tools=[
                BriefTool(),
                ScriptTool(),
                FunctionTool(
                    func=create_storyboard,
                    description="Use this when the user wants to create a visual storyboard from a script.",
                ),
                FunctionTool(
                    func=create_animatic,
                    description="Use this when the user wants to create a video, movie, or animatic from a script.",
                ),
            ],
        )

# Instantiate the main agent. The ADK CLI will discover this variable.
root_agent = MarketingAgent()
