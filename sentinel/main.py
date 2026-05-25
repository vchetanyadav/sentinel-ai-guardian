import asyncio
from dotenv import load_dotenv

load_dotenv()

from google.adk.runners import InMemoryRunner
from google.genai import types
from agent import create_sentinel


async def main():
    agent = create_sentinel()
    runner = InMemoryRunner(agent=agent, app_name="sentinel-cli")
    
    user_id = "operator"
    session = await runner.session_service.create_session(
        app_name="sentinel-cli",
        user_id=user_id,
    )
    
    user_message = types.Content(
        role="user",
        parts=[types.Part(text=(
            "RefundBot may have a regression. Check the last 15 minutes of traffic, "
            "diagnose any issues, propose a fix, and resolve it under human oversight."
        ))],
    )
    
    print("\n" + "="*60)
    print("🤖 SENTINEL ACTIVATED")
    print("="*60 + "\n")
    
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session.id,
        new_message=user_message,
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text)
                if part.function_call:
                    print(f"  → tool: {part.function_call.name}({dict(part.function_call.args)})")
                if part.function_response:
                    response = part.function_response.response
                    preview = str(response)[:200]
                    print(f"  ← result: {preview}")
    
    print("\n" + "="*60)
    print("🤖 SENTINEL FINISHED")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())