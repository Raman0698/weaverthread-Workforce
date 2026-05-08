import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai_tools import ScrapeWebsiteTool  # <-- 1. Import the specific tool

# Unlock the Vault
load_dotenv()

# ==========================================
# PHASE 1: FORGE THE WHITELISTED TOOLS
# ==========================================

# 2. Create the scoped tools. The agent cannot search outside of these specific URLs.
postgres_docs = ScrapeWebsiteTool(website_url='https://www.postgresql.org/docs/')
fastapi_docs = ScrapeWebsiteTool(website_url='https://fastapi.tiangolo.com/')

# ==========================================
# PHASE 2: DEFINE THE WORKFORCE (THE AGENTS)
# ==========================================

# Employee 1: The Product Manager
architect = Agent(
    role='Senior Technical Product Manager',
    goal='Break down business requirements into a highly detailed, step-by-step technical specification document.',
    backstory='You are the lead Architect at Weaverthread, an elite software agency. You never write actual code; instead, you write flawless, unambiguous instructions for developers. You are ruthless about security, efficiency, and scalable architecture.',
    verbose=True,
    allow_delegation=False,
    tools=[postgres_docs, fastapi_docs]  # <-- 3. Attach the restricted tools here
)

# Employee 2: The Developer
developer = Agent(
    role='Senior Full-Stack Developer',
    goal='Write clean, production-ready backend code based strictly on technical specifications.',
    backstory='You are the lead Backend Developer at Weaverthread. You take architectural blueprints and turn them into functional, secure, and highly optimized code. You specialize in Python, FastAPI, Next.js, and PostgreSQL.',
    verbose=True,
    allow_delegation=False
    # Notice we give the Developer NO tools. They must strictly follow the Architect's blueprint.
)

# ==========================================
# PHASE 3: DEFINE THE WORKFLOW (THE TASKS)
# ==========================================

architect_task = Task(
    description='Analyze this request: "We need a secure backend system for a local gym to manage memberships and class bookings." Use your tools to read the latest FastAPI and PostgreSQL documentation. Write a complete technical specification including the required database tables and API routes.',
    expected_output='A professional technical specification document formatted in Markdown.',
    agent=architect,
    output_file='architect_blueprint.md'
)

developer_task = Task(
    description='Read the technical specification provided by the Architect. Write the complete database schema (in SQL) and the foundational backend API routing code (in Python) to kickstart the project. Only build what is in the specification.',
    expected_output='Production-ready SQL and Python code blocks formatted in Markdown.',
    agent=developer,
    output_file='developer_backend_code.md'
)

# ==========================================
# PHASE 4: FORM THE COMPANY (THE CREW)
# ==========================================

weaverthread_crew = Crew(
    agents=[architect, developer],
    tasks=[architect_task, developer_task],
    process=Process.sequential 
)

# Execute the Pipeline
print("Weaverthread Assembly Line is Online. Architect is researching trusted sources...")
weaverthread_crew.kickoff()
print("Pipeline complete. Check your markdown files.")