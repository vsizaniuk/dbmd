from abc import ABC, abstractmethod


class Exporter(ABC):

    @abstractmethod
    def __init__(self):
        ...

