#!/usr/bin/env python

import sys
import warnings
from datetime import datetime

from autodev.crew import Autodev
from pathlib import Path

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def run():
    """Run AutoDev with a user-provided software request."""

    request = " ".join(sys.argv[1:]).strip()

    if not request:
        request = input(
            "Describe the software you want AutoDev to build:\n> "
        ).strip()
        
        if request.startswith("@"):
            prompt_file = Path(request[1:]).expanduser()
            request = prompt_file.read_text(encoding="utf-8").strip()

    if not request:
        raise ValueError("A software development request is required.")

    inputs = {
        "user_request": request,
        "current_year": str(datetime.now().year),
    }

    try:
        result = Autodev().crew().kickoff(inputs=inputs)
        print("\nAutoDev execution completed.")
        print(result)
    except Exception as e:
        raise RuntimeError(
            f"An error occurred while running AutoDev: {e}"
        ) from e


def train():
    """Train the crew using the standard CrewAI interface."""

    inputs = {
        "user_request": "Build a Python calculator with unit tests.",
        "current_year": str(datetime.now().year),
    }

    try:
        Autodev().crew().train(
            n_iterations=int(sys.argv[1]),
            filename=sys.argv[2],
            inputs=inputs,
        )
    except Exception as e:
        raise RuntimeError(f"Training failed: {e}") from e


def replay():
    """Replay a crew execution from a specific task."""

    try:
        Autodev().crew().replay(task_id=sys.argv[1])
    except Exception as e:
        raise RuntimeError(f"Replay failed: {e}") from e


def test():
    """Test the crew execution."""

    inputs = {
        "user_request": "Build a Python calculator with unit tests.",
        "current_year": str(datetime.now().year),
    }

    try:
        Autodev().crew().test(
            n_iterations=int(sys.argv[1]),
            eval_llm=sys.argv[2],
            inputs=inputs,
        )
    except Exception as e:
        raise RuntimeError(f"Crew test failed: {e}") from e
