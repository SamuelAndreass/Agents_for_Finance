from crewai import Agent, Crew, Task, Process
from tools.fundamental_analysis import FundamentalAnalysisTool
from tools.technical_analysis import TechnicalAnalysisTool
from tools.macroeconom_analysis import MacroeconomicTool
import yaml

class FinancialCrew:
    def __init__(self, api_key: None):
        with open("config/agents.yaml") as f:
            self.agents_config = yaml.safe_load(f)
        with open("config/tasks.yaml") as f:
            self.tasks_config = yaml.safe_load(f)

    def fundamental(self) -> Agent:
        return Agent(
            config=self.agents_config['fundamental'],
            tools=[FundamentalAnalysisTool()],
            verbose=True,
            allow_delegation=False,
        )

    def technical_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['technical'],
            tools=[TechnicalAnalysisTool()],
            verbose=True,
            allow_delegation=False,
        )

    def macro(self) -> Agent:
        return Agent(
            config=self.agents_config['macro'],
            tools=[MacroeconomicTool()],
            verbose=True,
            allow_delegation=False,
        )

    def summarizer(self) -> Agent:
        return Agent(
            config=self.agents_config['summarizer'],
            tools=[],
            verbose=True,
            allow_delegation=False,
        )

    def intent_router(self) -> Agent:
        return Agent(
            config=self.agents_config['intent_router'],
            tools=[],
            verbose=True,
            allow_delegation=False,
        )

    def conversational_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['conversational_agent'],
            tools=[],
            verbose=True,
            allow_delegation=False,
        )

    # Tasks
    def macro_task(self) -> Task:
        return Task(
            config=self.tasks_config['macro_task'],
            agent=self.macro()
        )

    def technical_task(self) -> Task:
        return Task(
            config=self.tasks_config['technical_task'],
            agent=self.technical_agent()
        )

    def fundamental_task(self) -> Task:
        return Task(
            config=self.tasks_config['fundamental_task'],
            agent=self.fundamental()
        )

    def summarizer_task(self) -> Task:
        return Task(
            config=self.tasks_config['summarizer_task'],
            agent=self.summarizer()
        )

    def intent_router_task(self) -> Task:
        return Task(
            config=self.tasks_config['intent_router_task'],
            agent=self.intent_router()
        )

    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.intent_router(),
                self.fundamental(),
                self.technical_agent(),
                self.macro(),
                self.summarizer(),
                self.conversational_agent(),
            ],
            tasks=[
                self.intent_router_task(),
                self.fundamental_task(),
                self.technical_task(),
                self.macro_task(),
                self.summarizer_task(),
            ],
            process=Process.sequential,
            verbose=True
        )
