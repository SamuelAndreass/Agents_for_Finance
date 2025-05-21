from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
from tools.fundamental_analysis import FundamentalAnalysisTool
from tools.technical_analysis import TechnicalAnalysisTool
from tools.macroeconom_analysis import MacroeconomicTool

	
@CrewBase
class FinancialCrew():
	"""Financial crew"""

	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'
	
	@agent
	def journalist(self) -> Agent:
		return Agent(
			config=self.agents_config['journalist'],
			tools=[SerperDevTool()],
			verbose=True,
		)

	@agent
	def fundamental(self) -> Agent:
		return Agent(
			config=self.agents_config['fundamental'],
			tools=[FundamentalAnalysisTool()],
			verbose=True,
    		allow_delegation=False,
		)
	
	@agent
	def technical_agent(self) -> Agent:
		from tools.technical_analysis import TechnicalAnalysisTool
		return Agent(
			config=self.agents_config['technical'],
			tools=[TechnicalAnalysisTool()],
			verbose=True,
			allow_delegation=False,
		)



	@agent
	def macro(self) -> Agent:
		return Agent(
			config=self.agents_config['macro'],
			tools=[MacroeconomicTool()],
			verbose=True,
			allow_delegation=False,
		)
	
	@agent
	def reporter(self) -> Agent:
		return Agent(
			config=self.agents_config['reporter'],
			tools=[SerperDevTool()],
			verbose=True,
			allow_delegation=False,
		)
	
	@agent
	def intent_router(self) -> Agent:
		return Agent(
			config=self.agents_config['intent_router'],
			tools=[],
			verbose=True,
			allow_delegation=False,
		)
	
	@agent
	def summarizer(self) -> Agent:
		return Agent(
			config=self.agents_config['summarizer'],
			tools=[],  # You can add an LLM tool here if you want
			verbose=True,
			allow_delegation=False,
    )

	@agent
	def conversational_agent(self) -> Agent:
		return Agent(
			config=self.agents_config['conversational_agent'],
			tools=[],
			verbose=True,
			allow_delegation=False
	)

	@task
	def technical_task(self) -> Task:
		return Task(
			config=self.tasks_config['technical_task'],
			agent=self.technical_agent()
		)


	@task
	def conversational_agent(self) -> Task:
		return Task(
			config=self.tasks_config['conversational_agent_task'],
			agent=self.interface()
	)


	@task
	def summarizer_task(self) -> Task:
		return Task(
			config=self.tasks_config['summarizer_task'],
			agent=self.summarizer()
    )

	@task
	def macro_task(self) -> Task:
		return Task(
			config=self.tasks_config['macro_task'],
			agent=self.macro()
		)
	
	@task
	def fundamental_task(self) -> Task:
		return Task(
			config=self.tasks_config['fundamental_task'],
			agent=self.fundamental()
		)

	@task
	def intent_router_task(self) -> Task:
		return Task(
			config=self.tasks_config['intent_router_task'],
			agent=self.intent_router()
		)
	
	@crew
	def crew(self) -> Crew:
		"""Creates the ResearchTest crew"""
		return Crew(
			agents=self.agents,
			tasks=self.tasks,
			process=Process.sequential,
			verbose=True,
		)



