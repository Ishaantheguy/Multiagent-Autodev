from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent

from autodev.utils.llm import create_llm
from autodev.tools.workspace import WriteWorkspaceFile


@CrewBase
class Autodev:
    """AutoDev autonomous software engineering crew."""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def product_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["product_analyst"],
            llm=create_llm(),
            verbose=True,
        )

    @agent
    def software_architect(self) -> Agent:
        return Agent(
            config=self.agents_config["software_architect"],
            llm=create_llm(),
            verbose=True,
        )

    @agent
    def software_developer(self) -> Agent:
        return Agent(
            config=self.agents_config["software_developer"],
            llm=create_llm(),
            tools=[WriteWorkspaceFile()],
            verbose=True,
            max_iter=8,
        )

    @agent
    def test_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["test_engineer"],
            llm=create_llm(),
            verbose=True,
        )

    @agent
    def code_reviewer(self) -> Agent:
        return Agent(
            config=self.agents_config["code_reviewer"],
            llm=create_llm(),
            verbose=True,
        )

    @task
    def analyse_requirements(self) -> Task:
        return Task(
            config=self.tasks_config["analyse_requirements"],
            agent=self.product_analyst(),
        )

    @task
    def design_architecture(self) -> Task:
        return Task(
            config=self.tasks_config["design_architecture"],
            agent=self.software_architect(),
            context=[self.analyse_requirements()],
        )

    @task
    def implement_software(self) -> Task:
        return Task(
            config=self.tasks_config["implement_software"],
            agent=self.software_developer(),
            context=[
                self.analyse_requirements(),
                self.design_architecture(),
            ],
        )

    @task
    def review_software(self) -> Task:
        return Task(
            config=self.tasks_config["review_software"],
            agent=self.code_reviewer(),
            context=[
                self.analyse_requirements(),
                self.implement_software(),
            ],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the AutoDev crew."""

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
