import json
import logging
from adk.agent import Agent
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
