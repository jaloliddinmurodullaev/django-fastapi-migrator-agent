from pathlib import Path


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


class DjangoDiscovery:
    def discover(self, project_path: str) -> dict:
        root = Path(project_path).resolve()

        manage_py = self.find_manage_py(root)

        if not manage_py:
            raise RuntimeError("Django manage.py not found")

        source_root = manage_py.parent

        return {
            "manage_py": str(manage_py.relative_to(root)),
            "source_root": str(source_root.relative_to(root)),
            "settings": self.find_settings(source_root),
            "urls": self.find_urls(source_root),
            "apps": self.find_apps(source_root),
        }

    def is_ignored(self, path: Path) -> bool:
        return any(
            part in IGNORED_DIRS
            for part in path.parts
        )

    def find_manage_py(self, root: Path) -> Path | None:
        for path in root.rglob("manage.py"):
            if not self.is_ignored(path):
                return path

        return None

    def find_settings(self, source_root: Path) -> list[str]:
        result = []

        for path in source_root.rglob("settings.py"):
            if not self.is_ignored(path):
                result.append(
                    str(path.relative_to(source_root))
                )

        return sorted(result)

    def find_urls(self, source_root: Path) -> list[str]:
        result = []

        for path in source_root.rglob("urls.py"):
            if not self.is_ignored(path):
                result.append(
                    str(path.relative_to(source_root))
                )

        return sorted(result)

    def find_apps(self, source_root: Path) -> list[str]:
        result = []

        for path in source_root.rglob("apps.py"):
            if self.is_ignored(path):
                continue

            result.append(
                str(path.parent.relative_to(source_root))
            )

        return sorted(result)