import logging
from adk.agent import Agent
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
