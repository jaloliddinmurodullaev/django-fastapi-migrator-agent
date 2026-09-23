from pathlib import Path

IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    ".pytest_cache",
    ".mypy_cache",
}


def get_project_structure(project_path: str, max_depth: int = 4) -> list[str]:
    root = Path(project_path).resolve()

    if not root.exists():
        raise FileNotFoundError(f"Project does not exist: {root}")

    result = []

    def walk(path: Path, depth: int):
        if depth > max_depth:
            return

        for item in sorted(path.iterdir()):
            if item.name in IGNORED_DIRS:
                continue

            relative = item.relative_to(root)

            if item.is_dir():
                result.append(f"{relative}/")
                walk(item, depth + 1)
            else:
                result.append(str(relative))

    walk(root, 0)

    return result