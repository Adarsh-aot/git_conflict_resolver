from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from git_conflict_resolver.tools.git_conflict_finder_tool import GitConflictFinderTool
from git_conflict_resolver.tools.git_conflict_resolver_tool import GitConflictResolverTool
from typing import List
import os

gemini_llm = LLM(
    model="gemini/gemini-2.0-flash-001",
    api_key=os.environ.get("GEMINI_API_KEY"),
    temperature=0
)

@CrewBase
class GitConflictResolverCrew:
    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def conflict_detector(self) -> Agent:
        return Agent(
            config=self.agents_config["conflict_detector"],
            tools=[GitConflictFinderTool()],
            llm=gemini_llm,
            verbose=True
        )

    @agent
    def conflict_resolver(self) -> Agent:
        return Agent(
            config=self.agents_config["conflict_resolver"],
            tools=[GitConflictResolverTool()],
            llm=gemini_llm,
            verbose=True
        )

    @agent
    def summary_reporter(self) -> Agent:
        return Agent(
            config=self.agents_config["summary_reporter"],
            llm=gemini_llm,
            verbose=True
        )

    @task
    def detect_conflicts_task(self) -> Task:
        return Task(config=self.tasks_config["detect_conflicts_task"])

    @task
    def resolve_conflicts_task(self) -> Task:
        return Task(config=self.tasks_config["resolve_conflicts_task"])

    @task
    def summary_task(self) -> Task:
        return Task(config=self.tasks_config["summary_task"])

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
