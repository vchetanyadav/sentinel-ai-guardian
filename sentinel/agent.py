import os
from dotenv import load_dotenv

load_dotenv()

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from prompts import SENTINEL_SYSTEM_PROMPT
import tools

# Wrap each function as an ADK FunctionTool
SENTINEL_TOOLS = [
    FunctionTool(tools.compute_metric_window),
    FunctionTool(tools.detect_regression),
    FunctionTool(tools.list_phoenix_prompts),
    FunctionTool(tools.deploy_prompt_version),
    FunctionTool(tools.run_dataset_evaluation),
    FunctionTool(tools.open_incident),
    FunctionTool(tools.update_incident),
    FunctionTool(tools.request_human_approval),
]


def create_sentinel() -> LlmAgent:
    return LlmAgent(
        model="gemini-3.1-pro-preview",
        name="sentinel",
        description="Autonomous SRE agent for production LLM applications",
        instruction=SENTINEL_SYSTEM_PROMPT,
        tools=SENTINEL_TOOLS,
    )