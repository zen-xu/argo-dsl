from typing import Callable
from typing import Type

from .template import ScriptTemplate


def script(func: Callable[..., None]) -> Type[ScriptTemplate]:
    ...


def bash(func: Callable[..., None]) -> Type[ScriptTemplate]:
    ...


def python(func: Callable[..., None]) -> Type[ScriptTemplate]:
    ...


def image(image_name: str) -> Callable[[Type[ScriptTemplate]], Type[ScriptTemplate]]:
    def wrapper(kls: Type[ScriptTemplate]) -> Type[ScriptTemplate]:
        ...

    return wrapper
