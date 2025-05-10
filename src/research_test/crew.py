from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from tools.custom_tool import MacroeconomicTool, FundamentalAnalysisTool
from crewai_tools import SerperDevTool

llm = "gpt-3.5-turbo"

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
    		allow_delegation=False,
			llm=llm
		)

	@agent
	def fundamental(self) -> Agent:
		return Agent(
			config=self.agents_config['fundamental'],
			tools=[FundamentalAnalysisTool()],
			verbose=True,
    		allow_delegation=False,
			llm=llm
		)
	
	@agent
	def macro(self) -> Agent:
		return Agent(
			config=self.agents_config['macro'],
			tools=[MacroeconomicTool()],
			verbose=True,
			allow_delegation=False,
			llm=llm
		)
	
	@agent
	def reporter(self) -> Agent:
		return Agent(
			config=self.agents_config['reporter'],
			tools=[SerperDevTool()],
			verbose=True,
			allow_delegation=False,
			llm=llm
		)
	
	@task
	def journalist_task(self) -> Task:
		return Task(
			config=self.tasks_config['journalist_task'],
			agent=self.journalist()
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
	def reporter_task(self) -> Task:
		return Task(
			config=self.tasks_config['reporter_task'],
			agent=self.reporter(),
			context=[self.journalist_task(), self.fundamental_task(), self.macro_task()] 
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

