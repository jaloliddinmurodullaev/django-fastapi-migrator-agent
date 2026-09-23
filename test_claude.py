from agent.workers.claude import ClaudeWorker

worker = ClaudeWorker()

result = worker.run(
    """
You are analyzing an existing software project.

Do not modify any files.

Inspect the project and identify:

1. Project architecture
2. Django applications
3. Main API structure
4. Authentication
5. Database configuration
6. External integrations
7. Background jobs
8. Tests
9. Docker/deployment setup
10. Important migration risks

Return a concise structured analysis.

Do not make any changes.
""",
    "/home/jaloliddin/Code/Skillup/skillcom",
)

print(result)