from adk.agent import Agent
from app.tools.script_tool import ScriptTool

class ScriptWriter(Agent):
    """A specialized agent that generates industry-standard commercial scripts."""
    def __init__(self):
        super().__init__(
            name="ScriptWriter",
            description="Use this agent when the user wants to create, draft, or write a commercial, ad, or video script.",
        )
        self.add_tool(ScriptTool())
