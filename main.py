from agent.core import Agent
from agent.workers.claude import ClaudeWorker
from agent.workers.codex import CodexWorker


def main():
    import sys

    if len(sys.argv) < 3:
        print("Usage: python main.py <project_path> <task>")
        sys.exit(1)

    project_path = sys.argv[1]
    task = sys.argv[2]

    # worker = ClaudeWorker()
    worker = CodexWorker()

    agent = Agent(
        project_path=project_path,
        worker=worker,
    )

    state = agent.run(task)

    print("\n=== RESULT ===")
    print(f"Phase: {state.phase}")
    print(f"Attempts: {state.test_attempts}")

    print("\n=== WORKER ANALYSIS ===")
    print(state.context["worker_analysis"])


if __name__ == "__main__":
    main()