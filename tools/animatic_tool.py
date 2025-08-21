import os
import json
import time
import requests
from typing import Dict, Any

from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext
# Switched to Gemini API, so we only need the API key from the environment
# from utils.gcp import get_gcp_token, get_api_endpoint

# Pin the models for production stability
GEMINI_MODEL = "gemini-2.5-flash"
VEO_MODEL = "veo-3.0-generate-preview" # As specified in Gemini API docs

# Use the official Gemini API endpoint
GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


async def _create_video_prompt_from_script(script: str, tool_context: ToolContext) -> str:
    """Internal helper to synthesize a script into a single, descriptive video prompt."""
    prompt_agent = LlmAgent(
        model=GEMINI_MODEL,
        instruction="""
You are an expert video editor. Your task is to read the provided script and synthesize it into a single, descriptive, temporally-aware prompt for a video generation model like Veo.
The prompt should describe the visual flow of the entire commercial from start to finish, focusing on the key visual moments.
It is crucial to include cues for audio, such as dialogue in quotes (e.g., "This is amazing!") or sound effects (e.g., SFX: a car horn honks).
Example: 'A cinematic sequence starting with a close-up on a laptop, then a shot of a person smiling, "I love this!", followed by a wide shot of a futuristic city skyline with the sound of flying cars (SFX: whoosh), ending with the company logo appearing on screen.'
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
    """Polls a long-running operation until completion using the Gemini API style."""
    polling_url = f"{GEMINI_API_BASE_URL}/{operation_name}"
    delay = 10  # Poll every 10 seconds as recommended in docs

    while True:
        print(f"Polling LRO '{operation_name}'... waiting {delay}s")
        time.sleep(delay)

        response = requests.get(polling_url, headers=headers)
        response.raise_for_status()
        op_status = response.json()

        if op_status.get("done"):
            print("✅ LRO completed successfully.")
            return op_status

        print("LRO not finished, polling again.")


async def generate_full_animatic(
    script: str,
    tool_context: ToolContext
) -> str:
    """
    Generates a video animatic from a script using the Veo Gemini API's long-running operation.

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

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY environment variable must be set."

    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }

    # Step A: Initiate LRO
    print("Step 2: Initiating video generation LRO with Veo...")
    initiate_url = f"{GEMINI_API_BASE_URL}/models/{VEO_MODEL}:predictLongRunning"
    # See https://ai.google.dev/gemini-api/docs/video for options
    request_body = {
        "instances": [{"prompt": video_prompt}],
        "parameters": {
            "aspectRatio": "16:9",
            "personGeneration": "allow_all",
            "negativePrompt": "cartoon, drawing, low quality, text, watermark"
            # durationSeconds, resolution, and generateAudio are determined by the model (Veo 3 = 8s, 720p, with audio)
            # storageUri is not used in the Gemini API; videos are temporarily stored and must be downloaded.
        }
    }

    try:
        init_response = requests.post(initiate_url, headers=headers, json=request_body)
        init_response.raise_for_status()
        operation_name = init_response.json().get("name") # Gemini API returns 'name'
        if not operation_name:
            return f"Failed to start video generation. Response: {init_response.text}"

        print(f"LRO initiated. Operation Name: {operation_name}")
        tool_context.set_intermediate_response("I've started generating your animatic. This may take a minute or two...")

        # Step B & C: Poll and Parse
        final_result = await _poll_lro(operation_name, headers)

        # The final downloadable video URI is in a different place in the Gemini API response
        video_uri = final_result.get("response", {}).get("generateVideoResponse", {}).get("generatedSamples", [{}])[0].get("video", {}).get("uri")
        if not video_uri:
            return f"Video generation finished, but could not find video URL in the final response: {json.dumps(final_result)}"

        # Note: The URI from Gemini API is temporary. For a real app, you'd download this and re-upload to your own GCS bucket.
        # For this agent, we'll just return the temporary link.
        return f"Animatic generation complete! You can view it here: {video_uri}"

    except requests.exceptions.RequestException as e:
        error_msg = f"An API error occurred during animatic generation: {e}"
        if e.response is not None:
            error_msg += f" | Response: {e.response.text}"
        print(f"🔴 ERROR: {error_msg}")
        return error_msg
