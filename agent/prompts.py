TEST_PROMPT = """
You are testing one completed step of a Django to FastAPI migration.

The implementation step has already been executed.

Your job is to independently verify the implementation.

Rules:
- Do NOT modify any files.
- Inspect the changes made by the previous step.
- Run the relevant tests and verification commands.
- Prefer focused tests related to the current step.
- If appropriate, also run static checks or other project-specific validation.
- Do not fix failures yourself.
- If a command fails, capture the actual error.
- Do not assume tests passed without running them.

Return ONLY valid JSON.
Do not wrap the JSON in markdown fences.

JSON schema:

{
  "status": "passed" | "failed",
  "commands": [
    "command that was executed"
  ],
  "failures": [
    {
      "command": "failed command",
      "error": "relevant error output"
    }
  ],
  "summary": "short summary"
}
"""