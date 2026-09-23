import json
from pathlib import Path

from agent.analyzer import ProjectAnalyzer
from agent.discovery import DjangoDiscovery
from agent.prompts import TEST_PROMPT
from agent.state import AgentState, Phase


class Agent:
    def __init__(self, project_path: str, worker):
        self.project_path = project_path
        self.worker = worker

    def run(self, task: str):
        state_file = Path(self.project_path) / ".agent" / "state.json"

        if state_file.exists():
            print("[AGENT] Resuming previous run...")
            state = AgentState.load(self.project_path)
        else:
            print("[AGENT] Starting new run...")
            state = AgentState(
                task=task,
                project_path=self.project_path,
            )
            state.save()

        while state.phase != Phase.COMPLETE:
            print(f"\n[AGENT] Phase: {state.phase.value}")

            if state.phase == Phase.ANALYZE:
                self.analyze(state)

            elif state.phase == Phase.PLAN:
                self.plan(state)

            elif state.phase == Phase.EXECUTE:
                self.execute(state)

            elif state.phase == Phase.TEST:
                self.test(state)

            elif state.phase == Phase.DEBUG:
                self.debug(state)

            elif state.phase == Phase.VERIFY:
                self.verify(state)

            elif state.phase == Phase.FAILED:
                print("[AGENT] Task failed.")
                break

            state.save()

        return state

    def analyze(self, state: AgentState):
        print("Analyzing project...")

        # 1. Deterministic analysis
        analyzer = ProjectAnalyzer()
        project_analysis = analyzer.analyze(self.project_path)

        state.context["project_analysis"] = project_analysis

        # 2. Django-specific discovery
        if "Django" in project_analysis["frameworks"]:
            discovery = DjangoDiscovery()
            django_analysis = discovery.discover(self.project_path)

            state.context["django"] = django_analysis

        # 3. LLM semantic analysis
        prompt = """
            You are analyzing an existing Django project.

            Do not modify any files.

            Understand the project deeply.

            Inspect:
            - project structure
            - Django configuration
            - installed applications
            - models
            - URLs
            - views
            - serializers
            - services
            - authentication
            - permissions
            - background jobs
            - database configuration
            - tests
            - Docker configuration
            - dependencies

            Identify:
            1. Architecture
            2. Main business domains
            3. API structure
            4. External integrations
            5. Important dependencies
            6. Potential migration risks

            Return a structured analysis.

            Do not make any changes.
        """

        print("Asking worker for semantic analysis...")

        worker_analysis = self.worker.run(
            prompt=prompt,
            project_path=self.project_path,
        )

        state.context["worker_analysis"] = worker_analysis

        state.phase = Phase.PLAN

    def plan(self, state: AgentState):
        print("Creating migration plan...")

        analysis = state.context.get("worker_analysis", "")

        prompt = f"""
            You are planning a Django to FastAPI migration.

            The project has already been analyzed.

            Here is the analysis:

            {analysis}

            Create a concrete, executable migration plan.

            Return ONLY valid JSON.
            Do not use markdown.
            Do not wrap the JSON in ```.

            The JSON must have exactly this structure:

            {{
            "steps": [
                {{
                "id": "0.1",
                "objective": "...",
                "affected_files": ["..."],
                "implementation": "...",
                "verification": ["..."]
                }}
            ]
            }}

            Rules:
            - Each step must be independently executable.
            - Steps must be ordered.
            - Preserve existing business behavior.
            - Preserve API behavior where practical.
            - Preserve authentication and permissions.
            - Preserve database models and relationships.
            - Preserve external integrations.
            - Include tests and verification.
            - Do not modify files while creating the plan.
            - Do not combine unrelated tasks into one step.
        """

        result = self.worker.run(
            prompt=prompt,
            project_path=self.project_path,
        )

        import json

        try:
            migration_plan = json.loads(result)
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"Worker returned invalid JSON plan:\n{result}"
            ) from e

        state.context["migration_plan"] = migration_plan

        print("\n=== MIGRATION PLAN ===")

        for step in migration_plan["steps"]:
            print(f'{step["id"]}: {step["objective"]}')

        state.phase = Phase.EXECUTE

    def execute(self, state: AgentState):
        plan = state.context["migration_plan"]

        prompt = f"""
            You are executing one specific step of a Django to FastAPI migration.

            This is the migration plan:

            {plan}

            The current step number is:

            {state.current_step}

            Execute ONLY this step.

            Rules:
            - Inspect the existing code before modifying it.
            - Work directly in the project files.
            - Actually implement the step.
            - Do not merely explain what should be done.
            - Do not start later steps.
            - Do not modify unrelated parts of the project.
            - Run the verification checks specified for this step.
            - If something fails, investigate and fix it.

            When finished, report:
            1. Step completed
            2. Files changed
            3. Tests/checks executed
            4. Results
            5. Any remaining issues
        """

        result = self.worker.run(
            prompt=prompt,
            project_path=self.project_path,
        )

        state.context["execution_result"] = result

        print("\n=== EXECUTION RESULT ===")
        print(result)

        state.phase = Phase.TEST

    def test(self, state: AgentState):
        print("Running tests...")

        step = state.context["migration_plan"]["steps"][state.current_step]

        prompt = f"""
            {TEST_PROMPT}

            Current migration step:

            ID:
            {step["id"]}

            Objective:
            {step["objective"]}

            Affected files:
            {step["affected_files"]}

            Implementation requirements:
            {step["implementation"]}

            Verification requirements:
            {step["verification"]}
        """

        result = self.worker.run(
            prompt=prompt,
            project_path=self.project_path,
        )

        try:
            test_result = json.loads(result)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Worker returned invalid test JSON:\n"
                f"{result}"
            ) from exc

        if test_result["status"] not in {"passed", "failed"}:
            raise RuntimeError(
                f"Invalid test status: {test_result['status']}"
            )

        state.context["test_result"] = test_result

        print("\n=== TEST RESULT ===")
        print(json.dumps(
            test_result,
            indent=2,
            ensure_ascii=False,
        ))

        if test_result["status"] == "passed":
            state.phase = Phase.VERIFY
        else:
            state.phase = Phase.DEBUG

    def debug(self, state: AgentState):
        print("Debugging failed step...")

        plan = state.context["migration_plan"]
        step = plan["steps"][state.current_step]
        test_result = state.context["test_result"]

        state.test_attempts += 1

        max_attempts = 3

        if state.test_attempts > max_attempts:
            print(
                f"[AGENT] Maximum debug attempts reached "
                f"({max_attempts})."
            )
            state.phase = Phase.FAILED
            return

        failures = test_result.get("failures", [])

        prompt = f"""
            You are debugging one failed step of a Django to FastAPI migration.

            Migration step:

            ID:
            {step["id"]}

            Objective:
            {step["objective"]}

            Affected files:
            {step["affected_files"]}

            Implementation requirements:
            {step["implementation"]}

            Verification requirements:
            {step["verification"]}

            The independent test phase failed.

            Test failures:
            {json.dumps(failures, indent=2, ensure_ascii=False)}

            Rules:
            - Inspect the actual project state before making changes.
            - Reproduce or investigate the failure.
            - Identify the root cause.
            - Fix the root cause.
            - Modify only files relevant to this migration step.
            - Do NOT start later migration steps.
            - Do NOT weaken or remove tests just to make them pass.
            - Do NOT change verification requirements to hide a failure.
            - After fixing the issue, run the relevant verification commands again.
            - Do not merely explain the solution. Actually modify the project.

            When finished, report:
            1. Root cause
            2. Changes made
            3. Files changed
            4. Commands executed
            5. Results
            6. Remaining issues
        """

        result = self.worker.run(
            prompt=prompt,
            project_path=self.project_path,
        )

        state.context["debug_result"] = result

        print("\n=== DEBUG RESULT ===")
        print(result)

        # Debugdan keyin aynan shu step yana test qilinadi.
        state.phase = Phase.TEST

    def verify(self, state: AgentState):
        print("Verifying result...")

        plan = state.context["migration_plan"]
        steps = plan["steps"]

        step = steps[state.current_step]
        test_result = state.context["test_result"]

        if test_result["status"] != "passed":
            raise RuntimeError(
                "Cannot verify a step with failed tests."
            )

        print(
            f"[AGENT] Step {step['id']} verified successfully."
        )

        state.current_step += 1

        state.test_attempts = 0

        if state.current_step >= len(steps):
            state.phase = Phase.COMPLETE
            print("[AGENT] All migration steps completed.")
        else:
            next_step = steps[state.current_step]

            print(
                f"[AGENT] Moving to next step: "
                f"{next_step['id']} - {next_step['objective']}"
            )

            state.phase = Phase.EXECUTE
