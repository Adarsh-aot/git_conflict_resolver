from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from git_conflict_resolver.tools.custom_tool import GitConflictFinderTool, GitConflictResolverTool
from typing import List
import os

# llm = LLM(
#     provider="ollama",
#     model="llama3",
#     base_url="http://localhost:11434"
# )

gemini_llm = LLM(
       model="gemini/gemini-2.0-flash-001",  # Or specify your desired Gemini model
       api_key=os.environ.get("GEMINI_API_KEY"),
       temperature=0.7  # Adjust temperature as needed
   )

@CrewBase
class GitConflictResolverCrew:
    """A crew for resolving Git conflicts using the GitConflictResolverTool."""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def conflict_detector(self) -> Agent:
        return Agent(
            config=self.agents_config["conflict_detector"],
            tools=[GitConflictFinderTool()],
            max_iter=3,
            llm = gemini_llm ,
            max_execution_time=60,
            verbose=True
        )

    @agent
    def conflict_resolver(self) -> Agent:
        return Agent(
           config=self.agents_config["conflict_resolver"],
            tools=[GitConflictResolverTool()],
            max_iter=3,
            llm = gemini_llm ,
            verbose=True
        )

    @agent
    def summary_reporter(self) -> Agent:
        return Agent(
            config=self.agents_config['summary_reporter'],
            llm=gemini_llm,
            verbose=True
        )

    @task
    def detect_conflicts_task(self) -> Task:
        
        return Task(
            config=self.tasks_config['detect_conflicts_task'], # type: ignore[index]
            output_file='conflicts.md'
        )

    @task
    def resolve_conflicts_task(self) -> Task:
        return Task(
            config=self.tasks_config['resolve_conflicts_task'], # type: ignore[index]
            output_file='report.md'
        )

    @task
    def summary_task(self) -> Task:
        return Task(
            config=self.tasks_config['summary_task'], # type: ignore[index]
            output_file='report.md'
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
