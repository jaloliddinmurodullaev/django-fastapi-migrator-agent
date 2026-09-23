import subprocess

from agent.workers.base import Worker


class ClaudeWorker(Worker):

    def run(self, prompt: str, project_path: str) -> str:
        result = subprocess.run(
            [
                "claude",
                "-p",
                prompt,
                "--output-format",
                "text",
                "--permission-mode",
                "bypassPermissions",
            ],
            cwd=project_path,
            text=True,
            capture_output=True,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"Claude failed:\n{result.stderr}"
            )

        return result.stdout