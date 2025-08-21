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

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from vertexai.generative_models import GenerativeModel

# ==============================================================================
#                      CONFIGURATION & INITIALIZATION
# ==============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    stream=sys.stdout
)
load_dotenv()

GCP_PROJECT = os.getenv("GCP_PROJECT")
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION")
BUCKET_NAME = os.getenv("BUCKET_NAME")

if not all([GCP_PROJECT, VERTEX_LOCATION, BUCKET_NAME]):
    logging.error("FATAL: Missing environment variables. Set GCP_PROJECT, VERTEX_LOCATION, and BUCKET_NAME in .env")
    sys.exit(1)

try:
    vertexai.init(project=GCP_PROJECT, location=VERTEX_LOCATION)
    logging.info(f"Vertex AI initialized for project '{GCP_PROJECT}' in '{VERTEX_LOCATION}'.")
except Exception as e:
    logging.error(f"FATAL: Error initializing Vertex AI: {e}", exc_info=True)
    sys.exit(1)

# ==============================================================================
#                               AGENT TOOLS
# ==============================================================================

def generate_marketing_brief(prompt: str) -> str:
    """Use this when the user wants to create, draft, or write a marketing brief."""
    model = GenerativeModel("gemini-1.5-flash")
    system_prompt = """You are an expert Marketing Strategist. Transform the user's prompt into a professional, structured marketing brief in Markdown format. The brief must contain: ## Objective, ## Target Audience, ## Key Message, ## Tone of Voice, and ## Mandatories."""
    try:
        logging.info(f"Generating brief for prompt: {prompt}")
        response = model.generate_content([system_prompt, f"User Prompt: {prompt}"])
        return response.text
    except Exception as e:
        logging.error(f"Error in generate_marketing_brief: {e}", exc_info=True)
        return "Error: I encountered a problem while generating the brief."

def generate_commercial_script(prompt_or_brief: str) -> str:
    """Use this when the user wants to create, draft, or write a commercial, ad, or video script."""
    model = GenerativeModel("gemini-1.5-pro-001")
    system_prompt = """You are a professional Screenwriter. Write a compelling commercial script based on the provided input. The output MUST follow industry-standard screenplay format (SCENE HEADINGS, ACTION, DIALOGUE)."""
    try:
        logging.info("Generating script from brief/prompt...")
        response = model.generate_content([system_prompt, f"Input Brief/Prompt: {prompt_or_brief}"])
        return response.text
    except Exception as e:
        logging.error(f"Error in generate_commercial_script: {e}", exc_info=True)
        return "Error: I had trouble writing the script."

def create_storyboard(script: str) -> str:
    """Use this when the user wants to create a visual storyboard from a script."""
    logging.info("Starting storyboard creation process...")
    parser_model = GenerativeModel("gemini-1.5-pro-001")
    parser_prompt = """You are a film director's assistant. Read the script and identify 3-5 key visual moments. For each moment, write a concise visual description for an image model. Output ONLY a valid JSON array of objects, where each object has a key "description" (str)."""
    
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
    
    image_urls = []
    api_endpoint = f"{VERTEX_LOCATION}-aiplatform.googleapis.com"
    client_options = {"api_endpoint": api_endpoint}
    client = aiplatform.gapic.PredictionServiceClient(client_options=client_options)
    
    # NOTE: This is a placeholder for the correct Imagen 3 model endpoint.
    # You may need to update this if the model name changes.
    model_endpoint = (
        f"projects/{GCP_PROJECT}/locations/{VERTEX_LOCATION}/"
        "publishers/google/models/imagen-3.0-generate-001"
    )

    for i, scene in enumerate(scenes, 1):
        desc = scene.get("description")
        if not desc:
            image_urls.append(f"Scene {i} was skipped (no description).")
            continue
            
        try:
            gcs_output_uri = f"gs://{BUCKET_NAME}/storyboards/{uuid.uuid4()}/"
            # Using Protobuf `Value` for instance and parameters
            instance = json_format.ParseDict({
                "prompt": f"{desc}, cinematic storyboard style, high quality, professional grade"
            }, Value())
            parameters = json_format.ParseDict({
                "sampleCount": 1, "aspectRatio": "16:9", "outputGcsUri": gcs_output_uri
            }, Value())
            
            request = aiplatform.gapic.PredictRequest(
                endpoint=model_endpoint,
                instances=[instance],
                parameters=parameters
            )
            
            client.predict(request=request)
            
            # Assuming the image is named '0.png' in the output directory
            generated_image_uri = f"https://storage.googleapis.com/{BUCKET_NAME}/storyboards/{gcs_output_uri.split('/')[-2]}/0.png"
            image_urls.append(generated_image_uri)
            logging.info(f"Generated image for scene {i}: {generated_image_uri}")
        except Exception as e:
            logging.error(f"Error generating image for scene {i}: {e}", exc_info=True)
            image_urls.append(f"Error generating image for scene {i}.")

    result = "Here is your storyboard:\n" + "\n".join([f"- Scene {i+1}: {url}" for i, url in enumerate(image_urls)])
    return result

def create_animatic(script: str) -> str:
    """Use this when the user wants to create a video, movie, or animatic from a script."""
    logging.info("Starting animatic creation process...")
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

    try:
        api_endpoint = f"{VERTEX_LOCATION}-aiplatform.googleapis.com"
        client_options = ClientOptions(api_endpoint=api_endpoint)
        client = aiplatform.gapic.PredictionServiceClient(client_options=client_options)
        
        gcs_output_path = f"gs://{BUCKET_NAME}/animatics/"
        
        # NOTE: This is a placeholder for the correct Veo model endpoint.
        # You may need to update this if the model name changes.
        veo_model_uri = (
            f"projects/{GCP_PROJECT}/locations/{VERTEX_LOCATION}/"
            "publishers/google/models/veo-2.0-generate-001"
        )
        
        instance = json_format.ParseDict({"prompt": video_prompt}, Value())
        parameters = json_format.ParseDict({
            "storageUri": gcs_output_path, "durationSeconds": 8, "aspectRatio": "16:9",
            "resolution": "720p", "generateAudio": True, "sampleCount": 1
        }, Value())
        
        request = aiplatform.gapic.PredictLongRunningRequest(
            endpoint=veo_model_uri,
            instances=[instance],
            parameters=parameters
        )
        
        lro_response = client.predict_long_running(request=request)
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

class MarketingAgent(LlmAgent):
    """A creative co-pilot for generating marketing content."""
    def __init__(self):
        super().__init__(
            name="MarketingAgent",
            description="A creative co-pilot for marketing content creation.",
            model="gemini-1.5-pro-001",
            tools=[
                FunctionTool(func=generate_marketing_brief),
                FunctionTool(func=generate_commercial_script),
                FunctionTool(func=create_storyboard),
                FunctionTool(func=create_animatic),
            ],
        )

root_agent = MarketingAgent()