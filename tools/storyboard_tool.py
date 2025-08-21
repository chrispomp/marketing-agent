import os
import json
import uuid
import requests
from typing import List, Dict, Any

from google.adk.agents import LlmAgent, ToolContext
from ..utils.gcp import get_gcp_token, get_api_endpoint

Pin the models for production stability
GEMINI_MODEL = "gemini-1.5-pro-001"
IMAGEN_MODEL = "imagen-4.0-generate-001" # As specified

async def _parse_script_for_scenes(script: str, tool_context: ToolContext) -> List[Dict[str, Any]]:
"""Internal helper to parse a script into JSON scenes using an LLM."""
parser_agent = LlmAgent(
model=GEMINI_MODEL,
instruction="""
You are a film director's assistant. Your task is to read the provided script and identify 3-5 key visual moments that are perfect for a storyboard.
For each moment, provide a concise, descriptive prompt for an image generation model.
Your output MUST be a valid JSON array of objects, where each object has two keys: 'scene' (an integer) and 'description' (a string).
Example: [{"scene": 1, "description": "A close-up shot of a steaming cup of coffee on a modern kitchen counter, morning light streaming in."}, {"scene": 2, "description": "A woman with a joyful expression, running through a field of wildflowers."}]
Do not output any text other than the JSON array.
"""
)
runner = tool_context.invocation_context.runner
json_response = ""
async for event in runner.run_sub_agent(agent=parser_agent, user_message=script, invocation_context=tool_context.invocation_context):
if event.is_final_response() and event.content:
raw_text = "".join(part.text for part in event.content.parts if part.text)
# Clean up potential markdown code blocks
json_response = raw_text.strip().replace("json", "").replace("", "").strip()
break
try:
return json.loads(json_response)
except json.JSONDecodeError:
print(f"🔴 ERROR: Failed to decode JSON from scene parser: {json_response}")
return []

async def _generate_image(scene_description: str, job_id: str, scene_number: int) -> str:
"""Internal helper to call the Imagen 4 API and return a GCS URL."""
project_id = os.getenv("GCP_PROJECT")
bucket_name = os.getenv("BUCKET_NAME")

if not all([project_id, bucket_name]):
    raise ValueError("GCP_PROJECT and BUCKET_NAME environment variables must be set.")

token = get_gcp_token()
api_endpoint = get_api_endpoint()

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json; charset=utf-8",
}

# Imagen saves outputs in a directory, we'll name the file `scene_{n}.png`
output_gcs_dir = f"gs://{bucket_name}/storyboards/{job_id}/"
output_gcs_path = f"{output_gcs_dir}scene_{scene_number}.png"

request_body = {
    "instances": [
        {
            "prompt": f"{scene_description}, cinematic storyboard style, high quality, professional grade"
        }
    ],
    "parameters": {
        "sampleCount": 1,
        "aspect_ratio": "16:9",
        "output_gcs_uri": f"{output_gcs_dir}scene_{scene_number}", # API expects URI without extension
        "person_generation": "allow_adult",
        "output_mime_type": "image/png"
    }
}

url = f"{api_endpoint}/projects/{project_id}/publishers/google/models/{IMAGEN_MODEL}:predict"

response = requests.post(url, headers=headers, json=request_body)
response.raise_for_status() # Raise an exception for bad status codes

# The API confirms the output location, but we already know it.
print(f"✅ Successfully generated image for scene {scene_number} at {output_gcs_path}")
return output_gcs_path
async def generate_full_storyboard(
script: str,
tool_context: ToolContext
) -> str:
"""
Generates a full storyboard by parsing a script into scenes and creating an image for each.

Args:
    script: The full text of the commercial script.
    tool_context: The context of the tool invocation.

Returns:
    A JSON string containing an ordered list of GCS URLs for the storyboard images.
"""
scenes = await _parse_script_for_scenes(script, tool_context)
if not scenes:
    return "Could not parse the script into scenes. Please try again."

job_id = str(uuid.uuid4())
image_urls = []

for scene in scenes:
    try:
        description = scene.get("description")
        scene_num = scene.get("scene")
        if description and scene_num:
            gcs_url = await _generate_image(description, job_id, scene_num)
            image_urls.append({"scene": scene_num, "url": gcs_url})
    except Exception as e:
        error_message = f"Failed to generate image for scene {scene.get('scene', 'N/A')}: {e}"
        print(f"🔴 ERROR: {error_message}")
        image_urls.append({"scene": scene.get('scene', 'N/A'), "error": error_message})
        
return json.dumps(image_urls, indent=2)
