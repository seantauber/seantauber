from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    """
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def execute(self, *args, **kwargs):
        pass
