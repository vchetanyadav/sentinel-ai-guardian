# sentinel-ai-guardian
Sentinel :- an AI observability agent built on Vertex AI Agent Builder (Gemini 3) and Arize Phoenix MCP. Sentinel watches production LLM applications, detects quality regressions, diagnoses likely causes, and proposes prompt rollbacks with human approval. Built for the Google Cloud Rapid Agent Hackathon 2026.
Sentinel

An autonomous AI agent that monitors a live AI system, reasons about its behaviour, and flags unreliable or unsafe outputs to a human before they reach users.

Sentinel is built around a perceive to reason to act loop: it observes a target system's outputs, runs a multi-step reasoning process with tool calls, evaluates the quality and reliability of what it sees, and escalates anything that looks wrong. It is my exploration of a question I care about: how do you catch an AI being confidently wrong, and keep a human in the loop when it matters?

What it does
Perceive - ingests outputs and signals from a live AI system (or a stream of model responses) for review.
Reason - works through a multi-step reasoning loop, calling tools to gather context and check facts rather than deciding in a single pass.
Act - produces structured, machine-readable decisions (for example: pass, flag, escalate) rather than free text, so the result can drive a workflow.
Evaluate - scores outputs for quality and reliability, and records why a decision was made.
Guardrails and human-in-the-loop - when confidence is low or a response trips a guardrail, Sentinel routes it to a human for review instead of letting it through.
Observability - logs each decision and its reasoning so behaviour can be audited and improved over time.
How it works
Target AI output
      |
      v
  Perceive  ->  Reason (multi-step loop, tool calls)  ->  Evaluate
                                                              |
                                        pass <----------------+----------------> flag / escalate
                                          |                                             |
                                          v                                             v
                                     continue                                  human review (guardrail)

The agent keeps context and state across steps in a single review, uses tool calling to fetch what it needs, and returns a structured verdict with a short rationale. The evaluation step is deliberately separate from the reasoning step, so the judgement about reliability is made explicitly rather than buried inside the generation.

Tech stack
Language: Python
AI / LLM: large language models via API, with prompt and instruction design for the reasoning and evaluation steps
Core ideas: agent loop, tool / function calling, structured outputs, output evaluation, guardrails, human-in-the-loop
Tooling: Git for version control; tests for the core logic

Customise: list the exact libraries and model provider you used (for example the specific LLM SDK, any agent framework, and how you store logs), so the stack is precise.

Getting started
bash
# clone
git clone https://github.com/vchetanyadav/sentinel.git
cd sentinel

# set up a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# install dependencies
pip install -r requirements.txt

# configure your API key
# create a .env file with your model provider key, for example:
# LLM_API_KEY=your_key_here

# run
python main.py

Customise: replace the clone URL with your real repository name, and confirm the install and run commands match your project (entry-point file name, requirements file, and any config or environment variables it needs).

What I learned
Where AI is confidently wrong. The hardest and most interesting part was not generating answers, it was judging them. Output that reads as correct is often not, so a separate, explicit evaluation step matters more than a better prompt.
Structure beats free text. Forcing the agent to return structured decisions made the whole system easier to test, reason about and build a workflow around.
Humans belong in the loop. Designing a clear escalation path, rather than trusting the model end to end, is what makes something like this safe to actually use.
Possible next steps
Add a small dashboard to view flagged cases and decision history.
Expand the evaluation checks and make the guardrail thresholds configurable.
Add more tools for the reasoning step to draw on.
