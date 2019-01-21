from abc import abstractmethod

from typing_extensions import Protocol


__all__ = ["Reader", "Writer", "ReaderWriter"]


class Reader(Protocol):
    @abstractmethod
    def read(self, i: int = -1):
        pass


class Writer(Protocol):
    @abstractmethod
    def write(self, content) -> int:
        pass


class ReaderWriter(Reader, Writer):
    pass
