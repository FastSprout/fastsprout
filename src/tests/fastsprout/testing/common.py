from threading import Event
from typing import Self

from testcontainers.core.container import DockerContainer


class RecordedContainer(DockerContainer):
    def __init__(self, *, fail: bool = False, blocked: bool = False) -> None:
        self.calls: list[str] = []
        self.fail = fail
        self.started = Event()
        self.release = Event()
        if not blocked:
            self.release.set()

    def start(self) -> Self:
        self.calls.append("start")
        self.started.set()
        if not self.release.wait(5):
            raise TimeoutError("Container startup was not released")
        if self.fail:
            raise RuntimeError("Startup failed")
        return self

    def stop(self, force: bool = True, delete_volume: bool = True) -> None:
        self.calls.append("stop")
