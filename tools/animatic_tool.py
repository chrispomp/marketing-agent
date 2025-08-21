import os
import json
import time
import requests
from typing import Dict, Any

from google.adk.agents import LlmAgent, ToolContext
from ..utils.gcp import get_gcp_token, get_api_endpoint

Pin the models for production stability
GEMINI_MODEL = "gemini-1.5-pro-001"
VEO_MODEL = "veo-3.0-generate-preview" # As specified

async def _create_video_prompt_from_script(script: str, tool_context: ToolContext) -> str:
"""Internal helper to synthesize a script into a single, descriptive video prompt."""
prompt_agent = LlmAgent(
model=GEMINI_MODEL,
instruction="""
You are an expert video editor. Your task is to read the provided script and synthesize it into a single, descriptive, temporally-aware prompt for a video generation model like Veo.
The prompt should describe the visual flow of the entire commercial from start to finish.
Example: "A cinematic sequence starting with a close-up on a laptop, then a shot of a person smiling, followed by a wide shot of a futuristic city skyline, ending with the company logo appearing on screen."
"""
)
runner = tool_context.invocation_context.runner
final_prompt = ""
async for event in runner.run_sub_agent(agent=prompt_agent, user_message=script, invocation_context=tool_context.invocation_context):
if event.is_final_response() and event.content:
final_prompt = "".join(part.text for part in event.content.parts if part.text)
break
return final_prompt

async def _poll_lro(operation_name: str, headers: Dict[str, str]) -> Dict[str, Any]:
"""Polls a long-running operation until completion."""
api_endpoint = get_api_endpoint()
project_id = os.getenv("GCP_PROJECT")
polling_url = f"{api_endpoint}/projects/{project_id}/publishers/google/models/{VEO_MODEL}:fetchPredictOperation"

# Exponential backoff parameters
delay = 5  # Initial delay in seconds
max_delay = 60

while True:
    print(f"Polling LRO '{operation_name}'... waiting {delay}s")
    time.sleep(delay)
    
    response = requests.post(polling_url, headers=headers, json={"operationName": operation_name})
    response.raise_for_status()
    op_status = response.json()
    
    if op_status.get("done"):
        print("✅ LRO completed successfully.")
        return op_status
    
    # Increase delay for next poll
    delay = min(delay * 2, max_delay)
async def generate_full_animatic(
script: str,
tool_context: ToolContext
) -> str:
"""
Generates a video animatic from a script using the Veo API's long-running operation.

Args:
    script: The full text of the commercial script.
    tool_context: The context of the tool invocation.

Returns:
    A GCS URL to the generated MP4 video, or an error message.
"""
print("Step 1: Creating a video prompt from the script...")
video_prompt = await _create_video_prompt_from_script(script, tool_context)
if not video_prompt:
    return "Failed to create a video prompt from the script."
print(f"Generated Video Prompt: {video_prompt}")

project_id = os.getenv("GCP_PROJECT")
bucket_name = os.getenv("BUCKET_NAME")

if not all([project_id, bucket_name]):
    return "Error: GCP_PROJECT and BUCKET_NAME environment variables must be set."

token = get_gcp_token()
api_endpoint = get_api_endpoint()
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json; charset=utf-8",
}

# Step A: Initiate LRO
print("Step 2: Initiating video generation LRO with Veo...")
initiate_url = f"{api_endpoint}/projects/{project_id}/publishers/google/models/{VEO_MODEL}:predictLongRunning"
request_body = {
    "instances": [{"prompt": video_prompt}],
    "parameters": {
        "storageUri": f"gs://{bucket_name}/animatics/",
        "durationSeconds": 8,
        "aspectRatio": "16:9",
        "resolution": "720p",
        "generateAudio": True,
        "personGeneration": "allow_adult",
        "sampleCount": 1
    }
}

try:
    init_response = requests.post(initiate_url, headers=headers, json=request_body)
    init_response.raise_for_status()
    operation_name = init_response.json().get("operationName")
    if not operation_name:
        return f"Failed to start video generation. Response: {init_response.text}"
    
    print(f"LRO initiated. Operation Name: {operation_name}")
    tool_context.set_intermediate_response("I've started generating your animatic. This may take a minute...")
    
    # Step B & C: Poll and Parse
    final_result = await _poll_lro(operation_name, headers)
    
    video_uri = final_result.get("response", {}).get("videos", [{}])[0].get("gcsUri")
    if not video_uri:
        return f"Video generation finished, but could not find video URL in the final response: {json.dumps(final_result)}"

    return f"Animatic generation complete! You can view it here: {video_uri}"

except requests.exceptions.RequestException as e:
    error_msg = f"An API error occurred during animatic generation: {e}"
    if e.response is not None:
        error_msg += f" | Response: {e.response.text}"
    print(f"🔴 ERROR: {error_msg}")
    return error_msg
