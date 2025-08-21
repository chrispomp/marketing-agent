import os
import logging
from adk.tools import Tool
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
    """A tool to generate a video animatic from a prompt using Veo via an LRO."""

    def __init__(self):
        super().__init__(
            name="generate_animatic_video",
            description="Generates a short video animatic from a prompt using Veo via a Long-Running Operation.",
        )
        self.api_endpoint = f"{VERTEX_LOCATION}-aiplatform.googleapis.com"
        # The full model URI is needed for the Model object
        self.model_name = f"projects/{GCP_PROJECT}/locations/{VERTEX_LOCATION}/publishers/google/models/veo-3.0-generate-preview"
        
    def _call(self, video_prompt: str) -> str:
        try:
            # Use the standard PredictionServiceClient for LROs
            client_options = {"api_endpoint": self.api_endpoint}
            client = aiplatform.PredictionServiceClient(client_options=client_options)
            
            model = aiplatform.Model(model_name=self.model_name)

            gcs_output_path = f"gs://{BUCKET_NAME}/animatics/"
            logging.info(f"Starting Veo LRO with prompt: '{video_prompt}'. Outputting to: {gcs_output_path}")

            # Parameters are passed directly as a dict
            parameters = {
                "storageUri": gcs_output_path,
                "durationSeconds": 8,
                "aspectRatio": "16:9",
                "resolution": "720p",
                "generateAudio": True,
                "personGeneration": "allow_adult",
                "sampleCount": 1
            }
            
            # Use long_running_predict for robust LRO handling
            lro_job = model.long_running_predict(
                instances=[{"prompt": video_prompt}],
                parameters=parameters,
            )
            
            logging.info(f"Veo LRO job started: {lro_job}. Waiting for result...")

            # This blocks until the LRO is complete
            result = lro_job.result()
            
            logging.info("Veo LRO complete. Parsing response.")

            # The result object contains the predictions
            if not result.predictions:
                logging.error("Veo LRO finished but returned no predictions.")
                return "Error: Video generation failed to produce a result."

            # Robustly parse the prediction to find the GCS URI
            prediction = result.predictions[0]
            if isinstance(prediction, dict) and "gcsUri" in prediction:
                final_video_uri = prediction.get("gcsUri")
                logging.info(f"Video generation successful. GCS URI: {final_video_uri}")
                return f"Video generation complete. Your animatic is available at: {final_video_uri}"
            else:
                logging.error(f"Veo LRO finished but no GCS URI found in response: {prediction}")
                return "Error: Video generation finished, but the output path could not be determined."

        except Exception as e:
            logging.error(f"Error in GenerateAnimaticTool: {e}", exc_info=True)
            return "Error: An unexpected error occurred while generating the animatic video."
