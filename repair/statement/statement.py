from abc import ABC, abstractmethod

class Statement(ABC):

    @abstractmethod
    def act(self):
        pass
