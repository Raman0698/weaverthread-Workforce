import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process

# Unlock the Vault
load_dotenv()

# ==========================================
# PHASE 1: THE HARDENED WORKFORCE
# ==========================================

architect = Agent(
    role='Senior Technical Product Manager',
    goal='Define a clear API contract and mandatory HTML IDs.',
    backstory='You ensure the Frontend and SDET are aligned. You must specify that the Register toggle button MUST have id="btnShowRegister" and the registration form inputs MUST have id="registerEmail", "registerUsername", and "registerPassword".',
    verbose=True,
    allow_delegation=False
)

backend_developer = Agent(
    role='Senior Backend Developer',
    goal='Write secure FastAPI/PostgreSQL code.',
    backstory='You implement JWT, bcrypt (8-72 chars), and parameterized SQL. You enable CORS for localhost:3000 and localhost:8000. Use asyncpg for database connections.',
    verbose=True,
    allow_delegation=False
)

frontend_developer = Agent(
    role='Senior Frontend UI/UX Developer',
    goal='Build the UI using ONLY the IDs provided by the Architect.',
    backstory='You create a single index.html using Tailwind CSS. CRITICAL: You MUST hide the registration form by default and show it ONLY when the button with id="btnShowRegister" is clicked.',
    verbose=True,
    allow_delegation=False
)

qa_engineer = Agent(
    role='Senior Full-Stack QA Engineer',
    goal='Verify security and logic.',
    backstory='Check for bcrypt 72-char limits and CORS headers. If the current code fixes previous issues, you MUST write "STATUS: APPROVED" at the very top of your report.',
    verbose=True,
    allow_delegation=False
)

automation_sdet = Agent(
    role='Senior Automation SDET',
    goal='Write a Playwright script that actually navigates the UI.',
    backstory='Your script MUST: 1. page.goto("http://localhost:3000") 2. page.click("#btnShowRegister") to reveal the form 3. page.fill the registration fields. OUTPUT RAW PYTHON CODE ONLY. DO NOT USE MARKDOWN BACKTICKS OR CODE BLOCKS.',
    verbose=True,
    allow_delegation=False
)

# ==========================================
# PHASE 2: THE DEFINED TASKS
# ==========================================

architect_task = Task(
    description='Create the technical spec for a Gym registration system. Include the mandatory HTML IDs: #btnShowRegister, #registerEmail, #registerUsername, #registerPassword.',
    expected_output='Markdown tech spec.',
    agent=architect,
    output_file='1_architect_blueprint.md'
)

backend_draft_task = Task(
    description='Write the FastAPI backend and SQL schema based on the blueprint.',
    expected_output='SQL and Python code.',
    agent=backend_developer,
    output_file='2_backend_draft_code.md'
)

frontend_draft_task = Task(
    description='Write index.html. Ensure the registration form is hidden until #btnShowRegister is clicked.',
    expected_output='HTML/JS code.',
    agent=frontend_developer,
    output_file='3_frontend_draft_code.md'
)

qa_review_task = Task(
    description='Review the LATEST code. If perfect, start with "STATUS: APPROVED".',
    expected_output='QA Report.',
    agent=qa_engineer,
    output_file='4_qa_feedback_report.md' 
)

backend_refactor_task = Task(
    description='Refine the backend based on QA feedback.',
    expected_output='Final SQL and Python code.',
    agent=backend_developer,
    output_file='5_final_backend_code.md'
)

frontend_refactor_task = Task(
    description='Refine index.html based on QA feedback.',
    expected_output='Final HTML code.',
    agent=frontend_developer,
    output_file='6_final_frontend_code.md'
)

e2e_automation_task = Task(
    description='Write the Playwright test script. Ensure it clicks the toggle button before filling the form. OUTPUT RAW CODE ONLY.',
    expected_output='Raw Python code (no markdown).',
    agent=automation_sdet,
    output_file='7_test_flow.py'
)

# ==========================================
# PHASE 3: EXECUTION LOOP
# ==========================================

print("--- Starting Weaverthread Factory: Phase 1 (Architect & Drafting) ---")
initial_crew = Crew(
    agents=[architect, backend_developer, frontend_developer],
    tasks=[architect_task, backend_draft_task, frontend_draft_task],
    process=Process.sequential 
)
initial_crew.kickoff()

max_iterations = 5
current_iteration = 1
is_approved = False

while current_iteration <= max_iterations and not is_approved:
    print(f"\n--- QA Review Loop: Iteration {current_iteration} ---")
    review_crew = Crew(
        agents=[qa_engineer, backend_developer, frontend_developer],
        tasks=[qa_review_task, backend_refactor_task, frontend_refactor_task],
        process=Process.sequential
    )
    review_crew.kickoff()
    
    with open('4_qa_feedback_report.md', 'r') as file:
        if "STATUS: APPROVED" in file.read():
            is_approved = True
            print("SUCCESS: Codebase approved.")
        else:
            print("REJECTED: Refactoring required.")
            current_iteration += 1

if is_approved:
    print("\n--- Final Phase: Generating UI Automation Test ---")
    e2e_crew = Crew(agents=[automation_sdet], tasks=[e2e_automation_task])
    e2e_crew.kickoff()
    print("\nFACTORY COMPLETE. Check your directory for 1-7 files.")