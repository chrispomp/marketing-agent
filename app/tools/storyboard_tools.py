import os
import json
import logging
import uuid
from adk.tools import Tool
from vertexai.generative_models import GenerativeModel, Part
from google.cloud import aiplatform
from google.api_core.client_options import ClientOptions

# Environment variables are loaded in main.py
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
            cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
            json.loads(cleaned_response) # Validate JSON format
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
        # Endpoint needs to be constructed with the correct region
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
            
            # The predict method is synchronous for Imagen
            response = client.predict(
                endpoint=self.model_endpoint,
                instances=[instance],
                parameters=parameters,
            )
            
            # Imagen response for GCS output doesn't contain the direct path in predictions.
            # We construct it based on the output URI we provided. Imagen creates files like '0.png'.
            generated_image_uri = f"{gcs_output_uri}0.png"
            logging.info(f"Successfully generated image: {generated_image_uri}")
            return generated_image_uri
        except Exception as e:
            logging.error(f"Error in GenerateImageTool: {e}", exc_info=True)
            return f"Error: Could not generate image for scene '{scene_description}'."
