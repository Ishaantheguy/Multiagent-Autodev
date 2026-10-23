import os
from crewai import LLM


def create_llm() -> LLM:
    model = os.getenv(
        "AUTODEV_MODEL",
        "gemini/gemini-3.5-flash-lite",
    )

    return LLM(
        model=model,
        temperature=0.2,
    )
