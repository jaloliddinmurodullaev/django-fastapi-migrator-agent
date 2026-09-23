from abc import ABC, abstractmethod


class Worker(ABC):

    @abstractmethod
    def run(self, prompt: str, project_path: str) -> str:
        pass