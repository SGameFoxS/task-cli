from enum import Enum, StrEnum, unique

__all__ = ("TaskStatusEnum", "MessageKind")


@unique
class TaskStatusEnum(StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"

    @property
    def label(self) -> str:
        return self.value.replace("_", " ").upper()


@unique
class MessageKind(Enum):
    INFO = "info"
    ERROR = "error"

    @property
    def label(self) -> str:
        return self.value.upper()
