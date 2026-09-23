import subprocess

from .base import Worker


class CodexWorker(Worker):
    def run(self, prompt: str, project_path: str) -> str:
        result = subprocess.run(
            [
                "codex",
                "exec",
                "--sandbox",
                "danger-full-access",
                prompt,
            ],
            cwd=project_path,
            text=True,
            capture_output=True,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"Codex failed:\n{result.stderr}"
            )

        return result.stdout