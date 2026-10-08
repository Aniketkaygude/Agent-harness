"""Provider factory"""
import os
from stream_mypy.types import Provider
from stream_mypy.providers.anthropic import create_anthropic
from stream_mypy.providers.openai_compat import create_openai_compat


PROVIDERS = {
    "anthropic": create_anthropic,
    "anthropic-openai": lambda: create_openai_compat(
        "anthropic-openai",
        "https://api.anthropic.com/v1/",
        os.getenv("ANTHROPIC_API_KEY"),
        "claude-sonnet-4-20250514",
    ),
    "groq": lambda: create_openai_compat(
        "groq",
        "https://api.groq.com/openai/v1",
        os.getenv("GROQ_API_KEY"),
        "mixtral-8x7b-32768",
    ),
}


def get_provider(name: str) -> Provider:
    """Get a provider by name"""
    create_func = PROVIDERS.get(name)
    if not create_func:
        raise RuntimeError(f"Unknown provider: {name}")
    return create_func()
