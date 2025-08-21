import os
from dotenv import load_dotenv

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool, AgentTool

# Import the tool functions
from tools.brief_tool import generate_brief
from tools.script_tool import generate_script
from tools.storyboard_tool import generate_full_storyboard
from tools.animatic_tool import generate_full_animatic

# Load environment variables from .env file
load_dotenv()

# Pin the orchestrator model for production stability
ORCHESTRATOR_MODEL = "gemini-2.5-flash"

# --- 1. Define Specialist Agents ---
brief_writer_agent = LlmAgent(
    name="BriefWriter",
    model=ORCHESTRATOR_MODEL,
    description="Writes structured marketing briefs based on user requirements.",
    instruction="Your sole purpose is to use the generate_brief tool to create a marketing brief.",
    tools=[FunctionTool(generate_brief)],
)

script_writer_agent = LlmAgent(
    name="ScriptWriter",
    model=ORCHESTRATOR_MODEL,
    description="Writes professionally formatted commercial scripts. It can use the context of a previously created brief in the conversation.",
    instruction="Your sole purpose is to use the generate_script tool. Analyze the user prompt and the conversation history to create the script.",
    tools=[FunctionTool(generate_script)],
)

storyboard_artist_agent = LlmAgent(
    name="StoryboardArtist",
    model=ORCHESTRATOR_MODEL,
    description="Creates a visual storyboard from a script. It identifies key scenes and generates an image for each.",
    instruction="Your sole purpose is to use the generate_full_storyboard tool. You must pass the entire script from the conversation history into the tool.",
    tools=[FunctionTool(generate_full_storyboard)],
)

animatic_creator_agent = LlmAgent(
    name="AnimaticCreator",
    model=ORCHESTRATOR_MODEL,
    description="Creates a simple video animatic with audio from a script. This is a long-running process.",
    instruction="Your sole purpose is to use the generate_full_animatic tool. Pass the full script from the conversation into the tool. Inform the user that the process has started.",
    tools=[FunctionTool(generate_full_animatic)],
)

# --- 2. Define the Orchestrator (Root) Agent ---
root_agent = LlmAgent(
    name="MarketingAgent",
    model=ORCHESTRATOR_MODEL,
    description="The primary marketing agent that orchestrates creative tasks.",
    global_instruction="""
You are the lead Creative Director of a marketing agency.
Your role is to understand the user's request and delegate it to the correct specialist agent on your team.

If the user asks for a 'brief', 'plan', or 'strategy', use the 'BriefWriter'.

If the user asks for a 'script' or 'ad copy', use the 'ScriptWriter'.

If the user asks for a 'storyboard', 'visuals', or 'scenes', use the 'StoryboardArtist'.

If the user asks for a 'video', 'animatic', or 'movie', use the 'AnimaticCreator'.

Maintain a helpful, professional, and encouraging tone. Acknowledge the user's request clearly before delegating.
""",
    # The tools of the root agent are the other agents
    tools=[
        AgentTool(agent=brief_writer_agent),
        AgentTool(agent=script_writer_agent),
        AgentTool(agent=storyboard_artist_agent),
        AgentTool(agent=animatic_creator_agent),
    ],
)
