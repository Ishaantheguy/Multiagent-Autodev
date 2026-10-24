from pathlib import Path

import yaml
from crewai import Agent, Crew, Process, Task

from autodev.utils.llm import create_llm
from autodev.tools.workspace import WriteWorkspaceFile


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = Path(__file__).resolve().parent / "config"

def load_yaml(filename: str) -> dict:
    """Load a YAML configuration file."""
    path = CONFIG_DIR / filename

    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML configuration: {path}")

    return data


class Autodev:
    """AutoDev autonomous software engineering crew."""

    def __init__(self, workspace_path: str | Path):
        self.workspace_path = Path(workspace_path).resolve()
        self.workspace_path.mkdir(parents=True, exist_ok=True)

        self.agents_config = load_yaml("agents.yaml")
        self.tasks_config = load_yaml("tasks.yaml")

        self._validate_config()

    def _validate_config(self) -> None:
        """Validate agent and task configuration names."""
        required_agents = {
            "product_analyst",
            "software_architect",
            "software_developer",
            "test_engineer",
            "code_reviewer",
        }

        missing_agents = required_agents - self.agents_config.keys()

        if missing_agents:
            raise ValueError(
                f"Missing agent configurations: {sorted(missing_agents)}"
            )

        for task_name, config in self.tasks_config.items():
            agent_name = config.get("agent")

            if agent_name not in self.agents_config:
                raise ValueError(
                    f"Task '{task_name}' references unknown agent "
                    f"'{agent_name}'"
                )

    def build_crew(self) -> Crew:
        """Build the crew with a job-specific file-writing tool."""

        llm = create_llm()

        # Construct agents explicitly.
        product_analyst = Agent(
            config=self.agents_config["product_analyst"],
            llm=llm,
            verbose=True,
        )

        software_architect = Agent(
            config=self.agents_config["software_architect"],
            llm=llm,
            verbose=True,
        )

        software_developer = Agent(
            config=self.agents_config["software_developer"],
            llm=llm,
            tools=[
                WriteWorkspaceFile(
                    workspace_path=self.workspace_path
                )
            ],
            verbose=True,
            max_iter=8,
        )

        test_engineer = Agent(
            config=self.agents_config["test_engineer"],
            llm=llm,
            verbose=True,
        )

        code_reviewer = Agent(
            config=self.agents_config["code_reviewer"],
            llm=llm,
            verbose=True,
        )

        # Construct tasks explicitly, preserving their dependencies.
        analyse_requirements = Task(
            config=self.tasks_config["analyse_requirements"],
            agent=product_analyst,
        )

        design_architecture = Task(
            config=self.tasks_config["design_architecture"],
            agent=software_architect,
            context=[analyse_requirements],
        )

        implement_software = Task(
            config=self.tasks_config["implement_software"],
            agent=software_developer,
            context=[
                analyse_requirements,
                design_architecture,
            ],
        )

        review_software = Task(
            config=self.tasks_config["review_software"],
            agent=code_reviewer,
            context=[
                analyse_requirements,
                design_architecture,
                implement_software,
            ],
        )

        return Crew(
            agents=[
                product_analyst,
                software_architect,
                software_developer,
                test_engineer,
                code_reviewer,
            ],
            tasks=[
                analyse_requirements,
                design_architecture,
                implement_software,
                review_software,
            ],
            process=Process.sequential,
            verbose=True,
        )

    def crew(self) -> Crew:
        """Compatibility method for callers expecting crew()."""
        return self.build_crew()
