from crewai import Agent, Crew, Process, Task, AgentConfig, TaskConfig
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from .tools.custom_tool import GitConflictResolverTool
from typing import List
from crewai import LLM
from pathlib import Path

llm = LLM(
    model="ollama/llama3",
    base_url="http://localhost:11434"
)

@CrewBase
class GitConflictResolverCrew:
    """A crew for resolving Git conflicts using the GitConflictResolverTool."""

    agents: List[BaseAgent]
    tasks: List[Task]

    def __init__(self):
        self.git_tool = GitConflictResolverTool()

        # Load agent/task configs
        base_path = Path(__file__).parent / "config"
        self.agents_config = AgentConfig.load(base_path / "agents.yaml", indexed=True)
        self.tasks_config = TaskConfig.load(base_path / "tasks.yaml", indexed=True)

    @agent
    def conflict_detector(self) -> Agent:
        return Agent(
            config=self.agents_config['conflict_detector'],
            llm=llm,
            tools=[self.git_tool],
            max_iter=3,
            max_execution_time=60,
            verbose=True
        )

    @agent
    def conflict_resolver(self) -> Agent:
        return Agent(
            config=self.agents_config['conflict_resolver'],
            llm=llm,
            tools=[self.git_tool],
            max_iter=3,
            max_execution_time=60,
            verbose=True
        )

    @agent
    def summary_reporter(self) -> Agent:
        return Agent(
            config=self.agents_config['summary_reporter'],
            llm=llm,
            verbose=True
        )

    @task
    def detect_conflicts(self) -> Task:
        return Task(
            description=self.tasks_config['detect_conflicts_task']['description'],
            expected_output=self.tasks_config['detect_conflicts_task']['expected_output'],
            agent=self.conflict_detector()
        )

    @task
    def resolve_conflicts(self) -> Task:
        return Task(
            description=self.tasks_config['resolve_conflicts_task']['description'],
            expected_output=self.tasks_config['resolve_conflicts_task']['expected_output'],
            agent=self.conflict_resolver(),
            context=self.tasks_config['resolve_conflicts_task'].get('context', None)
        )

    @task
    def summary_task(self) -> Task:
        return Task(
            description=self.tasks_config['summary_task']['description'],
            expected_output=self.tasks_config['summary_task']['expected_output'],
            agent=self.summary_reporter(),
            context=self.tasks_config['summary_task'].get('context', None),
            output_file=self.tasks_config['summary_task'].get('output_file', 'conflict_summary.md')
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Conflict Resolver crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
