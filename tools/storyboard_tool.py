import os
import json
import uuid
import time
import requests
from typing import List, Dict, Any

from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext

# Pin the models for production stability
GEMINI_MODEL = "gemini-2.5-flash"
# This is the recommended model for quality. See https://ai.google.dev/gemini-api/docs/models/imagen
IMAGEN_MODEL = "imagen-3.0-generate-001"

# Use the official Gemini API endpoint
GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

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
Your response must be perfect, valid JSON.
"""
    )
    runner = tool_context.invocation_context.runner
    json_response = ""
    async for event in runner.run_sub_agent(agent=parser_agent, user_message=script, invocation_context=tool_context.invocation_context):
        if event.is_final_response() and event.content:
            raw_text = "".join(part.text for part in event.content.parts if part.text)
            # Clean up potential markdown code blocks
            json_response = raw_text.strip().replace("json", "").replace("`", "").strip()
            break
    try:
        return json.loads(json_response)
    except json.JSONDecodeError as e:
        error_message = f"Error: The scene parser returned invalid JSON. Please try again. Raw output: {json_response}"
        print(f"🔴 {error_message}")
        # Re-raise the exception to be caught by the main function
        raise ValueError(error_message) from e

async def _poll_image_lro(operation_name: str, headers: Dict[str, str]) -> Dict[str, Any]:
    """Polls a long-running operation for Imagen until completion."""
    polling_url = f"{GEMINI_API_BASE_URL}/{operation_name}"
    delay = 5  # Initial delay in seconds

    while True:
        print(f"Polling Image LRO '{operation_name}'... waiting {delay}s")
        time.sleep(delay)

        response = requests.get(polling_url, headers=headers)
        response.raise_for_status()
        op_status = response.json()

        if op_status.get("done"):
            print("✅ Image LRO completed successfully.")
            return op_status

        print("Image LRO not finished, polling again.")
        delay = min(delay * 2, 30)


async def _generate_image(scene_description: str, job_id: str, scene_number: int, tool_context: ToolContext) -> str:
    """Internal helper to call the Imagen 3 Gemini API and return a temporary URL."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable must be set.")

    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }

    initiate_url = f"{GEMINI_API_BASE_URL}/models/{IMAGEN_MODEL}:generateImage"
    request_body = {
        "prompt": f"A detailed, high-quality, cinematic storyboard panel. Style: professional, clean lines, dynamic composition. Scene: {scene_description}",
        "aspect_ratio": "16:9",
        "negative_prompt": "text, watermark, signature, ugly, deformed",
        "person_generation": "allow_all"
    }

    init_response = requests.post(initiate_url, headers=headers, json=request_body)
    init_response.raise_for_status()

    operation_name = init_response.json().get("name")
    if not operation_name:
        raise ValueError(f"Failed to start image generation. Response: {init_response.text}")

    print(f"Image LRO initiated for scene {scene_number}. Operation Name: {operation_name}")

    final_result = await _poll_image_lro(operation_name, headers)

    image_data = final_result.get("response", {}).get("generated_images", [{}])[0]
    if not image_data:
        raise ValueError("API did not return image data in final LRO response.")

    temp_url = image_data.get("url")
    print(f"✅ Successfully generated temporary image URL for scene {scene_number}: {temp_url}")
    return temp_url

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
        A JSON string containing an ordered list of temporary URLs for the storyboard images.
    """
    scenes = await _parse_script_for_scenes(script, tool_context)
    if not scenes:
        return "Could not parse the script into scenes. Please try again."

    job_id = str(uuid.uuid4())
    image_urls = []

    tool_context.set_intermediate_response(f"I've parsed the script into {len(scenes)} scenes. Now, I'll start generating the images one by one. This might take a few moments.")

    for i, scene in enumerate(scenes):
        try:
            description = scene.get("description")
            scene_num = scene.get("scene")
            if description and scene_num:
                tool_context.set_intermediate_response(f"Generating image for scene {scene_num}/{len(scenes)}: '{description}'...")
                # Pass tool_context to the image generation function
                gcs_url = await _generate_image(description, job_id, scene_num, tool_context)
                image_urls.append({"scene": scene_num, "url": gcs_url})
        except Exception as e:
            error_message = f"Failed to generate image for scene {scene.get('scene', 'N/A')}: {e}"
            print(f"🔴 ERROR: {error_message}")
            image_urls.append({"scene": scene.get('scene', 'N/A'), "error": error_message})

    return json.dumps(image_urls, indent=2)
