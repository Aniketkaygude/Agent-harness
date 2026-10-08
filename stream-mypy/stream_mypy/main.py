"""Main entry point for stream-mypy"""
import sys
import os
import asyncio
import argparse
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load .env from the same directory as this file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path, verbose=False)

from stream_mypy.providers import get_provider
from stream_mypy.agent import run_agent, TextEvent, ToolStartEvent, ToolEndEvent, TurnEndEvent
from stream_mypy.tools import tools
from stream_mypy.types import Message


async def main_async():
    """Main async function"""
    parser = argparse.ArgumentParser(description="Stream MyPI agent")
    parser.add_argument(
        "-p", "--prompt",
        type=str,
        required=True,
        help="The prompt to send to the agent",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default="anthropic",
        help="The provider to use (anthropic, anthropic-openai, groq)",
    )
    parser.add_argument(
        "--model",
        type=str,
        help="The model to use (optional, uses provider default if not specified)",
    )
    
    args = parser.parse_args()
    
    if not args.prompt:
        print('no prompt sirr, mypi -p "prompt" --provider anthropic OR groq')
        sys.exit(1)
    
    try:
        provider = get_provider(args.provider)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
    
    model = args.model or provider.default_model
    
    messages: List[Message] = [
        {"role": "user", "content": args.prompt}
    ]
    
    def on_event(event):
        if isinstance(event, TextEvent):
            sys.stdout.write(event.delta)
            sys.stdout.flush()
        elif isinstance(event, ToolStartEvent):
            print(f"\n {event.call['name']}")
        elif isinstance(event, ToolEndEvent):
            if event.is_error:
                print(f"\n {event.result}")
            else:
                lines = event.result.split("\n")
                print(f"\n {len(lines)}")
        elif isinstance(event, TurnEndEvent):
            msg = event.message
            usage = msg["usage"]
            stop_reason = msg["stopReason"]
            print(f"\n\n  {provider.name} ... {model} ... {usage['input']} ... {usage['output']} ... {stop_reason}")
    
    try:
        await run_agent(
            provider=provider,
            model=model,
            tools=tools,
            messages=messages,
            on_event=on_event,
        )
    except Exception as e:
        print(f"Agent error: {str(e)}")
        sys.exit(1)


def main():
    """Main entry point"""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
