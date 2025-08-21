from adk.agent import Agent
from adk.config import STORE_CONVERSATIONS
from vertexai.generative_models import GenerativeModel

from app.agents.brief_writer import BriefWriter
from app.agents.script_writer import ScriptWriter
from app.agents.storyboard_artist import StoryboardArtist
from app.agents.animatic_creator import AnimaticCreator

# Enable conversation history for multi-turn interactions
STORE_CONVERSATIONS = True

class MarketingAgent(Agent):
    """
    A creative co-pilot that orchestrates brief writing, script writing, 
    storyboarding, and animatic creation by routing tasks to specialized sub-agents.
    """
    def __init__(self):
        super().__init__(
            name="MarketingAgent",
            description="A creative co-pilot for marketing content generation.",
            model=GenerativeModel("gemini-2.5-pro")
        )
        
        # Add the specialized sub-agents. The orchestrator will use their
        # descriptions to decide which one to route a user's request to.
        self.add_sub_agent(BriefWriter())
        self.add_sub_agent(ScriptWriter())
        self.add_sub_agent(StoryboardArtist())
        self.add_sub_agent(AnimaticCreator())

    def resolve(self, prompt: str) -> str:
        """
        This is the main entry point for the Marketing Agent.
        It uses Gemini 2.5's reasoning to select the correct sub-agent.
        """
        # The base Agent class's resolve method handles routing to the correct 
        # sub-agent based on its description and tools. For sub-agents with 
        # custom resolve methods (like StoryboardArtist), that method will be called.
        return super().resolve(prompt)
