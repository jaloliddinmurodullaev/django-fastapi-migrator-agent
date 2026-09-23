from pathlib import Path

from tools.filesystem import get_project_structure

IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
}

class ProjectAnalyzer:

    def analyze(self, project_path: str) -> dict:
        root = Path(project_path).resolve()

        structure = get_project_structure(project_path)

        return {
            "project_path": str(root),
            "structure": structure,
            "languages": self.detect_languages(root),
            "frameworks": self.detect_frameworks(root),
            "important_files": self.find_important_files(root),
        }

    def detect_languages(self, root: Path) -> list[str]:
        extensions = set()

        for path in root.rglob("*"):
            if not path.is_file():
                continue

            if any(part in {".git", ".venv", "venv", "node_modules"} for part in path.parts):
                continue

            if path.suffix:
                extensions.add(path.suffix)

        mapping = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".go": "Go",
            ".java": "Java",
            ".rs": "Rust",
        }

        return sorted(
            mapping[ext]
            for ext in extensions
            if ext in mapping
        )

    def detect_frameworks(self, root: Path) -> list[str]:
        frameworks = []

        # Django project detection
        manage_files = list(root.rglob("manage.py"))

        manage_files = [
            path
            for path in manage_files
            if not self.is_ignored(path, root)
        ]

        if manage_files:
            frameworks.append("Django")

        # Dependency files
        dependency_files = [
            root / "requirements.txt",
            root / "pyproject.toml",
            root / "Pipfile",
            root / "Pipfile.lock",
        ]

        dependency_content = ""

        for path in dependency_files:
            if path.exists() and path.is_file():
                dependency_content += (
                    path.read_text(
                        encoding="utf-8",
                        errors="ignore",
                    ).lower()
                )

        if "fastapi" in dependency_content:
            frameworks.append("FastAPI")

        if "django" in dependency_content and "Django" not in frameworks:
            frameworks.append("Django")

        return frameworks

    def is_ignored(self, path: Path, root: Path) -> bool:
        relative = path.relative_to(root)

        return any(
            part in IGNORED_DIRS
            for part in relative.parts
        )

    def find_important_files(self, root: Path) -> list[str]:
        names = {
            "manage.py",
            "requirements.txt",
            "pyproject.toml",
            "Pipfile",
            "Dockerfile",
            "docker-compose.yml",
            "docker-compose.yaml",
            ".env.example",
            "README.md",
        }

        result = []

        for path in root.rglob("*"):
            if not path.is_file():
                continue

            if self.is_ignored(path, root):
                continue

            if path.name in names:
                result.append(str(path.relative_to(root)))

        return sorted(result)
